"""Timer module endpoints (by-passcode for state, lecturer for control)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.db import get_db
from services.session_timer_service import SessionTimerService
from endpoints.v1.schemas import SessionTimerStateResponse
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Session Timer"])


@router.get(
    "/sessions/by-passcode/{passcode}/modules/timer/{module_id}/state",
    response_model=SessionTimerStateResponse,
    summary="Get timer state",
    description="Current timer state for participants and lecturer. No auth required.",
    responses={
        200: {"description": "Timer state"},
        404: {"description": "Session or module not found"},
    },
)
async def get_timer_state(
    passcode: str,
    module_id: int,
    db: Session = Depends(get_db),
):
    """Get timer state for display."""
    try:
        result = SessionTimerService.get_state(db, passcode, module_id)
        return SessionTimerStateResponse(**result)
    except ValueError as e:
        msg = str(e).lower()
        if "not found" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
