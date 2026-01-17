"""WorkspaceModule ORM model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from core.db import Base
import enum


class ModuleType(str, enum.Enum):
    """Module type enum."""
    QUIZ = "quiz"
    POLL = "poll"
    QUESTIONS = "questions"
    TIMER = "timer"


class WorkspaceModule(Base):
    """WorkspaceModule model."""
    __tablename__ = "workspace_modules"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    module_type = Column(String, nullable=False)  # quiz, poll, questions, timer
    settings = Column(JSON, nullable=True)  # JSON with module content and settings
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="workspace_modules")
    
    __table_args__ = (
        Index('ix_workspace_modules_workspace_id', 'workspace_id'),
        Index('ix_workspace_modules_is_deleted', 'is_deleted'),
    )

