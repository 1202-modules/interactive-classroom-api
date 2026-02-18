"""SessionModule repository."""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.session_module import SessionModule
from models.session import Session as SessionModel


class SessionModuleRepository:
    """Repository for session module operations."""
    
    @staticmethod
    def get_by_id(db: Session, module_id: int) -> Optional[SessionModule]:
        """Get session module by ID."""
        return db.query(SessionModule).filter(
            SessionModule.id == module_id
        ).first()
    
    @staticmethod
    def get_by_session_id(
        db: Session,
        session_id: int,
        include_deleted: bool = False
    ) -> List[SessionModule]:
        """Get session modules by session ID."""
        query = db.query(SessionModule).filter(SessionModule.session_id == session_id)
        
        if not include_deleted:
            query = query.filter(SessionModule.is_deleted == False)
        
        return query.order_by(SessionModule.created_at.asc()).all()
    
    @staticmethod
    def get_active_module(db: Session, session_id: int) -> Optional[SessionModule]:
        """Get active module for a session."""
        return db.query(SessionModule).filter(
            SessionModule.session_id == session_id,
            SessionModule.is_active == True,
            SessionModule.is_deleted == False
        ).first()
    
    @staticmethod
    def create(
        db: Session,
        session_id: int,
        name: str,
        module_type: str,
        settings: Optional[Dict[str, Any]] = None,
        is_active: bool = False
    ) -> SessionModule:
        """Create a new session module (without commit)."""
        module = SessionModule(
            session_id=session_id,
            name=name,
            module_type=module_type,
            settings=settings,
            is_active=is_active
        )
        db.add(module)
        return module
    
    @staticmethod
    def copy_from_workspace_module(
        db: Session,
        session_id: int,
        workspace_module_id: int,
        name: Optional[str] = None
    ) -> Optional[SessionModule]:
        """Copy a workspace module to a session (without commit)."""
        from repositories.workspace_module_repository import WorkspaceModuleRepository
        
        workspace_module = WorkspaceModuleRepository.get_by_id(db, workspace_module_id)
        if not workspace_module:
            return None
        
        # Use provided name or workspace module name
        module_name = name or workspace_module.name

        # Merge workspace_module_id into settings for used_in_sessions counting
        settings = dict(workspace_module.settings) if workspace_module.settings else {}
        settings['workspace_module_id'] = workspace_module_id

        # Create session module with workspace module data (clone)
        return SessionModuleRepository.create(
            db=db,
            session_id=session_id,
            name=module_name,
            module_type=workspace_module.module_type,
            settings=settings
        )
    
    @staticmethod
    def set_active_module(
        db: Session,
        session_id: int,
        module_id: int
    ) -> Optional[SessionModule]:
        """Set active module for a session (deactivates others, without commit)."""
        # Deactivate all other modules in the session
        db.query(SessionModule).filter(
            SessionModule.session_id == session_id,
            SessionModule.id != module_id,
            SessionModule.is_deleted == False
        ).update({SessionModule.is_active: False})
        
        # Activate the specified module
        module = SessionModuleRepository.get_by_id(db, module_id)
        if not module or module.session_id != session_id:
            return None
        
        module.is_active = True
        
        # Update session.active_module_id
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if session:
            session.active_module_id = module_id
        
        return module
    
    @staticmethod
    def deactivate_all_modules(db: Session, session_id: int) -> None:
        """Deactivate all modules in a session (without commit)."""
        db.query(SessionModule).filter(
            SessionModule.session_id == session_id,
            SessionModule.is_deleted == False
        ).update({SessionModule.is_active: False})
        
        # Clear session.active_module_id
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if session:
            session.active_module_id = None
    
    @staticmethod
    def update(
        db: Session,
        module_id: int,
        name: Optional[str] = None,
        module_type: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        order: Optional[int] = None
    ) -> Optional[SessionModule]:
        """Update an existing session module (without commit)."""
        module = SessionModuleRepository.get_by_id(db, module_id)
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
    def soft_delete(db: Session, module_id: int) -> Optional[SessionModule]:
        """Soft delete a session module (without commit)."""
        module = SessionModuleRepository.get_by_id(db, module_id)
        if not module or module.is_deleted:
            return None
        
        # If this was the active module, clear active_module_id in session
        if module.is_active:
            session = db.query(SessionModel).filter(SessionModel.id == module.session_id).first()
            if session:
                session.active_module_id = None
        
        module.is_deleted = True
        module.deleted_at = datetime.now(timezone.utc)
        module.is_active = False  # Deactivate when deleted
        return module
    
    @staticmethod
    def restore(db: Session, module_id: int) -> Optional[SessionModule]:
        """Restore a soft-deleted session module (without commit)."""
        module = db.query(SessionModule).filter(
            SessionModule.id == module_id,
            SessionModule.is_deleted == True
        ).first()
        
        if not module:
            return None
        
        module.is_deleted = False
        module.deleted_at = None
        return module
    
    @staticmethod
    def count_by_workspace_module_id(
        db: Session,
        workspace_id: int,
        workspace_module_id: int,
    ) -> int:
        """Count session modules (non-deleted) that were created from this workspace module."""
        sessions = db.query(SessionModel.id).filter(
            SessionModel.workspace_id == workspace_id,
            SessionModel.is_deleted == False,
        ).all()
        session_ids = [s.id for s in sessions]
        if not session_ids:
            return 0
        modules = (
            db.query(SessionModule)
            .filter(
                SessionModule.session_id.in_(session_ids),
                SessionModule.is_deleted == False,
            )
            .all()
        )
        return sum(
            1 for m in modules
            if m.settings and m.settings.get('workspace_module_id') == workspace_module_id
        )

    @staticmethod
    def delete(db: Session, module_id: int, hard: bool = False) -> Optional[SessionModule]:
        """Delete a session module (without commit)."""
        if hard:
            module = db.query(SessionModule).filter(SessionModule.id == module_id).first()
            if module:
                # If this was the active module, clear active_module_id in session
                if module.is_active:
                    session = db.query(SessionModel).filter(SessionModel.id == module.session_id).first()
                    if session:
                        session.active_module_id = None
                db.delete(module)
            return module
        else:
            return SessionModuleRepository.soft_delete(db, module_id)

