"""Request and response models for API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, Literal

from .golfer import GolferProfile, CourseSetup, ScoringTarget, EventStructure
from .team import TeamProfile, BestBallTarget, TeamEventStructure


# ============================================================================
# Individual Player Request/Response Models
# ============================================================================

class SingleRoundProbabilityRequest(BaseModel):
    """Request model for single-round probability calculation."""
    golfer: GolferProfile
    course: CourseSetup
    target: ScoringTarget


class SingleRoundProbabilityResponse(BaseModel):
    """Response model for single-round probability calculation."""
    expected_score: float = Field(
        ..., 
        description="Expected gross score based on handicap and course setup"
    )
    score_std: float = Field(
        ..., 
        description="Standard deviation of score distribution"
    )
    target_score: int = Field(
        ..., 
        description="Target score threshold"
    )
    probability_score_at_or_below_target: float = Field(
        ..., 
        description="Probability of shooting target score or better (0-1)",
        ge=0.0,
        le=1.0
    )
    distribution_type: str = Field(
        default="normal_approximation", 
        description="Type of distribution used for calculation"
    )
    z_score: Optional[float] = Field(
        None, 
        description=(
            "Z-score used in normal distribution calculation. "
            "Negative values indicate target is above expected score (harder to achieve), "
            "positive values indicate target is below expected score (easier to achieve)."
        )
    )


class MultiRoundProbabilityRequest(BaseModel):
    """Request model for multi-round probability calculation."""
    golfer: GolferProfile
    course: CourseSetup
    target: ScoringTarget
    event: EventStructure
    min_success_rounds: int = Field(
        default=1, 
        description="Minimum number of rounds to achieve target score",
        ge=1
    )


class MultiRoundProbabilityResponse(BaseModel):
    """Response model for multi-round probability calculation."""
    expected_score: float = Field(
        ..., 
        description="Expected gross score per round"
    )
    score_std: float = Field(
        ..., 
        description="Standard deviation of score distribution"
    )
    target_score: int = Field(
        ..., 
        description="Target score threshold"
    )
    num_rounds: int = Field(
        ..., 
        description="Number of rounds in the event"
    )
    min_success_rounds: int = Field(
        ..., 
        description="Minimum success rounds required"
    )
    probability_at_least_min_success_rounds: float = Field(
        ..., 
        description="Probability of achieving target in at least min_success_rounds",
        ge=0.0,
        le=1.0
    )
    probability_at_least_once: float = Field(
        ..., 
        description="Probability of achieving target at least once",
        ge=0.0,
        le=1.0
    )
    single_round_probability: float = Field(
        ..., 
        description="Probability of achieving target in a single round",
        ge=0.0,
        le=1.0
    )
    binomial_model_used: bool = Field(
        default=True, 
        description="Whether binomial model was used for multi-round calculation"
    )


class MilestoneResult(BaseModel):
    """Result for a single milestone score."""
    target_score: int = Field(
        ..., 
        description="Target score for this milestone"
    )
    prob_single_round_at_or_below: float = Field(
        ..., 
        description="Probability of achieving this score in a single round",
        ge=0.0,
        le=1.0
    )
    prob_at_least_once_in_event: float = Field(
        ..., 
        description="Probability of achieving this score at least once in the event",
        ge=0.0,
        le=1.0
    )


class MilestoneProbabilityRequest(BaseModel):
    """Request model for milestone probability calculation."""
    golfer: GolferProfile
    course: CourseSetup
    event: EventStructure


class MilestoneProbabilityResponse(BaseModel):
    """Response model for milestone probability calculation."""
    expected_score: float = Field(
        ..., 
        description="Expected gross score per round"
    )
    score_std: float = Field(
        ..., 
        description="Standard deviation of score distribution"
    )
    num_rounds: int = Field(
        ..., 
        description="Number of rounds in the event"
    )
    milestones: list[MilestoneResult] = Field(
        ..., 
        description="Probability results for each milestone score"
    )


# ============================================================================
# Team Best-Ball Request/Response Models
# ============================================================================

class TeamBestBallSingleRoundRequest(BaseModel):
    """Request model for single-round team best-ball probability."""
    team: TeamProfile
    course: CourseSetup
    bestball_target: BestBallTarget
    num_simulations: int = Field(
        default=10000, 
        description="Number of Monte Carlo simulations to run",
        ge=1000,
        le=1000000
    )


class TeamBestBallSingleRoundResponse(BaseModel):
    """Response model for single-round team best-ball probability."""
    target_net_score: int = Field(
        ..., 
        description="Target net best-ball score"
    )
    handicap_allowance_percent: float = Field(
        ..., 
        description="Handicap allowance percentage applied"
    )
    expected_team_bestball_score_single_round: float = Field(
        ..., 
        description="Expected team net best-ball score for a single round"
    )
    std_team_bestball_score_single_round: float = Field(
        ..., 
        description="Standard deviation of team net best-ball score"
    )
    probability_net_bestball_at_or_below_target_single_round: float = Field(
        ..., 
        description="Probability of achieving target net best-ball score in a single round",
        ge=0.0,
        le=1.0
    )
    num_simulations_used: int = Field(
        ..., 
        description="Number of simulations used in calculation"
    )
    approximation_notes: str = Field(
        default="Team best-ball modeled as min of two independent net round scores (round-level approximation)",
        description="Notes about the approximation method used"
    )


class TeamBestBallMultiRoundRequest(BaseModel):
    """Request model for multi-round team best-ball probability."""
    team: TeamProfile
    course: CourseSetup
    bestball_target: BestBallTarget
    event: TeamEventStructure
    min_success_rounds: int = Field(
        default=1, 
        description="Minimum number of rounds to achieve target score",
        ge=1
    )
    num_simulations: int = Field(
        default=10000, 
        description="Number of Monte Carlo simulations to run",
        ge=1000,
        le=1000000
    )


class TeamBestBallMultiRoundResponse(BaseModel):
    """Response model for multi-round team best-ball probability."""
    target_net_score: int = Field(
        ..., 
        description="Target net best-ball score"
    )
    handicap_allowance_percent: float = Field(
        ..., 
        description="Handicap allowance percentage applied"
    )
    num_rounds: int = Field(
        ..., 
        description="Number of rounds in the event"
    )
    min_success_rounds: int = Field(
        ..., 
        description="Minimum success rounds required"
    )
    probability_net_bestball_at_or_below_target_single_round: float = Field(
        ..., 
        description="Probability of achieving target in a single round",
        ge=0.0,
        le=1.0
    )
    probability_at_least_once_in_event: float = Field(
        ..., 
        description="Probability of achieving target at least once in the event",
        ge=0.0,
        le=1.0
    )
    probability_at_least_min_success_rounds: float = Field(
        ..., 
        description="Probability of achieving target in at least min_success_rounds",
        ge=0.0,
        le=1.0
    )
    expected_team_bestball_score_single_round: float = Field(
        ..., 
        description="Expected team net best-ball score for a single round"
    )
    std_team_bestball_score_single_round: float = Field(
        ..., 
        description="Standard deviation of team net best-ball score"
    )
    num_simulations_used: int = Field(
        ..., 
        description="Number of simulations used in calculation"
    )
    approximation_notes: str = Field(
        default="Team best-ball modeled as min of two independent net round scores (round-level approximation)",
        description="Notes about the approximation method used"
    )


# ============================================================================
# Consecutive Scores Request/Response Models
# ============================================================================

class ConsecutiveScoresProbabilityRequest(BaseModel):
    """Request model for consecutive scores probability calculation."""
    golfer: GolferProfile
    course: CourseSetup
    target: ScoringTarget
    consecutive_count: int = Field(
        ..., 
        description="Number of consecutive rounds to achieve target score",
        ge=1,
        le=20
    )
    total_matches: Optional[int] = Field(
        None, 
        description="Total number of matches to play (if specified, calculates probability of achieving streak within these matches)",
        ge=1,
        le=100
    )
    holes_per_round: Literal[9, 18] = Field(
        default=18,
        description="Number of holes per round (9 or 18)"
    )


class ConsecutiveScoresProbabilityResponse(BaseModel):
    """Response model for consecutive scores probability calculation."""
    expected_score: float = Field(
        ..., 
        description="Expected gross score per round"
    )
    score_std: float = Field(
        ..., 
        description="Standard deviation of score distribution"
    )
    target_score: int = Field(
        ..., 
        description="Target score threshold"
    )
    consecutive_count: int = Field(
        ..., 
        description="Number of consecutive rounds required"
    )
    holes_per_round: int = Field(
        ...,
        description="Number of holes per round (9 or 18)"
    )
    single_round_probability: float = Field(
        ..., 
        description="Probability of achieving target in a single round",
        ge=0.0,
        le=1.0
    )
    probability_all_consecutive: float = Field(
        ..., 
        description="Probability of achieving target in ALL consecutive rounds",
        ge=0.0,
        le=1.0
    )
    total_matches: Optional[int] = Field(
        None, 
        description="Total number of matches (if specified)"
    )
    probability_streak_in_matches: Optional[float] = Field(
        None, 
        description="Probability of achieving at least one streak within total matches",
        ge=0.0,
        le=1.0
    )
