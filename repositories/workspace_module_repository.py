"""WorkspaceModule repository."""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.workspace_module import WorkspaceModule


class WorkspaceModuleRepository:
    """Repository for workspace module operations."""
    
    @staticmethod
    def get_by_id(db: Session, module_id: int) -> Optional[WorkspaceModule]:
        """Get workspace module by ID."""
        return db.query(WorkspaceModule).filter(
            WorkspaceModule.id == module_id,
            WorkspaceModule.is_deleted == False
        ).first()
    
    @staticmethod
    def get_by_workspace_id(
        db: Session,
        workspace_id: int,
        include_deleted: bool = False
    ) -> List[WorkspaceModule]:
        """Get workspace modules by workspace ID."""
        query = db.query(WorkspaceModule).filter(WorkspaceModule.workspace_id == workspace_id)
        
        if not include_deleted:
            query = query.filter(WorkspaceModule.is_deleted == False)
        
        return query.order_by(WorkspaceModule.created_at.asc()).all()
    
    @staticmethod
    def create(
        db: Session,
        workspace_id: int,
        name: str,
        module_type: str,
        settings: Optional[Dict[str, Any]] = None
    ) -> WorkspaceModule:
        """Create a new workspace module (without commit)."""
        module = WorkspaceModule(
            workspace_id=workspace_id,
            name=name,
            module_type=module_type,
            settings=settings
        )
        db.add(module)
        return module
    
    @staticmethod
    def update(
        db: Session,
        module_id: int,
        name: Optional[str] = None,
        module_type: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkspaceModule]:
        """Update an existing workspace module (without commit)."""
        module = WorkspaceModuleRepository.get_by_id(db, module_id)
        if not module:
            return None
        
        updated = False
        if name is not None and module.name != name:
            module.name = name
            updated = True
        if module_type is not None and module.module_type != module_type:
            module.module_type = module_type
            updated = True
        if settings is not None:
            module.settings = settings
            updated = True
        
        return module if updated else None
    
    @staticmethod
    def soft_delete(db: Session, module_id: int) -> Optional[WorkspaceModule]:
        """Soft delete a workspace module (without commit)."""
        module = WorkspaceModuleRepository.get_by_id(db, module_id)
        if not module or module.is_deleted:
            return None
        
        module.is_deleted = True
        module.deleted_at = datetime.now(timezone.utc)
        return module
    
    @staticmethod
    def restore(db: Session, module_id: int) -> Optional[WorkspaceModule]:
        """Restore a soft-deleted workspace module (without commit)."""
        module = db.query(WorkspaceModule).filter(
            WorkspaceModule.id == module_id,
            WorkspaceModule.is_deleted == True
        ).first()
        
        if not module:
            return None
        
        module.is_deleted = False
        module.deleted_at = None
        return module
    
    @staticmethod
    def delete(db: Session, module_id: int, hard: bool = False) -> Optional[WorkspaceModule]:
        """Delete a workspace module (without commit)."""
        if hard:
            module = db.query(WorkspaceModule).filter(WorkspaceModule.id == module_id).first()
            if module:
                db.delete(module)
            return module
        else:
            return WorkspaceModuleRepository.soft_delete(db, module_id)

