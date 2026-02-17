"""Organization repository."""
from typing import List, Optional

from sqlalchemy.orm import Session as DBSession

from models.organization import Organization


class OrganizationRepository:
    """Repository for organization operations."""

    @staticmethod
    def get_by_id(db: DBSession, org_id: int) -> Optional[Organization]:
        """Get organization by ID (excluding deleted)."""
        return db.query(Organization).filter(
            Organization.id == org_id,
            Organization.is_deleted == False
        ).first()

    @staticmethod
    def get_all(db: DBSession) -> List[Organization]:
        """Get all non-deleted organizations."""
        return db.query(Organization).filter(
            Organization.is_deleted == False
        ).order_by(Organization.name).all()
