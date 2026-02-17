"""Service for session participants: heartbeat, list, resolve participant."""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session as DBSession

from core.auth import verify_token
from models.session_participant import SessionParticipant
from repositories.session_repository import SessionRepository
from repositories.session_participant_repository import (
    SessionParticipantRepository,
    HEARTBEAT_ACTIVE_SECONDS,
)
from repositories.workspace_repository import WorkspaceRepository
from repositories.guest_email_verification_repository import GuestEmailVerificationRepository
import structlog

logger = structlog.get_logger(__name__)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


class SessionParticipantService:
    """Business logic for participants: resolve, heartbeat, list."""

    @staticmethod
    def resolve_participant(
        db: DBSession,
        passcode: str,
        auth_token: Optional[str] = None,
        participant_token_from_body: Optional[str] = None,
    ) -> Tuple[SessionParticipant, Any]:
        """
        Resolve participant from token(s). Returns (participant, session).
        Tries: auth_token (Authorization) first, then participant_token_from_body.
        Raises ValueError if not found or invalid.
        """
        session = SessionRepository.get_by_passcode(db, passcode)
        if not session:
            raise ValueError("Session not found")

        token = auth_token or participant_token_from_body
        if not token:
            raise ValueError("Missing participant token or Authorization")

        payload = verify_token(token)
        if not payload:
            raise ValueError("Invalid or expired token")

        token_type = payload.get("type")

        if token_type == "session_participant":
            participant_id_str = payload.get("sub")
            session_id_from_token = payload.get("session_id")
            if not participant_id_str or session_id_from_token != session.id:
                raise ValueError("Invalid participant token for this session")
            try:
                participant_id = int(participant_id_str)
            except (ValueError, TypeError):
                raise ValueError("Invalid participant token")
            participant = SessionParticipantRepository.get_by_id(db, participant_id)
            if not participant or participant.session_id != session.id:
                raise ValueError("Participant not found")
            return participant, session

        if token_type == "session_guest":
            email = payload.get("sub")
            if not email or not isinstance(email, str):
                raise ValueError("Invalid guest token")
            email = _normalize_email(email)
            verification = GuestEmailVerificationRepository.get_by_email(db, email)
            if not verification:
                raise ValueError("Guest verification not found")
            participant = SessionParticipantRepository.get_by_session_and_guest_email(
                db, session.id, email
            )
            if not participant:
                raise ValueError("Participant not found (join first)")
            return participant, session

        # Regular user token (no type or type not session_*)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise ValueError("Invalid token")
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise ValueError("Invalid token")
        participant = SessionParticipantRepository.get_by_session_and_user(
            db, session.id, user_id
        )
        if not participant:
            raise ValueError("Participant not found (join first)")
        return participant, session

    @staticmethod
    def heartbeat(db: DBSession, participant_id: int) -> None:
        """Update last_heartbeat_at for participant. Commits."""
        SessionParticipantRepository.update_heartbeat(db, participant_id)
        db.commit()

    @staticmethod
    def list_participants(db: DBSession, session_id: int) -> List[Dict[str, Any]]:
        """List participants with display_name, participant_type, is_active."""
        participants = SessionParticipantRepository.get_by_session_id(db, session_id)
        threshold = datetime.now(timezone.utc) - timedelta(seconds=HEARTBEAT_ACTIVE_SECONDS)
        result = []
        for p in participants:
            is_active = p.last_heartbeat_at is not None and p.last_heartbeat_at >= threshold
            result.append({
                "id": p.id,
                "display_name": p.display_name,
                "participant_type": p.participant_type,
                "is_active": is_active,
            })
        return result

    @staticmethod
    def get_active_count(db: DBSession, session_id: int) -> int:
        """Count active participants (heartbeat within threshold)."""
        return SessionParticipantRepository.count_active(db, session_id)
