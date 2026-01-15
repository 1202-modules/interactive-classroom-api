"""Workspace ORM model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from core.db import Base
import enum


class WorkspaceStatus(str, enum.Enum):
    """Workspace status enum."""
    ACTIVE = "active"
    ARCHIVE = "archive"


class WorkspaceStatusType:
    """Workspace status type for SQLAlchemy."""
    def __init__(self):
        self.impl = String
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, WorkspaceStatus):
            return value.value
        return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return WorkspaceStatus(value.lower())


class Workspace(Base):
    """Workspace model."""
    __tablename__ = "workspaces"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False, default=WorkspaceStatus.ACTIVE.value)
    session_settings = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="workspaces")
    sessions = relationship("Session", back_populates="workspace", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_workspaces_user_id', 'user_id'),
        Index('ix_workspaces_status', 'status'),
    )

