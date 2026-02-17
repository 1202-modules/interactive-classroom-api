"""Service for guest join by passcode (email-code flow)."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session as DBSession

from core.config import settings
from core.auth import create_guest_access_token
from repositories.session_repository import SessionRepository
from repositories.workspace_repository import WorkspaceRepository
from repositories.guest_email_verification_repository import GuestEmailVerificationRepository
from repositories.session_pending_email_code_repository import SessionPendingEmailCodeRepository
from utils.email import generate_verification_code, send_verification_email
import structlog

logger = structlog.get_logger(__name__)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _email_domain(email: str) -> str:
    return email.split("@")[-1].lower() if "@" in email else ""


def _email_domain_allowed(email: str, merged_settings: Dict[str, Any]) -> bool:
    """Check if email domain is in whitelist. Empty/None whitelist = any domain."""
    domain = _email_domain(email)
    if not domain:
        return False
    whitelist = merged_settings.get("email_code_domains_whitelist")
    if not whitelist or (isinstance(whitelist, list) and len(whitelist) == 0):
        return True
    return domain in [d.strip().lower() for d in whitelist if isinstance(d, str) and d.strip()]


class SessionGuestService:
    """Business logic for guest session join (email-code)."""

    @staticmethod
    def get_session_by_passcode_public(
        db: DBSession,
        passcode: str,
        guest_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return public session info for guest join screen.
        If guest_token provided and valid (guest has verified this email, domain in whitelist),
        adds guest_authenticated=True so frontend can skip the form and use stored token.
        Raises ValueError if passcode not found or session deleted.
        """
        session = SessionRepository.get_by_passcode(db, passcode)
        if not session:
            raise ValueError("Session not found")
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace:
            raise ValueError("Session not found")
        template_settings = workspace.template_settings or {}
        merged = SessionRepository.get_merged_settings(session, template_settings)
        result = {
            "id": session.id,
            "name": session.name,
            "participant_entry_mode": merged.get("participant_entry_mode", "anonymous"),
            "email_code_domains_whitelist": merged.get("email_code_domains_whitelist") or [],
            "sso_organization_id": merged.get("sso_organization_id"),
        }
        if guest_token and merged.get("participant_entry_mode") == "email_code":
            guest_info = SessionGuestService._validate_guest_token_for_session(
                db, guest_token, merged
            )
            if guest_info:
                result["guest_authenticated"] = True
                result["email"] = guest_info["email"]
                result["display_name"] = guest_info.get("display_name")
        return result

    @staticmethod
    def _validate_guest_token_for_session(
        db: DBSession,
        token: str,
        merged_settings: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """If token is valid guest JWT and email domain in whitelist, return {email, display_name}."""
        from core.auth import verify_token

        payload = verify_token(token)
        if not payload or payload.get("type") != "session_guest":
            return None
        email = payload.get("sub")
        if not email or not isinstance(email, str):
            return None
        email = _normalize_email(email)
        if not _email_domain_allowed(email, merged_settings):
            return None
        verification = GuestEmailVerificationRepository.get_by_email(db, email)
        if not verification:
            return None
        return {"email": email, "display_name": verification.display_name}

    @staticmethod
    def request_code(
        db: DBSession,
        passcode: str,
        email: str,
    ) -> Dict[str, Any]:
        """
        Request verification code for email-code join. Always sends code to email.
        Token is issued only after verify_code — never here. Autologin happens when
        user already has token in browser (see get_session_by_passcode_public with Authorization).
        Commits on success.
        """
        email = _normalize_email(email)
        session = SessionRepository.get_by_passcode(db, passcode)
        if not session:
            raise ValueError("Session not found")
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        template_settings = workspace.template_settings or {}
        merged = SessionRepository.get_merged_settings(session, template_settings)
        mode = merged.get("participant_entry_mode")
        if mode != "email_code":
            raise ValueError("Session is not in email-code entry mode")
        if not _email_domain_allowed(email, merged):
            raise ValueError("Email domain not allowed for this session")

        # Always create/update pending code and send email — never return token
        code = generate_verification_code()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES
        )
        SessionPendingEmailCodeRepository.create_or_update(
            db, session.id, email, code, expires_at
        )
        email_sent = send_verification_email(email, code)
        db.commit()

        logger.info(
            "session_guest_code_requested",
            session_id=session.id,
            email_domain=_email_domain(email),
            email_sent=email_sent,
        )

        result = {"verification_code_sent": email_sent}
        if not all(
            [
                settings.SMTP_HOST,
                settings.SMTP_USER,
                settings.SMTP_PASSWORD,
                settings.SMTP_FROM_EMAIL,
            ]
        ):
            result["code"] = code
        return result

    @staticmethod
    def verify_code(
        db: DBSession,
        passcode: str,
        email: str,
        code: str,
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Verify code and issue guest token. Commits on success.
        """
        email = _normalize_email(email)
        session = SessionRepository.get_by_passcode(db, passcode)
        if not session:
            raise ValueError("Session not found")

        pending = SessionPendingEmailCodeRepository.get_by_session_email_code(
            db, session.id, email, code
        )
        if not pending:
            raise ValueError("Invalid verification code or email not found")
        if pending.expires_at < datetime.now(timezone.utc):
            SessionPendingEmailCodeRepository.delete(db, pending)
            db.commit()
            raise ValueError("Verification code expired")

        SessionPendingEmailCodeRepository.delete(db, pending)
        GuestEmailVerificationRepository.upsert(db, email, display_name or None)
        token = create_guest_access_token(email)
        db.commit()

        logger.info(
            "session_guest_verified",
            session_id=session.id,
            email_domain=_email_domain(email),
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "email": email,
            "display_name": display_name,
        }
