"""
API routes for configuration management.

This module provides endpoints for managing the suspicion detection
configuration, including mode switching between Caddyshack and Serious modes.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import (
    SuspicionConfig,
    SuspicionMode,
    SuspicionThresholds,
    get_default_config,
    get_conservative_config,
    get_aggressive_config,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Global config state (in production, this would be per-user or per-session)
_current_config: SuspicionConfig = get_default_config()


class ConfigUpdateRequest(BaseModel):
    """Request model for updating configuration."""
    mode: Optional[SuspicionMode] = Field(
        None,
        description="UI mode: 'caddyshack' (playful) or 'serious' (committee)"
    )
    preset: Optional[str] = Field(
        None,
        description="Threshold preset: 'default', 'conservative', or 'aggressive'"
    )


class ConfigResponse(BaseModel):
    """Response model for configuration."""
    mode: str = Field(..., description="Current UI mode")
    preset: str = Field(..., description="Current threshold preset")
    thresholds: dict = Field(..., description="Current threshold values")
    labels: dict = Field(..., description="Current labels for the mode")


@router.get(
    "/config",
    response_model=ConfigResponse,
    summary="Get Current Configuration",
    description="Get the current suspicion detection configuration including mode and thresholds."
)
async def get_config() -> ConfigResponse:
    """Get the current configuration settings."""
    global _current_config
    
    labels = _current_config.get_labels()
    
    return ConfigResponse(
        mode=_current_config.mode.value,
        preset="default",  # TODO: track which preset is active
        thresholds=_current_config.thresholds.model_dump(),
        labels={
            "tier_low": labels.tier_low,
            "tier_moderate": labels.tier_moderate,
            "tier_high": labels.tier_high,
            "tier_severe": labels.tier_severe,
            "badge_under_review": labels.badge_under_review,
            "badge_probable_bandit": labels.badge_probable_bandit,
            "badge_suspicion_high": labels.badge_suspicion_high,
            "badge_all_clear": labels.badge_all_clear,
        }
    )


@router.put(
    "/config",
    response_model=ConfigResponse,
    summary="Update Configuration",
    description="Update the suspicion detection configuration."
)
async def update_config(request: ConfigUpdateRequest) -> ConfigResponse:
    """Update configuration settings."""
    global _current_config
    
    # Update mode if provided
    if request.mode:
        _current_config.mode = request.mode
        logger.info(f"Configuration mode updated to: {request.mode.value}")
    
    # Update preset if provided
    if request.preset:
        if request.preset == "conservative":
            new_config = get_conservative_config()
            new_config.mode = _current_config.mode
            _current_config = new_config
        elif request.preset == "aggressive":
            new_config = get_aggressive_config()
            new_config.mode = _current_config.mode
            _current_config = new_config
        elif request.preset == "default":
            new_config = get_default_config()
            new_config.mode = _current_config.mode
            _current_config = new_config
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid preset: {request.preset}. Use 'default', 'conservative', or 'aggressive'"
            )
        logger.info(f"Configuration preset updated to: {request.preset}")
    
    return await get_config()


@router.post(
    "/config/reset",
    response_model=ConfigResponse,
    summary="Reset Configuration",
    description="Reset configuration to default values."
)
async def reset_config() -> ConfigResponse:
    """Reset configuration to defaults."""
    global _current_config
    _current_config = get_default_config()
    logger.info("Configuration reset to defaults")
    return await get_config()


def get_current_config() -> SuspicionConfig:
    """Get the current configuration (for use by other modules)."""
    global _current_config
    return _current_config
