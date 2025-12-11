"""
Enhanced Suspicion Scoring Engine

This module provides a robust, explainable suspicion scoring system for detecting
potential handicap manipulation patterns. All results are framed as statistical
anomalies requiring human review, NOT as accusations.

IMPORTANT DISCLAIMER:
This tool assists committees in reviewing potential anomalies. It does NOT declare
guilt or accuse anyone of actual cheating. All flagged patterns should be reviewed
by qualified personnel before any action is taken.
"""

import logging
import statistics
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from scipy import stats

from app.config import (
    SuspicionConfig,
    SuspicionMode,
    RiskTier,
    get_default_config,
)


logger = logging.getLogger(__name__)


class FlagType(str, Enum):
    """Types of suspicious pattern flags."""
    TOURNAMENT_EXCELLENCE = "TOURNAMENT_EXCELLENCE"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    IMPROBABLE_CONSISTENCY = "IMPROBABLE_CONSISTENCY"
    CASUAL_TOURNAMENT_DISPARITY = "CASUAL_TOURNAMENT_DISPARITY"
    PERFECT_TOURNAMENT_RECORD = "PERFECT_TOURNAMENT_RECORD"
    RAPID_IMPROVEMENT = "RAPID_IMPROVEMENT"
    CAREER_ROUND_FREQUENCY = "CAREER_ROUND_FREQUENCY"


class FlagSeverity(str, Enum):
    """Severity levels for flags - these are statistical indicators, not accusations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SuspicionReason:
    """
    A single reason/explanation for a suspicion flag.
    
    Designed to be both machine-readable and human-friendly.
    """
    flag_type: FlagType
    severity: FlagSeverity
    title: str
    description: str
    evidence: str
    metric_name: str
    metric_value: float
    threshold_value: float
    probability_note: Optional[str] = None
    caddyshack_quip: Optional[str] = None
    serious_note: Optional[str] = None
    
    def to_dict(self, mode: SuspicionMode = SuspicionMode.CADDYSHACK) -> Dict[str, Any]:
        """Convert to dictionary with mode-appropriate text."""
        result = {
            "flag_type": self.flag_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "metric": {
                "name": self.metric_name,
                "value": self.metric_value,
                "threshold": self.threshold_value,
            },
        }
        
        if self.probability_note:
            result["probability_note"] = self.probability_note
            
        if mode == SuspicionMode.CADDYSHACK and self.caddyshack_quip:
            result["quip"] = self.caddyshack_quip
        elif mode == SuspicionMode.SERIOUS and self.serious_note:
            result["note"] = self.serious_note
            
        return result


@dataclass
class SuspicionResult:
    """
    Complete suspicion analysis result for a player.
    
    This is the primary output of the suspicion scoring engine.
    All fields are designed to be explainable and transparent.
    """
    # Core metrics
    suspicion_score: float  # 0-100 scale
    risk_tier: RiskTier
    
    # Breakdown of score components
    tournament_performance_score: float
    percentile_score: float
    volatility_score: float
    red_flag_score: float
    
    # Detailed reasons/flags
    reasons: List[SuspicionReason] = field(default_factory=list)
    
    # Summary statistics
    tournament_avg_vs_expected: float = 0.0
    tournament_percentile: float = 50.0
    score_volatility: float = 0.0
    expected_volatility: float = 0.0
    joint_probability: float = 1.0
    
    # Comparison data (if available)
    has_casual_comparison: bool = False
    casual_vs_tournament_diff: Optional[float] = None
    
    # Mode-aware labels
    tier_label: str = ""
    summary: str = ""
    recommendation: str = ""
    
    def to_response_dict(self, mode: SuspicionMode = SuspicionMode.CADDYSHACK) -> Dict[str, Any]:
        """Convert to API response dictionary."""
        return {
            "suspicion_score": round(self.suspicion_score, 1),
            "risk_tier": self.risk_tier.value,
            "tier_label": self.tier_label,
            "score_breakdown": {
                "tournament_performance": round(self.tournament_performance_score, 1),
                "percentile": round(self.percentile_score, 1),
                "volatility": round(self.volatility_score, 1),
                "red_flags": round(self.red_flag_score, 1),
            },
            "statistics": {
                "tournament_avg_vs_expected": round(self.tournament_avg_vs_expected, 2),
                "tournament_percentile": round(self.tournament_percentile, 1),
                "score_volatility": round(self.score_volatility, 2),
                "expected_volatility": round(self.expected_volatility, 2),
                "joint_probability": self.joint_probability,
            },
            "reasons": [r.to_dict(mode) for r in self.reasons],
            "has_casual_comparison": self.has_casual_comparison,
            "casual_vs_tournament_diff": (
                round(self.casual_vs_tournament_diff, 2) 
                if self.casual_vs_tournament_diff is not None else None
            ),
            "summary": self.summary,
            "recommendation": self.recommendation,
        }


class SuspicionScoringEngine:
    """
    Main engine for calculating suspicion scores with full explainability.
    
    This engine analyzes tournament scoring patterns to identify statistical
    anomalies that may warrant committee review. It provides:
    
    - Configurable thresholds and weights
    - Mode-aware labels (Caddyshack/Serious)
    - Detailed, explainable reasons for every flag
    - Transparent score breakdown
    
    DISCLAIMER: Results are statistical indicators, not accusations.
    """
    
    def __init__(self, config: Optional[SuspicionConfig] = None):
        """Initialize the engine with optional custom configuration."""
        self.config = config or get_default_config()
        
    def analyze(
        self,
        tournament_scores: List[float],
        expected_scores: List[float],
        expected_std: float,
        casual_scores: Optional[List[float]] = None,
        casual_expected: Optional[float] = None,
    ) -> SuspicionResult:
        """
        Perform complete suspicion analysis.
        
        Args:
            tournament_scores: Actual scores from tournament rounds
            expected_scores: Expected scores for each tournament round
            expected_std: Expected standard deviation based on handicap
            casual_scores: Optional casual round scores for comparison
            casual_expected: Optional expected score for casual rounds
            
        Returns:
            SuspicionResult with complete analysis and explanations
        """
        logger.info(
            f"Analyzing {len(tournament_scores)} tournament scores, "
            f"expected_std={expected_std:.2f}"
        )
        
        # Calculate core statistics
        scores_vs_expected = [
            actual - expected 
            for actual, expected in zip(tournament_scores, expected_scores)
        ]
        
        tournament_avg = statistics.mean(tournament_scores)
        tournament_avg_vs_expected = statistics.mean(scores_vs_expected)
        
        # Calculate individual probabilities and percentiles
        probabilities = []
        percentiles = []
        expected_mean = statistics.mean(expected_scores)
        
        for actual, expected in zip(tournament_scores, expected_scores):
            z_score = (actual - expected) / expected_std
            prob = stats.norm.cdf(z_score)
            probabilities.append(prob)
            percentiles.append(prob * 100)
        
        tournament_percentile = statistics.mean(percentiles)
        
        # Calculate volatility
        if len(tournament_scores) > 1:
            score_volatility = statistics.stdev(tournament_scores)
        else:
            score_volatility = 0.0
        
        volatility_ratio = (
            score_volatility / expected_std if expected_std > 0 else 1.0
        )
        
        # Calculate joint probability
        joint_probability = 1.0
        for prob in probabilities:
            joint_probability *= prob
        
        # Detect flags and reasons
        reasons: List[SuspicionReason] = []
        
        # Flag 1: Tournament Excellence
        self._check_tournament_excellence(
            tournament_avg_vs_expected,
            tournament_percentile,
            len(tournament_scores),
            reasons
        )
        
        # Flag 2: Low Volatility
        self._check_low_volatility(
            score_volatility,
            expected_std,
            volatility_ratio,
            reasons
        )
        
        # Flag 3: Improbable Consistency
        self._check_improbable_consistency(
            joint_probability,
            len(tournament_scores),
            reasons
        )
        
        # Flag 4: Perfect Tournament Record
        self._check_perfect_record(
            scores_vs_expected,
            reasons
        )
        
        # Flag 5: Casual vs Tournament Disparity
        has_casual_comparison = False
        casual_vs_tournament_diff = None
        
        if casual_scores and casual_expected is not None:
            has_casual_comparison = True
            casual_avg = statistics.mean(casual_scores)
            casual_vs_tournament_diff = casual_avg - tournament_avg
            
            casual_vs_expected_avg = casual_avg - casual_expected
            tournament_vs_expected_avg = tournament_avg - expected_mean
            
            self._check_casual_disparity(
                casual_avg,
                tournament_avg,
                casual_vs_expected_avg,
                tournament_vs_expected_avg,
                len(casual_scores),
                len(tournament_scores),
                reasons
            )
        
        # Calculate component scores
        tournament_performance_score = self._calc_tournament_score(
            tournament_avg_vs_expected
        )
        percentile_score = self._calc_percentile_score(tournament_percentile)
        volatility_score = self._calc_volatility_score(volatility_ratio)
        red_flag_score = self._calc_red_flag_score(reasons)
        
        # Calculate total suspicion score
        suspicion_score = min(
            tournament_performance_score +
            percentile_score +
            volatility_score +
            red_flag_score,
            100.0
        )
        
        # Determine risk tier
        risk_tier = self._determine_risk_tier(suspicion_score)
        
        # Get mode-appropriate labels
        tier_label = self.config.get_tier_label(risk_tier)
        summary = self._generate_summary(risk_tier, tournament_avg_vs_expected, len(reasons))
        recommendation = self._generate_recommendation(risk_tier, reasons)
        
        result = SuspicionResult(
            suspicion_score=suspicion_score,
            risk_tier=risk_tier,
            tournament_performance_score=tournament_performance_score,
            percentile_score=percentile_score,
            volatility_score=volatility_score,
            red_flag_score=red_flag_score,
            reasons=reasons,
            tournament_avg_vs_expected=tournament_avg_vs_expected,
            tournament_percentile=tournament_percentile,
            score_volatility=score_volatility,
            expected_volatility=expected_std,
            joint_probability=joint_probability,
            has_casual_comparison=has_casual_comparison,
            casual_vs_tournament_diff=casual_vs_tournament_diff,
            tier_label=tier_label,
            summary=summary,
            recommendation=recommendation,
        )
        
        logger.info(
            f"Analysis complete: score={suspicion_score:.1f}, tier={risk_tier.value}, "
            f"flags={len(reasons)}"
        )
        
        return result
    
    def _check_tournament_excellence(
        self,
        avg_vs_expected: float,
        percentile: float,
        num_tournaments: int,
        reasons: List[SuspicionReason]
    ) -> None:
        """Check for tournament excellence pattern."""
        thresholds = self.config.thresholds
        labels = self.config.get_labels()
        
        if avg_vs_expected >= -0.5:
            return
        
        z_score = avg_vs_expected
        prob = stats.norm.cdf(z_score)
        
        severity = None
        if avg_vs_expected <= thresholds.tournament_excellence_critical and percentile < thresholds.percentile_critical:
            severity = FlagSeverity.CRITICAL
        elif avg_vs_expected <= thresholds.tournament_excellence_high and percentile < thresholds.percentile_high:
            severity = FlagSeverity.HIGH
        elif avg_vs_expected <= thresholds.tournament_excellence_medium and percentile < thresholds.percentile_medium:
            severity = FlagSeverity.MEDIUM
        
        if severity:
            reasons.append(SuspicionReason(
                flag_type=FlagType.TOURNAMENT_EXCELLENCE,
                severity=severity,
                title="Tournament Performance Pattern",
                description=f"Consistently performs better than handicap in tournaments",
                evidence=(
                    f"Averages {abs(avg_vs_expected):.1f} strokes better than expected "
                    f"in {num_tournaments} tournaments (top {percentile:.1f}%)"
                ),
                metric_name="avg_strokes_better_than_expected",
                metric_value=avg_vs_expected,
                threshold_value=getattr(thresholds, f"tournament_excellence_{severity.value.lower()}"),
                probability_note=f"Probability of this performance: {prob*100:.2f}%",
                caddyshack_quip=labels.explanation_tournament_excellence if hasattr(labels, 'explanation_tournament_excellence') else None,
                serious_note="Consistent overperformance relative to handicap index",
            ))
    
    def _check_low_volatility(
        self,
        actual_volatility: float,
        expected_volatility: float,
        volatility_ratio: float,
        reasons: List[SuspicionReason]
    ) -> None:
        """Check for suspiciously low score volatility."""
        thresholds = self.config.thresholds
        labels = self.config.get_labels()
        
        if volatility_ratio >= thresholds.volatility_suspicious_medium:
            return
        
        if volatility_ratio < thresholds.volatility_suspicious_low:
            severity = FlagSeverity.HIGH
        else:
            severity = FlagSeverity.MEDIUM
        
        reasons.append(SuspicionReason(
            flag_type=FlagType.LOW_VOLATILITY,
            severity=severity,
            title="Unusually Consistent Scoring",
            description="Score volatility is lower than expected for this handicap",
            evidence=(
                f"Volatility ({actual_volatility:.1f}) is "
                f"{(1-volatility_ratio)*100:.0f}% lower than expected ({expected_volatility:.1f})"
            ),
            metric_name="volatility_ratio",
            metric_value=volatility_ratio,
            threshold_value=thresholds.volatility_suspicious_medium,
            probability_note="Consistent excellence may indicate handicap inflation",
            caddyshack_quip=labels.explanation_low_volatility if hasattr(labels, 'explanation_low_volatility') else None,
            serious_note="Score variance significantly below statistical expectations",
        ))
    
    def _check_improbable_consistency(
        self,
        joint_probability: float,
        num_rounds: int,
        reasons: List[SuspicionReason]
    ) -> None:
        """Check for statistically improbable consistent performance."""
        thresholds = self.config.thresholds
        labels = self.config.get_labels()
        
        if joint_probability > thresholds.probability_medium:
            return
        
        if joint_probability < thresholds.probability_critical:
            severity = FlagSeverity.CRITICAL
            note = "This level of consistent excellence is extremely rare"
        elif joint_probability < thresholds.probability_high:
            severity = FlagSeverity.HIGH
            note = "This level of excellence is very rare"
        else:
            severity = FlagSeverity.MEDIUM
            note = None
        
        reasons.append(SuspicionReason(
            flag_type=FlagType.IMPROBABLE_CONSISTENCY,
            severity=severity,
            title="Statistically Improbable Pattern",
            description="Combined tournament performance is statistically unlikely",
            evidence=(
                f"Combined probability of all {num_rounds} tournament performances: "
                f"{joint_probability*100:.4f}%"
            ),
            metric_name="joint_probability",
            metric_value=joint_probability,
            threshold_value=thresholds.probability_medium,
            probability_note=note,
            caddyshack_quip=labels.explanation_improbable if hasattr(labels, 'explanation_improbable') else None,
            serious_note="Joint probability of observed performances is statistically rare",
        ))
    
    def _check_perfect_record(
        self,
        scores_vs_expected: List[float],
        reasons: List[SuspicionReason]
    ) -> None:
        """Check if ALL tournament scores beat expectations."""
        if not scores_vs_expected:
            return
        
        all_better = all(score < 0 for score in scores_vs_expected)
        if not all_better:
            return
        
        num_rounds = len(scores_vs_expected)
        avg_better = statistics.mean(scores_vs_expected)
        prob = 0.5 ** num_rounds
        
        if num_rounds >= 5:
            severity = FlagSeverity.HIGH
        elif num_rounds >= 3:
            severity = FlagSeverity.MEDIUM
        else:
            return
        
        reasons.append(SuspicionReason(
            flag_type=FlagType.PERFECT_TOURNAMENT_RECORD,
            severity=severity,
            title="Perfect Tournament Record",
            description=f"Every tournament round ({num_rounds}) exceeded expectations",
            evidence=(
                f"All {num_rounds} rounds beat expected score by average of "
                f"{abs(avg_better):.1f} strokes"
            ),
            metric_name="consecutive_better_rounds",
            metric_value=float(num_rounds),
            threshold_value=3.0,
            probability_note=f"Probability of this: {prob*100:.3f}% (1 in {int(1/prob):,})",
            caddyshack_quip="Every single tournament round was a personal best? Impressive... or suspicious.",
            serious_note="Perfect record of exceeding handicap expectations in all tournament rounds",
        ))
    
    def _check_casual_disparity(
        self,
        casual_avg: float,
        tournament_avg: float,
        casual_vs_expected: float,
        tournament_vs_expected: float,
        num_casual: int,
        num_tournaments: int,
        reasons: List[SuspicionReason]
    ) -> None:
        """Check for disparity between casual and tournament play."""
        thresholds = self.config.thresholds
        labels = self.config.get_labels()
        
        disparity = casual_vs_expected - tournament_vs_expected
        
        if disparity < thresholds.disparity_medium:
            return
        
        if disparity >= thresholds.disparity_critical:
            severity = FlagSeverity.CRITICAL
        elif disparity >= thresholds.disparity_high:
            severity = FlagSeverity.HIGH
        else:
            severity = FlagSeverity.MEDIUM
        
        reasons.append(SuspicionReason(
            flag_type=FlagType.CASUAL_TOURNAMENT_DISPARITY,
            severity=severity,
            title="Casual vs Tournament Disparity",
            description="Significant performance difference between casual and tournament play",
            evidence=(
                f"Casual rounds avg {casual_vs_expected:+.1f} vs expected, "
                f"tournaments {tournament_vs_expected:+.1f} vs expected "
                f"(difference: {disparity:.1f} strokes)"
            ),
            metric_name="casual_tournament_disparity",
            metric_value=disparity,
            threshold_value=thresholds.disparity_medium,
            probability_note=(
                f"Based on {num_casual} casual rounds and {num_tournaments} tournament rounds"
            ),
            caddyshack_quip=labels.explanation_disparity if hasattr(labels, 'explanation_disparity') else None,
            serious_note="Performance varies significantly based on round type",
        ))
    
    def _calc_tournament_score(self, avg_vs_expected: float) -> float:
        """Calculate tournament performance component of suspicion score."""
        weights = self.config.weights
        thresholds = self.config.thresholds
        
        if avg_vs_expected < thresholds.tournament_excellence_critical:
            return weights.tournament_performance_critical
        elif avg_vs_expected < thresholds.tournament_excellence_high:
            return weights.tournament_performance_high
        elif avg_vs_expected < thresholds.tournament_excellence_medium:
            return weights.tournament_performance_medium
        elif avg_vs_expected < 0:
            return weights.tournament_performance_low
        return 0.0
    
    def _calc_percentile_score(self, percentile: float) -> float:
        """Calculate percentile component of suspicion score."""
        weights = self.config.weights
        
        if percentile < 5:
            return weights.percentile_5
        elif percentile < 15:
            return weights.percentile_15
        elif percentile < 25:
            return weights.percentile_25
        elif percentile < 40:
            return weights.percentile_40
        return 0.0
    
    def _calc_volatility_score(self, volatility_ratio: float) -> float:
        """Calculate volatility component of suspicion score."""
        weights = self.config.weights
        thresholds = self.config.thresholds
        
        if volatility_ratio < thresholds.volatility_suspicious_low:
            return weights.volatility_very_low
        elif volatility_ratio < thresholds.volatility_suspicious_medium:
            return weights.volatility_low
        elif volatility_ratio < 0.9:
            return weights.volatility_slightly_low
        return 0.0
    
    def _calc_red_flag_score(self, reasons: List[SuspicionReason]) -> float:
        """Calculate red flag component of suspicion score."""
        weights = self.config.weights
        
        base_score = min(len(reasons) * weights.red_flag_points, weights.red_flag_max)
        
        critical_count = sum(
            1 for r in reasons if r.severity == FlagSeverity.CRITICAL
        )
        critical_bonus = critical_count * weights.critical_flag_bonus
        
        return base_score + critical_bonus
    
    def _determine_risk_tier(self, score: float) -> RiskTier:
        """Determine risk tier from suspicion score."""
        thresholds = self.config.thresholds
        
        if score >= thresholds.risk_tier_severe:
            return RiskTier.SEVERE
        elif score >= thresholds.risk_tier_high:
            return RiskTier.HIGH
        elif score >= thresholds.risk_tier_moderate:
            return RiskTier.MODERATE
        return RiskTier.LOW
    
    def _generate_summary(
        self,
        risk_tier: RiskTier,
        avg_vs_expected: float,
        num_flags: int
    ) -> str:
        """Generate mode-appropriate summary text."""
        return self.config.get_summary(risk_tier)
    
    def _generate_recommendation(
        self,
        risk_tier: RiskTier,
        reasons: List[SuspicionReason]
    ) -> str:
        """Generate action recommendation based on analysis."""
        critical_count = sum(
            1 for r in reasons if r.severity == FlagSeverity.CRITICAL
        )
        
        if self.config.mode == SuspicionMode.CADDYSHACK:
            if risk_tier == RiskTier.SEVERE:
                return (
                    "🚨 Time to convene the handicap committee! "
                    "These numbers need a thorough review before the next event. "
                    "Consider a friendly conversation and handicap verification."
                )
            elif risk_tier == RiskTier.HIGH:
                return (
                    "📋 Worth investigating further. Pull some additional score history "
                    "and keep an eye on the next few rounds. A chat might be in order."
                )
            elif risk_tier == RiskTier.MODERATE:
                return (
                    "👀 Keep watching, but no need to panic yet. "
                    "Could be a hot streak, could be something else. "
                    "Check back after 3-5 more rounds."
                )
            else:
                return (
                    "✅ All good here! Scores look legit. "
                    "Continue normal monitoring and enjoy the game."
                )
        else:
            # Serious mode
            if risk_tier == RiskTier.SEVERE:
                return (
                    "RECOMMENDED ACTION: Formal handicap committee review is strongly advised. "
                    "Consider requesting additional score history and handicap verification. "
                    "Monitor performance closely in future competitions."
                )
            elif risk_tier == RiskTier.HIGH:
                return (
                    "RECOMMENDED ACTION: Investigation warranted. Request additional score history "
                    "and consider discussing with the golfer. Monitor performance in upcoming events."
                )
            elif risk_tier == RiskTier.MODERATE:
                return (
                    "RECOMMENDED ACTION: Continue monitoring. If patterns persist over next 3-5 rounds, "
                    "consider deeper investigation. May represent normal variance or improvement."
                )
            else:
                return (
                    "RECOMMENDED ACTION: No action needed. Performance is consistent with handicap. "
                    "Continue standard monitoring procedures."
                )
