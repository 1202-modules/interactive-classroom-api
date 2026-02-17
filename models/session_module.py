"""SessionModule ORM model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from core.db import Base


class SessionModule(Base):
    """SessionModule model."""
    __tablename__ = "session_modules"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    module_type = Column(String, nullable=False)  # quiz, poll, questions, timer
    settings = Column(JSON, nullable=True)  # JSON with module content and settings
    is_active = Column(Boolean, default=False, nullable=False, index=True)  # Active module flag
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="session_modules", foreign_keys=[session_id])
    question_messages = relationship(
        "SessionQuestionMessage",
        back_populates="session_module",
        foreign_keys="SessionQuestionMessage.session_module_id",
        cascade="all, delete-orphan",
    )
    timer_state = relationship(
        "SessionModuleTimerState",
        back_populates="session_module",
        uselist=False,
        cascade="all, delete-orphan",
    )
    
    __table_args__ = (
        Index('ix_session_modules_session_id', 'session_id'),
        Index('ix_session_modules_is_deleted', 'is_deleted'),
        Index('ix_session_modules_is_active', 'is_active'),
        # Partial unique constraint will be created in migration
    )

