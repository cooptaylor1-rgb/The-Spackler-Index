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
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import settings
from app.routes import golf_router, team_router, config_router
from app.middleware import SimpleCacheMiddleware

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

# Add simple cache middleware (5 minute TTL for GET requests)
app.add_middleware(SimpleCacheMiddleware, ttl_seconds=300)


# Add performance monitoring middleware
@app.middleware("http")
async def add_performance_metrics(request: Request, call_next):
    """Log request duration and add performance headers."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))  # milliseconds
    
    # Log slow requests (> 500ms)
    if process_time > 0.5:
        logger.warning(
            f"Slow request: {request.method} {request.url.path} "
            f"completed in {process_time*1000:.2f}ms"
        )
    else:
        logger.debug(
            f"{request.method} {request.url.path} "
            f"completed in {process_time*1000:.2f}ms"
        )
    
    return response


# Include API routers
app.include_router(golf_router, prefix=settings.API_PREFIX, tags=["Individual Golf"])
app.include_router(team_router, prefix=settings.API_PREFIX, tags=["Team Golf"])
app.include_router(config_router, prefix=settings.API_PREFIX, tags=["Configuration"])

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
