"""SessionModule service."""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from repositories.session_module_repository import SessionModuleRepository
from repositories.workspace_module_repository import WorkspaceModuleRepository
from repositories.session_repository import SessionRepository
from repositories.workspace_repository import WorkspaceRepository
from models.session_module import SessionModule
from models.workspace_module import ModuleType
from utils.module_settings import validate_module_settings
import structlog

logger = structlog.get_logger(__name__)


class SessionModuleService:
    """Service for session module operations."""
    
    @staticmethod
    def add_module_from_workspace(
        db: Session,
        session_id: int,
        workspace_module_id: int,
        user_id: int,
        name: Optional[str] = None
    ) -> SessionModule:
        """
        Add a module from workspace to session with auto-naming (name-1, name-2, etc.).
        
        Args:
            db: Database session
            session_id: Session ID
            workspace_module_id: Workspace module ID to copy
            user_id: User ID (for authorization check)
            name: Optional custom name (if not provided, auto-generate with suffix)
        
        Returns:
            Created session module
        
        Raises:
            ValueError: If session/workspace module not found, access denied, or validation fails
        """
        # Check session ownership
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise ValueError("Session not found")
        
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Session not found or access denied")
        
        # Check workspace module exists
        workspace_module = WorkspaceModuleRepository.get_by_id(db, workspace_module_id)
        if not workspace_module:
            raise ValueError("Workspace module not found")
        
        if workspace_module.workspace_id != session.workspace_id:
            raise ValueError("Workspace module not found or access denied")
        
        # Auto-generate name if not provided:
        # - first module keeps base name (no suffix)
        # - next duplicates use " (1)", " (2)", ...
        if name is None:
            base_name = workspace_module.name
            # Find existing modules with same base name
            existing_modules = SessionModuleRepository.get_by_session_id(db, session_id)
            existing_names = {m.name for m in existing_modules}

            if base_name not in existing_names:
                name = base_name
            else:
                # Find next available suffix
                suffix = 1
                while f"{base_name} ({suffix})" in existing_names:
                    suffix += 1
                name = f"{base_name} ({suffix})"
        
        # Copy module from workspace
        module = SessionModuleRepository.copy_from_workspace_module(
            db=db,
            session_id=session_id,
            workspace_module_id=workspace_module_id,
            name=name
        )
        
        if not module:
            raise ValueError("Failed to create session module")
        
        # Commit transaction
        db.commit()
        db.refresh(module)
        
        logger.info("session_module_added_from_workspace", 
                   module_id=module.id, session_id=session_id, workspace_module_id=workspace_module_id)
        
        return module
    
    @staticmethod
    def update_module(
        db: Session,
        session_id: int,
        module_id: int,
        user_id: int,
        name: Optional[str] = None,
        module_type: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Optional[SessionModule]:
        """
        Update a session module.
        
        Args:
            db: Database session
            session_id: Session ID
            module_id: Module ID
            user_id: User ID (for authorization check)
            name: Module name (optional)
            module_type: Module type (optional)
            settings: Module settings (optional)
            order: Display order (optional)
        
        Returns:
            Updated session module or None if not found
        
        Raises:
            ValueError: If session/module not found, access denied, or validation fails
        """
        # Check session ownership
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise ValueError("Session not found")
        
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Session not found or access denied")
        
        # Check module exists and belongs to session
        module = SessionModuleRepository.get_by_id(db, module_id)
        if not module:
            raise ValueError("Module not found")
        
        if module.session_id != session_id:
            raise ValueError("Module not found or access denied")
        
        # Validate module type if provided
        if module_type is not None and module_type not in [mt.value for mt in ModuleType]:
            raise ValueError(f"Invalid module type: {module_type}")
        
        # Validate settings if provided
        if settings is not None:
            validate_module_settings(module_type or module.module_type, settings)
        
        # Update module
        updated_module = SessionModuleRepository.update(
            db=db,
            module_id=module_id,
            name=name,
            module_type=module_type,
            settings=settings
        )
        
        if updated_module:
            db.commit()
            db.refresh(updated_module)
            logger.info("session_module_updated", module_id=module_id, session_id=session_id)
        
        return updated_module
    
    @staticmethod
    def set_active_module(
        db: Session,
        session_id: int,
        module_id: int,
        user_id: int
    ) -> Optional[SessionModule]:
        """
        Set active module for a session (deactivates others).
        
        Args:
            db: Database session
            session_id: Session ID
            module_id: Module ID to activate
            user_id: User ID (for authorization check)
        
        Returns:
            Activated session module or None if not found
        
        Raises:
            ValueError: If session/module not found or access denied
        """
        # Check session ownership
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise ValueError("Session not found")
        
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Session not found or access denied")
        
        # Check module exists and belongs to session
        module = SessionModuleRepository.get_by_id(db, module_id)
        if not module:
            raise ValueError("Module not found")
        
        if module.session_id != session_id:
            raise ValueError("Module not found or access denied")
        
        # Set active module
        active_module = SessionModuleRepository.set_active_module(
            db=db,
            session_id=session_id,
            module_id=module_id
        )
        
        if active_module:
            db.commit()
            db.refresh(active_module)
            logger.info("session_module_activated", module_id=module_id, session_id=session_id)
        
        return active_module

    @staticmethod
    def deactivate_active_module(
        db: Session,
        session_id: int,
        user_id: int
    ) -> bool:
        """
        Deactivate the current active module for the session (clear active state).

        Returns:
            True if session was updated (had an active module), False otherwise.
        """
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise ValueError("Session not found")
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Session not found or access denied")
        if not session.active_module_id:
            return False
        SessionModuleRepository.deactivate_all_modules(db=db, session_id=session_id)
        db.commit()
        logger.info("session_module_deactivated", session_id=session_id)
        return True

    @staticmethod
    def delete_module(
        db: Session,
        session_id: int,
        module_id: int,
        user_id: int,
        hard: bool = False
    ) -> Optional[SessionModule]:
        """
        Delete a session module.
        
        Args:
            db: Database session
            session_id: Session ID
            module_id: Module ID
            user_id: User ID (for authorization check)
            hard: If True, hard delete; otherwise soft delete
        
        Returns:
            Deleted session module or None if not found
        
        Raises:
            ValueError: If session/module not found or access denied
        """
        # Check session ownership
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise ValueError("Session not found")
        
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != user_id:
            raise ValueError("Session not found or access denied")
        
        # Check module exists and belongs to session
        module = SessionModuleRepository.get_by_id(db, module_id)
        if not module:
            raise ValueError("Module not found")
        
        if module.session_id != session_id:
            raise ValueError("Module not found or access denied")
        
        # Delete module
        deleted_module = SessionModuleRepository.delete(db=db, module_id=module_id, hard=hard)
        
        if deleted_module:
            db.commit()
            logger.info("session_module_deleted", module_id=module_id, session_id=session_id, hard=hard)
        
        return deleted_module
    
    @staticmethod
    def validate_module_settings(module_type: str, settings: Optional[Dict[str, Any]]) -> None:
        """
        Validate module settings.
        
        Args:
            module_type: Module type
            settings: Settings dictionary
        
        Raises:
            ValueError: If settings are invalid
        """
        from utils.module_settings import validate_module_settings as validate_settings
        validate_settings(module_type, settings)
