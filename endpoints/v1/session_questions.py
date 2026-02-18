"""Questions module endpoints (by-passcode for participants)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.db import get_db
from services.session_questions_service import SessionQuestionsService
from services.session_participant_service import SessionParticipantService
from endpoints.v1.schemas import (
    SessionQuestionMessageCreateRequest,
    SessionQuestionMessagesResponse,
)
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Session Questions"])
optional_bearer = HTTPBearer(auto_error=False)


def _get_participant_id(
    passcode: str,
    db: Session,
    credentials: Optional[HTTPAuthorizationCredentials],
) -> int:
    """Resolve participant ID. Raises HTTPException if not authorized."""
    auth_token = credentials.credentials if credentials is not None else None
    if not auth_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        participant, _ = SessionParticipantService.resolve_participant(
            db, passcode, auth_token, None
        )
        return participant.id
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get(
    "/sessions/by-passcode/{passcode}/modules/questions/{module_id}/messages",
    response_model=SessionQuestionMessagesResponse,
    summary="List question messages",
    description="List messages for Questions module. Requires participant auth.",
    responses={
        200: {"description": "Messages list"},
        401: {"description": "Not authenticated"},
        404: {"description": "Session or module not found"},
    },
)
async def list_question_messages(
    passcode: str,
    module_id: int,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    participant_id = _get_participant_id(passcode, db, credentials)
    try:
        result = SessionQuestionsService.list_messages(
            db, passcode, module_id, limit=limit, offset=offset
        )
        return SessionQuestionMessagesResponse(**result)
    except ValueError as e:
        msg = str(e).lower()
        if "not found" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/sessions/by-passcode/{passcode}/modules/questions/{module_id}/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Create question message",
    description="Post a question or reply. Requires participant auth.",
    responses={
        201: {"description": "Message created"},
        401: {"description": "Not authenticated"},
        404: {"description": "Session or module not found"},
    },
)
async def create_question_message(
    passcode: str,
    module_id: int,
    body: SessionQuestionMessageCreateRequest,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
):
    participant_id = _get_participant_id(passcode, db, credentials)
    try:
        result = SessionQuestionsService.create_message(
            db, passcode, module_id, participant_id, body.content, body.parent_id, body.is_anonymous
        )
        return result
    except ValueError as e:
        msg = str(e).lower()
        if "not found" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/sessions/by-passcode/{passcode}/modules/questions/{module_id}/messages/{msg_id}/like",
    summary="Like a message",
    description="Add like (idempotent). Requires participant auth.",
    responses={
        200: {"description": "Like added or already liked"},
        401: {"description": "Not authenticated"},
        404: {"description": "Message not found"},
    },
)
async def like_question_message(
    passcode: str,
    module_id: int,
    msg_id: int,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
):
    participant_id = _get_participant_id(passcode, db, credentials)
    try:
        result = SessionQuestionsService.add_like(
            db, passcode, module_id, msg_id, participant_id
        )
        return result
    except ValueError as e:
        msg = str(e).lower()
        if "not found" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
