"""Pydantic schemas for API requests and responses."""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# Authentication Schemas
class RegisterRequest(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")


class RegisterResponse(BaseModel):
    """Schema for registration response."""
    email: str = Field(..., description="User email")
    verification_code_sent: bool = Field(..., description="Whether verification code was sent")


class VerifyEmailRequest(BaseModel):
    """Schema for email verification."""
    email: EmailStr = Field(..., description="User email address")
    code: str = Field(..., min_length=6, max_length=6, description="Verification code")


class VerifyEmailResponse(BaseModel):
    """Schema for email verification response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")


class LoginRequest(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Schema for login response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")


class ResendCodeRequest(BaseModel):
    """Schema for resending verification code."""
    email: EmailStr = Field(..., description="User email address")


class ResendCodeResponse(BaseModel):
    """Schema for resend code response."""
    verification_code_sent: bool = Field(..., description="Whether verification code was sent")


class RefreshResponse(BaseModel):
    """Schema for refresh token response."""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")


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
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")


# Workspace Schemas
class WorkspaceResponse(BaseModel):
    """Schema for workspace response."""
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    status: str
    session_settings: Optional[Dict[str, Any]] = None
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
    name: str = Field(..., min_length=1, max_length=200, description="Workspace name")
    description: Optional[str] = Field(None, max_length=1000, description="Workspace description")
    session_settings: Optional[Dict[str, Any]] = Field(None, description="Session settings (JSON)")


class WorkspaceUpdateRequest(BaseModel):
    """Schema for updating workspace."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Workspace name")
    description: Optional[str] = Field(None, max_length=1000, description="Workspace description")
    session_settings: Optional[Dict[str, Any]] = Field(None, description="Session settings (JSON)")


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
    status: str
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
    name: str = Field(..., min_length=1, max_length=200, description="Session name")
    description: Optional[str] = Field(None, max_length=1000, description="Session description")


class SessionUpdateRequest(BaseModel):
    """Schema for updating session."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Session name")
    description: Optional[str] = Field(None, max_length=1000, description="Session description")


# Common Schemas
class MessageResponse(BaseModel):
    """Schema for simple message response."""
    message: str = Field(..., description="Response message")


class ErrorResponse(BaseModel):
    """Schema for error response."""
    detail: str = Field(..., description="Error detail")

