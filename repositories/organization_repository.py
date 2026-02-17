"""Organization repository."""
from typing import Optional

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
