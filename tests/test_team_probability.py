"""Unit tests for team probability calculations."""

import pytest
import numpy as np
from app.services.team_probability import (
    compute_player_parameters,
    simulate_team_bestball_round_scores,
    get_team_approximation_notes,
)
from app.models import (
    CourseSetup,
    GolferProfile,
    TeamPlayer,
    TeamProfile,
    BestBallTarget,
)


@pytest.fixture
def sample_course():
    """Create a sample course for testing."""
    return CourseSetup(
        course_name="Test Course",
        tee_name="Blue",
        par=72,
        course_rating=73.5,
        slope_rating=135
    )


@pytest.fixture
def sample_team():
    """Create a sample team for testing."""
    return TeamProfile(
        player1=TeamPlayer(golfer=GolferProfile(handicap_index=12.0)),
        player2=TeamPlayer(golfer=GolferProfile(handicap_index=8.0))
    )


@pytest.fixture
def sample_target():
    """Create a sample best-ball target for testing."""
    return BestBallTarget(target_net_score=63, handicap_allowance_percent=100.0)


class TestComputePlayerParameters:
    """Tests for compute_player_parameters function."""

    def test_returns_three_values(self, sample_course):
        """Test that function returns expected, sigma, and course handicap."""
        expected, sigma, ch = compute_player_parameters(
            handicap_index=15.0,
            course_setup=sample_course
        )
        assert isinstance(expected, float)
        assert isinstance(sigma, float)
        assert isinstance(ch, float)

    def test_expected_score_reasonable(self, sample_course):
        """Test that expected score is reasonable."""
        expected, _, _ = compute_player_parameters(
            handicap_index=15.0,
            course_setup=sample_course
        )
        # Expected should be around par + course handicap
        assert 85 < expected < 95

    def test_sigma_based_on_handicap(self, sample_course):
        """Test that sigma is based on handicap."""
        _, sigma_low, _ = compute_player_parameters(3.0, sample_course)
        _, sigma_high, _ = compute_player_parameters(25.0, sample_course)
        # Higher handicap should have higher sigma
        assert sigma_high > sigma_low

    def test_allowance_reduces_ch(self, sample_course):
        """Test that allowance reduces course handicap."""
        _, _, ch_full = compute_player_parameters(15.0, sample_course, allowance_percent=100.0)
        _, _, ch_90 = compute_player_parameters(15.0, sample_course, allowance_percent=90.0)
        assert ch_90 < ch_full
        assert abs(ch_90 - ch_full * 0.9) < 0.01

    def test_course_handicap_override(self, sample_course):
        """Test course handicap override."""
        _, _, ch = compute_player_parameters(
            handicap_index=15.0,
            course_setup=sample_course,
            course_handicap_override=10.0
        )
        assert ch == 10.0


class TestSimulateTeamBestballRoundScores:
    """Tests for simulate_team_bestball_round_scores function."""

    def test_returns_expected_keys(self, sample_team, sample_course, sample_target):
        """Test that simulation returns expected keys."""
        results = simulate_team_bestball_round_scores(
            team=sample_team,
            course=sample_course,
            bestball_target=sample_target,
            num_rounds=3,
            num_simulations=1000
        )
        expected_keys = [
            "single_round_probability_at_or_below_target",
            "probability_at_least_once_in_event",
            "probability_at_least_min_success_rounds",
            "expected_team_bestball_score_single_round",
            "std_team_bestball_score_single_round",
            "num_simulations_used",
        ]
        for key in expected_keys:
            assert key in results

    def test_probabilities_in_valid_range(self, sample_team, sample_course, sample_target):
        """Test that all probabilities are between 0 and 1."""
        results = simulate_team_bestball_round_scores(
            team=sample_team,
            course=sample_course,
            bestball_target=sample_target,
            num_rounds=3,
            num_simulations=1000
        )
        assert 0 <= results["single_round_probability_at_or_below_target"] <= 1
        assert 0 <= results["probability_at_least_once_in_event"] <= 1
        assert 0 <= results["probability_at_least_min_success_rounds"] <= 1

    def test_multi_round_prob_geq_single(self, sample_team, sample_course, sample_target):
        """Test that multi-round probability is >= single round."""
        results = simulate_team_bestball_round_scores(
            team=sample_team,
            course=sample_course,
            bestball_target=sample_target,
            num_rounds=5,
            num_simulations=5000
        )
        # At least once should be >= single round
        assert results["probability_at_least_once_in_event"] >= \
               results["single_round_probability_at_or_below_target"] - 0.01  # Allow small variance

    def test_expected_bestball_lower_than_individual(self, sample_team, sample_course, sample_target):
        """Test that team best-ball is lower than individual expected scores."""
        results = simulate_team_bestball_round_scores(
            team=sample_team,
            course=sample_course,
            bestball_target=sample_target,
            num_rounds=1,
            num_simulations=5000
        )
        # Best-ball of two players should be lower than either individual
        # Get individual expected scores
        from app.services.probability import compute_expected_score, compute_course_handicap
        
        p1_expected = compute_expected_score(12.0, sample_course)
        p2_expected = compute_expected_score(8.0, sample_course)
        p1_ch = compute_course_handicap(12.0, sample_course.course_rating, 
                                        sample_course.slope_rating, sample_course.par)
        p2_ch = compute_course_handicap(8.0, sample_course.course_rating,
                                        sample_course.slope_rating, sample_course.par)
        
        # Net expected scores
        p1_net_expected = p1_expected - p1_ch
        p2_net_expected = p2_expected - p2_ch
        
        # Best-ball should be lower than either individual net score
        bb_expected = results["expected_team_bestball_score_single_round"]
        assert bb_expected < min(p1_net_expected, p2_net_expected) + 1  # Allow small variance

    def test_simulation_count(self, sample_team, sample_course, sample_target):
        """Test that correct number of simulations are run."""
        results = simulate_team_bestball_round_scores(
            team=sample_team,
            course=sample_course,
            bestball_target=sample_target,
            num_rounds=3,
            num_simulations=5000
        )
        assert results["num_simulations_used"] == 5000

    def test_reproducibility_with_seed(self, sample_team, sample_course, sample_target):
        """Test that results are reproducible with same random seed."""
        np.random.seed(42)
        results1 = simulate_team_bestball_round_scores(
            team=sample_team,
            course=sample_course,
            bestball_target=sample_target,
            num_rounds=3,
            num_simulations=1000
        )
        
        np.random.seed(42)
        results2 = simulate_team_bestball_round_scores(
            team=sample_team,
            course=sample_course,
            bestball_target=sample_target,
            num_rounds=3,
            num_simulations=1000
        )
        
        assert results1["expected_team_bestball_score_single_round"] == \
               results2["expected_team_bestball_score_single_round"]


class TestGetTeamApproximationNotes:
    """Tests for get_team_approximation_notes function."""

    def test_returns_string(self):
        """Test that function returns a string."""
        notes = get_team_approximation_notes()
        assert isinstance(notes, str)

    def test_mentions_approximation(self):
        """Test that notes mention approximation method."""
        notes = get_team_approximation_notes()
        assert "approximation" in notes.lower() or "modeled" in notes.lower()

    def test_mentions_round_level(self):
        """Test that notes mention round-level modeling."""
        notes = get_team_approximation_notes()
        assert "round" in notes.lower()
