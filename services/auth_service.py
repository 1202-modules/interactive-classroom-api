"""Authentication service."""
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from api.repositories.user_repository import UserRepository
from api.utils.password import hash_password, verify_password
from api.utils.email import generate_verification_code, send_verification_email
from api.core.auth import create_access_token
from api.core.config import settings
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
        expires_at = datetime.utcnow() + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        
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
        if not user.verification_code_expires_at or user.verification_code_expires_at < datetime.utcnow():
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
    ) -> Dict[str, any]:
        """
        Login user with email and password.
        
        Args:
            db: Database session
            email: User email
            password: User password
        
        Returns:
            Dict with access token
        
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
        
        logger.info("user_logged_in", user_id=user.id, email=email)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email
        }
    
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
        expires_at = datetime.utcnow() + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        
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

