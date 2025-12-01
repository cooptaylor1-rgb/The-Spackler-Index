"""Pydantic models for team/member-guest configurations."""

from pydantic import BaseModel, Field
from typing import Optional

from .golfer import GolferProfile


class TeamPlayer(BaseModel):
    """
    Represents a player on a team with optional overrides.
    """
    golfer: GolferProfile = Field(
        ..., 
        description="The golfer's profile including handicap index"
    )
    course_handicap_override: Optional[float] = Field(
        None, 
        description="Optional override for course handicap if event uses different allowances"
    )


class TeamProfile(BaseModel):
    """
    Represents a 2-player team for best-ball formats.
    """
    player1: TeamPlayer = Field(
        ..., 
        description="First player on the team"
    )
    player2: TeamPlayer = Field(
        ..., 
        description="Second player on the team"
    )
    team_name: Optional[str] = Field(
        None, 
        description="Optional team name for identification"
    )


class BestBallTarget(BaseModel):
    """
    Represents a target for team best-ball scoring.
    """
    target_net_score: int = Field(
        ..., 
        description="Net team best-ball score threshold (e.g., 62 for net 62 or better)",
        ge=40,
        le=100
    )
    handicap_allowance_percent: float = Field(
        default=100.0, 
        description="Handicap allowance percentage (e.g., 90% for 90% of course handicap)",
        ge=0.0,
        le=100.0
    )


class TeamEventStructure(BaseModel):
    """
    Represents a team event structure for best-ball tournaments.
    """
    num_rounds: int = Field(
        ..., 
        description="Number of rounds in the event (e.g., 3, 5 for member-guest)",
        ge=1,
        le=10
    )
    holes_per_round: int = Field(
        default=18, 
        description="Number of holes per round (9 or 18)",
        ge=9,
        le=18
    )
    event_name: Optional[str] = Field(
        None, 
        description="Optional event name for identification"
    )
    # Future enhancement: matches_per_round for formats like 5x9-hole matches
    matches_per_round: Optional[int] = Field(
        None, 
        description="For future extension: number of matches per round"
    )
