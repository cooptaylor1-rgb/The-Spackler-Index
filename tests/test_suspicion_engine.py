"""
Tests for the suspicion scoring engine and config system.

These tests verify the new Caddyshack-themed suspicion detection system
including configurable thresholds, mode-aware labels, and explainable scoring.
"""

import pytest
from app.config import (
    SuspicionMode,
    RiskTier,
    SuspicionThresholds,
    SuspicionConfig,
    get_default_config,
    get_conservative_config,
    get_aggressive_config,
    CONSERVATIVE_THRESHOLDS,
    AGGRESSIVE_THRESHOLDS,
)
from app.services import (
    SuspicionScoringEngine,
    SuspicionResult,
    SuspicionReason,
    FlagType,
    FlagSeverity,
)


class TestSuspicionConfig:
    """Tests for the suspicion configuration system."""
    
    def test_default_config_is_caddyshack_mode(self):
        """Default config should be in Caddyshack mode."""
        config = get_default_config()
        assert config.mode == SuspicionMode.CADDYSHACK
    
    def test_conservative_thresholds_stricter(self):
        """Conservative thresholds should be stricter (higher values)."""
        default = SuspicionThresholds()
        conservative = CONSERVATIVE_THRESHOLDS
        
        # Risk tier thresholds should be higher (need higher score to flag)
        assert conservative.risk_tier_severe > default.risk_tier_severe
        assert conservative.risk_tier_high > default.risk_tier_high
    
    def test_aggressive_thresholds_looser(self):
        """Aggressive thresholds should be looser (lower values)."""
        default = SuspicionThresholds()
        aggressive = AGGRESSIVE_THRESHOLDS
        
        # Risk tier thresholds should be lower (lower score triggers flag)
        assert aggressive.risk_tier_severe < default.risk_tier_severe
        assert aggressive.risk_tier_high < default.risk_tier_high
    
    def test_mode_labels_differ(self):
        """Caddyshack and Serious modes should have different labels."""
        caddyshack = get_default_config()
        serious = get_default_config()
        serious.mode = SuspicionMode.SERIOUS
        
        # Labels should reflect the mode
        assert caddyshack.get_labels().tier_severe != serious.get_labels().tier_severe
    
    def test_tier_label_getter(self):
        """get_tier_label should return appropriate label for tier."""
        config = get_default_config()
        
        label_low = config.get_tier_label(RiskTier.LOW)
        label_severe = config.get_tier_label(RiskTier.SEVERE)
        
        assert label_low != label_severe
        assert len(label_low) > 0
        assert len(label_severe) > 0
    
    def test_config_immutable_thresholds(self):
        """Config should have proper threshold validation."""
        # Valid thresholds should work
        config = SuspicionConfig(thresholds=SuspicionThresholds())
        assert config.thresholds.risk_tier_severe == 75.0
        
    def test_min_rounds_setting(self):
        """min_rounds_for_analysis should be respected."""
        config = get_default_config()
        assert config.thresholds.min_rounds_for_analysis >= 1


class TestFlagTypes:
    """Tests for flag type and severity enums."""
    
    def test_all_flag_types_exist(self):
        """All expected flag types should exist."""
        expected = [
            "TOURNAMENT_EXCELLENCE",
            "LOW_VOLATILITY",
            "IMPROBABLE_CONSISTENCY",
            "CASUAL_TOURNAMENT_DISPARITY",
            "PERFECT_TOURNAMENT_RECORD",
        ]
        for flag in expected:
            assert hasattr(FlagType, flag)
    
    def test_severity_ordering(self):
        """Severities should have correct ordering."""
        assert FlagSeverity.LOW.value == "LOW"
        assert FlagSeverity.MEDIUM.value == "MEDIUM"
        assert FlagSeverity.HIGH.value == "HIGH"
        assert FlagSeverity.CRITICAL.value == "CRITICAL"


class TestSuspicionScoringEngine:
    """Tests for the suspicion scoring engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = SuspicionScoringEngine()
    
    def test_engine_creation_with_default_config(self):
        """Engine should be created with default config."""
        engine = SuspicionScoringEngine()
        assert engine.config is not None
        assert engine.config.mode == SuspicionMode.CADDYSHACK
    
    def test_engine_creation_with_custom_config(self):
        """Engine should accept custom config."""
        config = get_aggressive_config()
        engine = SuspicionScoringEngine(config=config)
        assert engine.config == config
    
    def test_clean_golfer_low_risk(self):
        """Golfer with expected performance should have low risk."""
        # For a 15 handicap, expected score ~88, std ~5
        expected_scores = [88.0, 88.0, 88.0]
        expected_std = 5.0
        tournament_scores = [88, 89, 90]  # Around expected for 15 handicap
        
        result = self.engine.analyze(
            tournament_scores=tournament_scores,
            expected_scores=expected_scores,
            expected_std=expected_std,
        )
        
        assert isinstance(result, SuspicionResult)
        # Score should be relatively low for normal performance
        assert result.suspicion_score < 50  # Not high risk
    
    def test_suspicious_golfer_high_risk(self):
        """Golfer significantly outperforming handicap should flag."""
        # For a 20 handicap, expected score ~92, std ~6
        expected_scores = [92.0, 92.0, 92.0]
        expected_std = 6.0
        tournament_scores = [75, 74, 76]  # Way better than 20 handicap
        
        result = self.engine.analyze(
            tournament_scores=tournament_scores,
            expected_scores=expected_scores,
            expected_std=expected_std,
        )
        
        assert result.suspicion_score > 50  # Should be flagged
        assert result.risk_tier in [RiskTier.HIGH, RiskTier.SEVERE]
        assert len(result.reasons) > 0
    
    def test_result_contains_required_fields(self):
        """Result should contain all required fields."""
        expected_scores = [82.0, 82.0, 82.0]
        expected_std = 4.5
        tournament_scores = [80, 81, 82]
        
        result = self.engine.analyze(
            tournament_scores=tournament_scores,
            expected_scores=expected_scores,
            expected_std=expected_std,
        )
        
        assert hasattr(result, 'suspicion_score')
        assert hasattr(result, 'risk_tier')
        assert hasattr(result, 'tier_label')
        assert hasattr(result, 'reasons')
        assert hasattr(result, 'tournament_performance_score')
        assert hasattr(result, 'volatility_score')
    
    def test_casual_comparison_increases_score(self):
        """Disparity between casual and tournament should increase score."""
        expected_scores = [87.0, 87.0, 87.0]
        expected_std = 5.0
        tournament_scores = [78, 79, 80]
        casual_scores = [90, 92, 91]  # Plays worse casually
        
        # Tournament much better than casual
        result_with_casual = self.engine.analyze(
            tournament_scores=tournament_scores,
            expected_scores=expected_scores,
            expected_std=expected_std,
            casual_scores=casual_scores,
            casual_expected=87.0,
        )
        
        result_without_casual = self.engine.analyze(
            tournament_scores=tournament_scores,
            expected_scores=expected_scores,
            expected_std=expected_std,
        )
        
        # With casual scores showing disparity, score should be higher
        assert result_with_casual.suspicion_score >= result_without_casual.suspicion_score
    
    def test_insufficient_rounds_returns_minimal_result(self):
        """Too few rounds should return minimal analysis."""
        expected_scores = [87.0]
        expected_std = 5.0
        tournament_scores = [80]  # Only 1 round
        
        result = self.engine.analyze(
            tournament_scores=tournament_scores,
            expected_scores=expected_scores,
            expected_std=expected_std,
        )
        
        # Should still return a result but with low confidence
        assert isinstance(result, SuspicionResult)
    
    def test_mode_affects_labels(self):
        """Mode should affect tier labels in result."""
        caddyshack_engine = SuspicionScoringEngine(config=get_default_config())
        
        serious_config = get_default_config()
        serious_config.mode = SuspicionMode.SERIOUS
        serious_engine = SuspicionScoringEngine(config=serious_config)
        
        # Suspicious scores
        expected_scores = [92.0, 92.0, 92.0]
        expected_std = 6.0
        tournament_scores = [75, 74, 76]
        
        caddyshack_result = caddyshack_engine.analyze(
            tournament_scores=tournament_scores,
            expected_scores=expected_scores,
            expected_std=expected_std,
        )
        
        serious_result = serious_engine.analyze(
            tournament_scores=tournament_scores,
            expected_scores=expected_scores,
            expected_std=expected_std,
        )
        
        # Labels should differ based on mode
        assert caddyshack_result.tier_label != serious_result.tier_label
    
    def test_score_breakdown_components(self):
        """Score breakdown should contain component scores."""
        expected_scores = [92.0, 92.0, 92.0]
        expected_std = 6.0
        tournament_scores = [75, 74, 76]
        
        result = self.engine.analyze(
            tournament_scores=tournament_scores,
            expected_scores=expected_scores,
            expected_std=expected_std,
        )
        
        # SuspicionResult has individual score components as attributes
        assert hasattr(result, 'tournament_performance_score')
        assert hasattr(result, 'volatility_score')
        assert hasattr(result, 'percentile_score')
        assert hasattr(result, 'red_flag_score')


class TestSuspicionReason:
    """Tests for suspicion reason model."""
    
    def test_reason_creation(self):
        """SuspicionReason should be properly created."""
        reason = SuspicionReason(
            flag_type=FlagType.TOURNAMENT_EXCELLENCE,
            severity=FlagSeverity.HIGH,
            title="Test Title",
            description="Test description",
            evidence="Test evidence",
            metric_name="test_metric",
            metric_value=25.0,
            threshold_value=20.0,
        )
        
        assert reason.flag_type == FlagType.TOURNAMENT_EXCELLENCE
        assert reason.severity == FlagSeverity.HIGH
        assert reason.metric_value == 25.0
    
    def test_reason_with_probability_note(self):
        """Reason should support optional probability note."""
        reason = SuspicionReason(
            flag_type=FlagType.IMPROBABLE_CONSISTENCY,
            severity=FlagSeverity.CRITICAL,
            title="Test Title",
            description="Test",
            evidence="Test",
            metric_name="joint_probability",
            metric_value=0.0001,
            threshold_value=0.01,
            probability_note="Only 0.01% chance",
        )
        
        assert reason.probability_note == "Only 0.01% chance"


class TestConfigAPI:
    """Tests for config API endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)
    
    def test_get_config_endpoint(self):
        """GET /api/golf/config should return current config."""
        response = self.client.get("/api/golf/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "mode" in data
        assert "thresholds" in data
        assert "labels" in data
    
    def test_update_config_mode(self):
        """PUT /api/golf/config should allow mode change."""
        # Change to serious mode
        response = self.client.put(
            "/api/golf/config",
            json={"mode": "serious"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["mode"] == "serious"
        
        # Change back to caddyshack
        self.client.put("/api/golf/config", json={"mode": "caddyshack"})
    
    def test_update_config_preset(self):
        """PUT /api/golf/config should allow preset change."""
        response = self.client.put(
            "/api/golf/config",
            json={"preset": "conservative"}
        )
        assert response.status_code == 200
        
        # Reset to default
        self.client.post("/api/golf/config/reset")
    
    def test_reset_config(self):
        """POST /api/golf/config/reset should reset to defaults."""
        # First change something
        self.client.put("/api/golf/config", json={"mode": "serious"})
        
        # Then reset
        response = self.client.post("/api/golf/config/reset")
        assert response.status_code == 200
        
        data = response.json()
        assert data["mode"] == "caddyshack"  # Default mode
