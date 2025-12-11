"""Routes package for the golf probability engine."""

from .golf import router as golf_router
from .team import router as team_router
from .config import router as config_router

__all__ = ["golf_router", "team_router", "config_router"]
