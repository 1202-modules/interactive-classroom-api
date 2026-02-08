"""Session modules endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from core.db import get_db
from core.auth import get_current_user
from services.session_module_service import SessionModuleService
from repositories.session_module_repository import SessionModuleRepository
from endpoints.v1.schemas import (
    SessionModuleResponse,
    SessionModuleCreateRequest,
    SessionModuleUpdateRequest,
    MessageResponse
)
from utils.query_params import parse_fields, filter_model_response, filter_list_response

router = APIRouter(prefix="/sessions/{session_id}/modules", tags=["Session Modules"])


@router.get(
    "",
    summary="List session modules",
    description="Get list of modules in a session.",
    responses={
        200: {
            "description": "Modules retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "session_id": 1,
                            "name": "Quiz Module-1",
                            "module_type": "quiz",
                            "settings": {
                                "question": "What is 2+2?",
                                "options": [
                                    {"text": "3", "is_correct": False},
                                    {"text": "4", "is_correct": True}
                                ]
                            },
                            "is_active": False,
                            "created_at": "2025-01-16T10:00:00Z",
                            "updated_at": "2025-01-16T10:00:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {"description": "Session not found"}
    }
)
async def list_session_modules(
    session_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include (e.g., id,name,module_type)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all modules in a session."""
    try:
        # Check session ownership
        from repositories.session_repository import SessionRepository
        from repositories.workspace_repository import WorkspaceRepository
        
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with id {session_id} not found"
            )
        
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        modules = SessionModuleRepository.get_by_session_id(
            db=db,
            session_id=session_id,
            include_deleted=True
        )
        
        # Convert to response models
        module_responses = [SessionModuleResponse.model_validate(m) for m in modules]
        
        # When fields specified: return only requested keys (no defaults for missing fields)
        fields_set = parse_fields(fields)
        if fields_set:
            filtered_dicts = filter_list_response(module_responses, fields_set)
            return filtered_dicts
        
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
    summary="Clone workspace module to session",
    description="Clone a workspace module to session (creates independent copy).",
    responses={
        201: {
            "description": "Module cloned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "session_id": 1,
                        "name": "Quiz Module-1",
                        "module_type": "quiz",
                        "settings": {
                            "question": "What is 2+2?",
                            "options": [
                                {"text": "3", "is_correct": False},
                                {"text": "4", "is_correct": True}
                            ]
                        },
                        "is_active": False,
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
                        "detail": "workspace_module_id is required"
                    }
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {"description": "Session or workspace module not found"}
    }
)
async def create_session_module(
    session_id: int,
    module_data: SessionModuleCreateRequest,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Clone a workspace module to session (creates independent copy)."""
    try:
        # workspace_module_id is required - we only clone from workspace
        if not module_data.workspace_module_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="workspace_module_id is required"
            )
        
        module = SessionModuleService.add_module_from_workspace(
            db=db,
            session_id=session_id,
            workspace_module_id=module_data.workspace_module_id,
            user_id=current_user["user_id"],
            name=module_data.name
        )
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        module_response = SessionModuleResponse.model_validate(module)
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


@router.get(
    "/{module_id}",
    summary="Get session module",
    description="Get a session module by ID.",
    responses={
        200: {
            "description": "Module retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "session_id": 1,
                        "name": "Quiz Module-1",
                        "module_type": "quiz",
                        "settings": {
                            "question": "What is 2+2?",
                            "options": [
                                {"text": "3", "is_correct": False},
                                {"text": "4", "is_correct": True}
                            ]
                        },
                        "is_active": False,
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
async def get_session_module(
    session_id: int,
    module_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include (e.g., id,name,module_type)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a session module by ID."""
    try:
        # Check session ownership
        from repositories.session_repository import SessionRepository
        from repositories.workspace_repository import WorkspaceRepository
        
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with id {session_id} not found"
            )
        
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        module = SessionModuleRepository.get_by_id(db, module_id)
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module with id {module_id} not found"
            )
        
        if module.session_id != session_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found"
            )
        
        module_response = SessionModuleResponse.model_validate(module)
        
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
    summary="Update session module",
    description="Update an existing session module.",
    responses={
        200: {
            "description": "Module updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "session_id": 1,
                        "name": "Updated Quiz Module",
                        "module_type": "quiz",
                        "settings": {
                            "question": "Updated question"
                        },
                        "is_active": False,
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
async def update_session_module(
    session_id: int,
    module_id: int,
    module_data: SessionModuleUpdateRequest,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a session module."""
    try:
        module = SessionModuleService.update_module(
            db=db,
            session_id=session_id,
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
        
        module_response = SessionModuleResponse.model_validate(module)
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
async def delete_session_module(
    session_id: int,
    module_id: int,
    hard: bool = Query(False, description="Hard delete (permanent)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a session module."""
    try:
        deleted_module = SessionModuleService.delete_module(
            db=db,
            session_id=session_id,
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


@router.patch(
    "/{module_id}/activate",
    summary="Activate session module",
    description="Activate a session module (deactivates others).",
    responses={
        200: {
            "description": "Module activated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "session_id": 1,
                        "name": "Quiz Module-1",
                        "module_type": "quiz",
                        "settings": {
                            "question": "What is 2+2?",
                            "options": [
                                {"text": "3", "is_correct": False},
                                {"text": "4", "is_correct": True}
                            ]
                        },
                        "is_active": True,
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
                        "detail": "Module not found"
                    }
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {"description": "Module not found"}
    }
)
async def activate_session_module(
    session_id: int,
    module_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Activate a session module (deactivates others)."""
    try:
        module = SessionModuleService.set_active_module(
            db=db,
            session_id=session_id,
            module_id=module_id,
            user_id=current_user["user_id"]
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
        
        module_response = SessionModuleResponse.model_validate(module)
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



