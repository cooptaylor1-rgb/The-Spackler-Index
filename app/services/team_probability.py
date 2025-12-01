"""
Team best-ball probability calculation service.

This module implements Monte Carlo simulations for 2-player team best-ball
formats, commonly used in member-guest tournaments.

The approach models team best-ball at the round level (not hole-by-hole)
for simplicity in v1. The team net best-ball score is approximated as
the minimum of the two players' net round scores.

All calculations use conservative assumptions and clearly document
the approximations made.
"""

import numpy as np
from typing import Optional

from app.models import TeamProfile, CourseSetup, BestBallTarget, TeamEventStructure
from app.services.probability import (
    compute_course_handicap,
    compute_expected_score,
    estimate_score_std,
)


def compute_player_parameters(
    handicap_index: float,
    course_setup: CourseSetup,
    allowance_percent: float = 100.0,
    course_handicap_override: Optional[float] = None
) -> tuple[float, float, float]:
    """
    Compute all scoring parameters for a single player.
    
    Args:
        handicap_index: The player's USGA Handicap Index
        course_setup: The course configuration
        allowance_percent: Handicap allowance percentage (e.g., 90 for 90%)
        course_handicap_override: Optional override for course handicap
    
    Returns:
        Tuple of (expected_gross_score, sigma, course_handicap)
    """
    # Compute expected gross score (always uses full handicap for expectation)
    expected_gross = compute_expected_score(handicap_index, course_setup)
    
    # Compute standard deviation
    sigma = estimate_score_std(handicap_index)
    
    # Compute course handicap with allowance
    if course_handicap_override is not None:
        course_handicap = course_handicap_override * (allowance_percent / 100.0)
    else:
        course_handicap = compute_course_handicap(
            handicap_index,
            course_setup.course_rating,
            course_setup.slope_rating,
            course_setup.par,
            allowance_percent
        )
    
    return expected_gross, sigma, course_handicap


def simulate_team_bestball_round_scores(
    team: TeamProfile,
    course: CourseSetup,
    bestball_target: BestBallTarget,
    num_rounds: int,
    num_simulations: int = 10000,
    min_success_rounds: int = 1
) -> dict:
    """
    Simulate team best-ball scores using Monte Carlo simulation.
    
    This function models team best-ball at the round level:
    - Each player's gross score is drawn from Normal(expected, sigma)
    - Net scores are computed using course handicap with allowance
    - Team net best-ball = min(player1_net, player2_net) for each round
    
    This is an approximation to true hole-by-hole best-ball, but provides
    reasonable estimates for tournament preparation.
    
    Args:
        team: TeamProfile with two players
        course: CourseSetup with course parameters
        bestball_target: Target configuration including allowance
        num_rounds: Number of rounds per simulation (event length)
        num_simulations: Number of Monte Carlo iterations
        min_success_rounds: Minimum successful rounds for probability calculation
    
    Returns:
        Dictionary containing:
        - single_round_probability_at_or_below_target: P(team BB ≤ target) per round
        - probability_at_least_once_in_event: P(at least 1 round ≤ target)
        - probability_at_least_min_success_rounds: P(at least k rounds ≤ target)
        - expected_team_bestball_score_single_round: Mean team BB score
        - std_team_bestball_score_single_round: Std dev of team BB score
        - num_simulations_used: Actual simulations run
    """
    allowance = bestball_target.handicap_allowance_percent
    target = bestball_target.target_net_score
    
    # Get player parameters
    p1_expected, p1_sigma, p1_ch = compute_player_parameters(
        team.player1.golfer.handicap_index,
        course,
        allowance,
        team.player1.course_handicap_override
    )
    
    p2_expected, p2_sigma, p2_ch = compute_player_parameters(
        team.player2.golfer.handicap_index,
        course,
        allowance,
        team.player2.course_handicap_override
    )
    
    # Simulate gross scores for both players
    # Shape: (num_simulations, num_rounds)
    p1_gross = np.random.normal(p1_expected, p1_sigma, size=(num_simulations, num_rounds))
    p2_gross = np.random.normal(p2_expected, p2_sigma, size=(num_simulations, num_rounds))
    
    # Compute net scores
    p1_net = p1_gross - p1_ch
    p2_net = p2_gross - p2_ch
    
    # Team best-ball is minimum of the two net scores (round-level approximation)
    team_bestball = np.minimum(p1_net, p2_net)
    
    # Round to integers for discrete score comparison
    team_bestball_rounded = np.round(team_bestball).astype(int)
    
    # Calculate statistics
    expected_bb_score = float(np.mean(team_bestball))
    std_bb_score = float(np.std(team_bestball))
    
    # Single-round probability: count all rounds meeting target
    total_rounds = num_simulations * num_rounds
    single_round_successes = np.sum(team_bestball_rounded <= target)
    prob_single_round = float(single_round_successes / total_rounds)
    
    # Multi-round probabilities
    # Count successes per event (simulation)
    successes_per_event = np.sum(team_bestball_rounded <= target, axis=1)
    
    # At least once
    events_with_at_least_one = np.sum(successes_per_event >= 1)
    prob_at_least_once = float(events_with_at_least_one / num_simulations)
    
    # At least min_success_rounds
    events_with_min_success = np.sum(successes_per_event >= min_success_rounds)
    prob_at_least_min = float(events_with_min_success / num_simulations)
    
    return {
        "single_round_probability_at_or_below_target": prob_single_round,
        "probability_at_least_once_in_event": prob_at_least_once,
        "probability_at_least_min_success_rounds": prob_at_least_min,
        "expected_team_bestball_score_single_round": expected_bb_score,
        "std_team_bestball_score_single_round": std_bb_score,
        "num_simulations_used": num_simulations,
        # Additional details for debugging/validation
        "player1_expected_gross": p1_expected,
        "player1_course_handicap": p1_ch,
        "player2_expected_gross": p2_expected,
        "player2_course_handicap": p2_ch,
    }


def get_team_approximation_notes() -> str:
    """
    Return standard approximation notes for team best-ball calculations.
    
    This documents the assumptions and limitations of the round-level
    best-ball approximation used in v1.
    """
    return (
        "Team best-ball modeled as min of two independent net round scores "
        "(round-level approximation). This provides reasonable estimates but "
        "may slightly underestimate the true best-ball advantage compared to "
        "hole-by-hole modeling. Assumes rounds are independent and scores "
        "follow normal distributions."
    )
