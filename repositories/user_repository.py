"""User repository."""
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from models.user import User
from core.config import settings


class UserRepository:
    """Repository for user operations."""
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(
            User.id == user_id
        ).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email (case-insensitive)."""
        return db.query(User).filter(
            func.lower(User.email) == func.lower(email),
            User.is_deleted == False
        ).first()
    
    @staticmethod
    def get_all(db: Session) -> List[User]:
        """Get all users."""
        return db.query(User).filter(
            User.is_deleted == False
        ).order_by(User.created_at.desc()).all()
    
    @staticmethod
    def create(
        db: Session,
        email: str,
        password_hash: str,
        verification_code: str,
        verification_code_expires_at: datetime
    ) -> User:
        """Create a new user (without commit)."""
        user = User(
            email=email,
            password_hash=password_hash,
            email_verified=False,
            verification_code=verification_code,
            verification_code_expires_at=verification_code_expires_at
        )
        db.add(user)
        return user
    
    @staticmethod
    def update(
        db: Session,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        preferences: Optional[dict] = None
    ) -> Optional[User]:
        """Update an existing user (without commit)."""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            return None

        updated = False
        if first_name is not None and user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if last_name is not None and user.last_name != last_name:
            user.last_name = last_name
            updated = True
        if avatar_url is not None and user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
            updated = True
        if preferences is not None:
            current = user.preferences or {}
            merged = {**current, **{k: v for k, v in preferences.items() if v is not None}}
            if merged != (user.preferences or {}):
                user.preferences = merged
                updated = True

        return user if updated else None
    
    @staticmethod
    def verify_email(db: Session, user_id: int) -> Optional[User]:
        """Mark user email as verified (without commit)."""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            return None
        
        user.email_verified = True
        user.verification_code = None
        user.verification_code_expires_at = None
        return user
    
    @staticmethod
    def update_verification_code(
        db: Session,
        user_id: int,
        verification_code: str,
        verification_code_expires_at: datetime
    ) -> Optional[User]:
        """Update verification code (without commit)."""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            return None
        
        user.verification_code = verification_code
        user.verification_code_expires_at = verification_code_expires_at
        return user
    
    @staticmethod
    def soft_delete(db: Session, user_id: int) -> Optional[User]:
        """Soft delete a user (without commit)."""
        user = UserRepository.get_by_id(db, user_id)
        if not user or user.is_deleted:
            return None
        
        user.is_deleted = True
        user.deleted_at = datetime.now(timezone.utc)
        return user
    
    @staticmethod
    def delete(db: Session, user_id: int, hard: bool = False) -> Optional[User]:
        """Delete a user (without commit)."""
        if not hard:
            return UserRepository.soft_delete(db, user_id)
        
        # Hard delete
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        db.delete(user)
        return user

