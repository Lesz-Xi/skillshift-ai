"""
Enhanced Coaching System Data Models
===================================

This module defines the new data structures for the expanded coaching feedback system.
Maintains backward compatibility while adding advanced coaching capabilities.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
import time


class CoachingSeverity(str, Enum):
    """Coaching tip severity levels with consistent UI mapping."""
    INFO = "info"          # ℹ️ General guidance and information
    WARNING = "warning"    # ⚠️ Areas needing improvement
    SUCCESS = "success"    # ✅ Positive performance recognition  
    CRITICAL = "critical"  # ❌ Urgent issues requiring immediate attention


class CoachingCategory(str, Enum):
    """Multi-layer coaching system categories."""
    PERFORMANCE = "performance"    # Layer 1: KDA, GPM, damage output
    TACTICAL = "tactical"         # Layer 2: Positioning, farming, skill usage
    STRATEGIC = "strategic"       # Layer 3: Itemization, team synergy, meta
    PROGRESSION = "progression"   # Layer 4: Improvement trends, skill gaps


class FocusArea(str, Enum):
    """Specific coaching focus areas for targeted improvement."""
    # Performance areas
    KDA = "kda"
    GPM = "gpm" 
    DAMAGE_OUTPUT = "damage_output"
    TEAMFIGHTING = "teamfighting"
    
    # Tactical areas  
    POSITIONING = "positioning"
    FARMING = "farming"
    SKILL_USAGE = "skill_usage"
    OBJECTIVE_CONTROL = "objective_control"
    
    # Strategic areas
    ITEMIZATION = "itemization"
    TEAM_SYNERGY = "team_synergy"
    META_AWARENESS = "meta_awareness"
    MATCHUP_STRATEGY = "matchup_strategy"
    
    # Progression areas
    CONSISTENCY = "consistency"
    SKILL_DEVELOPMENT = "skill_development"
    WEAKNESS_PATTERNS = "weakness_patterns"
    ACHIEVEMENT_RECOGNITION = "achievement_recognition"


class ExpectedImpact(str, Enum):
    """Expected impact level of implementing coaching suggestions."""
    HIGH = "high"      # Major performance improvement expected
    MEDIUM = "medium"  # Moderate improvement expected  
    LOW = "low"       # Minor but meaningful improvement


class RankTier(str, Enum):
    """Mobile Legends rank tiers for contextual coaching."""
    WARRIOR = "warrior"
    ELITE = "elite" 
    MASTER = "master"
    GRANDMASTER = "grandmaster"
    EPIC = "epic"
    LEGEND = "legend"
    MYTHIC = "mythic"
    MYTHICAL_GLORY = "mythical_glory"


@dataclass
class CoachingTip:
    """
    Enhanced coaching tip structure with comprehensive metadata.
    
    This replaces the simple tuple format with rich, actionable guidance
    that supports multi-layer coaching and personalized improvement tracking.
    """
    # Core feedback (backward compatible)
    severity: CoachingSeverity
    message: str
    
    # Enhanced categorization
    category: CoachingCategory  
    focus_area: FocusArea
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    
    # Actionable guidance
    action_items: List[str] = field(default_factory=list)
    practice_suggestions: List[str] = field(default_factory=list) 
    expected_impact: ExpectedImpact = ExpectedImpact.MEDIUM
    
    # Contextual relevance
    rank_relevance: List[RankTier] = field(default_factory=list)
    meta_relevance: str = "current"  # "high", "medium", "low", "current"
    hero_specificity: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Progress tracking
    improvement_metric: Optional[str] = None
    target_threshold: Optional[float] = None
    timeline_estimate: str = "1-2 games"
    
    # Internal metadata
    generated_at: float = field(default_factory=time.time)
    source_evaluator: str = "unknown"
    
    def to_legacy_format(self) -> tuple:
        """Convert to legacy (severity, message) format for backward compatibility."""
        return (self.severity.value, self.message)
    
    def get_ui_symbol(self) -> str:
        """Get consistent UI symbol for severity level."""
        return {
            CoachingSeverity.INFO: "ℹ️",
            CoachingSeverity.WARNING: "⚠️", 
            CoachingSeverity.SUCCESS: "✅",
            CoachingSeverity.CRITICAL: "❌"
        }[self.severity]
        
    def format_for_display(self, include_actions: bool = True) -> str:
        """Format tip for user-friendly display."""
        symbol = self.get_ui_symbol()
        base = f"{symbol} {self.message}"
        
        if include_actions and self.action_items:
            actions = " | ".join(self.action_items[:2])  # Max 2 actions
            base += f" → {actions}"
            
        return base


class MatchContext(BaseModel):
    """Enhanced match context for intelligent coaching."""
    patch_version: str = "1.8.50"
    rank_tier: RankTier = RankTier.EPIC
    match_type: str = "ranked"  # "classic", "ranked", "tournament"  
    game_phase: str = "full_game"  # "early", "mid", "late", "full_game"
    
    # Team compositions (hero names)
    team_composition: List[str] = Field(default_factory=list)
    enemy_composition: List[str] = Field(default_factory=list)
    
    # Match metadata
    match_duration: Optional[float] = None
    season: Optional[str] = None


class AdvancedMetrics(BaseModel):
    """Advanced performance metrics for enhanced coaching analysis."""
    # Tactical metrics (future replay support)
    farming_efficiency: Optional[float] = None  # CS/min or jungle clear speed
    objective_participation: Optional[int] = None  # Lord/Turtle/turret percentage
    vision_control: Optional[float] = None  # Wards placed, vision score
    skill_accuracy: Dict[str, float] = Field(default_factory=dict)  # Hero-specific skill hit rates
    
    # Positioning analysis (future support)
    positioning_heatmap: List[Dict[str, float]] = Field(default_factory=list)  # Death/kill locations
    average_positioning_score: Optional[float] = None
    
    # Economy and efficiency
    gold_efficiency: Optional[float] = None  # Gold gained vs time spent
    experience_efficiency: Optional[float] = None
    item_timing_score: Optional[float] = None


class ProgressionData(BaseModel):  
    """Player progression tracking for personalized coaching."""
    recent_matches: List[Dict[str, Any]] = Field(default_factory=list)  # Last 10-20 games summary
    improvement_trends: Dict[str, float] = Field(default_factory=dict)  # Metric trend slopes
    personal_bests: Dict[str, float] = Field(default_factory=dict)  # Best recorded values
    weakness_patterns: List[str] = Field(default_factory=list)  # Recurring issue categories
    
    # Achievement tracking
    achievements_unlocked: List[str] = Field(default_factory=list)
    current_focus_areas: List[FocusArea] = Field(default_factory=list)
    improvement_goals: Dict[str, float] = Field(default_factory=dict)


class EnhancedMatchAnalysis(BaseModel):
    """
    Enhanced match data structure that extends the current system.
    
    Maintains full backward compatibility with existing basic stats while
    adding optional advanced metrics and context for intelligent coaching.
    """
    # === EXISTING BASIC STATS (preserved for backward compatibility) ===
    hero: str
    kills: int = 0
    deaths: int = 0  
    assists: int = 0
    gold_per_min: int = 0
    hero_damage: int = 0
    turret_damage: int = 0
    damage_taken: int = 0
    teamfight_participation: int = 0
    positioning_rating: str = "average"  # "low", "average", "high"
    ult_usage: str = "average"  # "low", "average", "high"
    match_duration: float = 0.0
    
    # Hero-specific stats (preserved)
    hooks_landed: int = 0  # Franco
    team_engages: int = 0  # Tanks
    vision_score: int = 0
    
    # === NEW ENHANCED FEATURES ===
    # Extended context awareness  
    match_context: MatchContext = Field(default_factory=MatchContext)
    
    # Advanced performance metrics (optional, future replay support)
    advanced_metrics: AdvancedMetrics = Field(default_factory=AdvancedMetrics)
    
    # Progression tracking (optional, for personalized coaching)
    progression: Optional[ProgressionData] = None
    
    # === COMPUTED PROPERTIES ===
    @property
    def kda_ratio(self) -> float:
        """Calculate KDA ratio for easy access."""
        return (self.kills + self.assists) / max(1, self.deaths)
    
    @property
    def damage_ratio(self) -> float:
        """Calculate damage dealt to damage taken ratio."""
        return self.hero_damage / max(1, self.damage_taken)
        
    def get_basic_stats(self) -> Dict[str, Any]:
        """Extract basic stats for legacy compatibility."""
        return {
            'hero': self.hero,
            'kills': self.kills,
            'deaths': self.deaths,
            'assists': self.assists,
            'gold_per_min': self.gold_per_min,
            'hero_damage': self.hero_damage,
            'turret_damage': self.turret_damage, 
            'damage_taken': self.damage_taken,
            'teamfight_participation': self.teamfight_participation,
            'positioning_rating': self.positioning_rating,
            'ult_usage': self.ult_usage,
            'match_duration': self.match_duration,
            'hooks_landed': self.hooks_landed,
            'team_engages': self.team_engages,
            'vision_score': self.vision_score
        }


class CoachingResult(BaseModel):
    """Complete coaching analysis result with metadata."""
    tips: List[CoachingTip]
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time: float = 0.0
    evaluator_chain: List[str] = Field(default_factory=list)  # Which evaluators were used
    
    def get_legacy_format(self, include_severity: bool = False) -> List[Union[str, tuple]]:
        """Convert to legacy format for backward compatibility."""
        if include_severity:
            return [tip.to_legacy_format() for tip in self.tips]
        else:
            return [tip.message for tip in self.tips]
    
    def format_for_ui(self, max_tips: int = 4) -> List[str]:
        """Format tips for UI display with prioritization."""
        # Sort by priority: success -> critical -> warning -> info
        priority_order = {
            CoachingSeverity.SUCCESS: 0,
            CoachingSeverity.CRITICAL: 1, 
            CoachingSeverity.WARNING: 2,
            CoachingSeverity.INFO: 3
        }
        
        sorted_tips = sorted(self.tips, key=lambda t: (priority_order[t.severity], -t.confidence))
        return [tip.format_for_display() for tip in sorted_tips[:max_tips]]


# === UTILITY FUNCTIONS ===

def humanize_number(value: Union[int, float], context: str = "") -> str:
    """
    Convert numbers to human-readable format.
    
    Examples:
    - 15435 damage -> "15.4k damage" 
    - 2500 gold -> "2.5k gold"
    - 95 -> "95%" (for percentages)
    """
    if isinstance(value, str):
        return value
        
    abs_value = abs(value)
    
    if context in ["percentage", "percent", "%"] or "participation" in context:
        return f"{int(value)}%"
    elif abs_value >= 1000:
        if abs_value >= 1000000:
            return f"{value/1000000:.1f}M"
        else:
            return f"{value/1000:.1f}k"
    else:
        return str(int(value))


def format_coaching_message(template: str, **kwargs) -> str:
    """
    Format coaching messages with humanized numbers and context.
    
    Example:
    format_coaching_message(
        "Damage {damage} (< {target}). {advice}", 
        damage=15435, 
        target=20000,
        advice="Focus on farming between fights"
    )
    -> "Damage 15.4k (< 20k). Focus on farming between fights"
    """
    # Humanize numeric values
    formatted_kwargs = {}
    for key, value in kwargs.items():
        if isinstance(value, (int, float)) and key in ['damage', 'gold', 'gpm']:
            formatted_kwargs[key] = humanize_number(value, key)
        elif isinstance(value, (int, float)) and 'participation' in key:
            formatted_kwargs[key] = humanize_number(value, "percentage")
        else:
            formatted_kwargs[key] = value
            
    return template.format(**formatted_kwargs)


# === EXAMPLE USAGE ===
if __name__ == "__main__":
    # Example coaching tip creation
    tip = CoachingTip(
        severity=CoachingSeverity.WARNING,
        message=format_coaching_message(
            "KDA {kda:.1f} is low for {hero}. Focus on {focus} to improve performance.",
            kda=2.3, hero="Kagura", focus="positioning and combo execution"
        ),
        category=CoachingCategory.PERFORMANCE,
        focus_area=FocusArea.KDA,
        confidence=0.85,
        action_items=["Practice umbrella positioning", "Work on escape timing"],
        practice_suggestions=["Use practice mode for combo timing", "Watch pro Kagura gameplay"],
        expected_impact=ExpectedImpact.HIGH,
        rank_relevance=[RankTier.EPIC, RankTier.LEGEND],
        hero_specificity=0.9,
        improvement_metric="kda_ratio", 
        target_threshold=3.0,
        timeline_estimate="5-10 games"
    )
    
    print("Enhanced Coaching Tip:")
    print(f"Display: {tip.format_for_display()}")
    print(f"Legacy: {tip.to_legacy_format()}")
    print(f"Symbol: {tip.get_ui_symbol()}")