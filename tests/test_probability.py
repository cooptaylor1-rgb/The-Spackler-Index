"""Unit tests for the probability calculation service."""

import pytest
import math
from app.services.probability import (
    compute_course_handicap,
    compute_expected_score,
    estimate_score_std,
    compute_single_round_probability,
    compute_multi_round_probability_at_least_once,
    binomial_tail,
    simulate_individual_scores,
    get_standard_milestones,
)
from app.models import CourseSetup


class TestComputeCourseHandicap:
    """Tests for compute_course_handicap function."""

    def test_typical_handicap(self):
        """Test with typical handicap values."""
        ch = compute_course_handicap(
            handicap_index=15.0,
            course_rating=72.5,
            slope_rating=130,
            par=72
        )
        # CH = 15 * (130/113) + (72.5 - 72) = 17.26 + 0.5 = 17.76
        assert abs(ch - 17.76) < 0.1

    def test_scratch_golfer(self):
        """Test with scratch (0) handicap."""
        ch = compute_course_handicap(
            handicap_index=0.0,
            course_rating=72.0,
            slope_rating=113,
            par=72
        )
        # CH = 0 * (113/113) + (72 - 72) = 0
        assert abs(ch) < 0.01

    def test_plus_handicap(self):
        """Test with plus handicap (negative index)."""
        ch = compute_course_handicap(
            handicap_index=-2.0,
            course_rating=72.0,
            slope_rating=120,
            par=72
        )
        # CH = -2 * (120/113) + 0 = -2.12
        assert ch < 0
        assert abs(ch - (-2.12)) < 0.1

    def test_high_handicap(self):
        """Test with high handicap."""
        ch = compute_course_handicap(
            handicap_index=30.0,
            course_rating=74.0,
            slope_rating=140,
            par=72
        )
        # CH = 30 * (140/113) + 2 = 37.17 + 2 = 39.17
        assert ch > 35

    def test_with_allowance(self):
        """Test with handicap allowance."""
        ch_full = compute_course_handicap(
            handicap_index=15.0,
            course_rating=72.5,
            slope_rating=130,
            par=72,
            allowance_percent=100.0
        )
        ch_90 = compute_course_handicap(
            handicap_index=15.0,
            course_rating=72.5,
            slope_rating=130,
            par=72,
            allowance_percent=90.0
        )
        # 90% allowance should give 90% of the full course handicap
        assert abs(ch_90 - ch_full * 0.9) < 0.01


class TestComputeExpectedScore:
    """Tests for compute_expected_score function."""

    def test_typical_golfer(self):
        """Test expected score for typical golfer."""
        course = CourseSetup(
            course_name="Test Course",
            tee_name="White",
            par=72,
            course_rating=72.5,
            slope_rating=130
        )
        expected = compute_expected_score(15.0, course)
        # Expected = par + CH = 72 + 17.76 ≈ 89.76
        assert abs(expected - 89.76) < 0.5

    def test_scratch_golfer(self):
        """Test expected score for scratch golfer."""
        course = CourseSetup(
            course_name="Test Course",
            tee_name="White",
            par=72,
            course_rating=72.0,
            slope_rating=113
        )
        expected = compute_expected_score(0.0, course)
        # Scratch golfer on standard slope, expected ≈ par
        assert abs(expected - 72) < 0.1


class TestEstimateScoreStd:
    """Tests for estimate_score_std function."""

    def test_low_handicap(self):
        """Test standard deviation for low handicap."""
        assert estimate_score_std(3.0) == 2.5
        assert estimate_score_std(5.0) == 2.5

    def test_mid_handicap(self):
        """Test standard deviation for mid handicap."""
        assert estimate_score_std(8.0) == 3.0
        assert estimate_score_std(10.0) == 3.0

    def test_high_mid_handicap(self):
        """Test standard deviation for high-mid handicap."""
        assert estimate_score_std(15.0) == 3.5
        assert estimate_score_std(18.0) == 3.5

    def test_high_handicap(self):
        """Test standard deviation for high handicap."""
        assert estimate_score_std(25.0) == 4.0
        assert estimate_score_std(28.0) == 4.0

    def test_very_high_handicap(self):
        """Test standard deviation for very high handicap."""
        assert estimate_score_std(35.0) == 4.5
        assert estimate_score_std(50.0) == 4.5

    def test_plus_handicap(self):
        """Test standard deviation for plus handicap."""
        # Should use absolute value
        assert estimate_score_std(-2.0) == 2.5


class TestComputeSingleRoundProbability:
    """Tests for compute_single_round_probability function."""

    def test_target_at_expected(self):
        """Test probability when target equals expected score."""
        prob, z = compute_single_round_probability(
            expected_score=85.0,
            sigma=3.5,
            target_score=85
        )
        # With continuity correction, should be slightly above 50%
        assert 0.5 < prob < 0.6
        # Z-score should be close to 0 but slightly positive
        assert abs(z) < 0.5

    def test_target_well_below_expected(self):
        """Test probability when target is well below expected."""
        prob, z = compute_single_round_probability(
            expected_score=90.0,
            sigma=3.5,
            target_score=80
        )
        # Very low probability
        assert prob < 0.01
        assert z < -2

    def test_target_well_above_expected(self):
        """Test probability when target is well above expected."""
        prob, z = compute_single_round_probability(
            expected_score=80.0,
            sigma=3.5,
            target_score=95
        )
        # Very high probability
        assert prob > 0.99
        assert z > 3

    def test_probability_in_valid_range(self):
        """Test that probability is always between 0 and 1."""
        for expected in [70, 85, 100]:
            for sigma in [2.5, 3.5, 4.5]:
                for target in [60, 75, 90, 105]:
                    prob, _ = compute_single_round_probability(expected, sigma, target)
                    assert 0 <= prob <= 1


class TestMultiRoundProbability:
    """Tests for compute_multi_round_probability_at_least_once function."""

    def test_single_round(self):
        """Test with single round (should equal single round prob)."""
        single_prob = 0.2
        multi_prob = compute_multi_round_probability_at_least_once(single_prob, 1)
        assert abs(multi_prob - single_prob) < 0.001

    def test_multiple_rounds(self):
        """Test with multiple rounds."""
        single_prob = 0.2
        multi_prob = compute_multi_round_probability_at_least_once(single_prob, 3)
        # P(at least once in 3) = 1 - 0.8^3 = 1 - 0.512 = 0.488
        assert abs(multi_prob - 0.488) < 0.001

    def test_zero_probability(self):
        """Test with zero single round probability."""
        multi_prob = compute_multi_round_probability_at_least_once(0.0, 5)
        assert multi_prob == 0.0

    def test_certain_probability(self):
        """Test with certain single round probability."""
        multi_prob = compute_multi_round_probability_at_least_once(1.0, 5)
        assert multi_prob == 1.0


class TestBinomialTail:
    """Tests for binomial_tail function."""

    def test_at_least_one(self):
        """Test probability of at least 1 success."""
        prob = binomial_tail(5, 0.3, 1)
        # P(X >= 1) = 1 - P(X = 0) = 1 - 0.7^5
        expected = 1 - 0.7**5
        assert abs(prob - expected) < 0.001

    def test_at_least_two(self):
        """Test probability of at least 2 successes."""
        prob = binomial_tail(5, 0.3, 2)
        # Should be less than at least 1
        prob_one = binomial_tail(5, 0.3, 1)
        assert prob < prob_one

    def test_impossible_k(self):
        """Test with k > n (impossible)."""
        prob = binomial_tail(3, 0.5, 5)
        assert prob == 0.0

    def test_k_zero(self):
        """Test with k = 0 (always true)."""
        prob = binomial_tail(5, 0.3, 0)
        assert prob == 1.0


class TestSimulateIndividualScores:
    """Tests for simulate_individual_scores function."""

    def test_mean_close_to_expected(self):
        """Test that simulated mean is close to expected."""
        result = simulate_individual_scores(
            num_rounds=1,
            num_simulations=10000,
            expected_score=85.0,
            sigma=3.5
        )
        # Mean should be within 0.5 of expected
        assert abs(result["simulated_mean"] - 85.0) < 0.5

    def test_std_close_to_sigma(self):
        """Test that simulated std is close to sigma."""
        result = simulate_individual_scores(
            num_rounds=1,
            num_simulations=10000,
            expected_score=85.0,
            sigma=3.5
        )
        # Std should be within 0.5 of sigma
        assert abs(result["simulated_std"] - 3.5) < 0.5

    def test_with_target(self):
        """Test simulation with target score."""
        result = simulate_individual_scores(
            num_rounds=3,
            num_simulations=10000,
            expected_score=85.0,
            sigma=3.5,
            target_score=85
        )
        # Should have probability keys
        assert "prob_single_round_at_or_below_target" in result
        assert "prob_at_least_once_in_event" in result
        # Probabilities should be in valid range
        assert 0 <= result["prob_single_round_at_or_below_target"] <= 1
        assert 0 <= result["prob_at_least_once_in_event"] <= 1


class TestGetStandardMilestones:
    """Tests for get_standard_milestones function."""

    def test_returns_sorted_descending(self):
        """Test that milestones are sorted in descending order."""
        milestones = get_standard_milestones(85.0)
        assert milestones == sorted(milestones, reverse=True)

    def test_includes_relevant_targets(self):
        """Test that relevant standard targets are included."""
        milestones = get_standard_milestones(85.0)
        # For expected 85, should include 90, 85, 80
        assert 90 in milestones
        assert 85 in milestones
        assert 80 in milestones

    def test_excludes_far_targets(self):
        """Test that very far targets are excluded."""
        milestones = get_standard_milestones(85.0)
        # For expected 85, breaking 70 is too ambitious
        # and 105 is too easy
        assert all(m >= 70 for m in milestones)
        assert all(m <= 100 for m in milestones)


class TestNineHoleFunctions:
    """Tests for 9-hole scoring functions."""

    def test_nine_hole_expected_score(self):
        """Test 9-hole expected score is half of 18-hole."""
        from app.services.probability import compute_nine_hole_expected_score
        from app.models import CourseSetup
        
        course = CourseSetup(
            course_name="Test Course",
            tee_name="White",
            par=72,
            course_rating=72.5,
            slope_rating=130
        )
        nine_hole_expected = compute_nine_hole_expected_score(15.0, course)
        # Should be roughly half of 18-hole expected score
        assert 40 < nine_hole_expected < 50

    def test_nine_hole_std(self):
        """Test 9-hole std is scaled appropriately."""
        from app.services.probability import estimate_nine_hole_score_std
        
        nine_hole_std = estimate_nine_hole_score_std(15.0)
        # Should be roughly 0.707 times the 18-hole std (3.5)
        expected_std = 3.5 * 0.707
        assert abs(nine_hole_std - expected_std) < 0.1


class TestConsecutiveScoresFunctions:
    """Tests for consecutive scores probability functions."""

    def test_consecutive_probability_basic(self):
        """Test basic consecutive probability calculation."""
        from app.services.probability import compute_consecutive_scores_probability
        
        # p^3 = 0.2^3 = 0.008
        prob = compute_consecutive_scores_probability(0.2, 3)
        assert abs(prob - 0.008) < 0.0001

    def test_consecutive_probability_single(self):
        """Test consecutive probability for single round equals single prob."""
        from app.services.probability import compute_consecutive_scores_probability
        
        prob = compute_consecutive_scores_probability(0.3, 1)
        assert abs(prob - 0.3) < 0.0001

    def test_consecutive_probability_zero(self):
        """Test consecutive probability with zero base probability."""
        from app.services.probability import compute_consecutive_scores_probability
        
        prob = compute_consecutive_scores_probability(0.0, 3)
        assert prob == 0.0

    def test_consecutive_in_matches(self):
        """Test probability of streak within multiple matches."""
        from app.services.probability import compute_consecutive_in_n_matches_probability
        
        # With high single round prob, should have good chance of streak
        prob = compute_consecutive_in_n_matches_probability(0.5, 2, 10)
        assert 0 < prob < 1
        # Probability should increase with more matches
        prob_more = compute_consecutive_in_n_matches_probability(0.5, 2, 20)
        assert prob_more > prob
