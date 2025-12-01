"""Pydantic models for golfer profiles, course setup, scoring targets, and events."""

from pydantic import BaseModel, Field
from typing import Optional


class GolferProfile(BaseModel):
    """
    Represents a golfer's handicap profile.
    
    For v1, we only require the handicap index. Future versions may include
    GHIN integration for actual score history.
    """
    handicap_index: float = Field(
        ..., 
        description="The golfer's USGA Handicap Index (e.g., 12.5)",
        ge=-10.0,  # Scratch or plus handicap
        le=54.0    # Maximum USGA handicap
    )
    name: Optional[str] = Field(
        None, 
        description="Optional golfer name for identification"
    )
    # Future enhancement: recent_scores for calibration
    recent_scores: Optional[list[float]] = Field(
        None, 
        description="Last N gross scores for future calibration (not used in v1)"
    )


class CourseSetup(BaseModel):
    """
    Represents a golf course/tee configuration.
    
    Contains all the information needed to compute course handicap
    and expected scoring distribution.
    """
    course_name: str = Field(
        ..., 
        description="Name of the golf course"
    )
    tee_name: str = Field(
        ..., 
        description="Name of the tee being played (e.g., 'White', 'Blue')"
    )
    par: int = Field(
        ..., 
        description="Course par (typically 70-72 for 18 holes)",
        ge=27,   # Minimum par for 9 holes
        le=80    # Maximum reasonable par for 18 holes
    )
    course_rating: float = Field(
        ..., 
        description="USGA Course Rating (e.g., 72.5)",
        ge=55.0,
        le=85.0
    )
    slope_rating: int = Field(
        ..., 
        description="USGA Slope Rating (e.g., 130, standard is 113)",
        ge=55,
        le=155
    )
    yardage: Optional[int] = Field(
        None, 
        description="Total yardage of the course",
        ge=2000,
        le=8500
    )


class ScoringTarget(BaseModel):
    """
    Represents a target score threshold for probability calculations.
    """
    target_score: int = Field(
        ..., 
        description="Gross score threshold (e.g., 80 for 'breaking 80', or 40 for 9-hole matches)",
        ge=25,   # Allow low scores for 9-hole matches
        le=150
    )


class EventStructure(BaseModel):
    """
    Represents a golf event structure (e.g., tournament rounds).
    """
    num_rounds: int = Field(
        ..., 
        description="Number of rounds in the event (e.g., 1, 3, 5)",
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
