"""Session participants: heartbeat, list (by-passcode and by session_id)."""
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.db import get_db
from core.auth import verify_token
from repositories.session_repository import SessionRepository
from repositories.session_module_repository import SessionModuleRepository
from repositories.workspace_repository import WorkspaceRepository
from repositories.workspace_repository import WorkspaceRepository
from repositories.user_repository import UserRepository
from services.session_participant_service import SessionParticipantService
from endpoints.v1.schemas import (
    SessionHeartbeatRequest,
    SessionParticipantItem,
    SessionParticipantsResponse,
)
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Session Participants"])
optional_bearer = HTTPBearer(auto_error=False)


def _handle_error(e: Exception) -> HTTPException:
    msg = str(e).lower()
    if "not found" in msg:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


def _get_auth_token(credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
    return credentials.credentials if credentials else None


def _resolve_participant_or_lecturer(
    passcode: str,
    db: Session,
    auth_token: Optional[str],
    participant_token_from_body: Optional[str],
):
    """
    Resolve participant for heartbeat. Raises HTTPException on failure.
    Returns (participant, session).
    """
    try:
        return SessionParticipantService.resolve_participant(
            db, passcode, auth_token, participant_token_from_body
        )
    except ValueError as e:
        raise _handle_error(e)


def _can_access_participants_list(
    passcode: str,
    db: Session,
    auth_token: Optional[str],
) -> int:
    """
    Check if caller can access participants list. Returns session_id.
    Caller is either: (a) lecturer (user owns workspace), or (b) participant in session.
    Raises HTTPException if not allowed.
    """
    session = SessionRepository.get_by_passcode(db, passcode)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if not auth_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    payload = verify_token(auth_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    token_type = payload.get("type")

    # Lecturer: user token, owns workspace
    if not token_type or token_type not in ("session_participant", "session_guest"):
        user_id_str = payload.get("sub")
        if user_id_str:
            try:
                user_id = int(user_id_str)
            except (ValueError, TypeError):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            user = UserRepository.get_by_id(db, user_id)
            if user and not getattr(user, "is_deleted", False):
                workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
                if workspace and workspace.user_id == user_id:
                    return session.id

    # Participant: must be in session
    try:
        participant, _ = SessionParticipantService.resolve_participant(
            db, passcode, auth_token, None
        )
        return session.id
    except ValueError:
        pass

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view participants")


@router.post(
    "/sessions/by-passcode/{passcode}/heartbeat",
    status_code=status.HTTP_200_OK,
    summary="Send heartbeat",
    description="Update last_heartbeat_at. Use Authorization Bearer (user/guest/participant_token) or body participant_token for anonymous.",
    responses={
        200: {"description": "Heartbeat recorded"},
        400: {"description": "Missing or invalid token"},
        404: {"description": "Session not found"},
    },
)
async def heartbeat(
    passcode: str,
    body: SessionHeartbeatRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
):
    auth_token = _get_auth_token(credentials)
    participant_token = body.participant_token if body else None

    if not auth_token and not participant_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide Authorization Bearer token or participant_token in body",
        )

    try:
        participant, _ = _resolve_participant_or_lecturer(
            passcode, db, auth_token, participant_token
        )
        SessionParticipantService.heartbeat(db, participant.id)
        return {}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("heartbeat_error", passcode=passcode, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/sessions/by-passcode/{passcode}/participants",
    response_model=SessionParticipantsResponse,
    summary="List participants (by passcode)",
    description="For lecturer (owner) or participant in session. Requires auth.",
    responses={
        200: {"description": "Participants list"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized"},
        404: {"description": "Session not found"},
    },
)
async def list_participants_by_passcode(
    passcode: str,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
):
    auth_token = _get_auth_token(credentials)
    try:
        session_id = _can_access_participants_list(passcode, db, auth_token)
        session = SessionRepository.get_by_id(db, session_id)
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id) if session else None
        merged = SessionRepository.get_merged_settings(session, workspace.template_settings or {}) if session and workspace else {}
        max_participants = merged.get("max_participants")
        participants = SessionParticipantService.list_participants(db, session_id)
        active_count = SessionParticipantService.get_active_count(db, session_id)
        items = [SessionParticipantItem(**p) for p in participants]
        return SessionParticipantsResponse(
            participants=items,
            total=len(items),
            active_count=active_count,
            max_participants=max_participants,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_participants_error", passcode=passcode, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/sessions/by-passcode/{passcode}/modules",
    summary="List session modules (by passcode)",
    description="For lecturer (owner) or participant in session. Requires auth. Returns minimal module info for participant UI.",
    responses={
        200: {"description": "Modules list"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized"},
        404: {"description": "Session not found"},
    },
)
async def list_modules_by_passcode(
    passcode: str,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
):
    auth_token = _get_auth_token(credentials)
    try:
        session_id = _can_access_participants_list(passcode, db, auth_token)
        modules = SessionModuleRepository.get_by_session_id(
            db=db,
            session_id=session_id,
            include_deleted=False,
        )
        items = [
            {
                "id": m.id,
                "name": m.name,
                "module_type": m.module_type,
                "is_active": m.is_active,
            }
            for m in modules
        ]
        active = next((m for m in items if m.get("is_active") is True), None)
        return {
            "modules": items,
            "active_module": active,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_modules_error", passcode=passcode, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
