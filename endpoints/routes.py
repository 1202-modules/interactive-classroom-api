"""Main API router."""
from fastapi import APIRouter
from endpoints import health
from endpoints.v1 import auth, users, workspaces, session_guest, session_join, session_participants, session_questions, session_timer, sessions, workspace_modules, session_modules

api_router = APIRouter()

# Include health check router
api_router.include_router(health.router)

# Include sub-routers
api_router.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
api_router.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["Workspaces"])

# Session guest and join (by-passcode) must be before sessions so /sessions/by-passcode/{passcode} is matched first
api_router.include_router(session_guest.router, prefix="/api/v1", tags=["Session Guest"])
api_router.include_router(session_join.router, prefix="/api/v1", tags=["Session Join"])
api_router.include_router(session_participants.router, prefix="/api/v1", tags=["Session Participants"])
api_router.include_router(session_questions.router, prefix="/api/v1", tags=["Session Questions"])
api_router.include_router(session_timer.router, prefix="/api/v1", tags=["Session Timer"])

# Sessions router - includes both workspace sessions and individual session operations
# Workspace sessions routes: /api/v1/workspaces/{workspace_id}/sessions
# Individual session routes: /api/v1/sessions/{session_id}/*
api_router.include_router(sessions.router, prefix="/api/v1", tags=["Sessions"])

# Module routers
api_router.include_router(workspace_modules.router, prefix="/api/v1", tags=["Workspace Modules"])
api_router.include_router(session_modules.router, prefix="/api/v1", tags=["Session Modules"])

