"""
Golf Scoring Probability Engine - FastAPI Application

This is the main entry point for the golf scoring probability engine.
It provides REST API endpoints for calculating individual and team
scoring probabilities based on GHIN handicap indices and course setup.

Run with:
    uvicorn app.main:app --reload

For production:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import settings
from app.routes import golf_router, team_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"API available at {settings.API_PREFIX}")
    logger.info(f"Documentation available at /docs")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(golf_router, prefix=settings.API_PREFIX, tags=["Individual Golf"])
app.include_router(team_router, prefix=settings.API_PREFIX, tags=["Team Golf"])

# Mount static files for the web UI
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    """Serve the main web UI."""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {
        "message": "Golf Scoring Probability Engine",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api": settings.API_PREFIX,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.APP_VERSION}
