"""SessionQuestionMessage repository."""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session as DBSession, joinedload
from sqlalchemy import desc

from models.session_question_message import SessionQuestionMessage, SessionQuestionMessageLike


class SessionQuestionMessageRepository:
    """Repository for session question messages."""

    @staticmethod
    def get_by_id(db: DBSession, message_id: int) -> Optional[SessionQuestionMessage]:
        """Get message by ID."""
        return db.query(SessionQuestionMessage).filter(
            SessionQuestionMessage.id == message_id,
            SessionQuestionMessage.is_deleted == False,
        ).first()

    @staticmethod
    def list_by_module(
        db: DBSession,
        session_module_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SessionQuestionMessage]:
        """List messages for module, sorted by likes_count DESC, created_at ASC.
        Returns top-level messages only (parent_id is NULL). Children via parent relationship.
        """
        return db.query(SessionQuestionMessage).options(
            joinedload(SessionQuestionMessage.participant),
        ).filter(
            SessionQuestionMessage.session_module_id == session_module_id,
            SessionQuestionMessage.is_deleted == False,
            SessionQuestionMessage.parent_id == None,
        ).order_by(
            desc(SessionQuestionMessage.pinned_at).nulls_last(),
            desc(SessionQuestionMessage.likes_count),
            SessionQuestionMessage.created_at,
        ).limit(limit).offset(offset).all()

    @staticmethod
    def get_children(db: DBSession, parent_id: int) -> List[SessionQuestionMessage]:
        """Get child messages (replies) for a parent."""
        return db.query(SessionQuestionMessage).options(
            joinedload(SessionQuestionMessage.participant),
        ).filter(
            SessionQuestionMessage.parent_id == parent_id,
            SessionQuestionMessage.is_deleted == False,
        ).order_by(SessionQuestionMessage.created_at).all()

    @staticmethod
    def count_top_level_by_module(db: DBSession, session_module_id: int) -> int:
        """Count top-level (parent_id is None) non-deleted messages in module."""
        return db.query(SessionQuestionMessage).filter(
            SessionQuestionMessage.session_module_id == session_module_id,
            SessionQuestionMessage.is_deleted == False,
            SessionQuestionMessage.parent_id == None,
        ).count()

    @staticmethod
    def get_last_by_participant_in_module(
        db: DBSession, session_module_id: int, participant_id: int
    ) -> Optional[SessionQuestionMessage]:
        """Get most recent message by participant in module (for cooldown)."""
        return db.query(SessionQuestionMessage).filter(
            SessionQuestionMessage.session_module_id == session_module_id,
            SessionQuestionMessage.participant_id == participant_id,
            SessionQuestionMessage.is_deleted == False,
        ).order_by(desc(SessionQuestionMessage.created_at)).first()

    @staticmethod
    def create(
        db: DBSession,
        session_module_id: int,
        participant_id: int,
        content: str,
        parent_id: Optional[int] = None,
        is_anonymous: bool = False,
    ) -> SessionQuestionMessage:
        """Create message (no commit)."""
        msg = SessionQuestionMessage(
            session_module_id=session_module_id,
            participant_id=participant_id,
            content=content,
            parent_id=parent_id,
            is_anonymous=is_anonymous,
        )
        db.add(msg)
        return msg

    @staticmethod
    def add_like(db: DBSession, message_id: int, participant_id: int) -> bool:
        """Add like if not already present. Idempotent. Returns True if added, False if already liked.
        Caller must increment likes_count and commit.
        """
        existing = db.query(SessionQuestionMessageLike).filter(
            SessionQuestionMessageLike.message_id == message_id,
            SessionQuestionMessageLike.participant_id == participant_id,
        ).first()
        if existing:
            return False
        like = SessionQuestionMessageLike(
            message_id=message_id,
            participant_id=participant_id,
        )
        db.add(like)
        return True

    @staticmethod
    def remove_like(db: DBSession, message_id: int, participant_id: int) -> bool:
        """Remove like if present. Returns True if removed, False if it did not exist."""
        existing = db.query(SessionQuestionMessageLike).filter(
            SessionQuestionMessageLike.message_id == message_id,
            SessionQuestionMessageLike.participant_id == participant_id,
        ).first()
        if not existing:
            return False
        db.delete(existing)
        return True

    @staticmethod
    def is_liked_by(db: DBSession, message_id: int, participant_id: int) -> bool:
        """Check if participant has liked a message."""
        existing = db.query(SessionQuestionMessageLike).filter(
            SessionQuestionMessageLike.message_id == message_id,
            SessionQuestionMessageLike.participant_id == participant_id,
        ).first()
        return existing is not None

    @staticmethod
    def update_is_answered(db: DBSession, message_id: int, is_answered: bool) -> Optional[SessionQuestionMessage]:
        """Update is_answered flag (no commit)."""
        msg = SessionQuestionMessageRepository.get_by_id(db, message_id)
        if msg:
            msg.is_answered = is_answered
        return msg

    @staticmethod
    def update_pinned_at(
        db: DBSession, message_id: int, pinned_at: Optional[datetime]
    ) -> Optional[SessionQuestionMessage]:
        """Update pinned_at (no commit). pinned_at=None to unpin."""
        msg = SessionQuestionMessageRepository.get_by_id(db, message_id)
        if msg:
            msg.pinned_at = pinned_at
        return msg

    @staticmethod
    def soft_delete(db: DBSession, message_id: int) -> Optional[SessionQuestionMessage]:
        """Soft delete message (no commit)."""
        msg = SessionQuestionMessageRepository.get_by_id(db, message_id)
        if msg:
            msg.is_deleted = True
            msg.deleted_at = datetime.now(timezone.utc)
        return msg
