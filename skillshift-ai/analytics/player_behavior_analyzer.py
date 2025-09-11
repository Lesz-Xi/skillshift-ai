"""
Player Behavior Analytics - Advanced behavioral pattern analysis
================================================================

Analyzes player behavior patterns, playstyles, and performance trends
to provide deep insights into gaming habits and improvement opportunities.
"""

import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns

from ..core.services.base_service import BaseService, ServiceResult

logger = logging.getLogger(__name__)


class PlayStyle(Enum):
    """Player playstyle classifications."""
    AGGRESSIVE_CARRY = "aggressive_carry"
    PASSIVE_FARMER = "passive_farmer"
    ROAMING_SUPPORT = "roaming_support"
    OBJECTIVE_FOCUSED = "objective_focused"
    TEAM_FIGHTER = "team_fighter"
    SPLIT_PUSHER = "split_pusher"
    DEFENSIVE_TANK = "defensive_tank"
    BALANCED_PLAYER = "balanced_player"


class RiskProfile(Enum):
    """Risk-taking behavior profiles."""
    HIGH_RISK = "high_risk"
    MODERATE_RISK = "moderate_risk"
    LOW_RISK = "low_risk"
    CALCULATED_RISK = "calculated_risk"


class GamePhasePreference(Enum):
    """Game phase performance preferences."""
    EARLY_GAME = "early_game"
    MID_GAME = "mid_game"
    LATE_GAME = "late_game"
    CONSISTENT = "consistent"


@dataclass
class BehaviorMetrics:
    """Behavioral metrics for analysis."""
    # Combat Behavior
    avg_kda: float = 0.0
    kill_participation: float = 0.0
    death_rate: float = 0.0
    aggression_score: float = 0.0
    
    # Economic Behavior
    gold_efficiency: float = 0.0
    farming_priority: float = 0.0
    resource_management: float = 0.0
    
    # Tactical Behavior
    map_awareness: float = 0.0
    objective_focus: float = 0.0
    team_coordination: float = 0.0
    positioning_score: float = 0.0
    
    # Temporal Behavior
    early_game_impact: float = 0.0
    mid_game_impact: float = 0.0
    late_game_impact: float = 0.0
    consistency_score: float = 0.0
    
    # Risk Behavior
    risk_taking_score: float = 0.0
    safety_score: float = 0.0
    decision_quality: float = 0.0
    
    # Social Behavior
    communication_score: float = 0.0
    leadership_score: float = 0.0
    teamwork_score: float = 0.0


@dataclass
class BehaviorProfile:
    """Complete behavioral profile of a player."""
    # Player Information
    player_id: str
    player_name: str
    
    # Classifications
    primary_playstyle: PlayStyle
    secondary_playstyle: Optional[PlayStyle] = None
    risk_profile: RiskProfile = RiskProfile.MODERATE_RISK
    game_phase_preference: GamePhasePreference = GamePhasePreference.CONSISTENT
    
    # Metrics
    behavior_metrics: BehaviorMetrics = field(default_factory=BehaviorMetrics)
    
    # Strengths and Weaknesses
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    
    # Patterns
    performance_patterns: Dict[str, Any] = field(default_factory=dict)
    temporal_patterns: Dict[str, Any] = field(default_factory=dict)
    hero_preferences: Dict[str, float] = field(default_factory=dict)
    
    # Confidence and Reliability
    profile_confidence: float = 0.0
    data_quality_score: float = 0.0
    sample_size: int = 0
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    analysis_version: str = "1.0"


class PlayerBehaviorAnalyzer(BaseService):
    """Advanced player behavior analysis system."""
    
    def __init__(self, 
                 data_dir: str = "data/player_behavior",
                 cache_dir: str = "cache/behavior_profiles"):
        super().__init__()
        
        # Directory setup
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        
        # Create directories
        for dir_path in [self.data_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Analysis models
        self.scaler = StandardScaler()
        self.clustering_model = None
        self.pca_model = None
        
        # Cached profiles
        self.behavior_profiles: Dict[str, BehaviorProfile] = {}
        
        # Analysis configuration
        self.min_matches_for_analysis = 10
        self.confidence_threshold = 0.7
        
        logger.info("Player Behavior Analyzer initialized")
    
    async def analyze_player_behavior(self, 
                                    player_id: str,
                                    match_history: List[Dict[str, Any]],
                                    force_refresh: bool = False) -> BehaviorProfile:
        """Analyze player behavior and create behavioral profile."""
        
        # Check cache first
        if not force_refresh and player_id in self.behavior_profiles:
            cached_profile = self.behavior_profiles[player_id]
            # Check if cache is still valid (within 24 hours)
            if datetime.now() - cached_profile.last_updated < timedelta(hours=24):
                return cached_profile
        
        logger.info(f"Analyzing behavior for player: {player_id}")
        
        # Validate data
        if len(match_history) < self.min_matches_for_analysis:
            logger.warning(f"Insufficient data for analysis: {len(match_history)} matches")
            return self._create_default_profile(player_id, len(match_history))
        
        # Extract behavioral features
        features_df = await self._extract_behavioral_features(match_history)
        
        # Calculate behavioral metrics
        behavior_metrics = await self._calculate_behavior_metrics(features_df)
        
        # Classify playstyle
        primary_playstyle, secondary_playstyle = await self._classify_playstyle(behavior_metrics)
        
        # Determine risk profile
        risk_profile = await self._determine_risk_profile(behavior_metrics)
        
        # Analyze game phase preferences
        game_phase_preference = await self._analyze_game_phase_preference(features_df)
        
        # Identify strengths and weaknesses
        strengths, weaknesses, improvements = await self._identify_strengths_weaknesses(behavior_metrics)
        
        # Analyze patterns
        performance_patterns = await self._analyze_performance_patterns(features_df)
        temporal_patterns = await self._analyze_temporal_patterns(features_df)
        hero_preferences = await self._analyze_hero_preferences(match_history)
        
        # Calculate confidence scores
        profile_confidence, data_quality = await self._calculate_confidence_scores(
            features_df, behavior_metrics
        )
        
        # Create behavior profile
        profile = BehaviorProfile(
            player_id=player_id,
            player_name=match_history[0].get('player_name', f'Player_{player_id}'),
            primary_playstyle=primary_playstyle,
            secondary_playstyle=secondary_playstyle,
            risk_profile=risk_profile,
            game_phase_preference=game_phase_preference,
            behavior_metrics=behavior_metrics,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_areas=improvements,
            performance_patterns=performance_patterns,
            temporal_patterns=temporal_patterns,
            hero_preferences=hero_preferences,
            profile_confidence=profile_confidence,
            data_quality_score=data_quality,
            sample_size=len(match_history)
        )
        
        # Cache profile
        self.behavior_profiles[player_id] = profile
        
        # Save profile to disk
        await self._save_behavior_profile(profile)
        
        logger.info(f"Behavior analysis completed for {player_id}: {primary_playstyle.value}")
        return profile
    
    async def _extract_behavioral_features(self, match_history: List[Dict[str, Any]]) -> pd.DataFrame:
        """Extract behavioral features from match history."""
        features = []
        
        for match in match_history:
            # Basic performance metrics
            kills = match.get('kills', 0)
            deaths = max(1, match.get('deaths', 1))  # Avoid division by zero
            assists = match.get('assists', 0)
            kda = (kills + assists) / deaths
            
            gold = match.get('gold', 0)
            damage = match.get('hero_damage', 0)
            damage_taken = match.get('damage_taken', 0)
            duration = match.get('match_duration', 20) * 60  # Convert to seconds
            
            # Calculate behavioral features
            features.append({
                # Combat Features
                'kills_per_min': kills / (duration / 60) if duration > 0 else 0,
                'deaths_per_min': deaths / (duration / 60) if duration > 0 else 0,
                'assists_per_min': assists / (duration / 60) if duration > 0 else 0,
                'kda_ratio': kda,
                'kill_participation': (kills + assists) / max(1, match.get('team_kills', 1)),
                
                # Economic Features
                'gold_per_min': gold / (duration / 60) if duration > 0 else 0,
                'damage_per_gold': damage / max(1, gold) if gold > 0 else 0,
                'gold_efficiency': gold / max(1, duration / 60) if duration > 0 else 0,
                
                # Damage Features
                'damage_per_min': damage / (duration / 60) if duration > 0 else 0,
                'damage_taken_per_min': damage_taken / (duration / 60) if duration > 0 else 0,
                'damage_ratio': damage / max(1, damage_taken) if damage_taken > 0 else 0,
                'survivability': max(1, damage_taken) / max(1, deaths),
                
                # Performance Features
                'performance_score': match.get('performance_score', 5.0),
                'mvp_score': 1.0 if match.get('mvp', False) else 0.0,
                'match_result': 1.0 if match.get('result', 'loss').lower() == 'win' else 0.0,
                
                # Temporal Features
                'match_duration_min': duration / 60,
                'early_game_score': self._calculate_early_game_score(match),
                'mid_game_score': self._calculate_mid_game_score(match),
                'late_game_score': self._calculate_late_game_score(match),
                
                # Hero and Role Features
                'hero': match.get('hero', 'unknown'),
                'role': match.get('role', 'unknown'),
                
                # Meta features
                'timestamp': match.get('timestamp', datetime.now().isoformat()),
                'match_id': match.get('match_id', 'unknown')
            })
        
        return pd.DataFrame(features)
    
    def _calculate_early_game_score(self, match: Dict[str, Any]) -> float:
        """Calculate early game performance score."""
        # Simplified early game scoring based on KDA and gold
        kills = match.get('kills', 0)
        deaths = match.get('deaths', 1)
        gold = match.get('gold', 0)
        
        # Early game is typically first 10 minutes
        # Higher kills and gold indicate good early game
        early_score = (kills * 2 - deaths + gold / 5000) / 3
        return max(0, min(10, early_score))
    
    def _calculate_mid_game_score(self, match: Dict[str, Any]) -> float:
        """Calculate mid game performance score."""
        assists = match.get('assists', 0)
        damage = match.get('hero_damage', 0)
        
        # Mid game focuses on team fights and damage
        mid_score = (assists * 1.5 + damage / 10000) / 2
        return max(0, min(10, mid_score))
    
    def _calculate_late_game_score(self, match: Dict[str, Any]) -> float:
        """Calculate late game performance score."""
        performance = match.get('performance_score', 5.0)
        result = 1.0 if match.get('result', 'loss').lower() == 'win' else 0.0
        
        # Late game is about closing out games
        late_score = (performance + result * 5) / 2
        return max(0, min(10, late_score))
    
    async def _calculate_behavior_metrics(self, features_df: pd.DataFrame) -> BehaviorMetrics:
        """Calculate comprehensive behavioral metrics."""
        
        # Combat Behavior
        avg_kda = features_df['kda_ratio'].mean()
        kill_participation = features_df['kill_participation'].mean()
        death_rate = features_df['deaths_per_min'].mean()
        aggression_score = (features_df['kills_per_min'].mean() * 2 + 
                          features_df['damage_per_min'].mean() / 1000) / 3
        
        # Economic Behavior
        gold_efficiency = features_df['gold_efficiency'].mean()
        farming_priority = features_df['gold_per_min'].mean() / 500  # Normalize
        resource_management = features_df['damage_per_gold'].mean()
        
        # Tactical Behavior (simplified calculations)
        map_awareness = features_df['assists_per_min'].mean() * 2  # Assists indicate map awareness
        objective_focus = features_df['performance_score'].mean()
        team_coordination = features_df['kill_participation'].mean() * 10
        positioning_score = features_df['survivability'].mean() / 1000
        
        # Temporal Behavior
        early_game_impact = features_df['early_game_score'].mean()
        mid_game_impact = features_df['mid_game_score'].mean()
        late_game_impact = features_df['late_game_score'].mean()
        consistency_score = 10 - features_df['performance_score'].std()  # Lower std = higher consistency
        
        # Risk Behavior
        risk_taking_score = (features_df['kills_per_min'].mean() * 2 + 
                           features_df['deaths_per_min'].mean()) / 3
        safety_score = 10 - features_df['deaths_per_min'].mean() * 5
        decision_quality = features_df['kda_ratio'].mean()
        
        # Social Behavior (simplified)
        communication_score = features_df['assists_per_min'].mean() * 3
        leadership_score = features_df['mvp_score'].mean() * 10
        teamwork_score = features_df['kill_participation'].mean() * 10
        
        return BehaviorMetrics(
            avg_kda=avg_kda,
            kill_participation=kill_participation,
            death_rate=death_rate,
            aggression_score=max(0, min(10, aggression_score)),
            gold_efficiency=gold_efficiency,
            farming_priority=max(0, min(10, farming_priority)),
            resource_management=resource_management,
            map_awareness=max(0, min(10, map_awareness)),
            objective_focus=objective_focus,
            team_coordination=max(0, min(10, team_coordination)),
            positioning_score=max(0, min(10, positioning_score)),
            early_game_impact=early_game_impact,
            mid_game_impact=mid_game_impact,
            late_game_impact=late_game_impact,
            consistency_score=max(0, min(10, consistency_score)),
            risk_taking_score=max(0, min(10, risk_taking_score)),
            safety_score=max(0, min(10, safety_score)),
            decision_quality=decision_quality,
            communication_score=max(0, min(10, communication_score)),
            leadership_score=leadership_score,
            teamwork_score=teamwork_score
        )
    
    async def _classify_playstyle(self, metrics: BehaviorMetrics) -> Tuple[PlayStyle, Optional[PlayStyle]]:
        """Classify player's primary and secondary playstyles."""
        
        # Calculate playstyle scores
        playstyle_scores = {
            PlayStyle.AGGRESSIVE_CARRY: (
                metrics.aggression_score * 0.3 +
                metrics.avg_kda * 0.2 +
                metrics.risk_taking_score * 0.2 +
                metrics.early_game_impact * 0.3
            ),
            PlayStyle.PASSIVE_FARMER: (
                metrics.farming_priority * 0.3 +
                metrics.gold_efficiency * 0.2 +
                metrics.safety_score * 0.3 +
                (10 - metrics.aggression_score) * 0.2
            ),
            PlayStyle.ROAMING_SUPPORT: (
                metrics.map_awareness * 0.3 +
                metrics.team_coordination * 0.3 +
                metrics.communication_score * 0.2 +
                metrics.kill_participation * 0.2
            ),
            PlayStyle.OBJECTIVE_FOCUSED: (
                metrics.objective_focus * 0.3 +
                metrics.decision_quality * 0.2 +
                metrics.mid_game_impact * 0.3 +
                metrics.teamwork_score * 0.2
            ),
            PlayStyle.TEAM_FIGHTER: (
                metrics.team_coordination * 0.3 +
                metrics.kill_participation * 0.3 +
                metrics.mid_game_impact * 0.2 +
                metrics.communication_score * 0.2
            ),
            PlayStyle.SPLIT_PUSHER: (
                metrics.farming_priority * 0.3 +
                (10 - metrics.team_coordination) * 0.2 +
                metrics.late_game_impact * 0.3 +
                metrics.positioning_score * 0.2
            ),
            PlayStyle.DEFENSIVE_TANK: (
                metrics.safety_score * 0.3 +
                metrics.positioning_score * 0.3 +
                metrics.teamwork_score * 0.2 +
                (10 - metrics.aggression_score) * 0.2
            ),
            PlayStyle.BALANCED_PLAYER: (
                metrics.consistency_score * 0.4 +
                (metrics.early_game_impact + metrics.mid_game_impact + metrics.late_game_impact) / 3 * 0.3 +
                metrics.decision_quality * 0.3
            )
        }
        
        # Sort by score
        sorted_styles = sorted(playstyle_scores.items(), key=lambda x: x[1], reverse=True)
        
        primary_style = sorted_styles[0][0]
        
        # Secondary style if significantly different and above threshold
        secondary_style = None
        if len(sorted_styles) > 1:
            if sorted_styles[1][1] > 5.0 and sorted_styles[0][1] - sorted_styles[1][1] < 2.0:
                secondary_style = sorted_styles[1][0]
        
        return primary_style, secondary_style
    
    async def _determine_risk_profile(self, metrics: BehaviorMetrics) -> RiskProfile:
        """Determine player's risk-taking profile."""
        
        # Calculate risk score
        risk_score = (
            metrics.risk_taking_score * 0.4 +
            metrics.aggression_score * 0.3 +
            (10 - metrics.safety_score) * 0.2 +
            metrics.death_rate * 10 * 0.1
        )
        
        if risk_score >= 7.5:
            return RiskProfile.HIGH_RISK
        elif risk_score >= 5.0:
            if metrics.decision_quality > 3.0:
                return RiskProfile.CALCULATED_RISK
            else:
                return RiskProfile.MODERATE_RISK
        else:
            return RiskProfile.LOW_RISK
    
    async def _analyze_game_phase_preference(self, features_df: pd.DataFrame) -> GamePhasePreference:
        """Analyze player's game phase preferences."""
        
        early_avg = features_df['early_game_score'].mean()
        mid_avg = features_df['mid_game_score'].mean()
        late_avg = features_df['late_game_score'].mean()
        
        scores = {
            GamePhasePreference.EARLY_GAME: early_avg,
            GamePhasePreference.MID_GAME: mid_avg,
            GamePhasePreference.LATE_GAME: late_avg
        }
        
        # Check if performance is consistent across phases
        std_dev = np.std([early_avg, mid_avg, late_avg])
        if std_dev < 1.0:  # Low variation
            return GamePhasePreference.CONSISTENT
        
        # Return phase with highest score
        return max(scores, key=scores.get)
    
    async def _identify_strengths_weaknesses(self, metrics: BehaviorMetrics) -> Tuple[List[str], List[str], List[str]]:
        """Identify player strengths, weaknesses, and improvement areas."""
        
        # Convert metrics to dict for analysis
        metrics_dict = asdict(metrics)
        
        strengths = []
        weaknesses = []
        improvements = []
        
        # Define thresholds
        strong_threshold = 7.0
        weak_threshold = 4.0
        
        # Analyze each metric
        metric_descriptions = {
            'avg_kda': ('KDA Management', 'Focus on staying alive while contributing to kills'),
            'kill_participation': ('Team Fighting', 'Participate more in team fights and objectives'),
            'aggression_score': ('Aggressive Play', 'Balance aggression with safety'),
            'gold_efficiency': ('Economic Management', 'Improve farming and gold utilization'),
            'farming_priority': ('Farming Skills', 'Focus on last-hitting and jungle efficiency'),
            'map_awareness': ('Map Awareness', 'Pay more attention to minimap and enemy movements'),
            'objective_focus': ('Objective Play', 'Prioritize towers, dragons, and other objectives'),
            'team_coordination': ('Team Coordination', 'Improve communication and teamwork'),
            'positioning_score': ('Positioning', 'Work on safer positioning in team fights'),
            'early_game_impact': ('Early Game', 'Improve early game performance and impact'),
            'mid_game_impact': ('Mid Game', 'Focus on mid game team fights and objectives'),
            'late_game_impact': ('Late Game', 'Improve late game decision making'),
            'consistency_score': ('Consistency', 'Work on maintaining consistent performance'),
            'decision_quality': ('Decision Making', 'Improve strategic decision making'),
            'leadership_score': ('Leadership', 'Take more initiative in leading the team'),
            'teamwork_score': ('Teamwork', 'Focus on better team coordination')
        }
        
        for metric_name, value in metrics_dict.items():
            if metric_name in metric_descriptions:
                description, improvement_tip = metric_descriptions[metric_name]
                
                if value >= strong_threshold:
                    strengths.append(description)
                elif value <= weak_threshold:
                    weaknesses.append(description)
                    improvements.append(improvement_tip)
        
        # Ensure we have at least some insights
        if not strengths:
            strengths.append("Consistent Performance")
        if not weaknesses:
            weaknesses.append("Room for optimization in all areas")
        
        return strengths, weaknesses, improvements
    
    async def _analyze_performance_patterns(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance patterns and trends."""
        
        patterns = {}
        
        # Win rate analysis
        patterns['win_rate'] = features_df['match_result'].mean()
        patterns['recent_form'] = features_df['match_result'].tail(5).mean()
        
        # Performance consistency
        patterns['performance_consistency'] = 1 - (features_df['performance_score'].std() / 10)
        
        # KDA trends
        patterns['kda_trend'] = self._calculate_trend(features_df['kda_ratio'])
        patterns['avg_kda'] = features_df['kda_ratio'].mean()
        
        # Economic patterns
        patterns['gold_trend'] = self._calculate_trend(features_df['gold_per_min'])
        patterns['avg_gold_per_min'] = features_df['gold_per_min'].mean()
        
        # Damage patterns
        patterns['damage_trend'] = self._calculate_trend(features_df['damage_per_min'])
        patterns['avg_damage_per_min'] = features_df['damage_per_min'].mean()
        
        # Match duration preferences
        patterns['preferred_game_length'] = features_df['match_duration_min'].mean()
        patterns['short_game_performance'] = features_df[features_df['match_duration_min'] < 15]['performance_score'].mean()
        patterns['long_game_performance'] = features_df[features_df['match_duration_min'] > 25]['performance_score'].mean()
        
        return patterns
    
    async def _analyze_temporal_patterns(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal patterns in performance."""
        
        patterns = {}
        
        # Convert timestamps to datetime
        features_df['datetime'] = pd.to_datetime(features_df['timestamp'])
        features_df['hour'] = features_df['datetime'].dt.hour
        features_df['day_of_week'] = features_df['datetime'].dt.dayofweek
        
        # Hourly performance
        hourly_performance = features_df.groupby('hour')['performance_score'].mean()
        patterns['best_hour'] = hourly_performance.idxmax()
        patterns['worst_hour'] = hourly_performance.idxmin()
        patterns['hourly_variance'] = hourly_performance.std()
        
        # Daily performance
        daily_performance = features_df.groupby('day_of_week')['performance_score'].mean()
        patterns['best_day'] = daily_performance.idxmax()
        patterns['worst_day'] = daily_performance.idxmin()
        
        # Recent performance trend
        if len(features_df) > 10:
            recent_matches = features_df.tail(10)
            older_matches = features_df.head(10)
            patterns['performance_trend'] = recent_matches['performance_score'].mean() - older_matches['performance_score'].mean()
        
        return patterns
    
    async def _analyze_hero_preferences(self, match_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze hero preferences and performance."""
        
        hero_stats = {}
        
        for match in match_history:
            hero = match.get('hero', 'unknown')
            performance = match.get('performance_score', 5.0)
            
            if hero not in hero_stats:
                hero_stats[hero] = {'total_score': 0, 'matches': 0}
            
            hero_stats[hero]['total_score'] += performance
            hero_stats[hero]['matches'] += 1
        
        # Calculate average performance per hero
        hero_preferences = {}
        for hero, stats in hero_stats.items():
            if stats['matches'] >= 2:  # Only include heroes played multiple times
                hero_preferences[hero] = stats['total_score'] / stats['matches']
        
        # Sort by performance
        hero_preferences = dict(sorted(hero_preferences.items(), key=lambda x: x[1], reverse=True))
        
        return hero_preferences
    
    async def _calculate_confidence_scores(self, features_df: pd.DataFrame, 
                                         metrics: BehaviorMetrics) -> Tuple[float, float]:
        """Calculate profile confidence and data quality scores."""
        
        # Data quality based on sample size and completeness
        sample_size = len(features_df)
        data_quality = min(1.0, sample_size / 50)  # Full quality at 50+ matches
        
        # Check for data completeness
        completeness_score = 1.0 - features_df.isnull().sum().sum() / (features_df.shape[0] * features_df.shape[1])
        data_quality *= completeness_score
        
        # Profile confidence based on metric consistency
        metric_values = list(asdict(metrics).values())
        metric_variance = np.var([v for v in metric_values if isinstance(v, (int, float))])
        confidence = max(0.5, 1.0 - (metric_variance / 100))  # Normalize variance
        
        # Adjust confidence based on sample size
        if sample_size < 20:
            confidence *= 0.8
        elif sample_size < 10:
            confidence *= 0.6
        
        return confidence, data_quality
    
    def _calculate_trend(self, series: pd.Series) -> float:
        """Calculate trend direction for a time series."""
        if len(series) < 3:
            return 0.0
        
        # Simple linear trend calculation
        x = np.arange(len(series))
        slope = np.polyfit(x, series, 1)[0]
        return slope
    
    def _create_default_profile(self, player_id: str, sample_size: int) -> BehaviorProfile:
        """Create a default profile for insufficient data."""
        return BehaviorProfile(
            player_id=player_id,
            player_name=f'Player_{player_id}',
            primary_playstyle=PlayStyle.BALANCED_PLAYER,
            profile_confidence=0.3,
            data_quality_score=0.2,
            sample_size=sample_size,
            strengths=['Potential for growth'],
            weaknesses=['Insufficient data'],
            improvement_areas=['Play more matches for better analysis']
        )
    
    async def _save_behavior_profile(self, profile: BehaviorProfile):
        """Save behavior profile to disk."""
        profile_path = self.cache_dir / f"{profile.player_id}_behavior_profile.json"
        
        # Convert to dict
        profile_dict = asdict(profile)
        profile_dict['last_updated'] = profile.last_updated.isoformat()
        
        # Save to file
        with open(profile_path, 'w') as f:
            json.dump(profile_dict, f, indent=2)
        
        logger.debug(f"Behavior profile saved: {profile_path}")
    
    async def compare_players(self, player_profiles: List[BehaviorProfile]) -> Dict[str, Any]:
        """Compare multiple player behavioral profiles."""
        
        if len(player_profiles) < 2:
            return {"error": "Need at least 2 players for comparison"}
        
        comparison = {
            'players': [p.player_name for p in player_profiles],
            'playstyles': [p.primary_playstyle.value for p in player_profiles],
            'strengths_comparison': {},
            'metrics_comparison': {},
            'recommendations': []
        }
        
        # Compare key metrics
        metrics_to_compare = ['avg_kda', 'aggression_score', 'team_coordination', 'consistency_score']
        
        for metric in metrics_to_compare:
            values = []
            for profile in player_profiles:
                metric_value = getattr(profile.behavior_metrics, metric, 0)
                values.append(metric_value)
            
            comparison['metrics_comparison'][metric] = {
                'values': values,
                'best_player': player_profiles[values.index(max(values))].player_name,
                'average': sum(values) / len(values)
            }
        
        return comparison
    
    async def process(self, request: Dict[str, Any]) -> ServiceResult:
        """Process behavior analysis requests."""
        try:
            action = request.get('action', 'analyze_behavior')
            
            if action == 'analyze_behavior':
                player_id = request.get('player_id')
                match_history = request.get('match_history', [])
                force_refresh = request.get('force_refresh', False)
                
                profile = await self.analyze_player_behavior(
                    player_id, match_history, force_refresh
                )
                
                return ServiceResult(
                    success=True,
                    data=asdict(profile),
                    metadata={'action': 'analyze_behavior', 'player_id': player_id}
                )
                
            elif action == 'get_cached_profile':
                player_id = request.get('player_id')
                profile = self.behavior_profiles.get(player_id)
                
                if profile:
                    return ServiceResult(
                        success=True,
                        data=asdict(profile),
                        metadata={'action': 'get_cached_profile', 'cached': True}
                    )
                else:
                    return ServiceResult(
                        success=False,
                        error=f"No cached profile found for player: {player_id}"
                    )
                    
            elif action == 'compare_players':
                player_ids = request.get('player_ids', [])
                profiles = [self.behavior_profiles.get(pid) for pid in player_ids]
                profiles = [p for p in profiles if p is not None]
                
                comparison = await self.compare_players(profiles)
                
                return ServiceResult(
                    success=True,
                    data=comparison,
                    metadata={'action': 'compare_players', 'player_count': len(profiles)}
                )
                
            else:
                return ServiceResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            logger.error(f"Player behavior analyzer error: {str(e)}")
            return ServiceResult(
                success=False,
                error=str(e)
            )


# Global player behavior analyzer instance
_behavior_analyzer = None

def get_behavior_analyzer() -> PlayerBehaviorAnalyzer:
    """Get global behavior analyzer instance."""
    global _behavior_analyzer
    if _behavior_analyzer is None:
        _behavior_analyzer = PlayerBehaviorAnalyzer()
    return _behavior_analyzer
