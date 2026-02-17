"""User ORM model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from core.db import Base


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_code = Column(String, nullable=True)
    verification_code_expires_at = Column(DateTime(timezone=True), nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    preferences = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    workspaces = relationship("Workspace", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_users_email_unique', 'email', unique=True, postgresql_where=(is_deleted == False)),
    )

