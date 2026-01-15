"""Session endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from core.db import get_db
from core.auth import get_current_user
from repositories.session_repository import SessionRepository
from repositories.workspace_repository import WorkspaceRepository
from services.session_service import SessionService
from endpoints.v1.schemas import (
    SessionResponse, SessionListResponse,
    SessionCreateRequest, SessionUpdateRequest,
    MessageResponse
)
from utils.query_params import parse_fields, filter_model_response, filter_list_response
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Sessions"])


@router.get(
    "/workspaces/{workspace_id}/sessions",
    response_model=SessionListResponse,
    summary="List sessions in workspace",
    description="Get list of sessions in a specific workspace.",
    responses={
        200: {"description": "Sessions retrieved successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Workspace not found"}
    }
)
async def list_sessions(
    workspace_id: int,
    status: Optional[str] = Query(None, description="Filter by status (active, archive)"),
    include_deleted: bool = Query(False, description="Include deleted sessions"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include (e.g., id,name,status)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List sessions in workspace."""
    try:
        # Check workspace ownership
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
        
        sessions = SessionRepository.get_by_workspace_id(
            db=db,
            workspace_id=workspace_id,
            status=status,
            include_deleted=include_deleted
        )
        
        # Get merged settings for each session
        session_responses = []
        for s in sessions:
            merged_settings = SessionRepository.get_merged_settings(s, workspace.template_settings)
            session_dict = SessionResponse.model_validate(s).model_dump()
            session_dict['settings'] = merged_settings
            session_responses.append(SessionResponse(**session_dict))
        
        # Apply fields filter if specified
        fields_set = parse_fields(fields)
        if fields_set:
            session_responses = filter_list_response(session_responses, fields_set)
        
        return SessionListResponse(
            sessions=session_responses,
            total=len(session_responses)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_sessions_error", workspace_id=workspace_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Get session details",
    description="Get detailed information about a specific session.",
    responses={
        200: {"description": "Session retrieved successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Session not found"}
    }
)
async def get_session(
    session_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include (e.g., id,name,status)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get session by ID."""
    try:
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with id {session_id} not found"
            )
        
        # Check workspace ownership
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Check if workspace is deleted
        if workspace.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot access session in deleted workspace"
            )
        
        # Get merged settings for response
        merged_settings = SessionRepository.get_merged_settings(session, workspace.template_settings)
        session_dict = SessionResponse.model_validate(session).model_dump()
        session_dict['settings'] = merged_settings
        session_response = SessionResponse(**session_dict)
        
        # Apply fields filter if specified
        fields_set = parse_fields(fields)
        if fields_set:
            filtered_dict = filter_model_response(session_response, fields_set)
            return filtered_dict
        
        return session_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_session_error", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/workspaces/{workspace_id}/sessions",
    status_code=status.HTTP_201_CREATED,
    summary="Create session",
    description="Create a new session in a workspace.",
    responses={
        201: {"description": "Session created successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Workspace not found"}
    }
)
async def create_session(
    workspace_id: int,
    session_data: SessionCreateRequest,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new session."""
    try:
        # Check workspace ownership
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
        
        # Check if workspace is deleted
        if workspace.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create session in deleted workspace"
            )
        
        # Check if workspace is archived
        if workspace.status == "archive":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create session in archived workspace"
            )
        
        # Validate session name
        SessionService.validate_session_name(session_data.name)
        
        # Check for duplicate name
        SessionService.check_session_name_duplicate(db, workspace_id, session_data.name)
        
        session = SessionRepository.create(
            db=db,
            workspace_id=workspace_id,
            name=session_data.name,
            description=session_data.description,
            template_settings=workspace.template_settings
        )
        
        db.commit()
        db.refresh(session)
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        # Get merged settings for response
        merged_settings = SessionRepository.get_merged_settings(session, workspace.template_settings)
        session_dict = SessionResponse.model_validate(session).model_dump()
        session_dict['settings'] = merged_settings
        session_response = SessionResponse(**session_dict)
        
        # Return only specified fields
        filtered_dict = filter_model_response(session_response, fields_set)
        return filtered_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_session_error", workspace_id=workspace_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put(
    "/sessions/{session_id}",
    summary="Update session",
    description="Update an existing session.",
    responses={
        200: {"description": "Session updated successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Session not found"}
    }
)
async def update_session(
    session_id: int,
    session_data: SessionUpdateRequest,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update session."""
    try:
        session = SessionRepository.get_by_id(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with id {session_id} not found"
            )
        
        # Check workspace ownership
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        if not workspace or workspace.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Check if session is deleted
        if session.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update deleted session"
            )
        
        # Check if workspace is archived
        if workspace.status == "archive":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update session in archived workspace"
            )
        
        # Validate session name if provided
        if session_data.name is not None:
            SessionService.validate_session_name(session_data.name)
            # Check for duplicate name
            SessionService.check_session_name_duplicate(db, session.workspace_id, session_data.name, exclude_session_id=session_id)
        
        updated = False
        updated_session = SessionRepository.update(
            db=db,
            session_id=session_id,
            name=session_data.name,
            description=session_data.description
        )
        
        if updated_session:
            updated = True
        
        # Handle settings update if provided
        if session_data.settings is not None:
            SessionService.update_session_settings(
                db=db,
                session_id=session_id,
                user_id=current_user["user_id"],
                new_settings=session_data.settings
            )
            updated = True
        
        if updated:
            db.commit()
            db.refresh(session)
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        # Get merged settings for response
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        merged_settings = SessionRepository.get_merged_settings(session, workspace.template_settings if workspace else None)
        session_dict = SessionResponse.model_validate(session).model_dump()
        session_dict['settings'] = merged_settings
        session_response = SessionResponse(**session_dict)
        
        # Return only specified fields
        filtered_dict = filter_model_response(session_response, fields_set)
        return filtered_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_session_error", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete session",
    description="Soft delete a session (moves to trash).",
    responses={
        204: {"description": "Session deleted successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Session not found"}
    }
)
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete session (soft delete)."""
    try:
        deleted_session = SessionService.delete_session(
            db=db,
            session_id=session_id,
            user_id=current_user["user_id"],
            hard=False
        )
        
        if not deleted_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with id {session_id} not found"
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
        logger.error("delete_session_error", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/sessions/{session_id}/start",
    summary="Start session",
    description="Start a session (set status to active and record start time).",
    responses={
        200: {"description": "Session started successfully"},
        401: {"description": "Not authenticated"},
        400: {"description": "Cannot start session in archived workspace"},
        404: {"description": "Session not found"}
    }
)
async def start_session(
    session_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Start session."""
    try:
        session = SessionService.start_session(
            db=db,
            session_id=session_id,
            user_id=current_user["user_id"]
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with id {session_id} not found"
            )
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        # Get merged settings for response
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        merged_settings = SessionRepository.get_merged_settings(session, workspace.template_settings if workspace else None)
        session_dict = SessionResponse.model_validate(session).model_dump()
        session_dict['settings'] = merged_settings
        session_response = SessionResponse(**session_dict)
        
        # Return only specified fields
        filtered_dict = filter_model_response(session_response, fields_set)
        return filtered_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("start_session_error", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/sessions/{session_id}/stop",
    summary="Stop session",
    description="Stop a session (set end_datetime and stopped_participant_count).",
    responses={
        200: {"description": "Session stopped successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Session not found"}
    }
)
async def stop_session(
    session_id: int,
    participant_count: int = Query(0, description="Number of participants at stop time (default 0)"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Stop session."""
    try:
        session = SessionService.stop_session(
            db=db,
            session_id=session_id,
            user_id=current_user["user_id"],
            participant_count=participant_count
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with id {session_id} not found"
            )
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        # Get merged settings for response
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        merged_settings = SessionRepository.get_merged_settings(session, workspace.template_settings if workspace else None)
        session_dict = SessionResponse.model_validate(session).model_dump()
        session_dict['settings'] = merged_settings
        session_response = SessionResponse(**session_dict)
        
        # Return only specified fields
        filtered_dict = filter_model_response(session_response, fields_set)
        return filtered_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("stop_session_error", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/sessions/{session_id}/archive",
    summary="Archive session",
    description="Archive a session (set status to archive).",
    responses={
        200: {"description": "Session archived successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Session not found"}
    }
)
async def archive_session(
    session_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Archive session."""
    try:
        session = SessionService.archive_session(
            db=db,
            session_id=session_id,
            user_id=current_user["user_id"]
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with id {session_id} not found"
            )
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        # Get merged settings for response
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        merged_settings = SessionRepository.get_merged_settings(session, workspace.template_settings if workspace else None)
        session_dict = SessionResponse.model_validate(session).model_dump()
        session_dict['settings'] = merged_settings
        session_response = SessionResponse(**session_dict)
        
        # Return only specified fields
        filtered_dict = filter_model_response(session_response, fields_set)
        return filtered_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("archive_session_error", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/sessions/{session_id}/unarchive",
    summary="Unarchive session",
    description="Unarchive a session (set status to active).",
    responses={
        200: {"description": "Session unarchived successfully"},
        401: {"description": "Not authenticated"},
        400: {"description": "Cannot unarchive session in archived workspace"},
        404: {"description": "Session not found"}
    }
)
async def unarchive_session(
    session_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Unarchive session."""
    try:
        session = SessionService.unarchive_session(
            db=db,
            session_id=session_id,
            user_id=current_user["user_id"]
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with id {session_id} not found"
            )
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        # Get merged settings for response
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        merged_settings = SessionRepository.get_merged_settings(session, workspace.template_settings if workspace else None)
        session_dict = SessionResponse.model_validate(session).model_dump()
        session_dict['settings'] = merged_settings
        session_response = SessionResponse(**session_dict)
        
        # Return only specified fields
        filtered_dict = filter_model_response(session_response, fields_set)
        return filtered_dict
    except ValueError as e:
        status_code = status.HTTP_400_BAD_REQUEST if "archived workspace" in str(e).lower() else status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("unarchive_session_error", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/sessions/{session_id}/restore",
    summary="Restore session from trash",
    description="Restore a session from trash (undo soft delete).",
    responses={
        200: {"description": "Session restored successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Session not found"}
    }
)
async def restore_session(
    session_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Restore session from trash."""
    try:
        session = SessionService.restore_session(
            db=db,
            session_id=session_id,
            user_id=current_user["user_id"]
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with id {session_id} not found"
            )
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        # Get merged settings for response
        workspace = WorkspaceRepository.get_by_id(db, session.workspace_id)
        merged_settings = SessionRepository.get_merged_settings(session, workspace.template_settings if workspace else None)
        session_dict = SessionResponse.model_validate(session).model_dump()
        session_dict['settings'] = merged_settings
        session_response = SessionResponse(**session_dict)
        
        # Return only specified fields
        filtered_dict = filter_model_response(session_response, fields_set)
        return filtered_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("restore_session_error", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete(
    "/sessions/{session_id}/permanent",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete session",
    description="Permanently delete a session (hard delete). This action cannot be undone.",
    responses={
        204: {"description": "Session permanently deleted"},
        401: {"description": "Not authenticated"},
        404: {"description": "Session not found"}
    }
)
async def delete_session_permanent(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Permanently delete session."""
    try:
        deleted_session = SessionService.delete_session(
            db=db,
            session_id=session_id,
            user_id=current_user["user_id"],
            hard=True
        )
        
        if not deleted_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with id {session_id} not found"
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
        logger.error("delete_session_permanent_error", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

