"""Main API router."""
from fastapi import APIRouter
from endpoints import health
from endpoints.v1 import auth, users, workspaces, sessions

api_router = APIRouter()

# Include health check router
api_router.include_router(health.router)

# Include sub-routers
api_router.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
api_router.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["Workspaces"])

# Sessions router - includes both workspace sessions and individual session operations
# Workspace sessions routes: /api/v1/workspaces/{workspace_id}/sessions
# Individual session routes: /api/v1/sessions/{session_id}/*
api_router.include_router(sessions.router, prefix="/api/v1", tags=["Sessions"])

