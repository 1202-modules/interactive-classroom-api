"""Session repository."""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.session import Session as SessionModel, SessionStatus, TemplateLinkType


class SessionRepository:
    """Repository for session operations."""
    
    @staticmethod
    def get_by_id(db: Session, session_id: int) -> Optional[SessionModel]:
        """Get session by ID."""
        return db.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.is_deleted == False
        ).first()
    
    @staticmethod
    def get_by_workspace_id(
        db: Session,
        workspace_id: int,
        status: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[SessionModel]:
        """Get sessions by workspace ID."""
        query = db.query(SessionModel).filter(SessionModel.workspace_id == workspace_id)
        
        if not include_deleted:
            query = query.filter(SessionModel.is_deleted == False)
        
        if status:
            query = query.filter(SessionModel.status == status)
        
        return query.order_by(SessionModel.created_at.desc()).all()
    
    @staticmethod
    def get_all(db: Session) -> List[SessionModel]:
        """Get all sessions."""
        return db.query(SessionModel).filter(
            SessionModel.is_deleted == False
        ).order_by(SessionModel.created_at.desc()).all()
    
    @staticmethod
    def create(
        db: Session,
        workspace_id: int,
        name: str,
        description: Optional[str] = None,
        template_settings: Optional[Dict[str, Any]] = None
    ) -> SessionModel:
        """Create a new session (without commit)."""
        session = SessionModel(
            workspace_id=workspace_id,
            name=name,
            description=description,
            status=SessionStatus.ACTIVE.value,
            template_link_type=TemplateLinkType.FULL.value,
            custom_settings=None,
            is_stopped=False
        )
        db.add(session)
        return session
    
    @staticmethod
    def update(
        db: Session,
        session_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[SessionModel]:
        """Update an existing session (without commit)."""
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            return None
        
        updated = False
        if name is not None and session.name != name:
            session.name = name
            updated = True
        if description is not None and session.description != description:
            session.description = description
            updated = True
        
        return session if updated else None
    
    @staticmethod
    def update_status(
        db: Session,
        session_id: int,
        status: str,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        clear_end_datetime: bool = False
    ) -> Optional[SessionModel]:
        """Update session status (without commit)."""
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            return None
        
        session.status = status
        if start_datetime is not None:
            session.start_datetime = start_datetime
        if clear_end_datetime:
            session.end_datetime = None
        elif end_datetime is not None:
            session.end_datetime = end_datetime
        
        return session
    
    @staticmethod
    def update_stopped_participant_count(
        db: Session,
        session_id: int,
        stopped_participant_count: int
    ) -> Optional[SessionModel]:
        """Update session stopped participant count (without commit)."""
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            return None
        
        session.stopped_participant_count = stopped_participant_count
        return session
    
    @staticmethod
    def clear_session_run_data(
        db: Session,
        session_id: int
    ) -> Optional[SessionModel]:
        """Clear end_datetime and stopped_participant_count for session restart (without commit)."""
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            return None
        
        session.end_datetime = None
        session.stopped_participant_count = 0
        session.is_stopped = False
        return session
    
    @staticmethod
    def update_settings(
        db: Session,
        session_id: int,
        new_settings: Dict[str, Any],
        template_settings: Dict[str, Any]
    ) -> Optional[SessionModel]:
        """
        Update session settings and handle template linkage.
        
        Args:
            db: Database session
            session_id: Session ID
            new_settings: New settings to apply
            template_settings: Current template settings from workspace
        
        Returns:
            Updated session or None if not found
        """
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            return None
        
        # Calculate differences between new_settings and template_settings
        differences = {}
        for key, value in new_settings.items():
            if key not in template_settings or template_settings[key] != value:
                differences[key] = value
        
        # Update template_link_type and custom_settings
        if differences:
            session.template_link_type = TemplateLinkType.PARTIAL.value
            # Merge with existing custom_settings if any
            if session.custom_settings:
                session.custom_settings = {**session.custom_settings, **differences}
            else:
                session.custom_settings = differences
        else:
            # If no differences, reset to full template link
            session.template_link_type = TemplateLinkType.FULL.value
            session.custom_settings = None
        
        return session
    
    @staticmethod
    def get_merged_settings(
        session: SessionModel,
        template_settings: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get merged settings for a session (template + custom overrides).
        
        Args:
            session: Session model instance
            template_settings: Template settings from workspace
        
        Returns:
            Merged settings dictionary
        """
        if not template_settings:
            template_settings = {}
        
        if session.template_link_type == TemplateLinkType.FULL.value:
            return template_settings.copy() if template_settings else {}
        
        # Partial: merge template with custom_settings
        merged = template_settings.copy() if template_settings else {}
        if session.custom_settings:
            merged.update(session.custom_settings)
        
        return merged
    
    @staticmethod
    def soft_delete(db: Session, session_id: int) -> Optional[SessionModel]:
        """Soft delete a session (without commit)."""
        session = SessionRepository.get_by_id(db, session_id)
        if not session or session.is_deleted:
            return None
        
        session.is_deleted = True
        session.deleted_at = datetime.now(timezone.utc)
        return session
    
    @staticmethod
    def restore(db: Session, session_id: int) -> Optional[SessionModel]:
        """Restore a soft-deleted session (without commit)."""
        session = db.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.is_deleted == True
        ).first()
        
        if not session:
            return None
        
        session.is_deleted = False
        session.deleted_at = None
        return session
    
    @staticmethod
    def delete(db: Session, session_id: int, hard: bool = False) -> Optional[SessionModel]:
        """Delete a session (without commit)."""
        if not hard:
            return SessionRepository.soft_delete(db, session_id)
        
        # Hard delete
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return None
        
        db.delete(session)
        return session

