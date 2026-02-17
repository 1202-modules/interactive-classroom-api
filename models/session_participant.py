"""SessionParticipant ORM model."""
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from core.db import Base


class ParticipantType(str, enum.Enum):
    """Participant type enum."""
    ANONYMOUS = "anonymous"
    USER = "user"
    GUEST_EMAIL = "guest_email"
    SSO = "sso"


class SessionParticipant(Base):
    """Session participant - one record per join to a session."""
    __tablename__ = "session_participants"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_type = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    guest_email = Column(String, nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    display_name = Column(String, nullable=True)
    anonymous_slug = Column(String, nullable=True, index=True)
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    session = relationship("Session", back_populates="session_participants")
    user = relationship("User", backref="session_participations")
    question_messages = relationship("SessionQuestionMessage", back_populates="participant")

    __table_args__ = (
        Index("ix_session_participants_session_id", "session_id"),
        Index("ix_session_participants_session_user", "session_id", "user_id"),
        Index("ix_session_participants_session_guest_email", "session_id", "guest_email"),
        Index("ix_session_participants_last_heartbeat_at", "last_heartbeat_at"),
    )
