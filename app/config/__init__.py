"""
Configuration module for the Golf Scoring Probability Engine.

This package contains configuration settings, thresholds, and customizable
options for the application.
"""

from .settings import Settings, settings
from .suspicion_config import (
    SuspicionMode,
    RiskTier,
    SuspicionThresholds,
    SuspicionWeights,
    CaddyshackLabels,
    SeriousLabels,
    SuspicionConfig,
    get_default_config,
    get_conservative_config,
    get_aggressive_config,
    CONSERVATIVE_THRESHOLDS,
    AGGRESSIVE_THRESHOLDS,
)

__all__ = [
    "Settings",
    "settings",
    "SuspicionMode",
    "RiskTier",
    "SuspicionThresholds",
    "SuspicionWeights",
    "CaddyshackLabels",
    "SeriousLabels",
    "SuspicionConfig",
    "get_default_config",
    "get_conservative_config",
    "get_aggressive_config",
    "CONSERVATIVE_THRESHOLDS",
    "AGGRESSIVE_THRESHOLDS",
]
