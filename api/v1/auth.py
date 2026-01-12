"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.db import get_db
from api.services.auth_service import AuthService
from api.api.v1.schemas import (
    RegisterRequest, RegisterResponse,
    VerifyEmailRequest, VerifyEmailResponse,
    LoginRequest, LoginResponse,
    ResendCodeRequest, ResendCodeResponse,
    MessageResponse, ErrorResponse
)
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Register a new user with email and password.
    
    After registration, a verification code will be sent to the provided email.
    The user must verify their email before they can log in.
    
    **Business Rules:**
    - Email must be unique
    - Password must be at least 8 characters
    - Verification code expires in 15 minutes
    """,
    responses={
        201: {"description": "User registered successfully"},
        400: {"description": "Email already exists or validation error"},
        422: {"description": "Validation error"}
    }
)
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        result = AuthService.register(
            db=db,
            email=register_data.email,
            password=register_data.password
        )
        return RegisterResponse(**result)
    except ValueError as e:
        logger.warning("registration_failed", email=register_data.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("registration_error", email=register_data.email, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    summary="Verify user email",
    description="""
    Verify user email with verification code.
    
    After successful verification, the user will receive an access token
    and can start using the API.
    
    **Business Rules:**
    - Verification code must match the one sent to email
    - Code expires after 15 minutes
    - Email can only be verified once
    """,
    responses={
        200: {"description": "Email verified successfully"},
        400: {"description": "Invalid code, expired code, or email already verified"},
        404: {"description": "User not found"}
    }
)
async def verify_email(
    verify_data: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """Verify user email with code."""
    try:
        result = AuthService.verify_email(
            db=db,
            email=verify_data.email,
            code=verify_data.code
        )
        return VerifyEmailResponse(**result)
    except ValueError as e:
        logger.warning("email_verification_failed", email=verify_data.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("email_verification_error", email=verify_data.email, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login user",
    description="""
    Login user with email and password.
    
    **Business Rules:**
    - Email must be verified before login
    - Invalid credentials will return 401
    """,
    responses={
        200: {"description": "Login successful"},
        400: {"description": "Invalid credentials or email not verified"},
        401: {"description": "Invalid credentials"}
    }
)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login user."""
    try:
        result = AuthService.login(
            db=db,
            email=login_data.email,
            password=login_data.password
        )
        return LoginResponse(**result)
    except ValueError as e:
        logger.warning("login_failed", email=login_data.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("login_error", email=login_data.email, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/resend-code",
    response_model=ResendCodeResponse,
    summary="Resend verification code",
    description="""
    Resend verification code to user email.
    
    **Business Rules:**
    - Can only be used if email is not yet verified
    - New code expires in 15 minutes
    """,
    responses={
        200: {"description": "Verification code resent"},
        400: {"description": "User not found or email already verified"}
    }
)
async def resend_code(
    resend_data: ResendCodeRequest,
    db: Session = Depends(get_db)
):
    """Resend verification code."""
    try:
        result = AuthService.resend_verification_code(
            db=db,
            email=resend_data.email
        )
        return ResendCodeResponse(**result)
    except ValueError as e:
        logger.warning("resend_code_failed", email=resend_data.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("resend_code_error", email=resend_data.email, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

