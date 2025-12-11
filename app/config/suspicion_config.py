"""
Suspicion Detection Configuration

This module provides configurable thresholds and settings for the sandbagging/suspicion
detection system. All labels and terminology are designed to be non-defamatory and
clearly framed as "patterns for review" rather than accusations.

IMPORTANT: This tool assists committees in reviewing potential anomalies.
It does NOT declare guilt or accuse anyone of actual cheating.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SuspicionMode(str, Enum):
    """
    UI/analysis mode for the suspicion detection system.
    
    CADDYSHACK: Playful, humorous UI with full animations and witty text
    SERIOUS: Neutral, committee-friendly wording with minimal embellishments
    """
    CADDYSHACK = "caddyshack"
    SERIOUS = "serious"


class RiskTier(str, Enum):
    """
    Risk tier classification for suspicion scores.
    
    These tiers indicate levels of statistical anomaly, NOT accusations.
    All players flagged should be reviewed by a committee.
    """
    LOW = "low"
    MODERATE = "moderate" 
    HIGH = "high"
    SEVERE = "severe"


class SuspicionThresholds(BaseModel):
    """Configurable thresholds for suspicion scoring."""
    
    # Tournament vs expected performance thresholds (strokes better than expected)
    tournament_excellence_critical: float = Field(
        default=-2.5,
        description="Strokes better than expected to trigger CRITICAL flag"
    )
    tournament_excellence_high: float = Field(
        default=-1.5,
        description="Strokes better than expected to trigger HIGH flag"
    )
    tournament_excellence_medium: float = Field(
        default=-1.0,
        description="Strokes better than expected to trigger MEDIUM flag"
    )
    
    # Percentile thresholds for tournament performance
    percentile_critical: float = Field(
        default=10.0,
        description="Performance percentile below which is CRITICAL"
    )
    percentile_high: float = Field(
        default=20.0,
        description="Performance percentile below which is HIGH"
    )
    percentile_medium: float = Field(
        default=30.0,
        description="Performance percentile below which is MEDIUM"
    )
    
    # Volatility ratio thresholds (actual/expected)
    volatility_suspicious_low: float = Field(
        default=0.5,
        description="Volatility ratio below which is highly suspicious"
    )
    volatility_suspicious_medium: float = Field(
        default=0.7,
        description="Volatility ratio below which is moderately suspicious"
    )
    
    # Joint probability thresholds
    probability_critical: float = Field(
        default=0.0001,
        description="Joint probability below which is CRITICAL (0.01%)"
    )
    probability_high: float = Field(
        default=0.001,
        description="Joint probability below which is HIGH (0.1%)"
    )
    probability_medium: float = Field(
        default=0.01,
        description="Joint probability below which is MEDIUM (1%)"
    )
    
    # Casual vs tournament disparity thresholds
    disparity_critical: float = Field(
        default=5.0,
        description="Stroke disparity to trigger CRITICAL flag"
    )
    disparity_high: float = Field(
        default=3.5,
        description="Stroke disparity to trigger HIGH flag"
    )
    disparity_medium: float = Field(
        default=2.0,
        description="Stroke disparity to trigger MEDIUM flag"
    )
    
    # Risk score tier boundaries
    risk_tier_severe: float = Field(
        default=75.0,
        description="Score threshold for SEVERE risk tier"
    )
    risk_tier_high: float = Field(
        default=50.0,
        description="Score threshold for HIGH risk tier"
    )
    risk_tier_moderate: float = Field(
        default=25.0,
        description="Score threshold for MODERATE risk tier"
    )
    
    # Minimum rounds for analysis
    min_rounds_for_analysis: int = Field(
        default=3,
        description="Minimum tournament rounds needed for meaningful analysis"
    )


class SuspicionWeights(BaseModel):
    """Configurable weights for suspicion score calculation."""
    
    # Tournament performance weight (0-40 points max)
    tournament_performance_max: float = Field(default=40.0)
    tournament_performance_critical: float = Field(default=40.0)
    tournament_performance_high: float = Field(default=30.0)
    tournament_performance_medium: float = Field(default=20.0)
    tournament_performance_low: float = Field(default=10.0)
    
    # Percentile performance weight (0-25 points max)
    percentile_max: float = Field(default=25.0)
    percentile_5: float = Field(default=25.0)
    percentile_15: float = Field(default=20.0)
    percentile_25: float = Field(default=15.0)
    percentile_40: float = Field(default=10.0)
    
    # Volatility weight (0-20 points max)
    volatility_max: float = Field(default=20.0)
    volatility_very_low: float = Field(default=20.0)
    volatility_low: float = Field(default=15.0)
    volatility_slightly_low: float = Field(default=10.0)
    
    # Red flag weights
    red_flag_points: float = Field(default=3.0)
    red_flag_max: float = Field(default=15.0)
    critical_flag_bonus: float = Field(default=10.0)


class CaddyshackLabels(BaseModel):
    """Humorous labels for Caddyshack mode."""
    
    # Risk tier labels
    tier_low: str = Field(default="All Clear - Nothing to See Here")
    tier_moderate: str = Field(default="Hmm... Worth a Second Look")
    tier_high: str = Field(default="Judge Smails Would Like a Word")
    tier_severe: str = Field(default="Carl Spackler Alert! 🐿️")
    
    # Badge labels
    badge_under_review: str = Field(default="Under the Microscope")
    badge_probable_bandit: str = Field(default="Probable Bandit")
    badge_suspicion_high: str = Field(default="Suspicion Index: Spicy 🌶️")
    badge_all_clear: str = Field(default="Fairway to Heaven ⛳")
    
    # Summary messages by risk level
    summary_low: str = Field(
        default="✅ This golfer's scores are as clean as a freshly raked bunker. " 
                "No suspicious patterns detected - they're playing it straight."
    )
    summary_moderate: str = Field(
        default="🤔 Interesting... This scorecard has some curious patterns. "
                "Not necessarily sandbagging, but worth keeping an eye on. "
                "Could be a hot streak, or could be something else."
    )
    summary_high: str = Field(
        default="🎯 Easy there, Judge Smails – these numbers deserve a closer look. "
                "Performance is notably better than their handicap suggests. "
                "Time for a friendly chat perhaps?"
    )
    summary_severe: str = Field(
        default="🚨 Whoa there! This scorecard has some serious Caddyshack vibes. "
                "The pencil might have had an eraser workout on these rounds. "
                "Committee review strongly recommended."
    )
    
    # Witty explanations
    explanation_tournament_excellence: str = Field(
        default="Turns into Tiger Woods whenever there's a trophy on the line"
    )
    explanation_low_volatility: str = Field(
        default="Scores more consistent than Carl's gopher-hunting technique"
    )
    explanation_disparity: str = Field(
        default="Jekyll and Hyde of the links - casual rounds vs tournaments"
    )
    explanation_improbable: str = Field(
        default="Statistically speaking, this is rarer than a hole-in-one on a par 5"
    )


class SeriousLabels(BaseModel):
    """Professional labels for Serious Committee mode."""
    
    # Risk tier labels
    tier_low: str = Field(default="Low Anomaly - No Action Required")
    tier_moderate: str = Field(default="Moderate Anomaly - Monitor")
    tier_high: str = Field(default="High Anomaly - Review Recommended")
    tier_severe: str = Field(default="Significant Anomaly - Investigation Advised")
    
    # Badge labels  
    badge_under_review: str = Field(default="Under Review")
    badge_probable_bandit: str = Field(default="Statistical Outlier")
    badge_suspicion_high: str = Field(default="High Anomaly Index")
    badge_all_clear: str = Field(default="Normal Variance")
    
    # Summary messages by risk level
    summary_low: str = Field(
        default="Performance analysis indicates scoring patterns consistent with "
                "the stated handicap index. No statistical anomalies detected."
    )
    summary_moderate: str = Field(
        default="Analysis indicates some variance from expected performance. "
                "Patterns are within possible normal range but warrant continued monitoring."
    )
    summary_high: str = Field(
        default="Statistical analysis reveals performance notably exceeding handicap expectations. "
                "Committee review is recommended to verify handicap accuracy."
    )
    summary_severe: str = Field(
        default="Multiple statistical indicators suggest significant deviation from expected performance. "
                "Formal handicap committee review is strongly advised."
    )
    
    # Professional explanations
    explanation_tournament_excellence: str = Field(
        default="Consistent overperformance in competitive rounds relative to handicap"
    )
    explanation_low_volatility: str = Field(
        default="Score variance significantly below expected standard deviation"
    )
    explanation_disparity: str = Field(
        default="Significant scoring differential between casual and tournament play"
    )
    explanation_improbable: str = Field(
        default="Combined probability of observed scores is statistically rare"
    )


class SuspicionConfig(BaseModel):
    """
    Complete configuration for the suspicion detection system.
    
    This configuration allows organizers to customize the sensitivity
    and presentation of the analysis system.
    """
    
    mode: SuspicionMode = Field(
        default=SuspicionMode.CADDYSHACK,
        description="UI mode - 'caddyshack' for playful, 'serious' for committee"
    )
    
    thresholds: SuspicionThresholds = Field(
        default_factory=SuspicionThresholds,
        description="Configurable thresholds for detection"
    )
    
    weights: SuspicionWeights = Field(
        default_factory=SuspicionWeights,
        description="Configurable weights for score calculation"
    )
    
    caddyshack_labels: CaddyshackLabels = Field(
        default_factory=CaddyshackLabels,
        description="Humorous labels for Caddyshack mode"
    )
    
    serious_labels: SeriousLabels = Field(
        default_factory=SeriousLabels,
        description="Professional labels for Serious mode"
    )
    
    def get_labels(self) -> CaddyshackLabels | SeriousLabels:
        """Get the appropriate labels based on current mode."""
        if self.mode == SuspicionMode.CADDYSHACK:
            return self.caddyshack_labels
        return self.serious_labels
    
    def get_tier_label(self, tier: RiskTier) -> str:
        """Get the display label for a risk tier."""
        labels = self.get_labels()
        tier_map = {
            RiskTier.LOW: labels.tier_low,
            RiskTier.MODERATE: labels.tier_moderate,
            RiskTier.HIGH: labels.tier_high,
            RiskTier.SEVERE: labels.tier_severe,
        }
        return tier_map.get(tier, labels.tier_low)
    
    def get_summary(self, tier: RiskTier) -> str:
        """Get the summary message for a risk tier."""
        labels = self.get_labels()
        summary_map = {
            RiskTier.LOW: labels.summary_low,
            RiskTier.MODERATE: labels.summary_moderate,
            RiskTier.HIGH: labels.summary_high,
            RiskTier.SEVERE: labels.summary_severe,
        }
        return summary_map.get(tier, labels.summary_low)


# Conservative preset - fewer false positives
CONSERVATIVE_THRESHOLDS = SuspicionThresholds(
    tournament_excellence_critical=-3.0,
    tournament_excellence_high=-2.0,
    tournament_excellence_medium=-1.5,
    percentile_critical=5.0,
    percentile_high=15.0,
    percentile_medium=25.0,
    volatility_suspicious_low=0.4,
    volatility_suspicious_medium=0.6,
    probability_critical=0.00005,
    probability_high=0.0005,
    probability_medium=0.005,
    disparity_critical=6.0,
    disparity_high=4.5,
    disparity_medium=3.0,
    risk_tier_severe=80.0,
    risk_tier_high=55.0,
    risk_tier_moderate=30.0,
    min_rounds_for_analysis=5,
)

# Aggressive preset - more sensitivity, more flags
AGGRESSIVE_THRESHOLDS = SuspicionThresholds(
    tournament_excellence_critical=-2.0,
    tournament_excellence_high=-1.0,
    tournament_excellence_medium=-0.5,
    percentile_critical=15.0,
    percentile_high=25.0,
    percentile_medium=35.0,
    volatility_suspicious_low=0.6,
    volatility_suspicious_medium=0.8,
    probability_critical=0.001,
    probability_high=0.01,
    probability_medium=0.05,
    disparity_critical=4.0,
    disparity_high=2.5,
    disparity_medium=1.5,
    risk_tier_severe=65.0,
    risk_tier_high=40.0,
    risk_tier_moderate=20.0,
    min_rounds_for_analysis=2,
)


def get_default_config() -> SuspicionConfig:
    """Get the default suspicion configuration."""
    return SuspicionConfig()


def get_conservative_config() -> SuspicionConfig:
    """Get a conservative configuration (fewer false positives)."""
    return SuspicionConfig(thresholds=CONSERVATIVE_THRESHOLDS)


def get_aggressive_config() -> SuspicionConfig:
    """Get an aggressive configuration (more sensitivity)."""
    return SuspicionConfig(thresholds=AGGRESSIVE_THRESHOLDS)
