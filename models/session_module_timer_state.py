"""SessionModuleTimerState ORM model for Timer module."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from core.db import Base


class SessionModuleTimerState(Base):
    """Timer state for a session module. One row per module."""
    __tablename__ = "session_module_timer_state"

    session_module_id = Column(
        Integer, ForeignKey("session_modules.id", ondelete="CASCADE"), primary_key=True
    )
    is_paused = Column(Boolean, default=False, nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=True)
    remaining_seconds = Column(Integer, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    session_module = relationship("SessionModule", back_populates="timer_state")
