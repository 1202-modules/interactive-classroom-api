"""PendingRegistration ORM model for unverified registrations."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Index
from core.db import Base


class PendingRegistration(Base):
    """PendingRegistration model for storing unverified user registrations."""
    __tablename__ = "pending_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    verification_code = Column(String, nullable=False)
    verification_code_expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    __table_args__ = (
        Index('ix_pending_registrations_email', 'email', unique=True),
        Index('ix_pending_registrations_expires_at', 'verification_code_expires_at'),
    )
