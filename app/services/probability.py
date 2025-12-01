"""
Probability calculation service for individual golf scoring.

This module implements the core probability calculations for individual golfers,
including course handicap computation, expected score calculation, scoring
distribution modeling, and multi-round probability calculations.

All calculations use conservative assumptions to avoid overstating the odds
of exceptional rounds.
"""

import math
from typing import Optional
from scipy import stats

from app.models import CourseSetup


# Standard USGA slope rating for comparison
STANDARD_SLOPE = 113.0


def compute_course_handicap(
    handicap_index: float,
    course_rating: float,
    slope_rating: int,
    par: int,
    allowance_percent: float = 100.0
) -> float:
    """
    Compute the course handicap for a golfer on a specific course.
    
    Formula: CH = (handicap_index * (slope_rating / 113)) + (course_rating - par)
    
    The allowance_percent parameter allows for team formats that use
    reduced handicap allowances (e.g., 90% in some member-guest formats).
    
    Args:
        handicap_index: The golfer's USGA Handicap Index
        course_rating: The USGA Course Rating for the tee being played
        slope_rating: The USGA Slope Rating for the tee being played
        par: The par for the course
        allowance_percent: Percentage of course handicap to use (default 100%)
    
    Returns:
        The computed course handicap (may be negative for plus handicaps)
    
    Examples:
        >>> compute_course_handicap(15.0, 72.5, 130, 72)
        17.745...
        >>> compute_course_handicap(15.0, 72.5, 130, 72, allowance_percent=90.0)
        15.97...
    """
    raw_course_handicap = (
        handicap_index * (slope_rating / STANDARD_SLOPE) 
        + (course_rating - par)
    )
    return raw_course_handicap * (allowance_percent / 100.0)


def compute_expected_score(
    handicap_index: float,
    course_setup: CourseSetup
) -> float:
    """
    Compute the expected gross score for a golfer on a specific course.
    
    Expected score = par + course_handicap
    
    Args:
        handicap_index: The golfer's USGA Handicap Index
        course_setup: The course configuration (rating, slope, par)
    
    Returns:
        The expected gross score for this golfer on this course
    
    Examples:
        >>> course = CourseSetup(course_name="Test", tee_name="White", 
        ...                      par=72, course_rating=72.5, slope_rating=130)
        >>> compute_expected_score(15.0, course)
        89.745...
    """
    course_handicap = compute_course_handicap(
        handicap_index,
        course_setup.course_rating,
        course_setup.slope_rating,
        course_setup.par
    )
    return course_setup.par + course_handicap


def estimate_score_std(handicap_index: float) -> float:
    """
    Estimate the standard deviation of scoring for a golfer.
    
    This uses a conservative mapping that increases standard deviation
    for higher handicaps, reflecting greater scoring variability among
    less consistent players.
    
    The mapping is:
    - handicap <= 5:  σ ≈ 2.5 (most consistent)
    - 5 < handicap <= 10:  σ ≈ 3.0
    - 10 < handicap <= 18: σ ≈ 3.5
    - 18 < handicap <= 28: σ ≈ 4.0
    - handicap > 28: σ ≈ 4.5 (least consistent)
    
    Args:
        handicap_index: The golfer's USGA Handicap Index
    
    Returns:
        Estimated standard deviation of scores
    
    Note:
        These values are conservative estimates. Future versions may
        calibrate against actual GHIN score data.
    """
    # Use absolute value to handle plus handicaps
    abs_handicap = abs(handicap_index)
    
    if abs_handicap <= 5:
        return 2.5
    elif abs_handicap <= 10:
        return 3.0
    elif abs_handicap <= 18:
        return 3.5
    elif abs_handicap <= 28:
        return 4.0
    else:
        return 4.5


def compute_single_round_probability(
    expected_score: float,
    sigma: float,
    target_score: int
) -> tuple[float, float]:
    """
    Compute the probability of shooting at or below a target score in a single round.
    
    Uses a normal distribution with continuity correction.
    
    The continuity correction adds 0.5 to the target score because golf scores
    are discrete integers, but we're using a continuous normal distribution.
    P(X <= target) ≈ P(X < target + 0.5) in the continuous approximation.
    
    Args:
        expected_score: The expected (mean) gross score
        sigma: Standard deviation of the score distribution
        target_score: Target score threshold (e.g., 80 for "breaking 80")
    
    Returns:
        A tuple of (probability, z_score) where:
        - probability is the chance of shooting target_score or better (0-1)
        - z_score is the standardized score used in the calculation
    
    Examples:
        >>> p, z = compute_single_round_probability(90.0, 3.5, 80)
        >>> 0 < p < 0.05  # Very low probability
        True
    """
    # Apply continuity correction for discrete scores
    adjusted_target = target_score + 0.5
    
    # Compute z-score
    z = (adjusted_target - expected_score) / sigma
    
    # Compute probability using normal CDF
    probability = stats.norm.cdf(z)
    
    return probability, z


def compute_multi_round_probability_at_least_once(
    single_round_prob: float,
    num_rounds: int
) -> float:
    """
    Compute the probability of achieving a target score at least once over N rounds.
    
    Uses the complement rule: P(at least once) = 1 - P(never)
    
    Assumes rounds are independent.
    
    Args:
        single_round_prob: Probability of success in a single round
        num_rounds: Number of rounds in the event
    
    Returns:
        Probability of achieving the target at least once
    
    Examples:
        >>> compute_multi_round_probability_at_least_once(0.2, 3)
        0.488  # 1 - 0.8^3
    """
    prob_never = (1 - single_round_prob) ** num_rounds
    return 1 - prob_never


def binomial_tail(n: int, p: float, k: int) -> float:
    """
    Compute the probability of at least k successes in n Bernoulli trials.
    
    P(X >= k) for X ~ Binomial(n, p)
    
    Args:
        n: Number of trials (rounds)
        p: Probability of success in each trial
        k: Minimum number of successes required
    
    Returns:
        Probability of at least k successes
    
    Examples:
        >>> binomial_tail(5, 0.2, 2)  # At least 2 successes in 5 rounds
        0.2627...
    """
    # P(X >= k) = 1 - P(X < k) = 1 - P(X <= k-1)
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    
    # Use survival function: sf(k-1) = 1 - cdf(k-1) = P(X >= k)
    return stats.binom.sf(k - 1, n, p)


def simulate_individual_scores(
    num_rounds: int,
    num_simulations: int,
    expected_score: float,
    sigma: float,
    target_score: Optional[int] = None
) -> dict:
    """
    Run Monte Carlo simulation of individual round scores.
    
    This provides an alternative to analytic probability calculations
    and can be used for validation or richer output analysis.
    
    Args:
        num_rounds: Number of rounds per simulation
        num_simulations: Number of Monte Carlo iterations
        expected_score: Mean score for the normal distribution
        sigma: Standard deviation for the normal distribution
        target_score: Optional target score for calculating success rates
    
    Returns:
        Dictionary containing:
        - simulated_mean: Mean of all simulated scores
        - simulated_std: Standard deviation of all simulated scores
        - min_score_per_event_mean: Average best score per event
        - If target_score provided:
          - prob_single_round_at_or_below_target: Single round success rate
          - prob_at_least_once_in_event: Event success rate (at least one round)
    
    Note:
        Results should closely match analytic probabilities when 
        num_simulations is large (e.g., >= 10000).
    """
    import numpy as np
    
    # Generate all scores: shape (num_simulations, num_rounds)
    scores = np.random.normal(expected_score, sigma, size=(num_simulations, num_rounds))
    
    # Round to integers for realistic score comparison
    scores_rounded = np.round(scores).astype(int)
    
    result = {
        "simulated_mean": float(np.mean(scores)),
        "simulated_std": float(np.std(scores)),
        "min_score_per_event_mean": float(np.mean(np.min(scores_rounded, axis=1))),
        "num_simulations": num_simulations,
        "num_rounds": num_rounds
    }
    
    if target_score is not None:
        # Count successes per round
        single_round_successes = np.sum(scores_rounded <= target_score)
        total_rounds = num_simulations * num_rounds
        result["prob_single_round_at_or_below_target"] = float(
            single_round_successes / total_rounds
        )
        
        # Count events with at least one success
        event_successes = np.sum(np.any(scores_rounded <= target_score, axis=1))
        result["prob_at_least_once_in_event"] = float(
            event_successes / num_simulations
        )
    
    return result


def get_standard_milestones(expected_score: float) -> list[int]:
    """
    Get standard milestone scores to calculate probabilities for.
    
    Returns milestones that are relevant to the golfer's expected score,
    ranging from achievable goals to stretch targets.
    
    Args:
        expected_score: The golfer's expected score
    
    Returns:
        List of target scores as milestones (sorted descending)
    """
    # Standard milestones that many golfers care about
    standard_milestones = [100, 95, 90, 85, 80, 75, 72]
    
    # Filter to milestones that are at most 15 strokes better than expected
    # and at most 10 strokes worse (to keep results relevant)
    relevant_milestones = [
        m for m in standard_milestones
        if (expected_score - 15) <= m <= (expected_score + 10)
    ]
    
    # Add the expected score rounded to nearest 5 if not already present
    expected_rounded = int(round(expected_score / 5) * 5)
    if expected_rounded not in relevant_milestones:
        relevant_milestones.append(expected_rounded)
    
    # Add one ambitious target (3 sigma below expected)
    # Use a conservative typical sigma for milestone calculation
    typical_sigma = 3.5  # Conservative middle value from estimate_score_std range
    ambitious = int(round(expected_score - 3 * typical_sigma))
    if ambitious not in relevant_milestones and ambitious >= 60:
        relevant_milestones.append(ambitious)
    
    return sorted(relevant_milestones, reverse=True)


def compute_nine_hole_expected_score(
    handicap_index: float,
    course_setup: CourseSetup
) -> float:
    """
    Compute the expected gross score for 9 holes.
    
    For 9-hole rounds, we scale the handicap proportionally.
    Expected 9-hole score = (par/2) + (course_handicap/2)
    
    Args:
        handicap_index: The golfer's USGA Handicap Index
        course_setup: The course configuration (rating, slope, par)
    
    Returns:
        The expected gross score for 9 holes
    """
    full_course_handicap = compute_course_handicap(
        handicap_index,
        course_setup.course_rating,
        course_setup.slope_rating,
        course_setup.par
    )
    # For 9 holes, use half the course handicap and half the par
    nine_hole_par = course_setup.par / 2
    nine_hole_ch = full_course_handicap / 2
    return nine_hole_par + nine_hole_ch


def estimate_nine_hole_score_std(handicap_index: float) -> float:
    """
    Estimate the standard deviation of scoring for 9 holes.
    
    For 9 holes, the variance is roughly half of 18-hole variance,
    so std dev is scaled by sqrt(0.5) ≈ 0.707.
    
    Args:
        handicap_index: The golfer's USGA Handicap Index
    
    Returns:
        Estimated standard deviation of 9-hole scores
    """
    eighteen_hole_std = estimate_score_std(handicap_index)
    return eighteen_hole_std * 0.707  # sqrt(0.5) for 9 holes


def compute_consecutive_scores_probability(
    single_round_prob: float,
    consecutive_count: int
) -> float:
    """
    Compute the probability of achieving a target score in N consecutive rounds.
    
    Since rounds are assumed independent:
    P(N consecutive successes) = p^N
    
    Args:
        single_round_prob: Probability of success in a single round
        consecutive_count: Number of consecutive rounds required
    
    Returns:
        Probability of achieving target score in all N consecutive rounds
    
    Examples:
        >>> compute_consecutive_scores_probability(0.2, 3)
        0.008  # 0.2^3
    """
    if consecutive_count <= 0:
        return 1.0
    return single_round_prob ** consecutive_count


def compute_consecutive_in_n_matches_probability(
    single_round_prob: float,
    consecutive_count: int,
    total_matches: int
) -> float:
    """
    Compute the probability of achieving at least one streak of N consecutive
    target scores within M total matches.
    
    Uses dynamic programming with Markov chain approach.
    
    The recurrence relation for f(n) = P(no k consecutive successes in n trials):
    f(n) = q*f(n-1) + p*q*f(n-2) + p^2*q*f(n-3) + ... + p^(k-1)*q*f(n-k)
    
    This is because to have no k consecutive successes ending at position n:
    - Either position n is a failure (prob q), and positions 1 to n-1 have no k consec
    - Or positions n-(j-1) to n are all successes (j < k), position n-j is failure,
      and positions 1 to n-j-1 have no k consecutive successes
    
    Args:
        single_round_prob: Probability of success in a single round
        consecutive_count: Length of consecutive streak required (N)
        total_matches: Total number of matches played (M)
    
    Returns:
        Probability of having at least one streak of N consecutive successes in M matches
    
    Examples:
        >>> compute_consecutive_in_n_matches_probability(0.5, 3, 5)
        # Probability of at least 3 in a row somewhere in 5 matches
    """
    if consecutive_count <= 0:
        return 1.0
    if consecutive_count > total_matches:
        return 0.0
    if single_round_prob == 0:
        return 0.0
    if single_round_prob == 1:
        return 1.0
    
    n = total_matches
    k = consecutive_count
    p = single_round_prob
    q = 1 - p
    
    # f[i] = probability of NOT having k consecutive successes in first i matches
    f = [0.0] * (n + 1)
    f[0] = 1.0  # Base case: no trials, no streak (trivially true)
    
    for i in range(1, n + 1):
        if i < k:
            # With fewer than k trials, we can't have a streak of k
            # All sequences that don't have k consecutive count
            # f[i] = sum of: (j successes ending at i) * (failure at i-j) * f[i-j-1]
            #        + all i successes (which is fine since i < k)
            for j in range(0, i):
                # j successes at end (positions i-j+1 to i), failure at i-j
                if i - j - 1 >= 0:
                    f[i] += (p ** j) * q * f[i - j - 1]
                else:
                    # i - j - 1 < 0 means j == i, so all i positions are part of this
                    f[i] += (p ** j) * q  # but j < i here, so this won't happen
            # Add the case where all i trials are successes (allowed since i < k)
            f[i] += p ** i
        else:
            # i >= k: We need to avoid k consecutive successes
            # Ending patterns: failure at position i, or 1 to k-1 successes at end
            # followed by failure
            for j in range(0, k):
                # j successes at end (positions i-j+1 to i), failure at i-j
                if i - j - 1 >= 0:
                    f[i] += (p ** j) * q * f[i - j - 1]
                elif i - j == 0:
                    # Failure at position 0 (doesn't exist), j = i
                    # This means j successes fill all i positions - but j < k and i >= k
                    # So this case won't trigger since j < k <= i means i - j > 0
                    pass
    
    return 1.0 - f[n]
