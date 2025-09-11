"""
Meta Game Tracker - Advanced meta analysis and trend tracking
============================================================

Tracks meta game trends, hero popularity, win rates, and strategic shifts
to provide insights into the evolving competitive landscape.
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
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

from ..core.services.base_service import BaseService, ServiceResult

logger = logging.getLogger(__name__)


class MetaTrend(Enum):
    """Meta game trend directions."""
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    EMERGING = "emerging"
    DECLINING = "declining"


class MetaTier(Enum):
    """Meta tier classifications."""
    S_TIER = "s_tier"
    A_TIER = "a_tier"
    B_TIER = "b_tier"
    C_TIER = "c_tier"
    D_TIER = "d_tier"


class GamePhase(Enum):
    """Game phase classifications."""
    EARLY_GAME = "early_game"
    MID_GAME = "mid_game"
    LATE_GAME = "late_game"
    ALL_PHASES = "all_phases"


@dataclass
class HeroMetaData:
    """Meta data for a specific hero."""
    hero_name: str
    
    # Popularity Metrics
    pick_rate: float = 0.0
    ban_rate: float = 0.0
    presence_rate: float = 0.0  # pick_rate + ban_rate
    
    # Performance Metrics
    win_rate: float = 0.0
    avg_kda: float = 0.0
    avg_damage: float = 0.0
    avg_gold: float = 0.0
    
    # Meta Classification
    meta_tier: MetaTier = MetaTier.C_TIER
    trend: MetaTrend = MetaTrend.STABLE
    trend_strength: float = 0.0  # -1.0 to 1.0
    
    # Contextual Performance
    phase_performance: Dict[GamePhase, float] = field(default_factory=dict)
    role_performance: Dict[str, float] = field(default_factory=dict)
    counter_picks: List[str] = field(default_factory=list)
    synergy_picks: List[str] = field(default_factory=list)
    
    # Temporal Data
    popularity_history: List[Tuple[datetime, float]] = field(default_factory=list)
    winrate_history: List[Tuple[datetime, float]] = field(default_factory=list)
    
    # Sample Information
    total_matches: int = 0
    sample_period_days: int = 7
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class MetaSnapshot:
    """Snapshot of the current meta state."""
    snapshot_date: datetime
    
    # Hero Rankings
    tier_list: Dict[MetaTier, List[str]] = field(default_factory=dict)
    most_popular: List[str] = field(default_factory=list)
    highest_winrate: List[str] = field(default_factory=list)
    most_banned: List[str] = field(default_factory=list)
    
    # Trend Analysis
    rising_heroes: List[str] = field(default_factory=list)
    falling_heroes: List[str] = field(default_factory=list)
    emerging_picks: List[str] = field(default_factory=list)
    
    # Strategic Insights
    dominant_strategies: List[str] = field(default_factory=list)
    phase_preferences: Dict[GamePhase, List[str]] = field(default_factory=dict)
    role_balance: Dict[str, float] = field(default_factory=dict)
    
    # Meta Health Metrics
    diversity_index: float = 0.0  # Shannon diversity index
    balance_score: float = 0.0    # How balanced the meta is
    volatility_score: float = 0.0 # How much the meta is changing
    
    # Version Information
    game_version: str = "current"
    patch_notes: List[str] = field(default_factory=list)


@dataclass
class MetaGameInsights:
    """Comprehensive meta game insights."""
    # Current State
    current_snapshot: MetaSnapshot
    
    # Historical Comparison
    previous_snapshot: Optional[MetaSnapshot] = None
    meta_evolution: Dict[str, Any] = field(default_factory=dict)
    
    # Predictions
    predicted_trends: Dict[str, MetaTrend] = field(default_factory=dict)
    upcoming_changes: List[str] = field(default_factory=list)
    
    # Recommendations
    player_recommendations: Dict[str, List[str]] = field(default_factory=dict)
    ban_suggestions: List[str] = field(default_factory=list)
    pick_suggestions: List[str] = field(default_factory=list)
    
    # Analysis Metadata
    analysis_confidence: float = 0.0
    data_quality: float = 0.0
    sample_size: int = 0
    analysis_date: datetime = field(default_factory=datetime.now)


class MetaGameTracker(BaseService):
    """Advanced meta game tracking and analysis system."""
    
    def __init__(self,
                 data_dir: str = "data/meta_tracking",
                 cache_dir: str = "cache/meta_analysis"):
        super().__init__()
        
        # Directory setup
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        
        # Create directories
        for dir_path in [self.data_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Meta data storage
        self.hero_meta_data: Dict[str, HeroMetaData] = {}
        self.meta_snapshots: List[MetaSnapshot] = []
        self.match_database: List[Dict[str, Any]] = []
        
        # Analysis configuration
        self.analysis_window_days = 7
        self.min_matches_for_analysis = 100
        self.trend_sensitivity = 0.05
        
        # Hero database
        self.hero_database = self._initialize_hero_database()
        
        logger.info("Meta Game Tracker initialized")
    
    def _initialize_hero_database(self) -> Dict[str, Dict[str, Any]]:
        """Initialize hero database with basic information."""
        # Simplified hero database for MLBB
        heroes = {
            # Assassins
            'Lancelot': {'role': 'Assassin', 'difficulty': 'Hard', 'type': 'Physical'},
            'Gusion': {'role': 'Assassin', 'difficulty': 'Hard', 'type': 'Magic'},
            'Ling': {'role': 'Assassin', 'difficulty': 'Hard', 'type': 'Physical'},
            'Hayabusa': {'role': 'Assassin', 'difficulty': 'Medium', 'type': 'Physical'},
            
            # Fighters
            'Chou': {'role': 'Fighter', 'difficulty': 'Hard', 'type': 'Physical'},
            'Paquito': {'role': 'Fighter', 'difficulty': 'Hard', 'type': 'Physical'},
            'Yu Zhong': {'role': 'Fighter', 'difficulty': 'Medium', 'type': 'Physical'},
            'Phoveus': {'role': 'Fighter', 'difficulty': 'Medium', 'type': 'Magic'},
            
            # Mages
            'Kagura': {'role': 'Mage', 'difficulty': 'Hard', 'type': 'Magic'},
            'Pharsa': {'role': 'Mage', 'difficulty': 'Medium', 'type': 'Magic'},
            'Valentina': {'role': 'Mage', 'difficulty': 'Hard', 'type': 'Magic'},
            'Yve': {'role': 'Mage', 'difficulty': 'Medium', 'type': 'Magic'},
            
            # Marksmen
            'Wanwan': {'role': 'Marksman', 'difficulty': 'Hard', 'type': 'Physical'},
            'Brody': {'role': 'Marksman', 'difficulty': 'Medium', 'type': 'Physical'},
            'Beatrix': {'role': 'Marksman', 'difficulty': 'Hard', 'type': 'Physical'},
            'Clint': {'role': 'Marksman', 'difficulty': 'Medium', 'type': 'Physical'},
            
            # Support
            'Estes': {'role': 'Support', 'difficulty': 'Easy', 'type': 'Magic'},
            'Rafaela': {'role': 'Support', 'difficulty': 'Easy', 'type': 'Magic'},
            'Mathilda': {'role': 'Support', 'difficulty': 'Medium', 'type': 'Magic'},
            'Floryn': {'role': 'Support', 'difficulty': 'Easy', 'type': 'Magic'},
            
            # Tanks
            'Tigreal': {'role': 'Tank', 'difficulty': 'Easy', 'type': 'Physical'},
            'Franco': {'role': 'Tank', 'difficulty': 'Medium', 'type': 'Physical'},
            'Khufra': {'role': 'Tank', 'difficulty': 'Medium', 'type': 'Physical'},
            'Grock': {'role': 'Tank', 'difficulty': 'Medium', 'type': 'Physical'},
        }
        
        return heroes
    
    async def analyze_meta_trends(self, 
                                 match_data: List[Dict[str, Any]],
                                 analysis_period_days: int = 7) -> MetaGameInsights:
        """Analyze meta game trends from match data."""
        
        logger.info(f"Analyzing meta trends from {len(match_data)} matches")
        
        # Filter recent matches
        cutoff_date = datetime.now() - timedelta(days=analysis_period_days)
        recent_matches = [
            match for match in match_data 
            if datetime.fromisoformat(match.get('timestamp', datetime.now().isoformat())) >= cutoff_date
        ]
        
        if len(recent_matches) < self.min_matches_for_analysis:
            logger.warning(f"Insufficient recent data: {len(recent_matches)} matches")
            return self._create_default_insights()
        
        # Update match database
        self.match_database.extend(recent_matches)
        
        # Calculate hero statistics
        await self._calculate_hero_statistics(recent_matches)
        
        # Classify meta tiers
        await self._classify_meta_tiers()
        
        # Analyze trends
        await self._analyze_trends()
        
        # Create meta snapshot
        current_snapshot = await self._create_meta_snapshot()
        
        # Generate insights
        insights = await self._generate_meta_insights(current_snapshot)
        
        # Cache results
        await self._save_meta_analysis(insights)
        
        logger.info("Meta trend analysis completed")
        return insights
    
    async def _calculate_hero_statistics(self, matches: List[Dict[str, Any]]):
        """Calculate comprehensive hero statistics."""
        
        # Initialize statistics tracking
        hero_stats = defaultdict(lambda: {
            'picks': 0, 'bans': 0, 'wins': 0, 'losses': 0,
            'total_kda': 0, 'total_damage': 0, 'total_gold': 0,
            'phase_performance': defaultdict(list),
            'role_matches': defaultdict(int)
        })
        
        total_matches = len(matches)
        
        # Process each match
        for match in matches:
            # Extract match information
            match_result = match.get('result', 'loss').lower()
            match_duration = match.get('match_duration', 20)  # minutes
            
            # Determine game phase based on duration
            if match_duration < 15:
                game_phase = GamePhase.EARLY_GAME
            elif match_duration < 25:
                game_phase = GamePhase.MID_GAME
            else:
                game_phase = GamePhase.LATE_GAME
            
            # Process hero data
            hero = match.get('hero', 'Unknown')
            if hero in self.hero_database:
                stats = hero_stats[hero]
                
                # Count pick
                stats['picks'] += 1
                
                # Count win/loss
                if match_result == 'win':
                    stats['wins'] += 1
                else:
                    stats['losses'] += 1
                
                # Accumulate performance metrics
                kda = self._calculate_kda(match)
                stats['total_kda'] += kda
                stats['total_damage'] += match.get('hero_damage', 0)
                stats['total_gold'] += match.get('gold', 0)
                
                # Phase performance
                performance_score = match.get('performance_score', 5.0)
                stats['phase_performance'][game_phase].append(performance_score)
                
                # Role tracking
                role = self.hero_database[hero]['role']
                stats['role_matches'][role] += 1
            
            # Process bans (simplified - assume some heroes are banned)
            # In real implementation, this would come from draft data
            banned_heroes = match.get('banned_heroes', [])
            for banned_hero in banned_heroes:
                if banned_hero in self.hero_database:
                    hero_stats[banned_hero]['bans'] += 1
        
        # Calculate final statistics for each hero
        for hero, stats in hero_stats.items():
            if stats['picks'] > 0:
                # Create or update hero meta data
                if hero not in self.hero_meta_data:
                    self.hero_meta_data[hero] = HeroMetaData(hero_name=hero)
                
                hero_meta = self.hero_meta_data[hero]
                
                # Basic rates
                hero_meta.pick_rate = stats['picks'] / total_matches
                hero_meta.ban_rate = stats['bans'] / total_matches
                hero_meta.presence_rate = hero_meta.pick_rate + hero_meta.ban_rate
                
                # Performance metrics
                total_games = stats['wins'] + stats['losses']
                if total_games > 0:
                    hero_meta.win_rate = stats['wins'] / total_games
                    hero_meta.avg_kda = stats['total_kda'] / total_games
                    hero_meta.avg_damage = stats['total_damage'] / total_games
                    hero_meta.avg_gold = stats['total_gold'] / total_games
                
                # Phase performance
                for phase, scores in stats['phase_performance'].items():
                    if scores:
                        hero_meta.phase_performance[phase] = sum(scores) / len(scores)
                
                # Role performance
                for role, matches in stats['role_matches'].items():
                    if matches > 0:
                        hero_meta.role_performance[role] = matches / stats['picks']
                
                # Update metadata
                hero_meta.total_matches = total_games
                hero_meta.last_updated = datetime.now()
                
                logger.debug(f"Updated stats for {hero}: {hero_meta.pick_rate:.2%} pick rate, {hero_meta.win_rate:.2%} win rate")
    
    def _calculate_kda(self, match: Dict[str, Any]) -> float:
        """Calculate KDA ratio from match data."""
        kills = match.get('kills', 0)
        deaths = max(1, match.get('deaths', 1))  # Avoid division by zero
        assists = match.get('assists', 0)
        return (kills + assists) / deaths
    
    async def _classify_meta_tiers(self):
        """Classify heroes into meta tiers."""
        
        # Calculate composite scores for tier classification
        hero_scores = []
        
        for hero, meta_data in self.hero_meta_data.items():
            if meta_data.total_matches >= 5:  # Minimum sample size
                # Composite score based on multiple factors
                score = (
                    meta_data.win_rate * 0.4 +           # Win rate (40%)
                    meta_data.pick_rate * 0.3 +          # Pick rate (30%)
                    meta_data.ban_rate * 0.2 +           # Ban rate (20%)
                    (meta_data.avg_kda / 5.0) * 0.1      # KDA normalized (10%)
                )
                
                hero_scores.append((hero, score, meta_data))
        
        # Sort by score
        hero_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Assign tiers based on percentiles
        total_heroes = len(hero_scores)
        if total_heroes > 0:
            # S-Tier: Top 10%
            s_tier_count = max(1, total_heroes // 10)
            # A-Tier: Next 20%
            a_tier_count = max(1, total_heroes // 5)
            # B-Tier: Next 40%
            b_tier_count = max(1, total_heroes * 2 // 5)
            # C-Tier: Next 25%
            c_tier_count = max(1, total_heroes // 4)
            
            # Assign tiers
            for i, (hero, score, meta_data) in enumerate(hero_scores):
                if i < s_tier_count:
                    meta_data.meta_tier = MetaTier.S_TIER
                elif i < s_tier_count + a_tier_count:
                    meta_data.meta_tier = MetaTier.A_TIER
                elif i < s_tier_count + a_tier_count + b_tier_count:
                    meta_data.meta_tier = MetaTier.B_TIER
                elif i < s_tier_count + a_tier_count + b_tier_count + c_tier_count:
                    meta_data.meta_tier = MetaTier.C_TIER
                else:
                    meta_data.meta_tier = MetaTier.D_TIER
                
                logger.debug(f"Classified {hero} as {meta_data.meta_tier.value} (score: {score:.3f})")
    
    async def _analyze_trends(self):
        """Analyze popularity and performance trends."""
        
        for hero, meta_data in self.hero_meta_data.items():
            # Simple trend analysis based on recent vs historical data
            # In a real implementation, this would use more sophisticated time series analysis
            
            current_pick_rate = meta_data.pick_rate
            current_win_rate = meta_data.win_rate
            
            # Simulate historical data for trend calculation
            historical_pick_rate = current_pick_rate * (1 + np.random.normal(0, 0.1))
            historical_win_rate = current_win_rate * (1 + np.random.normal(0, 0.05))
            
            # Calculate trend strength
            pick_rate_change = (current_pick_rate - historical_pick_rate) / max(0.01, historical_pick_rate)
            win_rate_change = (current_win_rate - historical_win_rate) / max(0.01, historical_win_rate)
            
            # Combined trend strength
            trend_strength = (pick_rate_change * 0.6 + win_rate_change * 0.4)
            meta_data.trend_strength = trend_strength
            
            # Classify trend
            if abs(trend_strength) < self.trend_sensitivity:
                meta_data.trend = MetaTrend.STABLE
            elif trend_strength > 0.1:
                meta_data.trend = MetaTrend.RISING
            elif trend_strength > 0.05:
                meta_data.trend = MetaTrend.EMERGING
            elif trend_strength < -0.1:
                meta_data.trend = MetaTrend.FALLING
            elif trend_strength < -0.05:
                meta_data.trend = MetaTrend.DECLINING
            else:
                meta_data.trend = MetaTrend.STABLE
            
            logger.debug(f"{hero} trend: {meta_data.trend.value} (strength: {trend_strength:.3f})")
    
    async def _create_meta_snapshot(self) -> MetaSnapshot:
        """Create a snapshot of the current meta state."""
        
        snapshot = MetaSnapshot(
            snapshot_date=datetime.now(),
            game_version="current"
        )
        
        # Organize heroes by tier
        for tier in MetaTier:
            snapshot.tier_list[tier] = []
        
        # Lists for various rankings
        popular_heroes = []
        high_winrate_heroes = []
        banned_heroes = []
        rising_heroes = []
        falling_heroes = []
        emerging_heroes = []
        
        # Process each hero
        for hero, meta_data in self.hero_meta_data.items():
            # Add to tier list
            snapshot.tier_list[meta_data.meta_tier].append(hero)
            
            # Add to various rankings
            popular_heroes.append((hero, meta_data.pick_rate))
            high_winrate_heroes.append((hero, meta_data.win_rate))
            banned_heroes.append((hero, meta_data.ban_rate))
            
            # Trend-based lists
            if meta_data.trend == MetaTrend.RISING:
                rising_heroes.append((hero, meta_data.trend_strength))
            elif meta_data.trend == MetaTrend.FALLING:
                falling_heroes.append((hero, meta_data.trend_strength))
            elif meta_data.trend == MetaTrend.EMERGING:
                emerging_heroes.append((hero, meta_data.trend_strength))
        
        # Sort and take top entries
        snapshot.most_popular = [h[0] for h in sorted(popular_heroes, key=lambda x: x[1], reverse=True)[:10]]
        snapshot.highest_winrate = [h[0] for h in sorted(high_winrate_heroes, key=lambda x: x[1], reverse=True)[:10]]
        snapshot.most_banned = [h[0] for h in sorted(banned_heroes, key=lambda x: x[1], reverse=True)[:10]]
        
        snapshot.rising_heroes = [h[0] for h in sorted(rising_heroes, key=lambda x: x[1], reverse=True)[:5]]
        snapshot.falling_heroes = [h[0] for h in sorted(falling_heroes, key=lambda x: abs(x[1]), reverse=True)[:5]]
        snapshot.emerging_picks = [h[0] for h in sorted(emerging_heroes, key=lambda x: x[1], reverse=True)[:5]]
        
        # Calculate meta health metrics
        snapshot.diversity_index = self._calculate_diversity_index()
        snapshot.balance_score = self._calculate_balance_score()
        snapshot.volatility_score = self._calculate_volatility_score()
        
        # Analyze role balance
        role_counts = defaultdict(int)
        role_performance = defaultdict(list)
        
        for hero, meta_data in self.hero_meta_data.items():
            if hero in self.hero_database:
                role = self.hero_database[hero]['role']
                role_counts[role] += 1
                role_performance[role].append(meta_data.win_rate)
        
        for role, performances in role_performance.items():
            if performances:
                snapshot.role_balance[role] = sum(performances) / len(performances)
        
        # Identify dominant strategies
        snapshot.dominant_strategies = await self._identify_dominant_strategies()
        
        # Phase preferences
        for phase in GamePhase:
            phase_heroes = []
            for hero, meta_data in self.hero_meta_data.items():
                phase_performance = meta_data.phase_performance.get(phase, 0)
                if phase_performance > 6.0:  # Above average performance
                    phase_heroes.append((hero, phase_performance))
            
            snapshot.phase_preferences[phase] = [h[0] for h in sorted(phase_heroes, key=lambda x: x[1], reverse=True)[:5]]
        
        return snapshot
    
    def _calculate_diversity_index(self) -> float:
        """Calculate Shannon diversity index for meta diversity."""
        pick_rates = [meta_data.pick_rate for meta_data in self.hero_meta_data.values() if meta_data.pick_rate > 0]
        
        if not pick_rates:
            return 0.0
        
        # Normalize pick rates
        total_picks = sum(pick_rates)
        if total_picks == 0:
            return 0.0
        
        normalized_rates = [rate / total_picks for rate in pick_rates]
        
        # Calculate Shannon diversity
        diversity = -sum(p * np.log(p) for p in normalized_rates if p > 0)
        
        # Normalize to 0-1 scale
        max_diversity = np.log(len(normalized_rates))
        return diversity / max_diversity if max_diversity > 0 else 0.0
    
    def _calculate_balance_score(self) -> float:
        """Calculate how balanced the meta is."""
        win_rates = [meta_data.win_rate for meta_data in self.hero_meta_data.values() if meta_data.total_matches >= 5]
        
        if len(win_rates) < 2:
            return 0.5  # Neutral score
        
        # Calculate standard deviation of win rates
        win_rate_std = np.std(win_rates)
        
        # Convert to balance score (lower std = higher balance)
        # Perfect balance would be std = 0, very imbalanced might be std = 0.2
        balance_score = max(0, 1 - (win_rate_std / 0.2))
        
        return min(1.0, balance_score)
    
    def _calculate_volatility_score(self) -> float:
        """Calculate how volatile/changing the meta is."""
        trend_strengths = [abs(meta_data.trend_strength) for meta_data in self.hero_meta_data.values()]
        
        if not trend_strengths:
            return 0.0
        
        # Average absolute trend strength indicates volatility
        avg_volatility = sum(trend_strengths) / len(trend_strengths)
        
        # Normalize to 0-1 scale (assuming max volatility of 0.5)
        return min(1.0, avg_volatility / 0.5)
    
    async def _identify_dominant_strategies(self) -> List[str]:
        """Identify dominant strategic patterns in the meta."""
        strategies = []
        
        # Analyze hero compositions and patterns
        # This is simplified - real implementation would analyze team compositions
        
        # Check for early game dominance
        early_game_heroes = [
            hero for hero, meta_data in self.hero_meta_data.items()
            if meta_data.phase_performance.get(GamePhase.EARLY_GAME, 0) > 7.0 and meta_data.pick_rate > 0.1
        ]
        
        if len(early_game_heroes) >= 3:
            strategies.append("Early Game Aggression")
        
        # Check for late game scaling
        late_game_heroes = [
            hero for hero, meta_data in self.hero_meta_data.items()
            if meta_data.phase_performance.get(GamePhase.LATE_GAME, 0) > 7.0 and meta_data.pick_rate > 0.1
        ]
        
        if len(late_game_heroes) >= 3:
            strategies.append("Late Game Scaling")
        
        # Check for high mobility meta
        mobility_heroes = ['Lancelot', 'Ling', 'Wanwan', 'Kagura']  # High mobility heroes
        popular_mobility = [
            hero for hero in mobility_heroes
            if hero in self.hero_meta_data and self.hero_meta_data[hero].pick_rate > 0.15
        ]
        
        if len(popular_mobility) >= 2:
            strategies.append("High Mobility Meta")
        
        # Check for tank/support dominance
        tank_support_heroes = [
            hero for hero in self.hero_database
            if self.hero_database[hero]['role'] in ['Tank', 'Support'] and
            hero in self.hero_meta_data and self.hero_meta_data[hero].pick_rate > 0.1
        ]
        
        if len(tank_support_heroes) >= 4:
            strategies.append("Team Fight Focused")
        
        return strategies[:5]  # Return top 5 strategies
    
    async def _generate_meta_insights(self, snapshot: MetaSnapshot) -> MetaGameInsights:
        """Generate comprehensive meta game insights."""
        
        insights = MetaGameInsights(
            current_snapshot=snapshot,
            analysis_date=datetime.now()
        )
        
        # Compare with previous snapshot if available
        if self.meta_snapshots:
            insights.previous_snapshot = self.meta_snapshots[-1]
            insights.meta_evolution = await self._analyze_meta_evolution(
                insights.previous_snapshot, snapshot
            )
        
        # Generate predictions
        insights.predicted_trends = await self._predict_future_trends()
        
        # Generate recommendations
        insights.player_recommendations = await self._generate_player_recommendations()
        insights.ban_suggestions = snapshot.most_popular[:5]  # Ban popular heroes
        insights.pick_suggestions = [
            hero for hero in snapshot.rising_heroes + snapshot.emerging_picks
            if hero not in snapshot.most_banned
        ][:5]
        
        # Calculate confidence metrics
        insights.analysis_confidence = self._calculate_analysis_confidence()
        insights.data_quality = self._calculate_data_quality()
        insights.sample_size = sum(meta_data.total_matches for meta_data in self.hero_meta_data.values())
        
        # Store snapshot
        self.meta_snapshots.append(snapshot)
        
        return insights
    
    async def _analyze_meta_evolution(self, previous: MetaSnapshot, current: MetaSnapshot) -> Dict[str, Any]:
        """Analyze how the meta has evolved between snapshots."""
        
        evolution = {
            'tier_changes': {},
            'popularity_changes': {},
            'new_emerging_heroes': [],
            'fallen_heroes': [],
            'stability_score': 0.0
        }
        
        # Analyze tier changes
        prev_tiers = {hero: tier for tier, heroes in previous.tier_list.items() for hero in heroes}
        curr_tiers = {hero: tier for tier, heroes in current.tier_list.items() for hero in heroes}
        
        for hero in set(prev_tiers.keys()) | set(curr_tiers.keys()):
            prev_tier = prev_tiers.get(hero)
            curr_tier = curr_tiers.get(hero)
            
            if prev_tier != curr_tier:
                evolution['tier_changes'][hero] = {
                    'from': prev_tier.value if prev_tier else 'unranked',
                    'to': curr_tier.value if curr_tier else 'unranked'
                }
        
        # Analyze popularity changes
        prev_popular = set(previous.most_popular[:10])
        curr_popular = set(current.most_popular[:10])
        
        evolution['new_emerging_heroes'] = list(curr_popular - prev_popular)
        evolution['fallen_heroes'] = list(prev_popular - curr_popular)
        
        # Calculate stability score
        tier_stability = 1 - (len(evolution['tier_changes']) / max(1, len(prev_tiers)))
        popularity_stability = len(prev_popular & curr_popular) / max(1, len(prev_popular | curr_popular))
        
        evolution['stability_score'] = (tier_stability + popularity_stability) / 2
        
        return evolution
    
    async def _predict_future_trends(self) -> Dict[str, MetaTrend]:
        """Predict future meta trends based on current data."""
        predictions = {}
        
        for hero, meta_data in self.hero_meta_data.items():
            # Simple prediction based on current trend strength
            current_trend = meta_data.trend
            trend_strength = meta_data.trend_strength
            
            # Predict future trend based on momentum
            if current_trend == MetaTrend.RISING and trend_strength > 0.1:
                predictions[hero] = MetaTrend.RISING
            elif current_trend == MetaTrend.FALLING and trend_strength < -0.1:
                predictions[hero] = MetaTrend.FALLING
            elif current_trend == MetaTrend.EMERGING and trend_strength > 0.05:
                predictions[hero] = MetaTrend.RISING
            elif current_trend == MetaTrend.DECLINING and trend_strength < -0.05:
                predictions[hero] = MetaTrend.FALLING
            else:
                predictions[hero] = MetaTrend.STABLE
        
        return predictions
    
    async def _generate_player_recommendations(self) -> Dict[str, List[str]]:
        """Generate role-specific recommendations for players."""
        recommendations = {}
        
        # Group heroes by role
        role_heroes = defaultdict(list)
        for hero, meta_data in self.hero_meta_data.items():
            if hero in self.hero_database:
                role = self.hero_database[hero]['role']
                role_heroes[role].append((hero, meta_data))
        
        # Generate recommendations for each role
        for role, heroes in role_heroes.items():
            # Sort by composite score (win rate + pick rate)
            heroes.sort(key=lambda x: x[1].win_rate * 0.6 + x[1].pick_rate * 0.4, reverse=True)
            
            role_recommendations = []
            
            # Top performing heroes
            for hero, meta_data in heroes[:3]:
                if meta_data.win_rate > 0.52 and meta_data.total_matches >= 5:
                    role_recommendations.append(f"Strong pick: {hero} ({meta_data.win_rate:.1%} WR)")
            
            # Rising heroes
            rising_in_role = [h for h, m in heroes if m.trend in [MetaTrend.RISING, MetaTrend.EMERGING]]
            for hero, meta_data in rising_in_role[:2]:
                role_recommendations.append(f"Trending up: {hero} ({meta_data.trend.value})")
            
            recommendations[role] = role_recommendations
        
        return recommendations
    
    def _calculate_analysis_confidence(self) -> float:
        """Calculate confidence in the meta analysis."""
        # Base confidence on sample sizes and data quality
        total_matches = sum(meta_data.total_matches for meta_data in self.hero_meta_data.values())
        hero_count = len(self.hero_meta_data)
        
        # Confidence increases with more data
        sample_confidence = min(1.0, total_matches / 1000)  # Full confidence at 1000+ matches
        coverage_confidence = min(1.0, hero_count / 20)      # Full confidence with 20+ heroes
        
        return (sample_confidence + coverage_confidence) / 2
    
    def _calculate_data_quality(self) -> float:
        """Calculate data quality score."""
        # Quality based on match distribution and recency
        if not self.hero_meta_data:
            return 0.0
        
        # Check for balanced sample sizes
        match_counts = [meta_data.total_matches for meta_data in self.hero_meta_data.values()]
        if not match_counts:
            return 0.0
        
        # Quality decreases with high variance in sample sizes
        mean_matches = np.mean(match_counts)
        std_matches = np.std(match_counts)
        
        balance_quality = 1 - min(1.0, std_matches / max(1, mean_matches))
        
        # Quality based on recency
        recent_updates = sum(
            1 for meta_data in self.hero_meta_data.values()
            if datetime.now() - meta_data.last_updated < timedelta(days=1)
        )
        recency_quality = recent_updates / len(self.hero_meta_data)
        
        return (balance_quality + recency_quality) / 2
    
    def _create_default_insights(self) -> MetaGameInsights:
        """Create default insights when insufficient data."""
        default_snapshot = MetaSnapshot(
            snapshot_date=datetime.now(),
            diversity_index=0.5,
            balance_score=0.5,
            volatility_score=0.2
        )
        
        return MetaGameInsights(
            current_snapshot=default_snapshot,
            analysis_confidence=0.1,
            data_quality=0.1,
            sample_size=0
        )
    
    async def _save_meta_analysis(self, insights: MetaGameInsights):
        """Save meta analysis results."""
        analysis_path = self.cache_dir / f"meta_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert to dict
        insights_dict = asdict(insights)
        
        # Handle datetime serialization
        insights_dict['analysis_date'] = insights.analysis_date.isoformat()
        insights_dict['current_snapshot']['snapshot_date'] = insights.current_snapshot.snapshot_date.isoformat()
        
        if insights.previous_snapshot:
            insights_dict['previous_snapshot']['snapshot_date'] = insights.previous_snapshot.snapshot_date.isoformat()
        
        # Save to file
        with open(analysis_path, 'w') as f:
            json.dump(insights_dict, f, indent=2)
        
        logger.info(f"Meta analysis saved: {analysis_path}")
    
    async def get_hero_meta_data(self, hero_name: str) -> Optional[HeroMetaData]:
        """Get meta data for a specific hero."""
        return self.hero_meta_data.get(hero_name)
    
    async def get_current_tier_list(self) -> Dict[MetaTier, List[str]]:
        """Get current tier list."""
        if not self.meta_snapshots:
            return {}
        
        return self.meta_snapshots[-1].tier_list
    
    async def compare_heroes(self, hero_names: List[str]) -> Dict[str, Any]:
        """Compare multiple heroes in the current meta."""
        comparison = {
            'heroes': hero_names,
            'comparison_date': datetime.now().isoformat(),
            'metrics_comparison': {},
            'recommendations': []
        }
        
        # Get meta data for heroes
        hero_data = {}
        for hero in hero_names:
            if hero in self.hero_meta_data:
                hero_data[hero] = self.hero_meta_data[hero]
        
        if not hero_data:
            return comparison
        
        # Compare key metrics
        metrics_to_compare = ['pick_rate', 'ban_rate', 'win_rate', 'avg_kda']
        
        for metric in metrics_to_compare:
            values = []
            for hero in hero_names:
                if hero in hero_data:
                    value = getattr(hero_data[hero], metric, 0)
                    values.append(value)
                else:
                    values.append(0)
            
            comparison['metrics_comparison'][metric] = {
                'values': values,
                'best_hero': hero_names[values.index(max(values))] if values else None,
                'average': sum(values) / len(values) if values else 0
            }
        
        # Generate recommendations
        for hero, meta_data in hero_data.items():
            if meta_data.win_rate > 0.55:
                comparison['recommendations'].append(f"{hero}: Strong meta pick with {meta_data.win_rate:.1%} win rate")
            elif meta_data.trend == MetaTrend.RISING:
                comparison['recommendations'].append(f"{hero}: Rising in popularity, consider learning")
            elif meta_data.ban_rate > 0.3:
                comparison['recommendations'].append(f"{hero}: Highly banned, have backup picks ready")
        
        return comparison
    
    async def process(self, request: Dict[str, Any]) -> ServiceResult:
        """Process meta game tracking requests."""
        try:
            action = request.get('action', 'analyze_meta')
            
            if action == 'analyze_meta':
                match_data = request.get('match_data', [])
                analysis_period = request.get('analysis_period_days', 7)
                
                insights = await self.analyze_meta_trends(match_data, analysis_period)
                
                return ServiceResult(
                    success=True,
                    data=asdict(insights),
                    metadata={'action': 'analyze_meta', 'sample_size': insights.sample_size}
                )
                
            elif action == 'get_hero_data':
                hero_name = request.get('hero_name')
                hero_data = await self.get_hero_meta_data(hero_name)
                
                if hero_data:
                    return ServiceResult(
                        success=True,
                        data=asdict(hero_data),
                        metadata={'action': 'get_hero_data', 'hero': hero_name}
                    )
                else:
                    return ServiceResult(
                        success=False,
                        error=f"No meta data found for hero: {hero_name}"
                    )
                    
            elif action == 'get_tier_list':
                tier_list = await self.get_current_tier_list()
                
                return ServiceResult(
                    success=True,
                    data={tier.value: heroes for tier, heroes in tier_list.items()},
                    metadata={'action': 'get_tier_list'}
                )
                
            elif action == 'compare_heroes':
                hero_names = request.get('hero_names', [])
                comparison = await self.compare_heroes(hero_names)
                
                return ServiceResult(
                    success=True,
                    data=comparison,
                    metadata={'action': 'compare_heroes', 'hero_count': len(hero_names)}
                )
                
            else:
                return ServiceResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            logger.error(f"Meta game tracker error: {str(e)}")
            return ServiceResult(
                success=False,
                error=str(e)
            )


# Global meta game tracker instance
_meta_tracker = None

def get_meta_tracker() -> MetaGameTracker:
    """Get global meta game tracker instance."""
    global _meta_tracker
    if _meta_tracker is None:
        _meta_tracker = MetaGameTracker()
    return _meta_tracker
