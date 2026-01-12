"""Workspace repository."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models.workspace import Workspace, WorkspaceStatus


class WorkspaceRepository:
    """Repository for workspace operations."""
    
    @staticmethod
    def get_by_id(db: Session, workspace_id: int) -> Optional[Workspace]:
        """Get workspace by ID."""
        return db.query(Workspace).filter(
            Workspace.id == workspace_id,
            Workspace.is_deleted == False
        ).first()
    
    @staticmethod
    def get_by_user_id(
        db: Session,
        user_id: int,
        status: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[Workspace]:
        """Get workspaces by user ID."""
        query = db.query(Workspace).filter(Workspace.user_id == user_id)
        
        if not include_deleted:
            query = query.filter(Workspace.is_deleted == False)
        
        if status:
            query = query.filter(Workspace.status == status)
        
        return query.order_by(Workspace.created_at.desc()).all()
    
    @staticmethod
    def get_all(db: Session) -> List[Workspace]:
        """Get all workspaces."""
        return db.query(Workspace).filter(
            Workspace.is_deleted == False
        ).order_by(Workspace.created_at.desc()).all()
    
    @staticmethod
    def create(
        db: Session,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        session_settings: Optional[dict] = None
    ) -> Workspace:
        """Create a new workspace (without commit)."""
        workspace = Workspace(
            user_id=user_id,
            name=name,
            description=description,
            status=WorkspaceStatus.ACTIVE.value,
            session_settings=session_settings
        )
        db.add(workspace)
        return workspace
    
    @staticmethod
    def update(
        db: Session,
        workspace_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        session_settings: Optional[dict] = None
    ) -> Optional[Workspace]:
        """Update an existing workspace (without commit)."""
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            return None
        
        updated = False
        if name is not None and workspace.name != name:
            workspace.name = name
            updated = True
        if description is not None and workspace.description != description:
            workspace.description = description
            updated = True
        if session_settings is not None:
            workspace.session_settings = session_settings
            updated = True
        
        return workspace if updated else None
    
    @staticmethod
    def update_status(db: Session, workspace_id: int, status: str) -> Optional[Workspace]:
        """Update workspace status (without commit)."""
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            return None
        
        workspace.status = status
        return workspace
    
    @staticmethod
    def update_stats(
        db: Session,
        workspace_id: int,
        session_count: Optional[int] = None,
        participant_count: Optional[int] = None,
        last_session_at: Optional[datetime] = None
    ) -> Optional[Workspace]:
        """Update workspace statistics (without commit)."""
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            return None
        
        if session_count is not None:
            workspace.session_count = session_count
        if participant_count is not None:
            workspace.participant_count = participant_count
        if last_session_at is not None:
            workspace.last_session_at = last_session_at
        
        return workspace
    
    @staticmethod
    def soft_delete(db: Session, workspace_id: int) -> Optional[Workspace]:
        """Soft delete a workspace (without commit)."""
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace or workspace.is_deleted:
            return None
        
        workspace.is_deleted = True
        workspace.deleted_at = datetime.utcnow()
        return workspace
    
    @staticmethod
    def restore(db: Session, workspace_id: int) -> Optional[Workspace]:
        """Restore a soft-deleted workspace (without commit)."""
        workspace = db.query(Workspace).filter(
            Workspace.id == workspace_id,
            Workspace.is_deleted == True
        ).first()
        
        if not workspace:
            return None
        
        workspace.is_deleted = False
        workspace.deleted_at = None
        return workspace
    
    @staticmethod
    def delete(db: Session, workspace_id: int, hard: bool = False) -> Optional[Workspace]:
        """Delete a workspace (without commit)."""
        if not hard:
            return WorkspaceRepository.soft_delete(db, workspace_id)
        
        # Hard delete
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            return None
        
        db.delete(workspace)
        return workspace

