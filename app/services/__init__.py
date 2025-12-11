"""Services package for the golf probability engine."""

from .probability import (
    compute_course_handicap,
    compute_expected_score,
    estimate_score_std,
    compute_single_round_probability,
    compute_multi_round_probability_at_least_once,
    binomial_tail,
    simulate_individual_scores,
    get_standard_milestones,
    compute_nine_hole_expected_score,
    estimate_nine_hole_score_std,
    compute_consecutive_scores_probability,
    compute_consecutive_in_n_matches_probability,
    analyze_completed_round,
    compute_joint_probability_independent_rounds,
    get_overall_performance_descriptor,
)

from .team_probability import (
    compute_player_parameters,
    simulate_team_bestball_round_scores,
    get_team_approximation_notes,
)

from .sandbagging import (
    calculate_sandbagging_risk_score,
    detect_tournament_excellence_pattern,
    detect_low_volatility_pattern,
    detect_improbable_performance,
    detect_casual_vs_tournament_disparity,
    detect_all_scores_better_than_expected,
    generate_sandbagging_summary,
    generate_recommendation,
)

from .suspicion_engine import (
    SuspicionScoringEngine,
    SuspicionResult,
    SuspicionReason,
    FlagType,
    FlagSeverity,
)

__all__ = [
    # Individual probability functions
    "compute_course_handicap",
    "compute_expected_score",
    "estimate_score_std",
    "compute_single_round_probability",
    "compute_multi_round_probability_at_least_once",
    "binomial_tail",
    "simulate_individual_scores",
    "get_standard_milestones",
    "compute_nine_hole_expected_score",
    "estimate_nine_hole_score_std",
    "compute_consecutive_scores_probability",
    "compute_consecutive_in_n_matches_probability",
    "analyze_completed_round",
    "compute_joint_probability_independent_rounds",
    "get_overall_performance_descriptor",
    # Team probability functions
    "compute_player_parameters",
    "simulate_team_bestball_round_scores",
    "get_team_approximation_notes",
    # Sandbagging detection functions
    "calculate_sandbagging_risk_score",
    "detect_tournament_excellence_pattern",
    "detect_low_volatility_pattern",
    "detect_improbable_performance",
    "detect_casual_vs_tournament_disparity",
    "detect_all_scores_better_than_expected",
    "generate_sandbagging_summary",
    "generate_recommendation",
    # Enhanced suspicion engine
    "SuspicionScoringEngine",
    "SuspicionResult",
    "SuspicionReason",
    "FlagType",
    "FlagSeverity",
]

