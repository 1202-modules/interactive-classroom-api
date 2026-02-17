"""Organization endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.db import get_db
from core.auth import get_current_user
from repositories.organization_repository import OrganizationRepository
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Organizations"])


@router.get(
    "",
    summary="List organizations",
    description="Get list of all non-deleted organizations (for SSO).",
    responses={
        200: {
            "description": "Organizations retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "organizations": [
                            {
                                "id": 1,
                                "name": "Example University",
                                "created_at": "2024-01-15T10:30:00Z",
                                "updated_at": "2024-01-15T10:30:00Z"
                            }
                        ],
                        "total": 1
                    }
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
async def list_organizations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all non-deleted organizations."""
    try:
        organizations = OrganizationRepository.get_all(db)
        items = [
            {
                "id": org.id,
                "name": org.name,
                "created_at": org.created_at.isoformat() if org.created_at else None,
                "updated_at": org.updated_at.isoformat() if org.updated_at else None,
            }
            for org in organizations
        ]
        return {
            "organizations": items,
            "total": len(items)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_organizations_error", user_id=current_user["user_id"], error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
