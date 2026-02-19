"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from core.db import get_db
from core.config import settings
from services.auth_service import AuthService
from endpoints.v1.schemas import (
    RegisterRequest, RegisterResponse,
    VerifyEmailRequest, VerifyEmailResponse,
    LoginRequest, LoginResponse,
    ResendCodeRequest, ResendCodeResponse,
    RefreshResponse,
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
    TEST Register a new user with email and password.
    
    After registration, a verification code will be sent to the provided email.
    The user must verify their email before they can log in.
    
    Business Rules:
    - Email must be unique
    - Password must be at least 8 characters
    - Verification code expires in 15 minutes
    """,
    responses={
        201: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "email": "user@example.com",
                        "verification_code_sent": True
                    }
                }
            }
        },
        400: {
            "description": "Email already exists or validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email already exists"
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        }
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
    except HTTPException:
        raise
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
    
    Business Rules:
    - Verification code must match the one sent to email
    - Code expires after 15 minutes
    - Email can only be verified once
    """,
    responses={
        200: {
            "description": "Email verified successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                        "token_type": "bearer",
                        "user_id": 1,
                        "email": "user@example.com"
                    }
                }
            }
        },
        400: {
            "description": "Invalid code, expired code, or email already verified",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid verification code"
                    }
                }
            }
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User not found"
                    }
                }
            }
        }
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
    except HTTPException:
        raise
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
    
    Returns access token in JSON response and refresh token in HTTP-only cookie.
    
    Business Rules:
    - Email must be verified before login
    - Invalid credentials will return 401
    - Refresh token is stored in HTTP-only cookie (not accessible via JavaScript)
    """,
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                        "token_type": "bearer",
                        "user_id": 1,
                        "email": "user@example.com"
                    }
                }
            }
        },
        400: {
            "description": "Invalid credentials or email not verified",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email not verified"
                    }
                }
            }
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid email or password"
                    }
                }
            }
        }
    }
)
async def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Login user."""
    try:
        result, refresh_token, expires_at = AuthService.login(
            db=db,
            email=login_data.email,
            password=login_data.password
        )
        
        # Set refresh token in HTTP-only cookie
        cookie_kwargs = {
            "key": settings.COOKIE_NAME,
            "value": refresh_token,
            "httponly": settings.COOKIE_HTTP_ONLY,
            "secure": settings.COOKIE_SECURE,
            "samesite": settings.COOKIE_SAME_SITE,
        }
        if login_data.remember_me:
            cookie_kwargs["max_age"] = settings.COOKIE_MAX_AGE
        response.set_cookie(**cookie_kwargs)
        
        return LoginResponse(**result)
    except ValueError as e:
        logger.warning("login_failed", email=login_data.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except HTTPException:
        raise
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
    
    Business Rules:
    - Can only be used if email is not yet verified
    - New code expires in 15 minutes
    """,
    responses={
        200: {
            "description": "Verification code resent",
            "content": {
                "application/json": {
                    "example": {
                        "verification_code_sent": True
                    }
                }
            }
        },
        400: {
            "description": "User not found or email already verified",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email already verified"
                    }
                }
            }
        }
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error("resend_code_error", email=resend_data.email, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Refresh access token",
    description="""
    Refresh access token using refresh token from HTTP-only cookie.
    
    Business Rules:
    - Refresh token is read from cookie (not from request body)
    - Old refresh token is revoked and new one is issued (token rotation)
    - Returns new access token in JSON and new refresh token in cookie
    - Invalid/expired refresh token returns 401
    """,
    responses={
        200: {
            "description": "Token refreshed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                        "token_type": "bearer",
                        "user_id": 1,
                        "email": "user@example.com"
                    }
                }
            }
        },
        401: {
            "description": "Invalid or expired refresh token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Refresh token not found"
                    }
                }
            }
        },
        403: {
            "description": "Refresh token revoked",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Refresh token revoked"
                    }
                }
            }
        }
    }
)
async def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Refresh access token."""
    try:
        # Get refresh token from cookie
        refresh_token = request.cookies.get(settings.COOKIE_NAME)
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found"
            )
        
        # Refresh access token
        result, new_refresh_token, expires_at = AuthService.refresh_access_token(
            db=db,
            refresh_token=refresh_token
        )
        
        # Set new refresh token in HTTP-only cookie
        response.set_cookie(
            key=settings.COOKIE_NAME,
            value=new_refresh_token,
            max_age=settings.COOKIE_MAX_AGE,
            httponly=settings.COOKIE_HTTP_ONLY,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAME_SITE
        )
        
        return RefreshResponse(**result)
    except ValueError as e:
        logger.warning("token_refresh_failed", error=str(e))
        # Clear cookie on error
        response.delete_cookie(
            key=settings.COOKIE_NAME,
            httponly=settings.COOKIE_HTTP_ONLY,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAME_SITE
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("token_refresh_error", error=str(e), exc_info=True)
        # Clear cookie on error
        response.delete_cookie(
            key=settings.COOKIE_NAME,
            httponly=settings.COOKIE_HTTP_ONLY,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAME_SITE
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="""
    Logout user by revoking refresh token and clearing cookie.
    
    Business Rules:
    - Refresh token is revoked in database
    - Cookie is cleared from browser
    - Access token remains valid until expiration (stateless)
    """,
    responses={
        200: {
            "description": "Logout successful",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Logged out successfully"
                    }
                }
            }
        },
        401: {
            "description": "Refresh token not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Refresh token not found"
                    }
                }
            }
        }
    }
)
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Logout user."""
    try:
        # Get refresh token from cookie
        refresh_token = request.cookies.get(settings.COOKIE_NAME)
        if not refresh_token:
            # If no token, still return success (idempotent)
            response.delete_cookie(
                key=settings.COOKIE_NAME,
                httponly=settings.COOKIE_HTTP_ONLY,
                secure=settings.COOKIE_SECURE,
                samesite=settings.COOKIE_SAME_SITE
            )
            return MessageResponse(message="Logged out successfully")
        
        # Revoke refresh token
        AuthService.logout(db=db, refresh_token=refresh_token)
        
        # Clear cookie
        response.delete_cookie(
            key=settings.COOKIE_NAME,
            httponly=settings.COOKIE_HTTP_ONLY,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAME_SITE
        )
        
        logger.info("user_logged_out")
        return MessageResponse(message="Logged out successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("logout_error", error=str(e), exc_info=True)
        # Clear cookie even on error
        response.delete_cookie(
            key=settings.COOKIE_NAME,
            httponly=settings.COOKIE_HTTP_ONLY,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAME_SITE
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

