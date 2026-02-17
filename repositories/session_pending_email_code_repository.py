"""SessionPendingEmailCode repository."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from models.session_pending_email_code import SessionPendingEmailCode


class SessionPendingEmailCodeRepository:
    """Repository for pending email codes per session (one active per session_id + email)."""

    @staticmethod
    def get_by_session_email_code(
        db: DBSession,
        session_id: int,
        email: str,
        code: str
    ) -> Optional[SessionPendingEmailCode]:
        """Get pending record by session, email and code."""
        return db.query(SessionPendingEmailCode).filter(
            SessionPendingEmailCode.session_id == session_id,
            SessionPendingEmailCode.email == email,
            SessionPendingEmailCode.code == code
        ).first()

    @staticmethod
    def create_or_update(
        db: DBSession,
        session_id: int,
        email: str,
        code: str,
        expires_at: datetime
    ) -> SessionPendingEmailCode:
        """Create or update one record for (session_id, email). Does not commit."""
        rec = db.query(SessionPendingEmailCode).filter(
            SessionPendingEmailCode.session_id == session_id,
            SessionPendingEmailCode.email == email
        ).first()
        if rec:
            rec.code = code
            rec.expires_at = expires_at
            return rec
        rec = SessionPendingEmailCode(
            session_id=session_id,
            email=email,
            code=code,
            expires_at=expires_at
        )
        db.add(rec)
        return rec

    @staticmethod
    def delete(db: DBSession, pending: SessionPendingEmailCode) -> None:
        """Delete pending record (no commit)."""
        db.delete(pending)
