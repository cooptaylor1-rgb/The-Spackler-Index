"""
Configuration settings for the golf probability engine.

This module handles environment variables and application settings.
Currently uses defaults suitable for development and GitHub Codespaces.
"""

import os
from typing import Optional


class Settings:
    """Application settings with environment variable support."""
    
    # Application info
    APP_NAME: str = "Golf Scoring Probability Engine"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "A professional-grade backend for calculating golf scoring probabilities "
        "based on GHIN Handicap Index, course setup, and statistical models."
    )
    
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
    
    # CORS settings (for development)
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]


settings = Settings()
