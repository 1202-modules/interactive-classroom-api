"""Workspace service."""
from typing import List, Optional
from sqlalchemy.orm import Session
from repositories.workspace_repository import WorkspaceRepository
from repositories.session_repository import SessionRepository
from models.workspace import Workspace, WorkspaceStatus
from models.session import SessionStatus
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class WorkspaceService:
    """Service for workspace operations."""
    
    @staticmethod
    def create_workspace(
        db: Session,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        template_settings: Optional[dict] = None
    ) -> Workspace:
        """
        Create a new workspace.
        
        Args:
            db: Database session
            user_id: User ID
            name: Workspace name
            description: Workspace description (optional)
            template_settings: Template settings for sessions (optional)
        
        Returns:
            Created workspace
        """
        workspace = WorkspaceRepository.create(
            db=db,
            user_id=user_id,
            name=name,
            description=description,
            template_settings=template_settings
        )
        
        # Commit transaction
        db.commit()
        db.refresh(workspace)
        
        logger.info("workspace_created", workspace_id=workspace.id, user_id=user_id, name=name)
        
        return workspace
    
    @staticmethod
    def archive_workspace(
        db: Session,
        workspace_id: int,
        user_id: int
    ) -> Optional[Workspace]:
        """
        Archive workspace and end all active sessions.
        
        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID (for authorization check)
        
        Returns:
            Archived workspace or None if not found
        """
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            return None
        
        # Check ownership
        if workspace.user_id != user_id:
            raise ValueError("Workspace not found or access denied")
        
        # Archive all active sessions in workspace
        active_sessions = SessionRepository.get_by_workspace_id(
            db=db,
            workspace_id=workspace_id,
            status=SessionStatus.ACTIVE.value
        )
        
        for session in active_sessions:
            SessionRepository.update_status(
                db=db,
                session_id=session.id,
                status=SessionStatus.ARCHIVE.value
            )
        
        # Update workspace status
        WorkspaceRepository.update_status(
            db=db,
            workspace_id=workspace_id,
            status=WorkspaceStatus.ARCHIVE.value
        )
        
        # Commit transaction
        db.commit()
        db.refresh(workspace)
        
        logger.info(
            "workspace_archived",
            workspace_id=workspace_id,
            user_id=user_id,
            sessions_ended=len(active_sessions)
        )
        
        return workspace
    
    @staticmethod
    def unarchive_workspace(
        db: Session,
        workspace_id: int,
        user_id: int
    ) -> Optional[Workspace]:
        """
        Unarchive workspace.
        
        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID (for authorization check)
        
        Returns:
            Unarchived workspace or None if not found
        """
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            return None
        
        # Check ownership
        if workspace.user_id != user_id:
            raise ValueError("Workspace not found or access denied")
        
        # Update workspace status
        WorkspaceRepository.update_status(
            db=db,
            workspace_id=workspace_id,
            status=WorkspaceStatus.ACTIVE.value
        )
        
        # Commit transaction
        db.commit()
        db.refresh(workspace)
        
        logger.info("workspace_unarchived", workspace_id=workspace_id, user_id=user_id)
        
        return workspace
    
    @staticmethod
    def restore_workspace(
        db: Session,
        workspace_id: int,
        user_id: int
    ) -> Optional[Workspace]:
        """
        Restore workspace from trash.
        
        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID (for authorization check)
        
        Returns:
            Restored workspace or None if not found
        """
        workspace = WorkspaceRepository.restore(db, workspace_id)
        if not workspace:
            return None
        
        # Check ownership
        if workspace.user_id != user_id:
            raise ValueError("Workspace not found or access denied")
        
        # Commit transaction
        db.commit()
        db.refresh(workspace)
        
        logger.info("workspace_restored", workspace_id=workspace_id, user_id=user_id)
        
        return workspace
    
    @staticmethod
    def delete_workspace(
        db: Session,
        workspace_id: int,
        user_id: int,
        hard: bool = False
    ) -> Optional[Workspace]:
        """
        Delete workspace (soft or hard).
        
        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID (for authorization check)
            hard: If True, perform hard delete
        
        Returns:
            Deleted workspace or None if not found
        """
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            return None
        
        # Check ownership
        if workspace.user_id != user_id:
            raise ValueError("Workspace not found or access denied")
        
        # Delete workspace
        deleted_workspace = WorkspaceRepository.delete(db, workspace_id, hard=hard)
        
        if deleted_workspace:
            # Commit transaction
            db.commit()
            
            logger.info(
                "workspace_deleted",
                workspace_id=workspace_id,
                user_id=user_id,
                hard=hard
            )
        
        return deleted_workspace
    
    @staticmethod
    def sync_sessions_on_template_update(
        db: Session,
        workspace_id: int,
        old_template: dict,
        new_template: dict
    ) -> None:
        """
        Synchronize all sessions in workspace when template settings are updated.
        
        For each session:
        - Get current merged settings (old template + custom_settings if exists)
        - Compare merged settings with new template recursively
        - Update custom_settings based on differences
        
        Args:
            db: Database session
            workspace_id: Workspace ID
            old_template: Old template settings (before update)
            new_template: New template settings (after update)
        """
        from utils.settings import merge_settings, calculate_settings_diff
        
        # Get all sessions in workspace (including archived/deleted)
        all_sessions = SessionRepository.get_by_workspace_id(
            db=db,
            workspace_id=workspace_id,
            status=None,  # Get all statuses
            include_deleted=True
        )
        
        for session in all_sessions:
            # Get current merged settings (old template + custom_settings if exists)
            current_merged = merge_settings(old_template or {}, session.custom_settings or {})
            
            # Calculate differences between merged and new template
            new_diff = calculate_settings_diff(new_template or {}, current_merged)
            
            # Update custom_settings
            if new_diff:
                session.custom_settings = new_diff
            else:
                # All values now match new template
                session.custom_settings = None
        
        logger.info(
            "sessions_synced_on_template_update",
            workspace_id=workspace_id,
            sessions_count=len(all_sessions)
        )
    
    @staticmethod
    def update_workspace(
        db: Session,
        workspace_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        template_settings: Optional[dict] = None
    ) -> Optional[Workspace]:
        """
        Update workspace.
        
        If template_settings is updated, synchronize all sessions in workspace.
        
        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID (for authorization check)
            name: Workspace name (optional)
            description: Workspace description (optional)
            template_settings: Template settings (optional)
        
        Returns:
            Updated workspace or None if not found
        """
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            return None
        
        # Check ownership
        if workspace.user_id != user_id:
            raise ValueError("Workspace not found or access denied")
        
        # Store old template for synchronization
        old_template = workspace.template_settings or {}
        
        # Update workspace
        updated_workspace = WorkspaceRepository.update(
            db=db,
            workspace_id=workspace_id,
            name=name,
            description=description,
            template_settings=template_settings
        )
        
        if not updated_workspace:
            return None
        
        # If template_settings was updated, synchronize all sessions
        if template_settings is not None and old_template != template_settings:
            new_template = template_settings or {}
            WorkspaceService.sync_sessions_on_template_update(
                db=db,
                workspace_id=workspace_id,
                old_template=old_template,
                new_template=new_template
            )
        
        # Commit transaction
        db.commit()
        db.refresh(workspace)
        
        logger.info("workspace_updated", workspace_id=workspace_id, user_id=user_id)
        
        return workspace

