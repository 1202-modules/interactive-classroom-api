"""Public session guest endpoints (by passcode, email-code flow). No auth required."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.db import get_db
from services.session_guest_service import SessionGuestService
from endpoints.v1.schemas import (
    SessionByPasscodePublicResponse,
    SessionEmailCodeRequestRequest,
    SessionEmailCodeRequestResponse,
    SessionEmailCodeVerifyRequest,
    SessionEmailCodeVerifyResponse,
)
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Session Guest"])
optional_bearer = HTTPBearer(auto_error=False)


@router.get(
    "/sessions/by-passcode/{passcode}",
    response_model=SessionByPasscodePublicResponse,
    summary="Get session by passcode (public)",
    description="Return session info for guest. If Authorization: Bearer <guest_token> sent and valid, returns guest_authenticated=True — frontend skips form and uses stored token.",
    responses={
        200: {"description": "Session info for guest"},
        404: {"description": "Session not found"},
    },
)
async def get_session_by_passcode(
    passcode: str,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
):
    guest_token = credentials.credentials if credentials else None
    try:
        data = SessionGuestService.get_session_by_passcode_public(db, passcode, guest_token)
        return SessionByPasscodePublicResponse(**data)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("get_session_by_passcode_error", passcode=passcode, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/sessions/by-passcode/{passcode}/email-code/request",
    response_model=SessionEmailCodeRequestResponse,
    summary="Request email verification code",
    description="""
    For session in email_code mode: submit email. Always sends code to email. Token is issued
    only from verify endpoint after code check. Autologin = frontend sends stored token in
    GET by-passcode Authorization header.
    """,
    responses={
        200: {"description": "Code sent to email"},
        400: {"description": "Invalid domain or session not in email_code mode"},
        404: {"description": "Session not found"},
    },
)
async def request_email_code(
    passcode: str,
    body: SessionEmailCodeRequestRequest,
    db: Session = Depends(get_db),
):
    try:
        result = SessionGuestService.request_code(db, passcode, body.email)
        return SessionEmailCodeRequestResponse(**result)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except Exception as e:
        logger.error(
            "request_email_code_error",
            passcode=passcode,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/sessions/by-passcode/{passcode}/email-code/verify",
    response_model=SessionEmailCodeVerifyResponse,
    summary="Verify email code and get guest token",
    description="Verify code sent to email and optionally set display_name. Returns guest access_token.",
    responses={
        200: {"description": "Verified, guest token returned"},
        400: {"description": "Invalid or expired code"},
        404: {"description": "Session not found"},
    },
)
async def verify_email_code(
    passcode: str,
    body: SessionEmailCodeVerifyRequest,
    db: Session = Depends(get_db),
):
    try:
        result = SessionGuestService.verify_code(
            db,
            passcode,
            body.email,
            body.code,
            body.display_name,
        )
        return SessionEmailCodeVerifyResponse(**result)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except Exception as e:
        logger.error(
            "verify_email_code_error",
            passcode=passcode,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
