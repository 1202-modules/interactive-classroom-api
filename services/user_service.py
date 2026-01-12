"""User service."""
from typing import Optional
from sqlalchemy.orm import Session
from repositories.user_repository import UserRepository
from models.user import User
import structlog

logger = structlog.get_logger(__name__)


class UserService:
    """Service for user profile operations."""
    
    @staticmethod
    def get_profile(
        db: Session,
        user_id: int
    ) -> Optional[User]:
        """
        Get user profile.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            User object or None if not found
        """
        return UserRepository.get_by_id(db, user_id)
    
    @staticmethod
    def update_profile(
        db: Session,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Optional[User]:
        """
        Update user profile.
        
        Args:
            db: Database session
            user_id: User ID
            first_name: First name (optional)
            last_name: Last name (optional)
            avatar_url: Avatar URL (optional)
        
        Returns:
            Updated user object or None if not found
        """
        updated_user = UserRepository.update(
            db=db,
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url
        )
        
        if updated_user:
            # Commit transaction
            db.commit()
            db.refresh(updated_user)
            
            logger.info(
                "user_profile_updated",
                user_id=user_id,
                first_name=first_name,
                last_name=last_name
            )
        
        return updated_user

