"""Session service."""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from repositories.session_repository import SessionRepository
from repositories.workspace_repository import WorkspaceRepository
from models.session import Session as SessionModel, SessionStatus
from models.workspace import WorkspaceStatus
from datetime import datetime, timezone
import structlog
import json

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
        
        # Check if workspace is deleted
        if workspace.is_deleted:
            raise ValueError("Cannot start session in deleted workspace")
        
        # Check if workspace is archived
        if workspace.status == WorkspaceStatus.ARCHIVE.value:
            raise ValueError("Cannot start session in archived workspace")
        
        # Check if session is deleted
        if session.is_deleted:
            raise ValueError("Cannot start deleted session")
        
        # Check if session is archived
        if session.status == SessionStatus.ARCHIVE.value:
            raise ValueError("Cannot start archived session")
        
        # Check if session is already started (not stopped)
        if not session.is_stopped and session.start_datetime:
            raise ValueError("Cannot start session that is already running")
        
        # Set start_datetime only if NULL (first start)
        start_datetime = None
        if not session.start_datetime:
            start_datetime = datetime.now(timezone.utc)
        
        # Update session: set start_datetime if needed, clear end_datetime
        SessionRepository.update_status(
            db=db,
            session_id=session_id,
            status=SessionStatus.ACTIVE.value,
            start_datetime=start_datetime,
            clear_end_datetime=True
        )
        
        # Clear stopped_participant_count and set is_stopped = False
        SessionRepository.clear_session_run_data(db=db, session_id=session_id)
        
        # Ensure is_stopped is False
        session.is_stopped = False
        
        # Commit transaction
        db.commit()
        db.refresh(session)
        
        logger.info("session_started", session_id=session_id, workspace_id=session.workspace_id)
        
        return session
    
    @staticmethod
    def stop_session(
        db: Session,
        session_id: int,
        user_id: int,
        participant_count: int = 0
    ) -> Optional[SessionModel]:
        """
        Stop a session.
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID (for authorization check)
            participant_count: Number of participants at stop time (default 0, TODO for future)
        
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
        
        # Check if workspace is deleted
        if workspace.is_deleted:
            raise ValueError("Cannot stop session in deleted workspace")
        
        # Check if workspace is archived
        if workspace.status == WorkspaceStatus.ARCHIVE.value:
            raise ValueError("Cannot stop session in archived workspace")
        
        # Check if session is deleted
        if session.is_deleted:
            raise ValueError("Cannot stop deleted session")
        
        # Check if session is archived
        if session.status == SessionStatus.ARCHIVE.value:
            raise ValueError("Cannot stop archived session")
        
        # Check if session is already stopped
        if session.is_stopped:
            raise ValueError("Cannot stop session that is already stopped")
        
        # Check if session was never started
        if not session.start_datetime:
            raise ValueError("Cannot stop session that was never started")
        
        # Validate participant_count
        if participant_count < 0:
            raise ValueError("Participant count cannot be negative")
        
        # Set end_datetime and stopped_participant_count, keep status as ACTIVE
        end_datetime = datetime.now(timezone.utc)
        
        # Validate end_datetime is not earlier than start_datetime
        if session.start_datetime and end_datetime < session.start_datetime:
            raise ValueError("end_datetime cannot be earlier than start_datetime")
        
        SessionRepository.update_status(
            db=db,
            session_id=session_id,
            status=SessionStatus.ACTIVE.value,  # Keep status as ACTIVE
            end_datetime=end_datetime
        )
        
        # Set stopped_participant_count
        SessionRepository.update_stopped_participant_count(
            db=db,
            session_id=session_id,
            stopped_participant_count=participant_count
        )
        
        # Set is_stopped = True
        session.is_stopped = True
        
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
        # Get session including deleted ones
        session = db.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.is_deleted == True
        ).first()
        
        if not session:
            # Check if session exists but is not deleted
            existing = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if existing and not existing.is_deleted:
                raise ValueError("Cannot restore session that is not deleted")
            return None
        
        # Check workspace ownership
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Session not found or access denied")
        
        # Restore session
        session.is_deleted = False
        session.deleted_at = None
        
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
        
        # Check if session is running (not stopped)
        if not session.is_stopped:
            raise ValueError("Cannot delete session that is currently running")
        
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
    
    @staticmethod
    def archive_session(
        db: Session,
        session_id: int,
        user_id: int
    ) -> Optional[SessionModel]:
        """
        Archive a session.
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID (for authorization check)
        
        Returns:
            Archived session or None if not found
        """
        # Get session including deleted ones to check deletion status
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return None
        
        # Check if session is deleted (must check before ownership check)
        if session.is_deleted:
            raise ValueError("Cannot archive deleted session")
        
        # Check workspace ownership
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Session not found or access denied")
        
        # Update session status to ARCHIVE
        SessionRepository.update_status(
            db=db,
            session_id=session_id,
            status=SessionStatus.ARCHIVE.value
        )
        
        # Commit transaction
        db.commit()
        db.refresh(session)
        
        logger.info("session_archived", session_id=session_id, workspace_id=session.workspace_id)
        
        return session
    
    @staticmethod
    def unarchive_session(
        db: Session,
        session_id: int,
        user_id: int
    ) -> Optional[SessionModel]:
        """
        Unarchive a session.
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID (for authorization check)
        
        Returns:
            Unarchived session or None if not found
        """
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            return None
        
        # Check workspace ownership
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Session not found or access denied")
        
        # Check if session is deleted
        if session.is_deleted:
            raise ValueError("Cannot unarchive deleted session")
        
        # Check if workspace is archived
        if workspace.status == WorkspaceStatus.ARCHIVE.value:
            raise ValueError("Cannot unarchive session in archived workspace")
        
        # Update session status to ACTIVE
        SessionRepository.update_status(
            db=db,
            session_id=session_id,
            status=SessionStatus.ACTIVE.value
        )
        
        # Commit transaction
        db.commit()
        db.refresh(session)
        
        logger.info("session_unarchived", session_id=session_id, workspace_id=session.workspace_id)
        
        return session
    
    @staticmethod
    def update_session_settings(
        db: Session,
        session_id: int,
        user_id: int,
        new_settings: dict
    ) -> Optional[SessionModel]:
        """
        Update session settings (full replace).
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID (for authorization check)
            new_settings: New settings to apply
        
        Returns:
            Updated session or None if not found
        """
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            return None
        
        # Check workspace ownership
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Session not found or access denied")
        
        # Check if workspace is deleted
        if workspace.is_deleted:
            raise ValueError("Cannot update settings for session in deleted workspace")
        
        # Check if session is deleted
        if session.is_deleted:
            raise ValueError("Cannot update settings for deleted session")
        
        # Check if workspace is archived
        if workspace.status == WorkspaceStatus.ARCHIVE.value:
            raise ValueError("Cannot update settings for session in archived workspace")
        
        SessionRepository.update_settings(db=db, session_id=session_id, new_settings=new_settings)
        
        # Commit transaction
        db.commit()
        db.refresh(session)
        
        logger.info("session_settings_updated", session_id=session_id, workspace_id=session.workspace_id)
        
        return session
    
    @staticmethod
    def validate_session_name(name: str) -> None:
        """
        Validate session name.
        
        Args:
            name: Session name
        
        Raises:
            ValueError: If name is invalid
        """
        if not name or not name.strip():
            raise ValueError("Session name cannot be empty")
        
        if len(name.strip()) > 200:
            raise ValueError("Session name cannot exceed 200 characters")
    
    @staticmethod
    def check_session_name_duplicate(
        db: Session,
        workspace_id: int,
        name: str,
        exclude_session_id: Optional[int] = None
    ) -> None:
        """
        Check if session name already exists in workspace.
        
        Args:
            db: Database session
            workspace_id: Workspace ID
            name: Session name
            exclude_session_id: Session ID to exclude from check (for updates)
        
        Raises:
            ValueError: If duplicate name found
        """
        sessions = SessionRepository.get_by_workspace_id(
            db=db,
            workspace_id=workspace_id,
            include_deleted=False
        )
        
        for session in sessions:
            if exclude_session_id and session.id == exclude_session_id:
                continue
            if session.name.strip().lower() == name.strip().lower():
                raise ValueError(f"Session with name '{name}' already exists in this workspace")
    
    @staticmethod
    def regenerate_passcode(
        db: Session,
        session_id: int,
        user_id: int
    ) -> Optional[SessionModel]:
        """
        Regenerate passcode for a session.
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID (for authorization check)
        
        Returns:
            Updated session or None if not found
        
        Raises:
            ValueError: If session not found or access denied
        """
        from utils.passcode import generate_unique_passcode
        
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            return None
        
        # Check workspace ownership
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Session not found or access denied")
        
        # Generate new unique passcode
        new_passcode = generate_unique_passcode(db)
        
        # Update session passcode
        session.passcode = new_passcode
        
        # Commit transaction
        db.commit()
        db.refresh(session)
        
        logger.info("session_passcode_regenerated", session_id=session_id, workspace_id=session.workspace_id)
        
        return session
    
    @staticmethod
    def validate_passcode(passcode: str) -> bool:
        """
        Validate passcode format.
        
        Args:
            passcode: Passcode to validate
        
        Returns:
            True if valid, False otherwise
        """
        from utils.passcode import validate_passcode_format
        return validate_passcode_format(passcode)

