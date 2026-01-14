"""RefreshToken repository for database operations."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Repository for refresh token operations."""
    
    @staticmethod
    def create(
        db: Session,
        user_id: int,
        token: str,
        expires_at: datetime
    ) -> RefreshToken:
        """
        Create a new refresh token.
        
        Args:
            db: Database session
            user_id: User ID
            token: Refresh token string
            expires_at: Token expiration datetime
        
        Returns:
            Created RefreshToken instance
        """
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            revoked=False
        )
        db.add(refresh_token)
        db.commit()
        db.refresh(refresh_token)
        return refresh_token
    
    @staticmethod
    def get_by_token(db: Session, token: str) -> Optional[RefreshToken]:
        """
        Get refresh token by token string.
        
        Args:
            db: Database session
            token: Refresh token string
        
        Returns:
            RefreshToken instance or None
        """
        return db.query(RefreshToken).filter(
            RefreshToken.token == token,
            RefreshToken.revoked == False
        ).first()
    
    @staticmethod
    def revoke_token(db: Session, token: str) -> bool:
        """
        Revoke a refresh token.
        
        Args:
            db: Database session
            token: Refresh token string
        
        Returns:
            True if token was revoked, False if not found
        """
        refresh_token = db.query(RefreshToken).filter(
            RefreshToken.token == token
        ).first()
        
        if refresh_token:
            refresh_token.revoked = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def revoke_all_user_tokens(db: Session, user_id: int) -> int:
        """
        Revoke all refresh tokens for a user.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Number of tokens revoked
        """
        count = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False
        ).update({"revoked": True})
        db.commit()
        return count
    
    @staticmethod
    def delete_expired(db: Session) -> int:
        """
        Delete expired refresh tokens.
        
        Args:
            db: Database session
        
        Returns:
            Number of tokens deleted
        """
        now = datetime.now(timezone.utc)
        count = db.query(RefreshToken).filter(
            RefreshToken.expires_at < now
        ).delete()
        db.commit()
        return count

