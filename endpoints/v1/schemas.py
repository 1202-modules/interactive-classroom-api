"""Pydantic schemas for API requests and responses."""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
import enum


# Authentication Schemas
class RegisterRequest(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(..., description="User email address", example="user@example.com")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)", example="SecurePass123")
    first_name: Optional[str] = Field(None, max_length=100, description="First name", example="John")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name", example="Doe")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "first_name": "John",
                "last_name": "Doe",
            }
        }


class RegisterResponse(BaseModel):
    """Schema for registration response."""
    email: str = Field(..., description="User email", example="user@example.com")
    verification_code_sent: bool = Field(..., description="Whether verification code was sent", example=True)
    code: Optional[str] = Field(None, description="Code in response (only when SMTP not configured, for testing)")

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
    remember_me: bool = Field(
        default=True,
        description="If True, keep logged in for 7 days (cookie). If False, session ends when browser closes."
    )

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
    code: Optional[str] = Field(None, description="Code in response (only when SMTP not configured, for testing)")

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
    preferences: Optional[Dict[str, Any]] = None
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


class UserPreferencesResponse(BaseModel):
    """Schema for user preferences response."""
    timezone: Optional[str] = Field(None, description="User timezone (IANA, e.g. Europe/Moscow)")
    timezone_mode: Optional[str] = Field(None, description="'auto' or 'manual'")
    theme: Optional[str] = Field(None, description="'light', 'dark', or 'auto'")
    sound_enabled: Optional[bool] = Field(None, description="Play notification sounds (e.g. timer)")
    browser_notifications: Optional[bool] = Field(None, description="Enable browser notifications")
    notification_sound: Optional[str] = Field(None, description="Sound preset: default, gentle, classic, none")


class UserPreferencesUpdateRequest(BaseModel):
    """Schema for updating user preferences."""
    timezone: Optional[str] = Field(None, description="User timezone (IANA)")
    timezone_mode: Optional[str] = Field(None, description="'auto' or 'manual'")
    theme: Optional[str] = Field(None, description="'light', 'dark', or 'auto'")
    sound_enabled: Optional[bool] = Field(None, description="Play notification sounds")
    browser_notifications: Optional[bool] = Field(None, description="Enable browser notifications")
    notification_sound: Optional[str] = Field(None, description="Sound preset")


# Workspace Schemas
class WorkspaceResponse(BaseModel):
    """Schema for workspace response."""
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    status: str
    template_settings: Optional[Dict[str, Any]] = None
    participant_count: int = Field(default=0, description="Sum of stopped_participant_count from stopped sessions + active participants in live sessions")
    session_count: int = Field(default=0, description="Number of live (active) sessions")
    has_live_session: bool = Field(default=False, description="Whether workspace has at least one live (running) session")
    last_session_started_at: Optional[datetime] = Field(default=None, description="Start time of the most recently started session in this workspace")
    is_deleted: bool = Field(default=False, description="Whether workspace is deleted")
    deleted_at: Optional[datetime] = Field(default=None, description="Timestamp when workspace was deleted")
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
    template_settings: Optional[Dict[str, Any]] = Field(
        None,
        description="Session defaults: default_session_duration_min (5-420), max_participants (1-500), participant_entry_mode (anonymous|registered|sso|email_code)",
        example={
            "default_session_duration_min": 90,
            "max_participants": 100,
            "participant_entry_mode": "anonymous",
        },
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Workspace",
                "description": "A workspace for my classes",
                "template_settings": {
                    "default_session_duration_min": 90,
                    "max_participants": 100,
                    "participant_entry_mode": "anonymous",
                }
            }
        }


class WorkspaceUpdateRequest(BaseModel):
    """Schema for updating workspace."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Workspace name", example="Updated Workspace")
    description: Optional[str] = Field(None, max_length=1000, description="Workspace description", example="Updated description")
    template_settings: Optional[Dict[str, Any]] = Field(
        None,
        description="Session defaults: default_session_duration_min (5-420), max_participants (1-500), participant_entry_mode (anonymous|registered|sso|email_code)",
        example={
            "default_session_duration_min": 60,
            "max_participants": 50,
            "participant_entry_mode": "registered",
        },
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Workspace",
                "description": "Updated description",
                "template_settings": {
                    "default_session_duration_min": 60,
                    "max_participants": 50,
                    "participant_entry_mode": "registered",
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
    participant_count: int = Field(default=0, description="Current participant count: stopped_participant_count if stopped, else active participants in live session")
    stopped_participant_count: int
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    is_stopped: bool
    status: str
    passcode: Optional[str] = None  # Session passcode (6 characters)
    settings: Optional[Dict[str, Any]] = None  # Session settings (full copy)
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None

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
    settings: Optional[Dict[str, Any]] = Field(None, description="Session settings (JSON). Merged with workspace template at creation; stored in full.", example={"default_session_duration_min": 60, "max_participants": 50})

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Lecture 1",
                "description": "Introduction to the course",
                "settings": {
                    "default_session_duration_min": 60,
                    "max_participants": 50
                }
            }
        }


class SessionUpdateRequest(BaseModel):
    """Schema for updating session."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Session name", example="Updated Lecture 1")
    description: Optional[str] = Field(None, max_length=1000, description="Session description", example="Updated description")
    settings: Optional[Dict[str, Any]] = Field(None, description="Session settings (JSON). Full replace.", example={"poll_duration": 45})

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


# Module Schemas
class ModuleType(str, enum.Enum):
    """Module type enum."""
    QUIZ = "quiz"
    POLL = "poll"
    QUESTIONS = "questions"
    TIMER = "timer"


# Workspace Module Schemas
class WorkspaceModuleResponse(BaseModel):
    """Schema for workspace module response."""
    id: int
    workspace_id: int
    name: str
    module_type: str
    settings: Optional[Dict[str, Any]] = None
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "workspace_id": 1,
                "name": "Quiz Module",
                "module_type": "quiz",
                "settings": {
                    "question": "What is 2+2?",
                    "options": [
                        {"text": "3", "is_correct": False},
                        {"text": "4", "is_correct": True},
                        {"text": "5", "is_correct": False}
                    ]
                },
                "created_at": "2025-01-16T10:00:00Z",
                "updated_at": "2025-01-16T10:00:00Z"
            }
        }


class WorkspaceModuleCreateRequest(BaseModel):
    """Schema for creating workspace module."""
    name: str = Field(..., min_length=1, max_length=200, description="Module name", example="Quiz Module")
    module_type: str = Field(..., description="Module type (quiz, poll, questions, timer)", example="quiz")
    settings: Optional[Dict[str, Any]] = Field(None, description="Module settings (JSON)", example={"question": "What is 2+2?"})

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Quiz Module",
                "module_type": "quiz",
                "settings": {
                    "question": "What is 2+2?",
                    "options": [
                        {"text": "3", "is_correct": False},
                        {"text": "4", "is_correct": True}
                    ]
                }
            }
        }


class WorkspaceModuleUpdateRequest(BaseModel):
    """Schema for updating workspace module."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Module name", example="Updated Quiz Module")
    module_type: Optional[str] = Field(None, description="Module type", example="quiz")
    settings: Optional[Dict[str, Any]] = Field(None, description="Module settings (JSON)", example={"question": "Updated question"})

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Quiz Module",
                "settings": {
                    "question": "Updated question"
                }
            }
        }


# Session Module Schemas
class SessionModuleResponse(BaseModel):
    """Schema for session module response."""
    id: int
    session_id: int
    name: str
    module_type: str
    settings: Optional[Dict[str, Any]] = None
    is_active: bool
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "session_id": 1,
                "name": "Quiz Module-1",
                "module_type": "quiz",
                "settings": {
                    "question": "What is 2+2?",
                    "options": [
                        {"text": "3", "is_correct": False},
                        {"text": "4", "is_correct": True}
                    ]
                },
                "is_active": False,
                "created_at": "2025-01-16T10:00:00Z",
                "updated_at": "2025-01-16T10:00:00Z"
            }
        }


class SessionModuleCreateRequest(BaseModel):
    """Schema for creating session module (clones from workspace module)."""
    workspace_module_id: int = Field(..., description="Workspace module ID to clone from", example=1)
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Module name (auto-generated with suffix if not provided)", example="Quiz Module-1")

    class Config:
        json_schema_extra = {
            "example": {
                "workspace_module_id": 1,
                "name": "Quiz Module-1"
            }
        }


class SessionModuleUpdateRequest(BaseModel):
    """Schema for updating session module."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Module name", example="Updated Quiz Module")
    module_type: Optional[str] = Field(None, description="Module type", example="quiz")
    settings: Optional[Dict[str, Any]] = Field(None, description="Module settings (JSON)", example={"question": "Updated question"})

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Quiz Module",
                "settings": {
                    "question": "Updated question"
                }
            }
        }


# Passcode Schemas
class PasscodeResponse(BaseModel):
    """Schema for passcode response."""
    passcode: str = Field(..., description="Session passcode", example="ABC123")

    class Config:
        json_schema_extra = {
            "example": {
                "passcode": "ABC123"
            }
        }


class RegeneratePasscodeRequest(BaseModel):
    """Schema for regenerating passcode (empty body)."""

    class Config:
        json_schema_extra = {
            "example": {}
        }


# Session guest (by-passcode, email-code) schemas
class SessionByPasscodePublicResponse(BaseModel):
    """Public session info for guest join screen."""
    id: int = Field(..., description="Session ID")
    name: str = Field(..., description="Session name")
    participant_entry_mode: str = Field(..., description="anonymous | registered | sso | email_code")
    is_started: bool = Field(..., description="True when session is started and participants can join")
    email_code_domains_whitelist: List[str] = Field(default_factory=list, description="Allowed email domains for email_code")
    sso_organization_id: Optional[int] = Field(None, description="Organization ID when participant_entry_mode is sso")
    guest_authenticated: Optional[bool] = Field(None, description="True if valid guest token in Authorization — skip form, use stored token")
    email: Optional[str] = Field(None, description="Guest email when guest_authenticated")
    display_name: Optional[str] = Field(None, description="Display name when guest_authenticated")
    participant_authenticated: Optional[bool] = Field(None, description="True if valid participant (anonymous) token — return to session without join form")
    participant_id: Optional[int] = Field(None, description="Participant ID when participant_authenticated")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Lecture 1",
                "participant_entry_mode": "email_code",
                "is_started": True,
                "email_code_domains_whitelist": ["uni.edu", "company.com"],
            }
        }


class SessionEmailCodeRequestRequest(BaseModel):
    """Request verification code for email-code join."""
    email: EmailStr = Field(..., description="Guest email", example="user@domain.com")


class SessionEmailCodeRequestResponse(BaseModel):
    """Response: code sent to email. Token only from verify endpoint."""
    verification_code_sent: bool = Field(..., description="True if code was sent to email")
    code: Optional[str] = Field(None, description="Code in response (only when SMTP not configured, for testing)")


class SessionEmailCodeVerifyRequest(BaseModel):
    """Verify email code and optional display name."""
    email: EmailStr = Field(..., description="Guest email", example="user@domain.com")
    code: str = Field(..., min_length=1, description="Verification code")
    display_name: Optional[str] = Field(None, description="Display name for the guest")


class SessionEmailCodeVerifyResponse(BaseModel):
    """Guest token after successful verification."""
    access_token: str = Field(..., description="Guest JWT")
    token_type: str = Field(default="bearer", description="Token type")
    email: str = Field(..., description="Guest email")
    display_name: Optional[str] = Field(None, description="Display name")


# Session join schemas (anonymous, registered, guest, sso)
class SessionJoinAnonymousRequest(BaseModel):
    """Optional display name for anonymous participant."""
    display_name: Optional[str] = Field(None, description="Display name", max_length=200)
    fingerprint: str = Field(..., min_length=1, max_length=1024, description="Client fingerprint")


class SessionJoinAnonymousResponse(BaseModel):
    """Participant token for anonymous join."""
    participant_token: str = Field(..., description="JWT for anonymous participant")
    token_type: str = Field(default="bearer", description="Token type")
    participant_id: int = Field(..., description="Participant ID")
    session_id: int = Field(..., description="Session ID")
    display_name: Optional[str] = Field(None, description="Display name; null = show translated fallback on frontend")


class SessionJoinRegisteredResponse(BaseModel):
    """Response for registered user join (use user token for subsequent requests)."""
    participant_id: int = Field(..., description="Participant ID")
    session_id: int = Field(..., description="Session ID")
    display_name: Optional[str] = Field(None, description="Display name; null = show translated fallback on frontend")


class SessionJoinGuestResponse(BaseModel):
    """Response for guest (email-code) join (use guest token for subsequent requests)."""
    participant_id: int = Field(..., description="Participant ID")
    session_id: int = Field(..., description="Session ID")
    display_name: Optional[str] = Field(None, description="Display name; null = show translated fallback on frontend")


class SessionJoinGuestRequest(BaseModel):
    """Client fingerprint for email-code join."""
    fingerprint: str = Field(..., min_length=1, max_length=1024, description="Client fingerprint")


# Heartbeat and participants
class SessionHeartbeatRequest(BaseModel):
    """Optional body for heartbeat. Anonymous may send participant_token here."""
    participant_token: Optional[str] = Field(None, description="Participant JWT for anonymous (alternative to Authorization)")


class SessionParticipantItem(BaseModel):
    """Single participant in list. display_name null/empty = show translated fallback on frontend."""
    id: int
    display_name: Optional[str] = None
    participant_type: str
    guest_email: Optional[str] = Field(None, description="Email for guest_email entry (show under name or instead of name)")
    is_active: bool
    is_banned: bool = False
    created_at: Optional[str] = Field(None, description="When the participant joined (ISO datetime)")


class SessionParticipantPatchRequest(BaseModel):
    """Patch participant (lecturer)."""
    is_banned: Optional[bool] = Field(None, description="Ban participant for this session")


class SessionParticipantSelfPatchRequest(BaseModel):
    """Patch own participant profile (by passcode)."""
    display_name: str = Field(..., min_length=1, max_length=200, description="New display name")


class SessionParticipantsResponse(BaseModel):
    """List of participants with active count and max limit."""
    participants: List["SessionParticipantItem"]
    total: int
    active_count: int
    max_participants: Optional[int] = Field(None, description="Max participants from session/workspace settings")


# Questions module
class SessionQuestionMessageCreateRequest(BaseModel):
    """Create question message."""
    content: str = Field(..., min_length=1, description="Message content")
    parent_id: Optional[int] = Field(None, description="Parent message ID for replies")
    is_anonymous: bool = Field(False, description="Submit as anonymous (requires allow_anonymous)")


class SessionQuestionMessageItem(BaseModel):
    """Single question message."""
    id: int
    session_module_id: int
    participant_id: int
    author_display_name: Optional[str] = None
    parent_id: Optional[int] = None
    content: str
    likes_count: int
    liked_by_me: bool = False
    is_answered: bool
    created_at: Optional[str] = None
    pinned_at: Optional[str] = None
    children: List["SessionQuestionMessageItem"] = Field(default_factory=list)


class SessionQuestionModuleSettings(BaseModel):
    """Questions module settings (subset for client)."""
    likes_enabled: bool = True
    allow_anonymous: bool = False
    allow_participant_answers: bool = True
    length_limit_mode: str = "moderate"
    max_length: int = 250


class SessionQuestionMessagesResponse(BaseModel):
    """List of question messages."""
    messages: List[SessionQuestionMessageItem]
    settings: Optional[SessionQuestionModuleSettings] = None


# Resolve forward reference for recursive SessionQuestionMessageItem
SessionQuestionMessageItem.model_rebuild()


class SessionQuestionLecturerPatchRequest(BaseModel):
    """Lecturer patch for message."""
    is_answered: Optional[bool] = Field(None, description="Mark as answered")
    delete: Optional[bool] = Field(None, description="Soft delete message")
    pin: Optional[bool] = Field(None, description="Pin message to top")
    unpin: Optional[bool] = Field(None, description="Unpin message")


# Timer module
class SessionTimerStateResponse(BaseModel):
    """Timer state for display."""
    is_paused: bool
    end_at: Optional[str] = None
    remaining_seconds: Optional[int] = None
    sound_notification_enabled: bool = True


class SessionTimerPauseRequest(BaseModel):
    """Pause timer with remaining seconds from client."""
    remaining_seconds: int = Field(..., ge=0, description="Remaining seconds when pausing")
