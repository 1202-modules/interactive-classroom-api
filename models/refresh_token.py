"""RefreshToken ORM model."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from core.db import Base


class RefreshToken(Base):
    """RefreshToken model for storing refresh tokens."""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User", backref="refresh_tokens")
    
    __table_args__ = (
        Index('ix_refresh_tokens_user_id', 'user_id'),
        Index('ix_refresh_tokens_token', 'token', unique=True),
        Index('ix_refresh_tokens_expires_at', 'expires_at'),
    )

