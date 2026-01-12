"""Workspace endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from api.core.db import get_db
from api.core.auth import get_current_user
from api.repositories.workspace_repository import WorkspaceRepository
from api.services.workspace_service import WorkspaceService
from api.endpoints.v1.schemas import (
    WorkspaceResponse, WorkspaceListResponse,
    WorkspaceCreateRequest, WorkspaceUpdateRequest,
    MessageResponse
)
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Workspaces"])


@router.get(
    "",
    response_model=WorkspaceListResponse,
    summary="List workspaces",
    description="""
    Get list of workspaces for the current user.
    
    Can be filtered by status (active, archive) and includes deleted workspaces if requested.
    """,
    responses={
        200: {"description": "Workspaces retrieved successfully"},
        401: {"description": "Not authenticated"}
    }
)
async def list_workspaces(
    status: Optional[str] = Query(None, description="Filter by status (active, archive)"),
    include_deleted: bool = Query(False, description="Include deleted workspaces"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List workspaces for current user."""
    try:
        workspaces = WorkspaceRepository.get_by_user_id(
            db=db,
            user_id=current_user["user_id"],
            status=status,
            include_deleted=include_deleted
        )
        return WorkspaceListResponse(
            workspaces=[WorkspaceResponse.model_validate(w) for w in workspaces],
            total=len(workspaces)
        )
    except Exception as e:
        logger.error("list_workspaces_error", user_id=current_user["user_id"], error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Get workspace details",
    description="Get detailed information about a specific workspace.",
    responses={
        200: {"description": "Workspace retrieved successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Workspace not found"}
    }
)
async def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get workspace by ID."""
    try:
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found"
            )
        
        # Check ownership
        if workspace.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        
        return WorkspaceResponse.model_validate(workspace)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_workspace_error", workspace_id=workspace_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workspace",
    description="Create a new workspace for the current user.",
    responses={
        201: {"description": "Workspace created successfully"},
        401: {"description": "Not authenticated"}
    }
)
async def create_workspace(
    workspace_data: WorkspaceCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new workspace."""
    try:
        workspace = WorkspaceService.create_workspace(
            db=db,
            user_id=current_user["user_id"],
            name=workspace_data.name,
            description=workspace_data.description,
            session_settings=workspace_data.session_settings
        )
        return WorkspaceResponse.model_validate(workspace)
    except Exception as e:
        logger.error("create_workspace_error", user_id=current_user["user_id"], error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Update workspace",
    description="Update an existing workspace.",
    responses={
        200: {"description": "Workspace updated successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Workspace not found"}
    }
)
async def update_workspace(
    workspace_id: int,
    workspace_data: WorkspaceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update workspace."""
    try:
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found"
            )
        
        # Check ownership
        if workspace.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        
        updated_workspace = WorkspaceRepository.update(
            db=db,
            workspace_id=workspace_id,
            name=workspace_data.name,
            description=workspace_data.description,
            session_settings=workspace_data.session_settings
        )
        
        if updated_workspace:
            db.commit()
            db.refresh(updated_workspace)
            return WorkspaceResponse.model_validate(updated_workspace)
        else:
            # No changes, return current workspace
            return WorkspaceResponse.model_validate(workspace)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_workspace_error", workspace_id=workspace_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete workspace",
    description="Soft delete a workspace (moves to trash).",
    responses={
        204: {"description": "Workspace deleted successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Workspace not found"}
    }
)
async def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete workspace (soft delete)."""
    try:
        deleted_workspace = WorkspaceService.delete_workspace(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user["user_id"],
            hard=False
        )
        
        if not deleted_workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found"
            )
        
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_workspace_error", workspace_id=workspace_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/{workspace_id}/archive",
    response_model=WorkspaceResponse,
    summary="Archive workspace",
    description="Archive a workspace and end all active sessions.",
    responses={
        200: {"description": "Workspace archived successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Workspace not found"}
    }
)
async def archive_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Archive workspace."""
    try:
        workspace = WorkspaceService.archive_workspace(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user["user_id"]
        )
        
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found"
            )
        
        return WorkspaceResponse.model_validate(workspace)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("archive_workspace_error", workspace_id=workspace_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/{workspace_id}/unarchive",
    response_model=WorkspaceResponse,
    summary="Unarchive workspace",
    description="Unarchive a workspace (restore from archive).",
    responses={
        200: {"description": "Workspace unarchived successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Workspace not found"}
    }
)
async def unarchive_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Unarchive workspace."""
    try:
        workspace = WorkspaceService.unarchive_workspace(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user["user_id"]
        )
        
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found"
            )
        
        return WorkspaceResponse.model_validate(workspace)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("unarchive_workspace_error", workspace_id=workspace_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/{workspace_id}/restore",
    response_model=WorkspaceResponse,
    summary="Restore workspace from trash",
    description="Restore a workspace from trash (undo soft delete).",
    responses={
        200: {"description": "Workspace restored successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Workspace not found"}
    }
)
async def restore_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Restore workspace from trash."""
    try:
        workspace = WorkspaceService.restore_workspace(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user["user_id"]
        )
        
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found"
            )
        
        return WorkspaceResponse.model_validate(workspace)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("restore_workspace_error", workspace_id=workspace_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete(
    "/{workspace_id}/permanent",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete workspace",
    description="Permanently delete a workspace (hard delete). This action cannot be undone.",
    responses={
        204: {"description": "Workspace permanently deleted"},
        401: {"description": "Not authenticated"},
        404: {"description": "Workspace not found"}
    }
)
async def delete_workspace_permanent(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Permanently delete workspace."""
    try:
        deleted_workspace = WorkspaceService.delete_workspace(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user["user_id"],
            hard=True
        )
        
        if not deleted_workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found"
            )
        
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_workspace_permanent_error", workspace_id=workspace_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

