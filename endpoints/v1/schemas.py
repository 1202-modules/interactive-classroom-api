"""Pydantic schemas for API requests and responses."""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# Authentication Schemas
class RegisterRequest(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(..., description="User email address", example="user@example.com")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)", example="SecurePass123")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class RegisterResponse(BaseModel):
    """Schema for registration response."""
    email: str = Field(..., description="User email", example="user@example.com")
    verification_code_sent: bool = Field(..., description="Whether verification code was sent", example=True)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "verification_code_sent": True
            }
        }


class VerifyEmailRequest(BaseModel):
    """Schema for email verification."""
    email: EmailStr = Field(..., description="User email address", example="user@example.com")
    code: str = Field(..., min_length=6, max_length=6, description="Verification code", example="123456")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "code": "123456"
            }
        }


class VerifyEmailResponse(BaseModel):
    """Schema for email verification response."""
    access_token: str = Field(..., description="JWT access token", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field(default="bearer", description="Token type", example="bearer")
    user_id: int = Field(..., description="User ID", example=1)
    email: str = Field(..., description="User email", example="user@example.com")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                "token_type": "bearer",
                "user_id": 1,
                "email": "user@example.com"
            }
        }


class LoginRequest(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User email address", example="user@example.com")
    password: str = Field(..., description="User password", example="SecurePass123")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class LoginResponse(BaseModel):
    """Schema for login response."""
    access_token: str = Field(..., description="JWT access token", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field(default="bearer", description="Token type", example="bearer")
    user_id: int = Field(..., description="User ID", example=1)
    email: str = Field(..., description="User email", example="user@example.com")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                "token_type": "bearer",
                "user_id": 1,
                "email": "user@example.com"
            }
        }


class ResendCodeRequest(BaseModel):
    """Schema for resending verification code."""
    email: EmailStr = Field(..., description="User email address", example="user@example.com")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ResendCodeResponse(BaseModel):
    """Schema for resend code response."""
    verification_code_sent: bool = Field(..., description="Whether verification code was sent", example=True)

    class Config:
        json_schema_extra = {
            "example": {
                "verification_code_sent": True
            }
        }


class RefreshResponse(BaseModel):
    """Schema for refresh token response."""
    access_token: str = Field(..., description="New JWT access token", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field(default="bearer", description="Token type", example="bearer")
    user_id: int = Field(..., description="User ID", example=1)
    email: str = Field(..., description="User email", example="user@example.com")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                "token_type": "bearer",
                "user_id": 1,
                "email": "user@example.com"
            }
        }


# User Schemas
class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    email_verified: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Schema for updating user profile."""
    first_name: Optional[str] = Field(None, max_length=100, description="First name", example="John")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name", example="Doe")
    avatar_url: Optional[str] = Field(None, description="Avatar URL", example="https://example.com/avatar.jpg")

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "avatar_url": "https://example.com/avatar.jpg"
            }
        }


# Workspace Schemas
class WorkspaceResponse(BaseModel):
    """Schema for workspace response."""
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    status: str
    template_settings: Optional[Dict[str, Any]] = None
    participant_count: int = Field(default=0, description="Total participant count from all stopped sessions")
    has_live_session: bool = Field(default=False, description="Whether workspace has at least one live (running) session")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkspaceListResponse(BaseModel):
    """Schema for workspace list response."""
    workspaces: List[WorkspaceResponse]
    total: int


class WorkspaceCreateRequest(BaseModel):
    """Schema for creating workspace."""
    name: str = Field(..., min_length=1, max_length=200, description="Workspace name", example="My Workspace")
    description: Optional[str] = Field(None, max_length=1000, description="Workspace description", example="A workspace for my classes")
    template_settings: Optional[Dict[str, Any]] = Field(None, description="Template settings for sessions (JSON)", example={"poll_duration": 30, "show_results": True})

    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Workspace",
                "description": "A workspace for my classes",
                "template_settings": {
                    "poll_duration": 30,
                    "show_results": True,
                    "allow_anonymous": False
                }
            }
        }


class WorkspaceUpdateRequest(BaseModel):
    """Schema for updating workspace."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Workspace name", example="Updated Workspace")
    description: Optional[str] = Field(None, max_length=1000, description="Workspace description", example="Updated description")
    template_settings: Optional[Dict[str, Any]] = Field(None, description="Template settings for sessions (JSON)", example={"poll_duration": 60})

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Workspace",
                "description": "Updated description",
                "template_settings": {
                    "poll_duration": 60,
                    "show_results": True
                }
            }
        }


# Session Schemas
class SessionResponse(BaseModel):
    """Schema for session response."""
    id: int
    workspace_id: int
    name: str
    description: Optional[str] = None
    stopped_participant_count: int
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    is_stopped: bool
    status: str
    settings: Optional[Dict[str, Any]] = None  # Computed merged settings (template + custom)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Schema for session list response."""
    sessions: List[SessionResponse]
    total: int


class SessionCreateRequest(BaseModel):
    """Schema for creating session."""
    name: str = Field(..., min_length=1, max_length=200, description="Session name", example="Lecture 1")
    description: Optional[str] = Field(None, max_length=1000, description="Session description", example="Introduction to the course")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Lecture 1",
                "description": "Introduction to the course"
            }
        }


class SessionUpdateRequest(BaseModel):
    """Schema for updating session."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Session name", example="Updated Lecture 1")
    description: Optional[str] = Field(None, max_length=1000, description="Session description", example="Updated description")
    settings: Optional[Dict[str, Any]] = Field(None, description="Session settings (JSON). Updates will create custom_settings if different from template.", example={"poll_duration": 45})

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Lecture 1",
                "description": "Updated description",
                "settings": {
                    "poll_duration": 45,
                    "show_results": False
                }
            }
        }


# Common Schemas
class MessageResponse(BaseModel):
    """Schema for simple message response."""
    message: str = Field(..., description="Response message", example="Operation completed successfully")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully"
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error response."""
    detail: str = Field(..., description="Error detail", example="Resource not found")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Resource not found"
            }
        }

