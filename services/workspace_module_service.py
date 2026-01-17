"""WorkspaceModule service."""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from repositories.workspace_module_repository import WorkspaceModuleRepository
from repositories.workspace_repository import WorkspaceRepository
from models.workspace_module import WorkspaceModule, ModuleType
from utils.module_settings import validate_module_settings
import structlog

logger = structlog.get_logger(__name__)


class WorkspaceModuleService:
    """Service for workspace module operations."""
    
    @staticmethod
    def create_module(
        db: Session,
        workspace_id: int,
        user_id: int,
        name: str,
        module_type: str,
        settings: Optional[Dict[str, Any]] = None
    ) -> WorkspaceModule:
        """
        Create a new workspace module.
        
        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID (for authorization check)
            name: Module name
            module_type: Module type (quiz, poll, questions, timer)
            settings: Module settings (JSON)
            order: Display order (optional)
        
        Returns:
            Created workspace module
        
        Raises:
            ValueError: If workspace not found, access denied, or validation fails
        """
        # Check workspace ownership
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            raise ValueError("Workspace not found")
        
        if workspace.user_id != user_id:
            raise ValueError("Workspace not found or access denied")
        
        if workspace.is_deleted:
            raise ValueError("Cannot create module in deleted workspace")
        
        # Validate module type
        if module_type not in [mt.value for mt in ModuleType]:
            raise ValueError(f"Invalid module type: {module_type}")
        
        # Validate settings
        validate_module_settings(module_type, settings)
        
        # Create module
        module = WorkspaceModuleRepository.create(
            db=db,
            workspace_id=workspace_id,
            name=name,
            module_type=module_type,
            settings=settings
        )
        
        # Commit transaction
        db.commit()
        db.refresh(module)
        
        logger.info("workspace_module_created", module_id=module.id, workspace_id=workspace_id, module_type=module_type)
        
        return module
    
    @staticmethod
    def update_module(
        db: Session,
        workspace_id: int,
        module_id: int,
        user_id: int,
        name: Optional[str] = None,
        module_type: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkspaceModule]:
        """
        Update a workspace module.
        
        Args:
            db: Database session
            workspace_id: Workspace ID
            module_id: Module ID
            user_id: User ID (for authorization check)
            name: Module name (optional)
            module_type: Module type (optional)
            settings: Module settings (optional)
            order: Display order (optional)
        
        Returns:
            Updated workspace module or None if not found
        
        Raises:
            ValueError: If workspace/module not found, access denied, or validation fails
        """
        # Check workspace ownership
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            raise ValueError("Workspace not found")
        
        if workspace.user_id != user_id:
            raise ValueError("Workspace not found or access denied")
        
        # Check module exists and belongs to workspace
        module = WorkspaceModuleRepository.get_by_id(db, module_id)
        if not module:
            raise ValueError("Module not found")
        
        if module.workspace_id != workspace_id:
            raise ValueError("Module not found or access denied")
        
        # Validate module type if provided
        if module_type is not None and module_type not in [mt.value for mt in ModuleType]:
            raise ValueError(f"Invalid module type: {module_type}")
        
        # Validate settings if provided
        if settings is not None:
            validate_module_settings(module_type or module.module_type, settings)
        
        # Update module
        updated_module = WorkspaceModuleRepository.update(
            db=db,
            module_id=module_id,
            name=name,
            module_type=module_type,
            settings=settings
        )
        
        if updated_module:
            db.commit()
            db.refresh(updated_module)
            logger.info("workspace_module_updated", module_id=module_id, workspace_id=workspace_id)
        
        return updated_module
    
    @staticmethod
    def delete_module(
        db: Session,
        workspace_id: int,
        module_id: int,
        user_id: int,
        hard: bool = False
    ) -> Optional[WorkspaceModule]:
        """
        Delete a workspace module.
        
        Args:
            db: Database session
            workspace_id: Workspace ID
            module_id: Module ID
            user_id: User ID (for authorization check)
            hard: If True, hard delete; otherwise soft delete
        
        Returns:
            Deleted workspace module or None if not found
        
        Raises:
            ValueError: If workspace/module not found or access denied
        """
        # Check workspace ownership
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            raise ValueError("Workspace not found")
        
        if workspace.user_id != user_id:
            raise ValueError("Workspace not found or access denied")
        
        # Check module exists and belongs to workspace
        module = WorkspaceModuleRepository.get_by_id(db, module_id)
        if not module:
            raise ValueError("Module not found")
        
        if module.workspace_id != workspace_id:
            raise ValueError("Module not found or access denied")
        
        # Delete module
        deleted_module = WorkspaceModuleRepository.delete(db=db, module_id=module_id, hard=hard)
        
        if deleted_module:
            db.commit()
            logger.info("workspace_module_deleted", module_id=module_id, workspace_id=workspace_id, hard=hard)
        
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

