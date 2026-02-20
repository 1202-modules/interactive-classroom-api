"""SessionParticipant repository."""
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session as DBSession

from models.session_participant import SessionParticipant, ParticipantType


HEARTBEAT_ACTIVE_SECONDS = 30


class SessionParticipantRepository:
    """Repository for session participant operations."""

    @staticmethod
    def get_by_id(db: DBSession, participant_id: int) -> Optional[SessionParticipant]:
        """Get participant by ID."""
        return db.query(SessionParticipant).filter(
            SessionParticipant.id == participant_id,
            SessionParticipant.is_deleted == False
        ).first()

    @staticmethod
    def get_by_session_and_user(db: DBSession, session_id: int, user_id: int) -> Optional[SessionParticipant]:
        """Get participant by session and user_id (for registered)."""
        return db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == user_id,
            SessionParticipant.is_deleted == False
        ).first()

    @staticmethod
    def get_by_session_and_guest_email(db: DBSession, session_id: int, email: str) -> Optional[SessionParticipant]:
        """Get participant by session and guest_email (for email_code)."""
        return db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.guest_email == email,
            SessionParticipant.is_deleted == False
        ).first()

    @staticmethod
    def get_by_session_id(db: DBSession, session_id: int) -> List[SessionParticipant]:
        """Get all participants for a session."""
        return db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.is_deleted == False
        ).order_by(SessionParticipant.created_at).all()

    @staticmethod
    def count_active(db: DBSession, session_id: int) -> int:
        """Count participants with last_heartbeat_at within HEARTBEAT_ACTIVE_SECONDS."""
        threshold = datetime.now(timezone.utc) - timedelta(seconds=HEARTBEAT_ACTIVE_SECONDS)
        return db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.is_deleted == False,
            SessionParticipant.last_heartbeat_at >= threshold
        ).count()

    @staticmethod
    def count_all(db: DBSession, session_id: int) -> int:
        """Count all participants for a session (not deleted)."""
        return db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.is_deleted == False
        ).count()

    @staticmethod
    def create(
        db: DBSession,
        session_id: int,
        participant_type: str,
        user_id: Optional[int] = None,
        guest_email: Optional[str] = None,
        organization_id: Optional[int] = None,
        display_name: Optional[str] = None,
        anonymous_slug: Optional[str] = None,
    ) -> SessionParticipant:
        """Create participant (no commit)."""
        p = SessionParticipant(
            session_id=session_id,
            participant_type=participant_type,
            user_id=user_id,
            guest_email=guest_email,
            organization_id=organization_id,
            display_name=display_name,
            anonymous_slug=anonymous_slug,
        )
        db.add(p)
        return p

    @staticmethod
    def update_heartbeat(db: DBSession, participant_id: int) -> Optional[SessionParticipant]:
        """Update last_heartbeat_at for participant (no commit)."""
        p = SessionParticipantRepository.get_by_id(db, participant_id)
        if p:
            p.last_heartbeat_at = datetime.now(timezone.utc)
        return p

    @staticmethod
    def update_banned(db: DBSession, participant_id: int, is_banned: bool) -> Optional[SessionParticipant]:
        """Update is_banned for participant (no commit)."""
        p = SessionParticipantRepository.get_by_id(db, participant_id)
        if p:
            p.is_banned = is_banned
        return p

    @staticmethod
    def soft_delete(db: DBSession, participant_id: int) -> Optional[SessionParticipant]:
        """Soft-delete participant (no commit). Sets is_deleted=True, deleted_at=now. Token becomes invalid."""
        p = SessionParticipantRepository.get_by_id(db, participant_id)
        if p:
            p.is_deleted = True
            p.deleted_at = datetime.now(timezone.utc)
        return p
