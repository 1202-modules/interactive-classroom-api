"""GuestEmailVerification ORM model for email-code session guest tokens."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Index
from core.db import Base


class GuestEmailVerification(Base):
    """One record per email; reusable across sessions with matching domain whitelist. Expiration = JWT exp."""
    __tablename__ = "guest_email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_guest_email_verifications_email", "email", unique=True),
    )
