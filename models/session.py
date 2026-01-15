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


class TemplateLinkType(str, enum.Enum):
    """Template link type enum."""
    FULL = "full"
    PARTIAL = "partial"


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
    template_link_type = Column(String, nullable=False, default=TemplateLinkType.FULL.value)
    custom_settings = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="sessions")
    
    __table_args__ = (
        Index('ix_sessions_workspace_id', 'workspace_id'),
        Index('ix_sessions_status', 'status'),
    )

