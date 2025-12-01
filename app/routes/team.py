"""
API routes for team best-ball probability calculations.

This module defines the FastAPI endpoints for calculating single-round
and multi-round team best-ball probabilities, commonly used for
member-guest tournament preparation.
"""

import logging
from fastapi import APIRouter

from app.models import (
    TeamBestBallSingleRoundRequest,
    TeamBestBallSingleRoundResponse,
    TeamBestBallMultiRoundRequest,
    TeamBestBallMultiRoundResponse,
)
from app.services import (
    simulate_team_bestball_round_scores,
    get_team_approximation_notes,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/team/bestball/probability/single-round",
    response_model=TeamBestBallSingleRoundResponse,
    summary="Calculate Team Best-Ball Single Round Probability",
    description=(
        "Calculate the probability of a 2-player team achieving a target net "
        "best-ball score in a single round. Uses Monte Carlo simulation."
    )
)
async def calculate_team_bestball_single_round(
    request: TeamBestBallSingleRoundRequest
) -> TeamBestBallSingleRoundResponse:
    """
    Calculate single round team best-ball probability.
    
    Uses Monte Carlo simulation with round-level best-ball approximation.
    """
    logger.info(
        f"Team single-round calculation: "
        f"P1 handicap={request.team.player1.golfer.handicap_index}, "
        f"P2 handicap={request.team.player2.golfer.handicap_index}, "
        f"target={request.bestball_target.target_net_score}, "
        f"allowance={request.bestball_target.handicap_allowance_percent}%"
    )
    
    # Run simulation for single round
    results = simulate_team_bestball_round_scores(
        team=request.team,
        course=request.course,
        bestball_target=request.bestball_target,
        num_rounds=1,  # Single round
        num_simulations=request.num_simulations,
        min_success_rounds=1
    )
    
    logger.info(
        f"Result: expected_bb={results['expected_team_bestball_score_single_round']:.1f}, "
        f"probability={results['single_round_probability_at_or_below_target']:.4f}"
    )
    
    return TeamBestBallSingleRoundResponse(
        target_net_score=request.bestball_target.target_net_score,
        handicap_allowance_percent=request.bestball_target.handicap_allowance_percent,
        expected_team_bestball_score_single_round=round(
            results["expected_team_bestball_score_single_round"], 2
        ),
        std_team_bestball_score_single_round=round(
            results["std_team_bestball_score_single_round"], 2
        ),
        probability_net_bestball_at_or_below_target_single_round=round(
            results["single_round_probability_at_or_below_target"], 6
        ),
        num_simulations_used=results["num_simulations_used"],
        approximation_notes=get_team_approximation_notes()
    )


@router.post(
    "/team/bestball/probability/multi-round",
    response_model=TeamBestBallMultiRoundResponse,
    summary="Calculate Team Best-Ball Multi-Round Probability",
    description=(
        "Calculate probabilities for a 2-player team achieving a target net "
        "best-ball score over multiple rounds (e.g., member-guest tournament). "
        "Uses Monte Carlo simulation."
    )
)
async def calculate_team_bestball_multi_round(
    request: TeamBestBallMultiRoundRequest
) -> TeamBestBallMultiRoundResponse:
    """
    Calculate multi-round team best-ball probability.
    
    Uses Monte Carlo simulation with round-level best-ball approximation.
    """
    logger.info(
        f"Team multi-round calculation: "
        f"P1 handicap={request.team.player1.golfer.handicap_index}, "
        f"P2 handicap={request.team.player2.golfer.handicap_index}, "
        f"target={request.bestball_target.target_net_score}, "
        f"rounds={request.event.num_rounds}, "
        f"min_success={request.min_success_rounds}"
    )
    
    # Run simulation for multiple rounds
    results = simulate_team_bestball_round_scores(
        team=request.team,
        course=request.course,
        bestball_target=request.bestball_target,
        num_rounds=request.event.num_rounds,
        num_simulations=request.num_simulations,
        min_success_rounds=request.min_success_rounds
    )
    
    logger.info(
        f"Result: expected_bb={results['expected_team_bestball_score_single_round']:.1f}, "
        f"single_prob={results['single_round_probability_at_or_below_target']:.4f}, "
        f"at_least_once={results['probability_at_least_once_in_event']:.4f}"
    )
    
    return TeamBestBallMultiRoundResponse(
        target_net_score=request.bestball_target.target_net_score,
        handicap_allowance_percent=request.bestball_target.handicap_allowance_percent,
        num_rounds=request.event.num_rounds,
        min_success_rounds=request.min_success_rounds,
        probability_net_bestball_at_or_below_target_single_round=round(
            results["single_round_probability_at_or_below_target"], 6
        ),
        probability_at_least_once_in_event=round(
            results["probability_at_least_once_in_event"], 6
        ),
        probability_at_least_min_success_rounds=round(
            results["probability_at_least_min_success_rounds"], 6
        ),
        expected_team_bestball_score_single_round=round(
            results["expected_team_bestball_score_single_round"], 2
        ),
        std_team_bestball_score_single_round=round(
            results["std_team_bestball_score_single_round"], 2
        ),
        num_simulations_used=results["num_simulations_used"],
        approximation_notes=get_team_approximation_notes()
    )
