"""
Configuration settings for the golf probability engine.

This module handles environment variables and application settings.
Currently uses defaults suitable for development and GitHub Codespaces.
"""

import os
import subprocess
from datetime import datetime, timezone
from typing import Optional


def get_build_version() -> str:
    """Generate build version from git commit SHA or timestamp."""
    # Try to get git commit SHA
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    
    # Fallback to timestamp
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def get_build_time() -> str:
    """Get ISO timestamp for build time."""
    return datetime.now(timezone.utc).isoformat()


class Settings:
    """Application settings with environment variable support."""
    
    # Application info
    APP_NAME: str = "Golf Scoring Probability Engine"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "A professional-grade backend for calculating golf scoring probabilities "
        "based on GHIN Handicap Index, course setup, and statistical models."
    )
    
    # Build info (generated at startup)
    BUILD_VERSION: str = os.getenv("BUILD_VERSION", get_build_version())
    BUILD_TIME: str = os.getenv("BUILD_TIME", get_build_time())
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Simulation defaults
    DEFAULT_NUM_SIMULATIONS: int = 10000
    MAX_NUM_SIMULATIONS: int = 1000000
    MIN_NUM_SIMULATIONS: int = 1000
    
    # USGA constants
    STANDARD_SLOPE: float = 113.0
    MAX_HANDICAP_INDEX: float = 54.0
    MIN_HANDICAP_INDEX: float = -10.0  # Plus handicaps
    
    # API settings
    API_PREFIX: str = "/api/golf"
    
    # CORS settings (for development and mobile access)
    CORS_ORIGINS: list[str] = ["*"]  # Allow all origins for mobile access


settings = Settings()
