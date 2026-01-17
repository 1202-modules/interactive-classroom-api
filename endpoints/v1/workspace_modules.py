"""Workspace modules endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from core.db import get_db
from core.auth import get_current_user
from services.workspace_module_service import WorkspaceModuleService
from repositories.workspace_module_repository import WorkspaceModuleRepository
from endpoints.v1.schemas import (
    WorkspaceModuleResponse,
    WorkspaceModuleCreateRequest,
    WorkspaceModuleUpdateRequest,
    MessageResponse
)
from utils.query_params import parse_fields, filter_model_response, filter_list_response

router = APIRouter(prefix="/workspaces/{workspace_id}/modules", tags=["Workspace Modules"])


@router.get(
    "",
    summary="List workspace modules",
    description="Get list of modules in a workspace.",
    responses={
        200: {
            "description": "Modules retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "workspace_id": 1,
                            "name": "Quiz Module",
                            "module_type": "quiz",
                            "settings": {
                                "question": "What is 2+2?",
                                "options": [
                                    {"text": "3", "is_correct": False},
                                    {"text": "4", "is_correct": True}
                                ]
                            },
                            "created_at": "2025-01-16T10:00:00Z",
                            "updated_at": "2025-01-16T10:00:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {"description": "Workspace not found"}
    }
)
async def list_workspace_modules(
    workspace_id: int,
    include_deleted: bool = Query(False, description="Include deleted modules"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include (e.g., id,name,module_type)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all modules in a workspace."""
    try:
        # Check workspace ownership
        from repositories.workspace_repository import WorkspaceRepository
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found"
            )
        
        if workspace.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        
        modules = WorkspaceModuleRepository.get_by_workspace_id(
            db=db,
            workspace_id=workspace_id,
            include_deleted=include_deleted
        )
        
        # Convert to response models
        module_responses = [WorkspaceModuleResponse.model_validate(m) for m in modules]
        
        # Apply fields filter if specified
        fields_set = parse_fields(fields)
        if fields_set:
            filtered_list = filter_list_response(module_responses, fields_set)
            return filtered_list
        
        return module_responses
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create workspace module",
    description="Create a new module in a workspace.",
    responses={
        201: {
            "description": "Module created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "workspace_id": 1,
                        "name": "Quiz Module",
                        "module_type": "quiz",
                        "settings": {
                            "question": "What is 2+2?",
                            "options": [
                                {"text": "3", "is_correct": False},
                                {"text": "4", "is_correct": True}
                            ]
                        },
                        "created_at": "2025-01-16T10:00:00Z",
                        "updated_at": "2025-01-16T10:00:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid module type"
                    }
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {"description": "Workspace not found"}
    }
)
async def create_workspace_module(
    workspace_id: int,
    module_data: WorkspaceModuleCreateRequest,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new workspace module."""
    try:
        module = WorkspaceModuleService.create_module(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user["user_id"],
            name=module_data.name,
            module_type=module_data.module_type,
            settings=module_data.settings
        )
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        module_response = WorkspaceModuleResponse.model_validate(module)
        filtered_dict = filter_model_response(module_response, fields_set)
        return filtered_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/{module_id}",
    summary="Get workspace module",
    description="Get a workspace module by ID.",
    responses={
        200: {
            "description": "Module retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "workspace_id": 1,
                        "name": "Quiz Module",
                        "module_type": "quiz",
                        "settings": {
                            "question": "What is 2+2?",
                            "options": [
                                {"text": "3", "is_correct": False},
                                {"text": "4", "is_correct": True}
                            ]
                        },
                        "created_at": "2025-01-16T10:00:00Z",
                        "updated_at": "2025-01-16T10:00:00Z"
                    }
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {"description": "Module not found"}
    }
)
async def get_workspace_module(
    workspace_id: int,
    module_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include (e.g., id,name,module_type)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a workspace module by ID."""
    try:
        # Check workspace ownership
        from repositories.workspace_repository import WorkspaceRepository
        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found"
            )
        
        if workspace.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        
        module = WorkspaceModuleRepository.get_by_id(db, module_id)
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module with id {module_id} not found"
            )
        
        if module.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found"
            )
        
        module_response = WorkspaceModuleResponse.model_validate(module)
        
        # Apply fields filter if specified
        fields_set = parse_fields(fields)
        if fields_set:
            filtered_dict = filter_model_response(module_response, fields_set)
            return filtered_dict
        
        return module_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put(
    "/{module_id}",
    summary="Update workspace module",
    description="Update an existing workspace module.",
    responses={
        200: {
            "description": "Module updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "workspace_id": 1,
                        "name": "Updated Quiz Module",
                        "module_type": "quiz",
                        "settings": {
                            "question": "Updated question"
                        },
                        "created_at": "2025-01-16T10:00:00Z",
                        "updated_at": "2025-01-16T11:00:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid module type"
                    }
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {"description": "Module not found"}
    }
)
async def update_workspace_module(
    workspace_id: int,
    module_id: int,
    module_data: WorkspaceModuleUpdateRequest,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a workspace module."""
    try:
        module = WorkspaceModuleService.update_module(
            db=db,
            workspace_id=workspace_id,
            module_id=module_id,
            user_id=current_user["user_id"],
            name=module_data.name,
            module_type=module_data.module_type,
            settings=module_data.settings
        )
        
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module with id {module_id} not found"
            )
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        module_response = WorkspaceModuleResponse.model_validate(module)
        filtered_dict = filter_model_response(module_response, fields_set)
        return filtered_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{module_id}", response_model=MessageResponse)
async def delete_workspace_module(
    workspace_id: int,
    module_id: int,
    hard: bool = Query(False, description="Hard delete (permanent)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a workspace module."""
    try:
        deleted_module = WorkspaceModuleService.delete_module(
            db=db,
            workspace_id=workspace_id,
            module_id=module_id,
            user_id=current_user["user_id"],
            hard=hard
        )
        
        if not deleted_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module with id {module_id} not found"
            )
        
        return MessageResponse(message="Module deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )



