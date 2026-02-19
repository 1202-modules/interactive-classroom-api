"""Main API application."""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Use absolute imports with explicit path
from sqlalchemy.exc import OperationalError, InterfaceError

from core.config import settings
from endpoints.routes import api_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="""
    Interactive Classroom Platform API
    
    API for managing interactive classroom sessions, workspaces, and user accounts.
    
    Features:
    
    - User Management: Registration, email verification, and profile management
    - Workspace Management: Create and manage workspaces for organizing sessions
    - Session Management: Create, start, stop, and manage interactive sessions
    
    Authentication:
    
    Most endpoints require JWT authentication. Include the token in the Authorization header:
    
    Authorization: Bearer <your-token>
    """,
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User registration, email verification, and login"
        },
        {
            "name": "Users",
            "description": "User profile management"
        },
        {
            "name": "Workspaces",
            "description": "Workspace management operations"
        },
        {
            "name": "Sessions",
            "description": "Session management operations"
        }
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)


def _handle_db_unavailable(request, exc):
    """Log full error server-side, return short 503 to client."""
    logger.error(
        "database_unavailable",
        path=request.url.path,
        error=str(exc.orig) if getattr(exc, "orig", None) else str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=503,
        content={"detail": "Service temporarily unavailable. Please try again later."},
    )


app.add_exception_handler(OperationalError, _handle_db_unavailable)
app.add_exception_handler(InterfaceError, _handle_db_unavailable)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "message": "Interactive Classroom Platform API",
        "version": settings.API_VERSION
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("api_started", version=settings.API_VERSION)


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("api_shutdown")

