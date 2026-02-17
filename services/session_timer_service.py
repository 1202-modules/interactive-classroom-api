"""Service for Timer module: state, start, pause, resume, reset."""
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session as DBSession

from models.workspace_module import ModuleType
from repositories.session_module_repository import SessionModuleRepository
from repositories.session_repository import SessionRepository
from repositories.workspace_repository import WorkspaceRepository
from repositories.session_module_timer_state_repository import SessionModuleTimerStateRepository
from utils.module_settings import get_timer_settings
import structlog

logger = structlog.get_logger(__name__)


def _get_timer_options(module) -> dict:
    """Get Timer module settings with defaults."""
    return get_timer_settings(module.settings)


def _format_timer_response(state, opts: dict) -> dict:
    """Build timer state response dict."""
    return {
        "is_paused": state.is_paused if state else True,
        "end_at": state.end_at.isoformat() if state and state.end_at else None,
        "remaining_seconds": state.remaining_seconds if state else None,
        "sound_notification_enabled": opts.get("sound_notification_enabled", True),
    }


class SessionTimerService:
    """Business logic for Timer module."""

    @staticmethod
    def _check_lecturer_access(db: DBSession, session_id: int, user_id: int) -> None:
        """Verify user owns session workspace. Raises ValueError if not authorized."""
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise ValueError("Session not found")
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Not authorized")

    @staticmethod
    def _validate_timer_module(db: DBSession, session_module_id: int, session_id: int) -> None:
        """Ensure module exists, is Timer type, and belongs to session."""
        module = SessionModuleRepository.get_by_id(db, session_module_id)
        if not module or module.is_deleted:
            raise ValueError("Module not found")
        if module.session_id != session_id:
            raise ValueError("Module not in this session")
        if module.module_type != ModuleType.TIMER.value:
            raise ValueError("Module is not a Timer module")

    @staticmethod
    def get_state(
        db: DBSession,
        passcode: str,
        module_id: int,
    ) -> Dict[str, Any]:
        """Get timer state for participants/lecturer. No auth required for by-passcode."""
        session = SessionRepository.get_by_passcode(db, passcode)
        if not session:
            raise ValueError("Session not found")
        SessionTimerService._validate_timer_module(db, module_id, session.id)

        module = SessionModuleRepository.get_by_id(db, module_id)
        opts = _get_timer_options(module) if module else {}
        state = SessionModuleTimerStateRepository.get_by_module(db, module_id)
        return _format_timer_response(state, opts)

    @staticmethod
    def start(db: DBSession, session_id: int, user_id: int, module_id: int) -> Dict[str, Any]:
        """Lecturer: start timer. Commits."""
        SessionTimerService._check_lecturer_access(db, session_id, user_id)
        SessionTimerService._validate_timer_module(db, module_id, session_id)
        module = SessionModuleRepository.get_by_id(db, module_id)
        opts = _get_timer_options(module)
        duration = opts.get("duration_seconds") or 60
        if duration <= 0:
            duration = 60

        SessionModuleTimerStateRepository.start(db, module_id, duration)
        db.commit()
        state = SessionModuleTimerStateRepository.get_by_module(db, module_id)
        logger.info("session_timer_started", module_id=module_id, duration=duration)
        return _format_timer_response(state, opts)

    @staticmethod
    def pause(
        db: DBSession,
        session_id: int,
        user_id: int,
        module_id: int,
        remaining_seconds: int,
    ) -> Dict[str, Any]:
        """Lecturer: pause timer. Commits."""
        SessionTimerService._check_lecturer_access(db, session_id, user_id)
        SessionTimerService._validate_timer_module(db, module_id, session_id)

        state = SessionModuleTimerStateRepository.pause(db, module_id, remaining_seconds)
        if not state:
            raise ValueError("Timer state not found (start timer first)")
        module = SessionModuleRepository.get_by_id(db, module_id)
        opts = _get_timer_options(module) if module else {}
        db.commit()
        db.refresh(state)
        return _format_timer_response(state, opts)

    @staticmethod
    def resume(db: DBSession, session_id: int, user_id: int, module_id: int) -> Dict[str, Any]:
        """Lecturer: resume timer. Commits."""
        SessionTimerService._check_lecturer_access(db, session_id, user_id)
        SessionTimerService._validate_timer_module(db, module_id, session_id)

        state = SessionModuleTimerStateRepository.resume(db, module_id)
        if not state:
            raise ValueError("Timer state not found or not paused")
        module = SessionModuleRepository.get_by_id(db, module_id)
        opts = _get_timer_options(module) if module else {}
        db.commit()
        db.refresh(state)
        return _format_timer_response(state, opts)

    @staticmethod
    def reset(db: DBSession, session_id: int, user_id: int, module_id: int) -> Dict[str, Any]:
        """Lecturer: reset timer. Commits."""
        SessionTimerService._check_lecturer_access(db, session_id, user_id)
        SessionTimerService._validate_timer_module(db, module_id, session_id)

        state = SessionModuleTimerStateRepository.reset(db, module_id)
        module = SessionModuleRepository.get_by_id(db, module_id)
        opts = _get_timer_options(module) if module else {}
        resp = _format_timer_response(state, opts)
        if state:
            db.commit()
            db.refresh(state)
        return resp
