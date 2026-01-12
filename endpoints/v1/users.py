"""User profile endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.db import get_db
from core.auth import get_current_user
from services.user_service import UserService
from endpoints.v1.schemas import UserResponse, UserUpdateRequest
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
        return UserResponse.model_validate(user)
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
            # User exists but no changes were made, return current user
            user = UserService.get_profile(db, current_user["user_id"])
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return UserResponse.model_validate(user)
        
        return UserResponse.model_validate(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_profile_error", user_id=current_user["user_id"], error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

