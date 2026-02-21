"""SessionJoinFingerprint ORM model for join attempts per session and fingerprint hash."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from core.db import Base


class SessionJoinFingerprint(Base):
    """Track successful joins to enforce device-based limits in a rolling time window."""
    __tablename__ = "session_join_fingerprints"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    participant_id = Column(Integer, ForeignKey("session_participants.id", ondelete="SET NULL"), nullable=True)
    fingerprint_hash = Column(String(64), nullable=False)
    entry_type = Column(String(32), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    session = relationship("Session", backref="join_fingerprints")
    participant = relationship("SessionParticipant", backref="join_fingerprint_records")

    __table_args__ = (
        Index(
            "ix_session_join_fingerprints_session_hash_entry",
            "session_id",
            "fingerprint_hash",
            "entry_type",
        ),
        Index("ix_session_join_fingerprints_participant_id", "participant_id"),
        Index("ix_session_join_fingerprints_created_at", "created_at"),
    )
