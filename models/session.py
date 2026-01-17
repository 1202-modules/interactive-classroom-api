"""Session ORM model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from core.db import Base
import enum


class SessionStatus(str, enum.Enum):
    """Session status enum."""
    ACTIVE = "active"
    ARCHIVE = "archive"


class Session(Base):
    """Session model."""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    stopped_participant_count = Column(Integer, default=0, nullable=False)
    start_datetime = Column(DateTime(timezone=True), nullable=True)
    end_datetime = Column(DateTime(timezone=True), nullable=True)
    is_stopped = Column(Boolean, default=False, nullable=False, index=True)
    status = Column(String, nullable=False, default=SessionStatus.ACTIVE.value)
    custom_settings = Column(JSON, nullable=True)
    passcode = Column(String(6), unique=True, nullable=True, index=True)  # 6-character alphanumeric code
    active_module_id = Column(Integer, ForeignKey("session_modules.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="sessions")
    session_modules = relationship("SessionModule", back_populates="session", foreign_keys="SessionModule.session_id")
    active_module = relationship("SessionModule", foreign_keys=[active_module_id], post_update=True)
    
    __table_args__ = (
        Index('ix_sessions_workspace_id', 'workspace_id'),
        Index('ix_sessions_status', 'status'),
        Index('ix_sessions_passcode', 'passcode'),
    )

