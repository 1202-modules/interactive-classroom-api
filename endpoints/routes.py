"""Main API router."""
from fastapi import APIRouter
from endpoints import health
from endpoints.v1 import auth, users, workspaces, sessions, workspace_modules, session_modules

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

# Module routers
api_router.include_router(workspace_modules.router, prefix="/api/v1", tags=["Workspace Modules"])
api_router.include_router(session_modules.router, prefix="/api/v1", tags=["Session Modules"])

