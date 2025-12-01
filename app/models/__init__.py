"""Models package for the golf probability engine."""

from .golfer import GolferProfile, CourseSetup, ScoringTarget, EventStructure
from .team import TeamPlayer, TeamProfile, BestBallTarget, TeamEventStructure
from .requests import (
    SingleRoundProbabilityRequest,
    SingleRoundProbabilityResponse,
    MultiRoundProbabilityRequest,
    MultiRoundProbabilityResponse,
    MilestoneResult,
    MilestoneProbabilityRequest,
    MilestoneProbabilityResponse,
    TeamBestBallSingleRoundRequest,
    TeamBestBallSingleRoundResponse,
    TeamBestBallMultiRoundRequest,
    TeamBestBallMultiRoundResponse,
    ConsecutiveScoresProbabilityRequest,
    ConsecutiveScoresProbabilityResponse,
)

__all__ = [
    # Golfer models
    "GolferProfile",
    "CourseSetup",
    "ScoringTarget",
    "EventStructure",
    # Team models
    "TeamPlayer",
    "TeamProfile",
    "BestBallTarget",
    "TeamEventStructure",
    # Request/Response models
    "SingleRoundProbabilityRequest",
    "SingleRoundProbabilityResponse",
    "MultiRoundProbabilityRequest",
    "MultiRoundProbabilityResponse",
    "MilestoneResult",
    "MilestoneProbabilityRequest",
    "MilestoneProbabilityResponse",
    "TeamBestBallSingleRoundRequest",
    "TeamBestBallSingleRoundResponse",
    "TeamBestBallMultiRoundRequest",
    "TeamBestBallMultiRoundResponse",
    "ConsecutiveScoresProbabilityRequest",
    "ConsecutiveScoresProbabilityResponse",
]
