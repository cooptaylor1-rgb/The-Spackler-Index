"""Routes package for the golf probability engine."""

from .golf import router as golf_router
from .team import router as team_router

__all__ = ["golf_router", "team_router"]
