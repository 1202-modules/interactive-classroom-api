"""Workspace endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from core.db import get_db
from core.auth import get_current_user
from repositories.workspace_repository import WorkspaceRepository
from repositories.session_repository import SessionRepository
from repositories.session_participant_repository import SessionParticipantRepository
from services.workspace_service import WorkspaceService
from endpoints.v1.schemas import (
    WorkspaceResponse, WorkspaceListResponse,
    WorkspaceCreateRequest, WorkspaceUpdateRequest,
    MessageResponse
)
from utils.query_params import parse_fields, filter_model_response, filter_list_response
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Workspaces"])


@router.get(
    "",
    summary="List workspaces",
    description="""
    Get list of workspaces for the current user.
    
    Can be filtered by status (active, archive) and includes deleted workspaces.
    """,
    responses={
        200: {
            "description": "Workspaces retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "workspaces": [
                            {
                                "id": 1,
                                "user_id": 1,
                                "name": "My Workspace",
                                "description": "A workspace for my classes",
                                "status": "active",
                                "template_settings": {"poll_duration": 30},
                                "participant_count": 25,
                                "has_live_session": True,
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
async def list_workspaces(
    status_filter: Optional[str] = Query(None, description="Filter by status (active, archive)", alias="status"),
    include_deleted: bool = Query(False, description="Include deleted workspaces in the result"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include (e.g., id,name,status)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List workspaces for current user."""
    try:
        workspaces = WorkspaceRepository.get_by_user_id(
            db=db,
            user_id=current_user["user_id"],
            status=status_filter,
            include_deleted=include_deleted
        )
        
        # Calculate participant_count and has_live_session for each workspace
        workspace_responses = []
        for workspace in workspaces:
            # Get all non-deleted sessions in workspace
            sessions = SessionRepository.get_by_workspace_id(
                db=db,
                workspace_id=workspace.id,
                include_deleted=False
            )
            
            # Calculate participant_count: sum(stopped_participant_count) + active participants in live sessions
            participant_count = sum(
                session.stopped_participant_count
                for session in sessions
                if session.is_stopped
            )
            live_sessions = [
                s for s in sessions
                if not s.is_stopped and s.start_datetime is not None
            ]
            for live_session in live_sessions:
                participant_count += SessionParticipantRepository.count_active(db, live_session.id)

            # Count live (active) sessions
            session_count = len(live_sessions)
            has_live_session = session_count > 0

            workspace_response = WorkspaceResponse.model_validate(workspace)
            workspace_response.participant_count = participant_count
            workspace_response.session_count = session_count
            workspace_response.has_live_session = has_live_session
            workspace_responses.append(workspace_response)
        
        # When fields specified: return only requested keys (no defaults for missing fields)
        fields_set = parse_fields(fields)
        if fields_set:
            filtered_dicts = filter_list_response(workspace_responses, fields_set)
            return {"workspaces": filtered_dicts, "total": len(workspace_responses)}
        
        return WorkspaceListResponse(
            workspaces=workspace_responses,
            total=len(workspace_responses)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_workspaces_error", user_id=current_user["user_id"], error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{workspace_id}",
    summary="Get workspace details",
    description="Get detailed information about a specific workspace.",
    responses={
        200: {
            "description": "Workspace retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_id": 1,
                        "name": "My Workspace",
                        "description": "A workspace for my classes",
                        "status": "active",
                        "template_settings": {"poll_duration": 30},
                        "participant_count": 25,
                        "has_live_session": True,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {
            "description": "Workspace not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Workspace with id 1 not found"
                    }
                }
            }
        }
    }
)
async def get_workspace(
    workspace_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include (e.g., id,name,status)", example="id,name,status"),
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
        
        # Get all non-deleted sessions in workspace
        sessions = SessionRepository.get_by_workspace_id(
            db=db,
            workspace_id=workspace_id,
            include_deleted=False
        )
        
        # Calculate participant_count: sum(stopped_participant_count) + active participants in live sessions
        participant_count = sum(
            session.stopped_participant_count
            for session in sessions
            if session.is_stopped
        )
        live_sessions = [
            s for s in sessions
            if not s.is_stopped and s.start_datetime is not None
        ]
        for live_session in live_sessions:
            participant_count += SessionParticipantRepository.count_active(db, live_session.id)

        # Count live (active) sessions
        session_count = len(live_sessions)
        has_live_session = session_count > 0

        workspace_response = WorkspaceResponse.model_validate(workspace)
        workspace_response.participant_count = participant_count
        workspace_response.session_count = session_count
        workspace_response.has_live_session = has_live_session
        
        # Apply fields filter if specified
        fields_set = parse_fields(fields)
        if fields_set:
            filtered_dict = filter_model_response(workspace_response, fields_set)
            return filtered_dict
        
        return workspace_response
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
    status_code=status.HTTP_201_CREATED,
    summary="Create workspace",
    description="Create a new workspace for the current user.",
    responses={
        201: {
            "description": "Workspace created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_id": 1,
                        "name": "My Workspace",
                        "description": "A workspace for my classes",
                        "status": "active",
                        "template_settings": {"poll_duration": 30},
                        "participant_count": 0,
                        "has_live_session": False,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Workspace name already exists"
                    }
                }
            }
        },
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
            template_settings=workspace_data.template_settings
        )
        return WorkspaceResponse.model_validate(workspace)
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("create_workspace_validation_error", user_id=current_user["user_id"], error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("create_workspace_error", user_id=current_user["user_id"], error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put(
    "/{workspace_id}",
    summary="Update workspace",
    description="Update an existing workspace.",
    responses={
        200: {
            "description": "Workspace updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Updated Workspace",
                        "status": "active"
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Workspace name already exists"
                    }
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {
            "description": "Workspace not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Workspace with id 1 not found"
                    }
                }
            }
        }
    }
)
async def update_workspace(
    workspace_id: int,
    workspace_data: WorkspaceUpdateRequest,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response.", example="id,name,status"),
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
        
        updated_workspace = WorkspaceService.update_workspace(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user["user_id"],
            name=workspace_data.name,
            description=workspace_data.description,
            template_settings=workspace_data.template_settings
        )
        
        if not updated_workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found"
            )
        
        workspace = updated_workspace
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        workspace_response = WorkspaceResponse.model_validate(workspace)
        filtered_dict = filter_model_response(workspace_response, fields_set)
        return filtered_dict
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("update_workspace_validation_error", workspace_id=workspace_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
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
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot delete workspace with active running session"
                    }
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {
            "description": "Workspace not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Workspace with id 1 not found"
                    }
                }
            }
        }
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
        # Check if it's a business logic validation error (active sessions) or access denied
        error_msg = str(e)
        if "Cannot delete workspace" in error_msg or "active running session" in error_msg:
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            # Access denied or not found
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail=error_msg
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
    summary="Archive workspace",
    description="Archive a workspace and end all active sessions.",
    responses={
        200: {
            "description": "Workspace archived successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "My Workspace",
                        "status": "archive"
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot archive deleted workspace"
                    }
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {
            "description": "Workspace not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Workspace with id 1 not found"
                    }
                }
            }
        }
    }
)
async def archive_workspace(
    workspace_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
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
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        workspace_response = WorkspaceResponse.model_validate(workspace)
        filtered_dict = filter_model_response(workspace_response, fields_set)
        return filtered_dict
    except ValueError as e:
        # Check if it's a business logic validation error or access denied
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in [
            "cannot archive", "deleted workspace"
        ]):
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            # Access denied or not found
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
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
    summary="Unarchive workspace",
    description="Unarchive a workspace (restore from archive).",
    responses={
        200: {
            "description": "Workspace unarchived successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "My Workspace",
                        "status": "active"
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot unarchive deleted workspace"
                    }
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {
            "description": "Workspace not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Workspace with id 1 not found"
                    }
                }
            }
        }
    }
)
async def unarchive_workspace(
    workspace_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
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
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        workspace_response = WorkspaceResponse.model_validate(workspace)
        filtered_dict = filter_model_response(workspace_response, fields_set)
        return filtered_dict
    except ValueError as e:
        # Check if it's a business logic validation error or access denied
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in [
            "cannot unarchive", "deleted workspace"
        ]):
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            # Access denied or not found
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
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
    summary="Restore workspace from trash",
    description="Restore a workspace from trash (undo soft delete).",
    responses={
        200: {
            "description": "Workspace restored successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "My Workspace",
                        "status": "active"
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot restore workspace that is not deleted"
                    }
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {
            "description": "Workspace not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Workspace with id 1 not found"
                    }
                }
            }
        }
    }
)
async def restore_workspace(
    workspace_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
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
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        workspace_response = WorkspaceResponse.model_validate(workspace)
        filtered_dict = filter_model_response(workspace_response, fields_set)
        return filtered_dict
    except ValueError as e:
        # Check if it's a business logic validation error or access denied
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in [
            "cannot restore", "not deleted", "that is not deleted"
        ]):
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            # Access denied or not found
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
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
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot delete workspace with active running session"
                    }
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {
            "description": "Workspace not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Workspace with id 1 not found"
                    }
                }
            }
        }
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
        # Check if it's a business logic validation error (active sessions) or access denied
        error_msg = str(e)
        if "Cannot delete workspace" in error_msg or "active running session" in error_msg:
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            # Access denied or not found
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail=error_msg
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_workspace_permanent_error", workspace_id=workspace_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

