"""SessionPendingEmailCode ORM model for one-time email verification codes per session."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from core.db import Base


class SessionPendingEmailCode(Base):
    """Pending email verification for a session: one active (session_id, email) pair; code expires."""
    __tablename__ = "session_pending_email_codes"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    code = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    session = relationship("Session", backref="pending_email_codes")

    __table_args__ = (
        UniqueConstraint("session_id", "email", name="uq_session_pending_email_code_session_email"),
        Index("ix_session_pending_email_codes_expires_at", "expires_at"),
    )
