"""Session join endpoints (anonymous, registered, guest, sso)."""
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.db import get_db
from core.auth import get_current_user, get_current_guest_user
from services.session_join_service import SessionJoinService
from endpoints.v1.schemas import (
    SessionJoinAnonymousRequest,
    SessionJoinAnonymousResponse,
    SessionJoinRegisteredResponse,
    SessionJoinGuestResponse,
)
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Session Join"])


def _handle_join_error(e: Exception, passcode: str) -> HTTPException:
    """Map service errors to HTTP responses."""
    msg = str(e).lower()
    if "not found" in msg:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if isinstance(e, NotImplementedError):
        return HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/sessions/by-passcode/{passcode}/join/anonymous",
    response_model=SessionJoinAnonymousResponse,
    summary="Join session as anonymous",
    description="Create anonymous participant. Returns participant_token for subsequent requests (heartbeat, etc). No auth required.",
    responses={
        200: {"description": "Joined, participant_token returned"},
        400: {"description": "Session not in anonymous mode or max participants reached"},
        404: {"description": "Session not found"},
    },
)
async def join_anonymous(
    passcode: str,
    body: SessionJoinAnonymousRequest | None = Body(default=None),
    db: Session = Depends(get_db),
):
    try:
        display_name = (body.display_name if body else None)
        result = SessionJoinService.join_anonymous(db, passcode, display_name)
        return SessionJoinAnonymousResponse(**result)
    except ValueError as e:
        raise _handle_join_error(e, passcode)
    except Exception as e:
        logger.error("join_anonymous_error", passcode=passcode, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/sessions/by-passcode/{passcode}/join/registered",
    response_model=SessionJoinRegisteredResponse,
    summary="Join session as registered user",
    description="Create or return participant for authenticated user. Use Authorization: Bearer <user_token>.",
    responses={
        200: {"description": "Joined"},
        400: {"description": "Session not in registered mode"},
        401: {"description": "Invalid user token"},
        404: {"description": "Session not found"},
    },
)
async def join_registered(
    passcode: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        result = SessionJoinService.join_registered(db, passcode, current_user["user_id"])
        return SessionJoinRegisteredResponse(**result)
    except ValueError as e:
        raise _handle_join_error(e, passcode)
    except Exception as e:
        logger.error("join_registered_error", passcode=passcode, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/sessions/by-passcode/{passcode}/join/guest",
    response_model=SessionJoinGuestResponse,
    summary="Join session as guest (email-code)",
    description="Create or return participant for verified guest. Use Authorization: Bearer <guest_token>. Complete email-code flow first.",
    responses={
        200: {"description": "Joined"},
        400: {"description": "Session not in email_code mode or guest not verified"},
        401: {"description": "Invalid guest token"},
        404: {"description": "Session not found"},
    },
)
async def join_guest(
    passcode: str,
    db: Session = Depends(get_db),
    current_guest: dict = Depends(get_current_guest_user),
):
    try:
        result = SessionJoinService.join_guest(db, passcode, current_guest["email"])
        return SessionJoinGuestResponse(**result)
    except ValueError as e:
        raise _handle_join_error(e, passcode)
    except Exception as e:
        logger.error("join_guest_error", passcode=passcode, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/sessions/by-passcode/{passcode}/join/sso",
    summary="Join session via SSO (stub)",
    description="SSO join is WIP. Returns 501 NotImplemented.",
    responses={
        400: {"description": "Session not in sso mode"},
        404: {"description": "Session not found"},
        501: {"description": "SSO not implemented"},
    },
)
async def join_sso(
    passcode: str,
    db: Session = Depends(get_db),
):
    try:
        SessionJoinService.join_sso(db, passcode)
    except NotImplementedError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except ValueError as e:
        raise _handle_join_error(e, passcode)
    except Exception as e:
        logger.error("join_sso_error", passcode=passcode, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
