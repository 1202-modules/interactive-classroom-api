"""Workspace service."""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from repositories.workspace_repository import WorkspaceRepository
from repositories.session_repository import SessionRepository
from repositories.organization_repository import OrganizationRepository
from models.workspace import Workspace, WorkspaceStatus
from models.session import SessionStatus
from datetime import datetime
import structlog

from utils.template_settings import validate_template_settings as validate_template_settings_schema

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
        # Validate workspace name
        WorkspaceService.validate_workspace_name(name)
        
        # Check for duplicate name
        WorkspaceService.check_workspace_name_duplicate(db, user_id, name)
        
        # Validate template_settings
        WorkspaceService.validate_template_settings(template_settings, db)
        
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
        
        # Check if workspace is deleted
        if workspace.is_deleted:
            raise ValueError("Cannot archive deleted workspace")
        
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
        
        # Check if workspace is deleted
        if workspace.is_deleted:
            raise ValueError("Cannot unarchive deleted workspace")
        
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
        # Get workspace including deleted ones
        workspace = db.query(Workspace).filter(
            Workspace.id == workspace_id,
            Workspace.is_deleted == True
        ).first()
        
        if not workspace:
            # Check if workspace exists but is not deleted
            existing = db.query(Workspace).filter(Workspace.id == workspace_id).first()
            if existing and not existing.is_deleted:
                raise ValueError("Cannot restore workspace that is not deleted")
            return None
        
        # Check ownership
        if workspace.user_id != user_id:
            raise ValueError("Workspace not found or access denied")
        
        # Restore workspace
        workspace.is_deleted = False
        workspace.deleted_at = None
        
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
        
        # Check if workspace has active (running) sessions
        if not hard:
            active_sessions = SessionRepository.get_by_workspace_id(
                db=db,
                workspace_id=workspace_id,
                status=SessionStatus.ACTIVE.value
            )
            # Filter only running sessions (not stopped)
            running_sessions = [s for s in active_sessions if not s.is_stopped]
            if running_sessions:
                raise ValueError(f"Cannot delete workspace with {len(running_sessions)} active running session(s)")
        
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
    def update_workspace(
        db: Session,
        workspace_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        template_settings: Optional[dict] = None
    ) -> Optional[Workspace]:
        """
        Update workspace. Session settings are independent (full copy per session).
        
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
        
        # Check if workspace is deleted
        if workspace.is_deleted:
            raise ValueError("Cannot update deleted workspace")
        
        # Validate workspace name if provided
        if name is not None:
            WorkspaceService.validate_workspace_name(name)
            # Check for duplicate name
            WorkspaceService.check_workspace_name_duplicate(db, user_id, name, exclude_workspace_id=workspace_id)
        
        # Validate template_settings if provided
        if template_settings is not None:
            WorkspaceService.validate_template_settings(template_settings, db)
        
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

        # Commit transaction
        db.commit()
        db.refresh(workspace)
        
        logger.info("workspace_updated", workspace_id=workspace_id, user_id=user_id)
        
        return workspace
    
    @staticmethod
    def validate_workspace_name(name: str) -> None:
        """
        Validate workspace name.
        
        Args:
            name: Workspace name
        
        Raises:
            ValueError: If name is invalid
        """
        if not name or not name.strip():
            raise ValueError("Workspace name cannot be empty")
        
        if len(name.strip()) > 200:
            raise ValueError("Workspace name cannot exceed 200 characters")
    
    @staticmethod
    def check_workspace_name_duplicate(
        db: Session,
        user_id: int,
        name: str,
        exclude_workspace_id: Optional[int] = None
    ) -> None:
        """
        Check if workspace name already exists for user.
        
        Args:
            db: Database session
            user_id: User ID
            name: Workspace name
            exclude_workspace_id: Workspace ID to exclude from check (for updates)
        
        Raises:
            ValueError: If duplicate name found
        """
        workspaces = WorkspaceRepository.get_by_user_id(
            db=db,
            user_id=user_id,
            include_deleted=False
        )
        
        for workspace in workspaces:
            if exclude_workspace_id and workspace.id == exclude_workspace_id:
                continue
            if workspace.name.strip().lower() == name.strip().lower():
                raise ValueError(f"Workspace with name '{name}' already exists")
    
    @staticmethod
    def validate_template_settings(
        template_settings: Optional[dict],
        db: Optional[Session] = None
    ) -> None:
        """
        Validate template_settings against Session defaults schema.

        Validates known fields. When participant_entry_mode is sso and
        sso_organization_id is set, verifies organization exists (requires db).

        Args:
            template_settings: Template settings dictionary (Session defaults)
            db: Optional DB session for organization existence check

        Raises:
            ValueError: If template_settings is invalid
        """
        validate_template_settings_schema(template_settings)
        if db and template_settings and template_settings.get("participant_entry_mode") == "sso":
            org_id = template_settings.get("sso_organization_id")
            if org_id and not OrganizationRepository.get_by_id(db, org_id):
                raise ValueError(f"Organization with id {org_id} not found")

