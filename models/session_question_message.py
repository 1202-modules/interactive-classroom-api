"""SessionQuestionMessage ORM model for Questions module."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from core.db import Base


class SessionQuestionMessage(Base):
    """Question/answer message in a Questions module."""
    __tablename__ = "session_question_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_module_id = Column(
        Integer, ForeignKey("session_modules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_id = Column(
        Integer, ForeignKey("session_participants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id = Column(
        Integer, ForeignKey("session_question_messages.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, default=False, nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    is_answered = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    session_module = relationship("SessionModule", back_populates="question_messages")
    participant = relationship("SessionParticipant", back_populates="question_messages")
    parent = relationship("SessionQuestionMessage", remote_side="SessionQuestionMessage.id")
    likes = relationship("SessionQuestionMessageLike", back_populates="message", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_session_question_messages_session_module_id", "session_module_id"),
        Index("ix_session_question_messages_participant_id", "participant_id"),
        Index("ix_session_question_messages_parent_id", "parent_id"),
    )


class SessionQuestionMessageLike(Base):
    """Like on a question message. One per participant per message (idempotent)."""
    __tablename__ = "session_question_message_likes"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(
        Integer, ForeignKey("session_question_messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_id = Column(
        Integer, ForeignKey("session_participants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    message = relationship("SessionQuestionMessage", back_populates="likes")
    participant = relationship("SessionParticipant")

    __table_args__ = (
        Index("ix_session_question_message_likes_message_participant", "message_id", "participant_id", unique=True),
    )
