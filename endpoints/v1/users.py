"""User profile endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from core.db import get_db
from core.auth import get_current_user
from services.user_service import UserService
from endpoints.v1.schemas import UserResponse, UserUpdateRequest
from utils.query_params import parse_fields, filter_model_response
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get the profile of the currently authenticated user.",
    responses={
        200: {"description": "User profile retrieved successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "User not found"}
    }
)
async def get_current_user_profile(
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include (e.g., id,email,first_name)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user profile."""
    try:
        user = UserService.get_profile(db, current_user["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        user_response = UserResponse.model_validate(user)
        
        # Apply fields filter if specified
        fields_set = parse_fields(fields)
        if fields_set:
            filtered_dict = filter_model_response(user_response, fields_set)
            return filtered_dict
        
        return user_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_profile_error", user_id=current_user["user_id"], error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="""
    Update the profile of the currently authenticated user.
    
    All fields are optional - only provided fields will be updated.
    """,
    responses={
        200: {"description": "Profile updated successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "User not found"}
    }
)
async def update_current_user_profile(
    user_data: UserUpdateRequest,
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include. If not specified, returns empty response."),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update current user profile."""
    try:
        updated_user = UserService.update_profile(
            db=db,
            user_id=current_user["user_id"],
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            avatar_url=user_data.avatar_url
        )
        
        if not updated_user:
            # User exists but no changes were made, get current user
            user = UserService.get_profile(db, current_user["user_id"])
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            user_response = UserResponse.model_validate(user)
        else:
            user_response = UserResponse.model_validate(updated_user)
        
        # If fields not specified, return empty response
        fields_set = parse_fields(fields)
        if not fields_set:
            return {}
        
        filtered_dict = filter_model_response(user_response, fields_set)
        return filtered_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_profile_error", user_id=current_user["user_id"], error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

