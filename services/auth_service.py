"""Authentication service."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple
from sqlalchemy.orm import Session
from repositories.user_repository import UserRepository
from repositories.refresh_token_repository import RefreshTokenRepository
from utils.password import hash_password, verify_password
from utils.email import generate_verification_code, send_verification_email
from core.auth import create_access_token, create_refresh_token
from core.config import settings
import structlog

logger = structlog.get_logger(__name__)


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def register(
        db: Session,
        email: str,
        password: str
    ) -> Dict[str, any]:
        """
        Register a new user.
        
        Args:
            db: Database session
            email: User email
            password: User password
        
        Returns:
            Dict with user_id and verification_code_sent status
        
        Raises:
            ValueError: If email already exists
        """
        # Check if user already exists
        existing_user = UserRepository.get_by_email(db, email)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")
        
        # Hash password
        password_hash = hash_password(password)
        
        # Generate verification code
        verification_code = generate_verification_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        
        # Create user
        user = UserRepository.create(
            db=db,
            email=email,
            password_hash=password_hash,
            verification_code=verification_code,
            verification_code_expires_at=expires_at
        )
        
        # Commit transaction
        db.commit()
        db.refresh(user)
        
        # Send verification email
        email_sent = send_verification_email(email, verification_code)
        
        logger.info(
            "user_registered",
            user_id=user.id,
            email=email,
            email_sent=email_sent
        )
        
        return {
            "user_id": user.id,
            "email": user.email,
            "verification_code_sent": email_sent
        }
    
    @staticmethod
    def verify_email(
        db: Session,
        email: str,
        code: str
    ) -> Dict[str, any]:
        """
        Verify user email with code.
        
        Args:
            db: Database session
            email: User email
            code: Verification code
        
        Returns:
            Dict with success status and access token
        
        Raises:
            ValueError: If user not found, code invalid, or expired
        """
        user = UserRepository.get_by_email(db, email)
        if not user:
            raise ValueError("User not found")
        
        if user.email_verified:
            raise ValueError("Email already verified")
        
        # Check verification code
        if not user.verification_code or user.verification_code != code:
            raise ValueError("Invalid verification code")
        
        # Check expiration
        if not user.verification_code_expires_at or user.verification_code_expires_at < datetime.now(timezone.utc):
            raise ValueError("Verification code expired")
        
        # Verify email
        UserRepository.verify_email(db, user.id)
        
        # Commit transaction
        db.commit()
        db.refresh(user)
        
        # Generate access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=access_token_expires
        )
        
        logger.info("email_verified", user_id=user.id, email=email)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email
        }
    
    @staticmethod
    def login(
        db: Session,
        email: str,
        password: str
    ) -> Tuple[Dict[str, any], str, datetime]:
        """
        Login user with email and password.
        
        Args:
            db: Database session
            email: User email
            password: User password
        
        Returns:
            Tuple of (response dict, refresh_token, expires_at)
        
        Raises:
            ValueError: If credentials invalid or email not verified
        """
        user = UserRepository.get_by_email(db, email)
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        # Check if email is verified
        if not user.email_verified:
            raise ValueError("Email not verified. Please verify your email first.")
        
        # Generate access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=access_token_expires
        )
        
        # Generate refresh token
        refresh_token_str = create_refresh_token(user.id)
        refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Store refresh token in database
        RefreshTokenRepository.create(
            db=db,
            user_id=user.id,
            token=refresh_token_str,
            expires_at=refresh_token_expires_at
        )
        
        logger.info("user_logged_in", user_id=user.id, email=email)
        
        response = {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email
        }
        
        return response, refresh_token_str, refresh_token_expires_at
    
    @staticmethod
    def resend_verification_code(
        db: Session,
        email: str
    ) -> Dict[str, any]:
        """
        Resend verification code to user email.
        
        Args:
            db: Database session
            email: User email
        
        Returns:
            Dict with verification_code_sent status
        
        Raises:
            ValueError: If user not found or already verified
        """
        user = UserRepository.get_by_email(db, email)
        if not user:
            raise ValueError("User not found")
        
        if user.email_verified:
            raise ValueError("Email already verified")
        
        # Generate new verification code
        verification_code = generate_verification_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        
        # Update verification code
        UserRepository.update_verification_code(
            db=db,
            user_id=user.id,
            verification_code=verification_code,
            verification_code_expires_at=expires_at
        )
        
        # Commit transaction
        db.commit()
        
        # Send verification email
        email_sent = send_verification_email(email, verification_code)
        
        logger.info("verification_code_resent", user_id=user.id, email=email, email_sent=email_sent)
        
        return {
            "verification_code_sent": email_sent
        }
    
    @staticmethod
    def refresh_access_token(
        db: Session,
        refresh_token: str
    ) -> Tuple[Dict[str, any], Optional[str], Optional[datetime]]:
        """
        Refresh access token using refresh token.
        
        Args:
            db: Database session
            refresh_token: Refresh token string
        
        Returns:
            Tuple of (response dict, new_refresh_token, expires_at) or (None, None, None) if invalid
        
        Raises:
            ValueError: If refresh token invalid, expired, or revoked
        """
        # Get refresh token from database
        token_record = RefreshTokenRepository.get_by_token(db, refresh_token)
        if not token_record:
            raise ValueError("Invalid refresh token")
        
        # Check if token is expired
        if token_record.expires_at < datetime.now(timezone.utc):
            raise ValueError("Refresh token expired")
        
        # Check if token is revoked
        if token_record.revoked:
            raise ValueError("Refresh token revoked")
        
        # Get user
        user = UserRepository.get_by_id(db, token_record.user_id)
        if not user or not user.email_verified:
            raise ValueError("User not found or email not verified")
        
        # Generate new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=access_token_expires
        )
        
        # Optionally rotate refresh token (create new one and revoke old)
        new_refresh_token_str = create_refresh_token(user.id)
        new_refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Revoke old token
        RefreshTokenRepository.revoke_token(db, refresh_token)
        
        # Create new refresh token
        RefreshTokenRepository.create(
            db=db,
            user_id=user.id,
            token=new_refresh_token_str,
            expires_at=new_refresh_token_expires_at
        )
        
        logger.info("token_refreshed", user_id=user.id)
        
        response = {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email
        }
        
        return response, new_refresh_token_str, new_refresh_token_expires_at
    
    @staticmethod
    def logout(
        db: Session,
        refresh_token: str
    ) -> bool:
        """
        Logout user by revoking refresh token.
        
        Args:
            db: Database session
            refresh_token: Refresh token string
        
        Returns:
            True if token was revoked, False if not found
        """
        revoked = RefreshTokenRepository.revoke_token(db, refresh_token)
        if revoked:
            logger.info("user_logged_out", refresh_token=refresh_token[:10] + "...")
        return revoked

