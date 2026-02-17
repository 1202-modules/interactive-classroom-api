"""Service for session join (all entry modes)."""
import secrets
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session as DBSession

from core.auth import create_participant_token
from core.config import settings as app_settings
from models.session_participant import ParticipantType
from repositories.session_repository import SessionRepository
from repositories.workspace_repository import WorkspaceRepository
from repositories.session_participant_repository import SessionParticipantRepository
from repositories.guest_email_verification_repository import GuestEmailVerificationRepository
from repositories.user_repository import UserRepository
import structlog

logger = structlog.get_logger(__name__)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _generate_anonymous_slug() -> str:
    return app_settings.ANONYMOUS_SLUG_PREFIX + secrets.token_hex(8)


class SessionJoinService:
    """Business logic for joining a session (anonymous, registered, guest, sso)."""

    @staticmethod
    def _get_merged_settings(db: DBSession, session) -> Dict[str, Any]:
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        template_settings = workspace.template_settings or {} if workspace else {}
        return SessionRepository.get_merged_settings(session, template_settings)

    @staticmethod
    def _check_entry_mode(merged: Dict[str, Any], expected: str) -> None:
        mode = merged.get("participant_entry_mode", "anonymous")
        if mode != expected:
            raise ValueError(f"Session is not in {expected} entry mode (current: {mode})")

    @staticmethod
    def _check_max_participants(db: DBSession, session_id: int, merged: Dict[str, Any]) -> None:
        max_p = merged.get("max_participants")
        if max_p is not None:
            count = len(SessionParticipantRepository.get_by_session_id(db, session_id))
            if count >= max_p:
                raise ValueError("Maximum participants reached")

    @staticmethod
    def join_anonymous(
        db: DBSession,
        passcode: str,
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create anonymous participant, return participant_token. Commits."""
        session = SessionRepository.get_by_passcode(db, passcode)
        if not session:
            raise ValueError("Session not found")
        merged = SessionJoinService._get_merged_settings(db, session)
        SessionJoinService._check_entry_mode(merged, "anonymous")
        SessionJoinService._check_max_participants(db, session.id, merged)

        slug = _generate_anonymous_slug()
        disp = (display_name or "").strip() or f"{app_settings.ANONYMOUS_DISPLAY_NAME_PREFIX}{secrets.token_hex(4)[:4]}"
        participant = SessionParticipantRepository.create(
            db,
            session_id=session.id,
            participant_type=ParticipantType.ANONYMOUS.value,
            display_name=disp,
            anonymous_slug=slug,
        )
        db.commit()
        db.refresh(participant)

        token = create_participant_token(participant.id, session.id)
        logger.info("session_join_anonymous", session_id=session.id, participant_id=participant.id)
        return {
            "participant_token": token,
            "token_type": "bearer",
            "participant_id": participant.id,
            "session_id": session.id,
            "display_name": participant.display_name,
        }

    @staticmethod
    def join_registered(db: DBSession, passcode: str, user_id: int) -> Dict[str, Any]:
        """Create or get participant for registered user. Commits if created."""
        session = SessionRepository.get_by_passcode(db, passcode)
        if not session:
            raise ValueError("Session not found")
        merged = SessionJoinService._get_merged_settings(db, session)
        SessionJoinService._check_entry_mode(merged, "registered")

        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")
        disp = (user.first_name or "").strip() or (user.last_name or "").strip() or user.email or None

        existing = SessionParticipantRepository.get_by_session_and_user(db, session.id, user_id)
        if existing:
            logger.info("session_join_registered_existing", session_id=session.id, participant_id=existing.id)
            return {
                "participant_id": existing.id,
                "session_id": session.id,
                "display_name": existing.display_name or disp,
            }

        SessionJoinService._check_max_participants(db, session.id, merged)
        participant = SessionParticipantRepository.create(
            db,
            session_id=session.id,
            participant_type=ParticipantType.USER.value,
            user_id=user_id,
            display_name=disp,
        )
        db.commit()
        db.refresh(participant)
        logger.info("session_join_registered", session_id=session.id, participant_id=participant.id)
        return {
            "participant_id": participant.id,
            "session_id": session.id,
            "display_name": participant.display_name,
        }

    @staticmethod
    def join_guest(db: DBSession, passcode: str, email: str) -> Dict[str, Any]:
        """Create or get participant for email-code guest. Commits if created."""
        email = _normalize_email(email)
        session = SessionRepository.get_by_passcode(db, passcode)
        if not session:
            raise ValueError("Session not found")
        merged = SessionJoinService._get_merged_settings(db, session)
        SessionJoinService._check_entry_mode(merged, "email_code")

        verification = GuestEmailVerificationRepository.get_by_email(db, email)
        if not verification:
            raise ValueError("Guest email not verified. Complete email-code flow first.")

        existing = SessionParticipantRepository.get_by_session_and_guest_email(db, session.id, email)
        if existing:
            logger.info("session_join_guest_existing", session_id=session.id, participant_id=existing.id)
            return {
                "participant_id": existing.id,
                "session_id": session.id,
                "display_name": existing.display_name or email,
            }

        SessionJoinService._check_max_participants(db, session.id, merged)
        participant = SessionParticipantRepository.create(
            db,
            session_id=session.id,
            participant_type=ParticipantType.GUEST_EMAIL.value,
            guest_email=email,
            display_name=verification.display_name or email,
        )
        db.commit()
        db.refresh(participant)
        logger.info("session_join_guest", session_id=session.id, participant_id=participant.id)
        return {
            "participant_id": participant.id,
            "session_id": session.id,
            "display_name": participant.display_name,
        }

    @staticmethod
    def join_sso(db: DBSession, passcode: str, sso_user_id: Optional[int] = None) -> Dict[str, Any]:
        """Stub for SSO join. Real SSO is WIP. Raises NotImplementedError."""
        session = SessionRepository.get_by_passcode(db, passcode)
        if not session:
            raise ValueError("Session not found")
        merged = SessionJoinService._get_merged_settings(db, session)
        SessionJoinService._check_entry_mode(merged, "sso")
        if not merged.get("sso_organization_id"):
            raise ValueError("Session has no sso_organization_id configured")
        raise NotImplementedError("SSO join is not implemented yet (WIP)")
