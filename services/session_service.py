"""Session service."""
from typing import Optional
from sqlalchemy.orm import Session
from api.repositories.session_repository import SessionRepository
from api.repositories.workspace_repository import WorkspaceRepository
from api.models.session import Session as SessionModel, SessionStatus
from api.models.workspace import WorkspaceStatus
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class SessionService:
    """Service for session operations."""
    
    @staticmethod
    def start_session(
        db: Session,
        session_id: int,
        user_id: int
    ) -> Optional[SessionModel]:
        """
        Start a session.
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID (for authorization check)
        
        Returns:
            Started session or None if not found
        """
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            return None
        
        # Check workspace ownership
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Session not found or access denied")
        
        # Check if workspace is archived
        if workspace.status == WorkspaceStatus.ARCHIVE.value:
            raise ValueError("Cannot start session in archived workspace")
        
        # Update session status
        SessionRepository.update_status(
            db=db,
            session_id=session_id,
            status=SessionStatus.ACTIVE.value,
            start_datetime=datetime.utcnow()
        )
        
        # Update workspace last_session_at
        WorkspaceRepository.update_stats(
            db=db,
            workspace_id=session.workspace_id,
            last_session_at=datetime.utcnow()
        )
        
        # Commit transaction
        db.commit()
        db.refresh(session)
        
        logger.info("session_started", session_id=session_id, workspace_id=session.workspace_id)
        
        return session
    
    @staticmethod
    def stop_session(
        db: Session,
        session_id: int,
        user_id: int
    ) -> Optional[SessionModel]:
        """
        Stop a session.
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID (for authorization check)
        
        Returns:
            Stopped session or None if not found
        """
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            return None
        
        # Check workspace ownership
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Session not found or access denied")
        
        # Update session status
        SessionRepository.update_status(
            db=db,
            session_id=session_id,
            status=SessionStatus.ENDED.value
        )
        
        # Commit transaction
        db.commit()
        db.refresh(session)
        
        logger.info("session_stopped", session_id=session_id, workspace_id=session.workspace_id)
        
        return session
    
    @staticmethod
    def restore_session(
        db: Session,
        session_id: int,
        user_id: int
    ) -> Optional[SessionModel]:
        """
        Restore session from trash.
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID (for authorization check)
        
        Returns:
            Restored session or None if not found
        """
        session = SessionRepository.restore(db, session_id)
        if not session:
            return None
        
        # Check workspace ownership
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Session not found or access denied")
        
        # Commit transaction
        db.commit()
        db.refresh(session)
        
        logger.info("session_restored", session_id=session_id, workspace_id=session.workspace_id)
        
        return session
    
    @staticmethod
    def delete_session(
        db: Session,
        session_id: int,
        user_id: int,
        hard: bool = False
    ) -> Optional[SessionModel]:
        """
        Delete session (soft or hard).
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID (for authorization check)
            hard: If True, perform hard delete
        
        Returns:
            Deleted session or None if not found
        """
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            return None
        
        # Check workspace ownership
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Session not found or access denied")
        
        # Delete session
        deleted_session = SessionRepository.delete(db, session_id, hard=hard)
        
        if deleted_session:
            # Commit transaction
            db.commit()
            
            logger.info(
                "session_deleted",
                session_id=session_id,
                workspace_id=session.workspace_id,
                hard=hard
            )
        
        return deleted_session

