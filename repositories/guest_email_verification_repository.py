"""GuestEmailVerification repository."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from models.guest_email_verification import GuestEmailVerification


class GuestEmailVerificationRepository:
    """Repository for guest email verification (one record per email, reusable across sessions). Expiration via JWT exp."""

    @staticmethod
    def get_by_email(db: DBSession, email: str) -> Optional[GuestEmailVerification]:
        """Get verification record by email. Record exists = not revoked."""
        return db.query(GuestEmailVerification).filter(
            GuestEmailVerification.email == email
        ).first()

    @staticmethod
    def upsert(
        db: DBSession,
        email: str,
        display_name: Optional[str] = None,
    ) -> GuestEmailVerification:
        """Create or update record by email (no commit)."""
        rec = db.query(GuestEmailVerification).filter(
            GuestEmailVerification.email == email
        ).first()
        now = datetime.now(timezone.utc)
        if rec:
            rec.display_name = display_name
            rec.updated_at = now
            return rec
        rec = GuestEmailVerification(
            email=email,
            display_name=display_name,
        )
        db.add(rec)
        return rec
