"""SessionModuleTimerState repository."""
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from models.session_module_timer_state import SessionModuleTimerState


class SessionModuleTimerStateRepository:
    """Repository for timer state."""

    @staticmethod
    def get_by_module(db: DBSession, session_module_id: int) -> Optional[SessionModuleTimerState]:
        """Get timer state by module ID."""
        return db.query(SessionModuleTimerState).filter(
            SessionModuleTimerState.session_module_id == session_module_id
        ).first()

    @staticmethod
    def get_or_create(
        db: DBSession,
        session_module_id: int,
    ) -> SessionModuleTimerState:
        """Get existing state or create default (no commit)."""
        state = SessionModuleTimerStateRepository.get_by_module(db, session_module_id)
        if state:
            return state
        state = SessionModuleTimerState(
            session_module_id=session_module_id,
            is_paused=True,
            end_at=None,
            remaining_seconds=None,
        )
        db.add(state)
        return state

    @staticmethod
    def start(db: DBSession, session_module_id: int, duration_seconds: int) -> SessionModuleTimerState:
        """Start timer: end_at = now + duration, is_paused = False (no commit)."""
        state = SessionModuleTimerStateRepository.get_or_create(db, session_module_id)
        now = datetime.now(timezone.utc)
        state.end_at = now + timedelta(seconds=duration_seconds)
        state.remaining_seconds = None
        state.is_paused = False
        state.updated_at = now
        return state

    @staticmethod
    def pause(db: DBSession, session_module_id: int, remaining_seconds: int) -> Optional[SessionModuleTimerState]:
        """Pause: remaining_seconds, is_paused = True, end_at = None (no commit)."""
        state = SessionModuleTimerStateRepository.get_by_module(db, session_module_id)
        if not state:
            return None
        now = datetime.now(timezone.utc)
        state.remaining_seconds = remaining_seconds
        state.end_at = None
        state.is_paused = True
        state.updated_at = now
        return state

    @staticmethod
    def resume(db: DBSession, session_module_id: int) -> Optional[SessionModuleTimerState]:
        """Resume: remaining_seconds -> end_at, is_paused = False (no commit)."""
        state = SessionModuleTimerStateRepository.get_by_module(db, session_module_id)
        if not state or state.remaining_seconds is None:
            return None
        now = datetime.now(timezone.utc)
        state.end_at = now + timedelta(seconds=state.remaining_seconds)
        state.remaining_seconds = None
        state.is_paused = False
        state.updated_at = now
        return state

    @staticmethod
    def reset(db: DBSession, session_module_id: int) -> Optional[SessionModuleTimerState]:
        """Reset: clear state to default (no commit)."""
        state = SessionModuleTimerStateRepository.get_by_module(db, session_module_id)
        if not state:
            return None
        now = datetime.now(timezone.utc)
        state.is_paused = True
        state.end_at = None
        state.remaining_seconds = None
        state.updated_at = now
        return state
