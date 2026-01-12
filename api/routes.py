"""Main API router."""
from fastapi import APIRouter
from api.api.v1 import auth, users, workspaces, sessions

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
api_router.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["Workspaces"])
api_router.include_router(sessions.router, prefix="/api/v1", tags=["Sessions"])

