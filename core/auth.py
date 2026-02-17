"""JWT authentication utilities."""
from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from core.config import settings
from core.db import get_db
from repositories.user_repository import UserRepository
from repositories.guest_email_verification_repository import GuestEmailVerificationRepository

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    # Ensure 'sub' is a string (JWT standard requires string subject)
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def create_guest_access_token(email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT for session guest (email-code flow). Payload: sub=email, type=session_guest."""
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.GUEST_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": email,
        "type": "session_guest",
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_participant_token(participant_id: int, session_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT for anonymous session participant. Payload: sub=participant_id, session_id, type=session_participant."""
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.GUEST_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": str(participant_id),
        "session_id": session_id,
        "type": "session_participant",
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """
    Create a refresh token (random string, not JWT).
    
    Args:
        user_id: User ID
    
    Returns:
        Refresh token string
    """
    # Generate a secure random token
    token = secrets.token_urlsafe(32)
    return token


def verify_refresh_token(token: str) -> Optional[int]:
    """
    Verify refresh token format (basic validation).
    In production, this would also check against database.
    
    Args:
        token: Refresh token string
    
    Returns:
        User ID if token is valid format, None otherwise
    """
    # Basic validation - token should be a non-empty string
    if not token or not isinstance(token, str) or len(token) < 32:
        return None
    
    # Actual validation happens in the service layer by checking database
    return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """Dependency to get current user from JWT token."""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convert string user_id back to int
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user exists and is not deleted
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )
    
    return {
        "user_id": user_id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


async def get_current_guest_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """Dependency to get current guest from JWT (type=session_guest). Expiration via JWT exp; record exists = not revoked."""
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("type") != "session_guest":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = payload.get("sub")
    if not email or not isinstance(email, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    verification = GuestEmailVerificationRepository.get_by_email(db, email)
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Guest verification not found or revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "email": verification.email,
        "display_name": verification.display_name,
        "type": "guest",
    }
