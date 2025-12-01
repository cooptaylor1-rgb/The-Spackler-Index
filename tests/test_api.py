"""Tests for the API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestSingleRoundEndpoint:
    """Tests for single-round probability endpoint."""

    def test_single_round_success(self, client):
        """Test successful single-round calculation."""
        response = client.post(
            "/api/golf/probability/single-round",
            json={
                "golfer": {"handicap_index": 15.0},
                "course": {
                    "course_name": "Test Course",
                    "tee_name": "White",
                    "par": 72,
                    "course_rating": 72.5,
                    "slope_rating": 130
                },
                "target": {"target_score": 85}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "expected_score" in data
        assert "score_std" in data
        assert "probability_score_at_or_below_target" in data
        assert 0 <= data["probability_score_at_or_below_target"] <= 1

    def test_single_round_validation_error(self, client):
        """Test validation error for invalid input."""
        response = client.post(
            "/api/golf/probability/single-round",
            json={
                "golfer": {"handicap_index": 100.0},  # Invalid - too high
                "course": {
                    "course_name": "Test Course",
                    "tee_name": "White",
                    "par": 72,
                    "course_rating": 72.5,
                    "slope_rating": 130
                },
                "target": {"target_score": 85}
            }
        )
        assert response.status_code == 422  # Validation error


class TestMultiRoundEndpoint:
    """Tests for multi-round probability endpoint."""

    def test_multi_round_success(self, client):
        """Test successful multi-round calculation."""
        response = client.post(
            "/api/golf/probability/multi-round",
            json={
                "golfer": {"handicap_index": 15.0},
                "course": {
                    "course_name": "Test Course",
                    "tee_name": "White",
                    "par": 72,
                    "course_rating": 72.5,
                    "slope_rating": 130
                },
                "target": {"target_score": 85},
                "event": {"num_rounds": 3}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "probability_at_least_once" in data
        assert "single_round_probability" in data
        assert data["num_rounds"] == 3

    def test_multi_round_with_min_success(self, client):
        """Test multi-round with min_success_rounds parameter."""
        response = client.post(
            "/api/golf/probability/multi-round",
            json={
                "golfer": {"handicap_index": 10.0},
                "course": {
                    "course_name": "Test Course",
                    "tee_name": "White",
                    "par": 72,
                    "course_rating": 72.5,
                    "slope_rating": 130
                },
                "target": {"target_score": 85},
                "event": {"num_rounds": 5},
                "min_success_rounds": 2
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["min_success_rounds"] == 2
        assert "probability_at_least_min_success_rounds" in data


class TestMilestonesEndpoint:
    """Tests for milestones probability endpoint."""

    def test_milestones_success(self, client):
        """Test successful milestones calculation."""
        response = client.post(
            "/api/golf/probability/milestones",
            json={
                "golfer": {"handicap_index": 15.0},
                "course": {
                    "course_name": "Test Course",
                    "tee_name": "White",
                    "par": 72,
                    "course_rating": 72.5,
                    "slope_rating": 130
                },
                "event": {"num_rounds": 3}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "milestones" in data
        assert len(data["milestones"]) > 0
        for milestone in data["milestones"]:
            assert "target_score" in milestone
            assert "prob_single_round_at_or_below" in milestone
            assert "prob_at_least_once_in_event" in milestone


class TestTeamBestBallSingleRoundEndpoint:
    """Tests for team best-ball single-round endpoint."""

    def test_team_single_round_success(self, client):
        """Test successful team single-round calculation."""
        response = client.post(
            "/api/golf/team/bestball/probability/single-round",
            json={
                "team": {
                    "player1": {"golfer": {"handicap_index": 12.0}},
                    "player2": {"golfer": {"handicap_index": 8.0}}
                },
                "course": {
                    "course_name": "Test Course",
                    "tee_name": "Blue",
                    "par": 72,
                    "course_rating": 73.5,
                    "slope_rating": 135
                },
                "bestball_target": {
                    "target_net_score": 63,
                    "handicap_allowance_percent": 100.0
                },
                "num_simulations": 1000
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "probability_net_bestball_at_or_below_target_single_round" in data
        assert "expected_team_bestball_score_single_round" in data
        assert "approximation_notes" in data


class TestTeamBestBallMultiRoundEndpoint:
    """Tests for team best-ball multi-round endpoint."""

    def test_team_multi_round_success(self, client):
        """Test successful team multi-round calculation."""
        response = client.post(
            "/api/golf/team/bestball/probability/multi-round",
            json={
                "team": {
                    "player1": {"golfer": {"handicap_index": 12.0}},
                    "player2": {"golfer": {"handicap_index": 8.0}}
                },
                "course": {
                    "course_name": "Test Course",
                    "tee_name": "Blue",
                    "par": 72,
                    "course_rating": 73.5,
                    "slope_rating": 135
                },
                "bestball_target": {
                    "target_net_score": 63,
                    "handicap_allowance_percent": 90.0
                },
                "event": {"num_rounds": 3},
                "min_success_rounds": 1,
                "num_simulations": 1000
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["num_rounds"] == 3
        assert "probability_at_least_once_in_event" in data
        assert "probability_at_least_min_success_rounds" in data
        assert data["handicap_allowance_percent"] == 90.0


class TestConsecutiveScoresEndpoint:
    """Tests for consecutive scores probability endpoint."""

    def test_consecutive_scores_18_hole(self, client):
        """Test consecutive scores calculation for 18-hole rounds."""
        response = client.post(
            "/api/golf/probability/consecutive",
            json={
                "golfer": {"handicap_index": 15.0},
                "course": {
                    "course_name": "Test Course",
                    "tee_name": "White",
                    "par": 72,
                    "course_rating": 72.5,
                    "slope_rating": 130
                },
                "target": {"target_score": 85},
                "consecutive_count": 3,
                "holes_per_round": 18
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["holes_per_round"] == 18
        assert data["consecutive_count"] == 3
        assert "single_round_probability" in data
        assert "probability_all_consecutive" in data
        assert data["probability_all_consecutive"] <= data["single_round_probability"]

    def test_consecutive_scores_9_hole(self, client):
        """Test consecutive scores calculation for 9-hole rounds."""
        response = client.post(
            "/api/golf/probability/consecutive",
            json={
                "golfer": {"handicap_index": 15.0},
                "course": {
                    "course_name": "Test Course",
                    "tee_name": "White",
                    "par": 72,
                    "course_rating": 72.5,
                    "slope_rating": 130
                },
                "target": {"target_score": 42},
                "consecutive_count": 3,
                "holes_per_round": 9
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["holes_per_round"] == 9
        # 9-hole expected score should be lower than 18-hole
        assert data["expected_score"] < 50

    def test_consecutive_scores_with_total_matches(self, client):
        """Test consecutive scores with total matches specified."""
        response = client.post(
            "/api/golf/probability/consecutive",
            json={
                "golfer": {"handicap_index": 15.0},
                "course": {
                    "course_name": "Test Course",
                    "tee_name": "White",
                    "par": 72,
                    "course_rating": 72.5,
                    "slope_rating": 130
                },
                "target": {"target_score": 42},
                "consecutive_count": 3,
                "holes_per_round": 9,
                "total_matches": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_matches"] == 10
        assert "probability_streak_in_matches" in data
        assert data["probability_streak_in_matches"] is not None
        # Streak probability should be higher than all consecutive
        assert data["probability_streak_in_matches"] >= data["probability_all_consecutive"]
