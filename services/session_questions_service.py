"""Service for Questions module: messages, likes, lecturer actions."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session as DBSession

from models.workspace_module import ModuleType
from repositories.session_module_repository import SessionModuleRepository
from repositories.session_repository import SessionRepository
from repositories.workspace_repository import WorkspaceRepository
from repositories.session_question_message_repository import SessionQuestionMessageRepository
from utils.module_settings import get_questions_settings, get_questions_max_length
import structlog

logger = structlog.get_logger(__name__)


def _serialize_message(msg, children: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """Serialize message for API response."""
    author = msg.participant.display_name if msg.participant else None
    return {
        "id": msg.id,
        "session_module_id": msg.session_module_id,
        "participant_id": msg.participant_id,
        "author_display_name": author,
        "parent_id": msg.parent_id,
        "content": msg.content,
        "likes_count": msg.likes_count,
        "is_answered": msg.is_answered,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
        "children": children or [],
    }


class SessionQuestionsService:
    """Business logic for Questions module."""

    @staticmethod
    def _validate_questions_module(db: DBSession, session_module_id: int, session_id: int):
        """Ensure module exists, is Questions type, and belongs to session. Returns module."""
        module = SessionModuleRepository.get_by_id(db, session_module_id)
        if not module or module.is_deleted:
            raise ValueError("Module not found")
        if module.session_id != session_id:
            raise ValueError("Module not in this session")
        if module.module_type != ModuleType.QUESTIONS.value:
            raise ValueError("Module is not a Questions module")
        return module

    @staticmethod
    def list_messages(
        db: DBSession,
        passcode: str,
        module_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List messages for Questions module. Caller must be participant (validated in endpoint)."""
        session = SessionRepository.get_by_passcode(db, passcode)
        if not session:
            raise ValueError("Session not found")
        module = SessionQuestionsService._validate_questions_module(db, module_id, session.id)
        opts = get_questions_settings(module.settings)

        messages = SessionQuestionMessageRepository.list_by_module(db, module_id, limit=limit, offset=offset)
        result = []
        for msg in messages:
            children = SessionQuestionMessageRepository.get_children(db, msg.id)
            result.append(_serialize_message(
                msg,
                children=[_serialize_message(c) for c in children],
            ))
        return {
            "messages": result,
            "settings": {
                "likes_enabled": opts["likes_enabled"],
                "allow_participant_answers": opts["allow_participant_answers"],
                "length_limit_mode": opts["length_limit_mode"],
                "max_length": get_questions_max_length(opts),
            },
        }

    @staticmethod
    def create_message(
        db: DBSession,
        passcode: str,
        module_id: int,
        participant_id: int,
        content: str,
        parent_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create message. Commits."""
        session = SessionRepository.get_by_passcode(db, passcode)
        if not session:
            raise ValueError("Session not found")
        module = SessionQuestionsService._validate_questions_module(db, module_id, session.id)
        opts = get_questions_settings(module.settings)

        content = (content or "").strip()
        if not content:
            raise ValueError("Content is required")

        max_len = get_questions_max_length(opts)
        if len(content) > max_len:
            raise ValueError(f"Message exceeds maximum length ({max_len} characters)")

        if parent_id is not None and not opts["allow_participant_answers"]:
            raise ValueError("Participant answers are disabled for this module")

        if parent_id is None and opts["max_questions_total"] is not None:
            count = SessionQuestionMessageRepository.count_top_level_by_module(db, module_id)
            if count >= opts["max_questions_total"]:
                raise ValueError("Maximum number of questions reached")

        if opts["cooldown_enabled"] and opts["cooldown_seconds"] > 0:
            last = SessionQuestionMessageRepository.get_last_by_participant_in_module(
                db, module_id, participant_id
            )
            if last and last.created_at:
                elapsed = (datetime.now(timezone.utc) - last.created_at).total_seconds()
                if elapsed < opts["cooldown_seconds"]:
                    wait = int(opts["cooldown_seconds"] - elapsed)
                    raise ValueError(f"Please wait {wait} seconds before posting again")

        msg = SessionQuestionMessageRepository.create(
            db, module_id, participant_id, content, parent_id
        )
        db.commit()
        db.refresh(msg)
        logger.info("session_question_message_created", message_id=msg.id, module_id=module_id)
        return _serialize_message(msg)

    @staticmethod
    def add_like(
        db: DBSession,
        passcode: str,
        module_id: int,
        message_id: int,
        participant_id: int,
    ) -> Dict[str, Any]:
        """Add like (idempotent). Commits."""
        session = SessionRepository.get_by_passcode(db, passcode)
        if not session:
            raise ValueError("Session not found")
        module = SessionQuestionsService._validate_questions_module(db, module_id, session.id)
        opts = get_questions_settings(module.settings)
        if not opts["likes_enabled"]:
            raise ValueError("Likes are disabled for this module")

        msg = SessionQuestionMessageRepository.get_by_id(db, message_id)
        if not msg or msg.session_module_id != module_id:
            raise ValueError("Message not found")

        added = SessionQuestionMessageRepository.add_like(db, message_id, participant_id)
        if added:
            msg.likes_count += 1
        db.commit()
        db.refresh(msg)
        return {"likes_count": msg.likes_count}

    @staticmethod
    def lecturer_patch_message(
        db: DBSession,
        session_id: int,
        user_id: int,
        module_id: int,
        message_id: int,
        is_answered: Optional[bool] = None,
        delete: bool = False,
    ) -> Dict[str, Any]:
        """Lecturer: set is_answered or soft delete. Commits."""
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise ValueError("Session not found")
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Not authorized")

        SessionQuestionsService._validate_questions_module(db, module_id, session_id)

        msg = SessionQuestionMessageRepository.get_by_id(db, message_id)
        if not msg or msg.session_module_id != module_id:
            raise ValueError("Message not found")

        if delete:
            SessionQuestionMessageRepository.soft_delete(db, message_id)
            db.commit()
            return {"deleted": True}

        if is_answered is not None:
            SessionQuestionMessageRepository.update_is_answered(db, message_id, is_answered)
        db.commit()
        db.refresh(msg)
        return _serialize_message(msg)
