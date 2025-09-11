"""
Achievement System - Comprehensive skill-based achievement tracking
==================================================================

Provides a complete achievement system with skill-based achievements,
progress tracking, leaderboards, and social recognition features.
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import numpy as np

from ..core.services.base_service import BaseService, ServiceResult

logger = logging.getLogger(__name__)


class AchievementType(Enum):
    """Types of achievements available."""
    PERFORMANCE = "performance"
    SKILL_MASTERY = "skill_mastery"
    CONSISTENCY = "consistency"
    IMPROVEMENT = "improvement"
    SOCIAL = "social"
    MILESTONE = "milestone"
    SPECIAL = "special"
    SEASONAL = "seasonal"


class AchievementTier(Enum):
    """Achievement tier/difficulty levels."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"
    LEGENDARY = "legendary"


class AchievementCategory(Enum):
    """Achievement categories for organization."""
    COMBAT = "combat"
    STRATEGY = "strategy"
    TEAMWORK = "teamwork"
    LEARNING = "learning"
    SOCIAL = "social"
    MASTERY = "mastery"
    SPECIAL_EVENTS = "special_events"


@dataclass
class Achievement:
    """Individual achievement definition."""
    # Basic Information
    achievement_id: str
    name: str
    description: str
    category: AchievementCategory
    type: AchievementType
    tier: AchievementTier
    
    # Requirements
    requirements: Dict[str, Any] = field(default_factory=dict)
    prerequisites: List[str] = field(default_factory=list)  # Required achievement IDs
    
    # Rewards
    xp_reward: int = 0
    badge_icon: str = ""
    title_reward: Optional[str] = None
    special_rewards: List[str] = field(default_factory=list)
    
    # Metadata
    is_hidden: bool = False  # Hidden until unlocked
    is_repeatable: bool = False
    max_completions: int = 1
    difficulty_score: float = 1.0
    
    # Tracking
    total_earned: int = 0
    first_earned_date: Optional[datetime] = None
    last_earned_date: Optional[datetime] = None
    
    # Conditions
    is_active: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class PlayerProgress:
    """Player's progress towards an achievement."""
    player_id: str
    achievement_id: str
    
    # Progress Tracking
    current_progress: Dict[str, float] = field(default_factory=dict)
    target_values: Dict[str, float] = field(default_factory=dict)
    progress_percentage: float = 0.0
    
    # Status
    is_completed: bool = False
    completion_date: Optional[datetime] = None
    completion_count: int = 0
    
    # Tracking
    first_progress_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Additional Data
    milestone_history: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""


@dataclass
class PlayerAchievementSummary:
    """Summary of player's achievement status."""
    player_id: str
    
    # Overall Statistics
    total_achievements: int = 0
    completed_achievements: int = 0
    completion_rate: float = 0.0
    total_xp_earned: int = 0
    
    # By Tier
    tier_breakdown: Dict[AchievementTier, int] = field(default_factory=dict)
    
    # By Category
    category_breakdown: Dict[AchievementCategory, int] = field(default_factory=dict)
    
    # Recent Activity
    recent_completions: List[str] = field(default_factory=list)
    active_progress: List[str] = field(default_factory=list)
    
    # Rankings
    global_rank: Optional[int] = None
    category_ranks: Dict[AchievementCategory, int] = field(default_factory=dict)
    
    # Special Recognition
    earned_titles: List[str] = field(default_factory=list)
    special_badges: List[str] = field(default_factory=list)
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)


class AchievementEngine(BaseService):
    """Comprehensive achievement system engine."""
    
    def __init__(self,
                 achievements_dir: str = "data/achievements",
                 progress_dir: str = "data/player_progress"):
        super().__init__()
        
        # Directory setup
        self.achievements_dir = Path(achievements_dir)
        self.progress_dir = Path(progress_dir)
        
        # Create directories
        for dir_path in [self.achievements_dir, self.progress_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Achievement storage
        self.achievements: Dict[str, Achievement] = {}
        self.player_progress: Dict[str, Dict[str, PlayerProgress]] = {}  # player_id -> achievement_id -> progress
        self.player_summaries: Dict[str, PlayerAchievementSummary] = {}
        
        # Configuration
        self.auto_check_interval = 300  # 5 minutes
        self.batch_size = 100
        
        # Initialize achievement definitions
        asyncio.create_task(self._initialize_achievements())
        
        logger.info("Achievement Engine initialized")
    
    async def _initialize_achievements(self):
        """Initialize achievement definitions."""
        # Load existing achievements or create default set
        await self._load_achievements()
        
        if not self.achievements:
            await self._create_default_achievements()
            await self._save_achievements()
    
    async def _create_default_achievements(self):
        """Create default achievement set for MLBB Coach AI."""
        
        # Performance Achievements
        performance_achievements = [
            Achievement(
                achievement_id="first_mvp",
                name="Rising Star",
                description="Earn your first MVP in a match",
                category=AchievementCategory.COMBAT,
                type=AchievementType.MILESTONE,
                tier=AchievementTier.BRONZE,
                requirements={"mvp_count": 1},
                xp_reward=100,
                badge_icon="🌟"
            ),
            Achievement(
                achievement_id="kda_master",
                name="KDA Master",
                description="Achieve a KDA of 5.0 or higher in a single match",
                category=AchievementCategory.COMBAT,
                type=AchievementType.PERFORMANCE,
                tier=AchievementTier.SILVER,
                requirements={"max_kda": 5.0},
                xp_reward=250,
                badge_icon="⚔️"
            ),
            Achievement(
                achievement_id="damage_dealer",
                name="Damage Dealer",
                description="Deal over 50,000 hero damage in a single match",
                category=AchievementCategory.COMBAT,
                type=AchievementType.PERFORMANCE,
                tier=AchievementTier.GOLD,
                requirements={"max_hero_damage": 50000},
                xp_reward=500,
                badge_icon="💥"
            ),
            Achievement(
                achievement_id="pentakill",
                name="Legendary Warrior",
                description="Achieve a pentakill in any match",
                category=AchievementCategory.COMBAT,
                type=AchievementType.SPECIAL,
                tier=AchievementTier.LEGENDARY,
                requirements={"pentakill_count": 1},
                xp_reward=2000,
                badge_icon="👑",
                title_reward="Legendary Warrior"
            )
        ]
        
        # Consistency Achievements
        consistency_achievements = [
            Achievement(
                achievement_id="win_streak_5",
                name="On Fire",
                description="Win 5 matches in a row",
                category=AchievementCategory.STRATEGY,
                type=AchievementType.CONSISTENCY,
                tier=AchievementTier.SILVER,
                requirements={"win_streak": 5},
                xp_reward=300,
                badge_icon="🔥"
            ),
            Achievement(
                achievement_id="consistent_performer",
                name="Consistent Performer",
                description="Maintain a performance score above 7.0 for 10 consecutive matches",
                category=AchievementCategory.STRATEGY,
                type=AchievementType.CONSISTENCY,
                tier=AchievementTier.GOLD,
                requirements={"consistent_performance": {"score": 7.0, "matches": 10}},
                xp_reward=750,
                badge_icon="📈"
            ),
            Achievement(
                achievement_id="monthly_warrior",
                name="Monthly Warrior",
                description="Play at least 100 matches in a single month",
                category=AchievementCategory.MASTERY,
                type=AchievementType.MILESTONE,
                tier=AchievementTier.PLATINUM,
                requirements={"monthly_matches": 100},
                xp_reward=1000,
                badge_icon="🗓️"
            )
        ]
        
        # Skill Mastery Achievements
        skill_achievements = [
            Achievement(
                achievement_id="hero_specialist",
                name="Hero Specialist",
                description="Play 50 matches with a single hero",
                category=AchievementCategory.MASTERY,
                type=AchievementType.SKILL_MASTERY,
                tier=AchievementTier.SILVER,
                requirements={"hero_matches": 50},
                xp_reward=400,
                badge_icon="🎯"
            ),
            Achievement(
                achievement_id="role_master",
                name="Role Master",
                description="Achieve 70%+ win rate with 20+ matches in any role",
                category=AchievementCategory.MASTERY,
                type=AchievementType.SKILL_MASTERY,
                tier=AchievementTier.GOLD,
                requirements={"role_mastery": {"win_rate": 0.7, "min_matches": 20}},
                xp_reward=800,
                badge_icon="🏆"
            ),
            Achievement(
                achievement_id="versatile_player",
                name="Versatile Player",
                description="Play all 5 roles with at least 10 matches each",
                category=AchievementCategory.MASTERY,
                type=AchievementType.SKILL_MASTERY,
                tier=AchievementTier.PLATINUM,
                requirements={"role_versatility": {"roles": 5, "min_matches_per_role": 10}},
                xp_reward=1200,
                badge_icon="🎭"
            )
        ]
        
        # Improvement Achievements
        improvement_achievements = [
            Achievement(
                achievement_id="comeback_king",
                name="Comeback King",
                description="Win a match after being behind by 5+ kills",
                category=AchievementCategory.STRATEGY,
                type=AchievementType.IMPROVEMENT,
                tier=AchievementTier.GOLD,
                requirements={"comeback_wins": 1},
                xp_reward=600,
                badge_icon="🔄"
            ),
            Achievement(
                achievement_id="improvement_streak",
                name="Rising Phoenix",
                description="Improve your average performance score by 2+ points over 20 matches",
                category=AchievementCategory.LEARNING,
                type=AchievementType.IMPROVEMENT,
                tier=AchievementTier.PLATINUM,
                requirements={"performance_improvement": {"increase": 2.0, "matches": 20}},
                xp_reward=1000,
                badge_icon="🔥"
            )
        ]
        
        # Social Achievements
        social_achievements = [
            Achievement(
                achievement_id="team_player",
                name="Team Player",
                description="Play 25 matches with friends",
                category=AchievementCategory.SOCIAL,
                type=AchievementType.SOCIAL,
                tier=AchievementTier.SILVER,
                requirements={"team_matches": 25},
                xp_reward=300,
                badge_icon="👥"
            ),
            Achievement(
                achievement_id="mentor",
                name="Mentor",
                description="Help 5 players improve their performance",
                category=AchievementCategory.SOCIAL,
                type=AchievementType.SOCIAL,
                tier=AchievementTier.GOLD,
                requirements={"mentorship_count": 5},
                xp_reward=750,
                badge_icon="🎓",
                title_reward="Mentor"
            ),
            Achievement(
                achievement_id="community_leader",
                name="Community Leader",
                description="Reach top 10 in any leaderboard",
                category=AchievementCategory.SOCIAL,
                type=AchievementType.SOCIAL,
                tier=AchievementTier.DIAMOND,
                requirements={"leaderboard_rank": 10},
                xp_reward=1500,
                badge_icon="👑",
                title_reward="Community Leader"
            )
        ]
        
        # Learning Achievements
        learning_achievements = [
            Achievement(
                achievement_id="first_analysis",
                name="Analytical Mind",
                description="Complete your first match analysis",
                category=AchievementCategory.LEARNING,
                type=AchievementType.MILESTONE,
                tier=AchievementTier.BRONZE,
                requirements={"analyses_completed": 1},
                xp_reward=50,
                badge_icon="🔍"
            ),
            Achievement(
                achievement_id="coaching_student",
                name="Coaching Student",
                description="Follow coaching recommendations for 10 matches",
                category=AchievementCategory.LEARNING,
                type=AchievementType.LEARNING,
                tier=AchievementTier.SILVER,
                requirements={"coaching_follows": 10},
                xp_reward=400,
                badge_icon="📚"
            ),
            Achievement(
                achievement_id="meta_aware",
                name="Meta Aware",
                description="Play current S-tier heroes in 15 matches",
                category=AchievementCategory.LEARNING,
                type=AchievementType.LEARNING,
                tier=AchievementTier.GOLD,
                requirements={"meta_hero_matches": 15},
                xp_reward=600,
                badge_icon="📊"
            )
        ]
        
        # Special/Seasonal Achievements
        special_achievements = [
            Achievement(
                achievement_id="early_adopter",
                name="Early Adopter",
                description="Join MLBB Coach AI in its first month",
                category=AchievementCategory.SPECIAL_EVENTS,
                type=AchievementType.SPECIAL,
                tier=AchievementTier.LEGENDARY,
                requirements={"early_adopter": True},
                xp_reward=1000,
                badge_icon="🚀",
                title_reward="Early Adopter",
                is_hidden=True
            ),
            Achievement(
                achievement_id="perfect_month",
                name="Perfect Month",
                description="Achieve 100% win rate with 20+ matches in a calendar month",
                category=AchievementCategory.SPECIAL_EVENTS,
                type=AchievementType.SPECIAL,
                tier=AchievementTier.LEGENDARY,
                requirements={"perfect_month": {"win_rate": 1.0, "min_matches": 20}},
                xp_reward=2500,
                badge_icon="💎",
                title_reward="Perfect Player"
            )
        ]
        
        # Combine all achievements
        all_achievements = (
            performance_achievements + consistency_achievements + 
            skill_achievements + improvement_achievements + 
            social_achievements + learning_achievements + special_achievements
        )
        
        # Store achievements
        for achievement in all_achievements:
            self.achievements[achievement.achievement_id] = achievement
        
        logger.info(f"Created {len(all_achievements)} default achievements")
    
    async def check_player_achievements(self, player_id: str, match_data: Dict[str, Any]) -> List[str]:
        """Check and update player achievements based on match data."""
        
        newly_earned = []
        
        # Ensure player progress exists
        if player_id not in self.player_progress:
            self.player_progress[player_id] = {}
        
        # Check each achievement
        for achievement_id, achievement in self.achievements.items():
            if not achievement.is_active:
                continue
            
            # Skip if prerequisites not met
            if not await self._check_prerequisites(player_id, achievement.prerequisites):
                continue
            
            # Get or create progress
            if achievement_id not in self.player_progress[player_id]:
                self.player_progress[player_id][achievement_id] = PlayerProgress(
                    player_id=player_id,
                    achievement_id=achievement_id,
                    target_values=achievement.requirements
                )
            
            progress = self.player_progress[player_id][achievement_id]
            
            # Skip if already completed and not repeatable
            if progress.is_completed and not achievement.is_repeatable:
                continue
            
            # Check if max completions reached
            if progress.completion_count >= achievement.max_completions:
                continue
            
            # Update progress based on match data
            updated = await self._update_achievement_progress(achievement, progress, match_data)
            
            if updated:
                progress.last_updated = datetime.now()
                
                # Check if achievement is now completed
                if await self._is_achievement_completed(achievement, progress):
                    await self._complete_achievement(player_id, achievement, progress)
                    newly_earned.append(achievement_id)
        
        # Update player summary
        if newly_earned:
            await self._update_player_summary(player_id)
        
        return newly_earned
    
    async def _check_prerequisites(self, player_id: str, prerequisites: List[str]) -> bool:
        """Check if player has completed prerequisite achievements."""
        if not prerequisites:
            return True
        
        player_progress = self.player_progress.get(player_id, {})
        
        for prereq_id in prerequisites:
            if prereq_id not in player_progress:
                return False
            if not player_progress[prereq_id].is_completed:
                return False
        
        return True
    
    async def _update_achievement_progress(self, achievement: Achievement, 
                                         progress: PlayerProgress, match_data: Dict[str, Any]) -> bool:
        """Update progress for a specific achievement based on match data."""
        
        updated = False
        requirements = achievement.requirements
        
        # Performance-based achievements
        if achievement.type == AchievementType.PERFORMANCE:
            if "mvp_count" in requirements:
                if match_data.get("mvp", False):
                    progress.current_progress["mvp_count"] = progress.current_progress.get("mvp_count", 0) + 1
                    updated = True
            
            if "max_kda" in requirements:
                current_kda = match_data.get("kda", 0)
                if current_kda > progress.current_progress.get("max_kda", 0):
                    progress.current_progress["max_kda"] = current_kda
                    updated = True
            
            if "max_hero_damage" in requirements:
                current_damage = match_data.get("hero_damage", 0)
                if current_damage > progress.current_progress.get("max_hero_damage", 0):
                    progress.current_progress["max_hero_damage"] = current_damage
                    updated = True
            
            if "pentakill_count" in requirements:
                if match_data.get("pentakill", False):
                    progress.current_progress["pentakill_count"] = progress.current_progress.get("pentakill_count", 0) + 1
                    updated = True
        
        # Consistency-based achievements
        elif achievement.type == AchievementType.CONSISTENCY:
            if "win_streak" in requirements:
                if match_data.get("result", "").lower() == "win":
                    progress.current_progress["current_streak"] = progress.current_progress.get("current_streak", 0) + 1
                    progress.current_progress["max_streak"] = max(
                        progress.current_progress.get("max_streak", 0),
                        progress.current_progress["current_streak"]
                    )
                else:
                    progress.current_progress["current_streak"] = 0
                updated = True
            
            if "consistent_performance" in requirements:
                performance_score = match_data.get("performance_score", 0)
                target_score = requirements["consistent_performance"]["score"]
                target_matches = requirements["consistent_performance"]["matches"]
                
                if "performance_history" not in progress.current_progress:
                    progress.current_progress["performance_history"] = []
                
                progress.current_progress["performance_history"].append(performance_score)
                
                # Keep only recent matches for streak calculation
                if len(progress.current_progress["performance_history"]) > target_matches:
                    progress.current_progress["performance_history"] = progress.current_progress["performance_history"][-target_matches:]
                
                # Check if current streak meets requirement
                recent_scores = progress.current_progress["performance_history"][-target_matches:]
                if len(recent_scores) == target_matches and all(score >= target_score for score in recent_scores):
                    progress.current_progress["consistent_streak"] = target_matches
                
                updated = True
            
            if "monthly_matches" in requirements:
                current_month = datetime.now().strftime("%Y-%m")
                if "monthly_data" not in progress.current_progress:
                    progress.current_progress["monthly_data"] = {}
                
                if current_month not in progress.current_progress["monthly_data"]:
                    progress.current_progress["monthly_data"][current_month] = 0
                
                progress.current_progress["monthly_data"][current_month] += 1
                updated = True
        
        # Skill Mastery achievements
        elif achievement.type == AchievementType.SKILL_MASTERY:
            if "hero_matches" in requirements:
                hero = match_data.get("hero", "unknown")
                if "hero_counts" not in progress.current_progress:
                    progress.current_progress["hero_counts"] = {}
                
                progress.current_progress["hero_counts"][hero] = progress.current_progress["hero_counts"].get(hero, 0) + 1
                progress.current_progress["max_hero_matches"] = max(progress.current_progress["hero_counts"].values())
                updated = True
            
            if "role_mastery" in requirements:
                role = match_data.get("role", "unknown")
                result = match_data.get("result", "").lower()
                
                if "role_stats" not in progress.current_progress:
                    progress.current_progress["role_stats"] = {}
                
                if role not in progress.current_progress["role_stats"]:
                    progress.current_progress["role_stats"][role] = {"matches": 0, "wins": 0}
                
                progress.current_progress["role_stats"][role]["matches"] += 1
                if result == "win":
                    progress.current_progress["role_stats"][role]["wins"] += 1
                
                # Calculate best role performance
                best_performance = 0
                for role_data in progress.current_progress["role_stats"].values():
                    if role_data["matches"] >= requirements["role_mastery"]["min_matches"]:
                        win_rate = role_data["wins"] / role_data["matches"]
                        if win_rate > best_performance:
                            best_performance = win_rate
                
                progress.current_progress["best_role_performance"] = best_performance
                updated = True
            
            if "role_versatility" in requirements:
                role = match_data.get("role", "unknown")
                if "role_matches" not in progress.current_progress:
                    progress.current_progress["role_matches"] = {}
                
                progress.current_progress["role_matches"][role] = progress.current_progress["role_matches"].get(role, 0) + 1
                
                # Count roles with minimum matches
                min_matches = requirements["role_versatility"]["min_matches_per_role"]
                qualified_roles = sum(1 for count in progress.current_progress["role_matches"].values() if count >= min_matches)
                progress.current_progress["qualified_roles"] = qualified_roles
                updated = True
        
        # Learning achievements
        elif achievement.type == AchievementType.LEARNING:
            if "analyses_completed" in requirements:
                if match_data.get("analysis_completed", False):
                    progress.current_progress["analyses_completed"] = progress.current_progress.get("analyses_completed", 0) + 1
                    updated = True
            
            if "coaching_follows" in requirements:
                if match_data.get("followed_coaching", False):
                    progress.current_progress["coaching_follows"] = progress.current_progress.get("coaching_follows", 0) + 1
                    updated = True
            
            if "meta_hero_matches" in requirements:
                hero = match_data.get("hero", "")
                hero_tier = match_data.get("hero_meta_tier", "")
                if hero_tier == "S":
                    progress.current_progress["meta_hero_matches"] = progress.current_progress.get("meta_hero_matches", 0) + 1
                    updated = True
        
        # Social achievements
        elif achievement.type == AchievementType.SOCIAL:
            if "team_matches" in requirements:
                if match_data.get("played_with_friends", False):
                    progress.current_progress["team_matches"] = progress.current_progress.get("team_matches", 0) + 1
                    updated = True
            
            if "mentorship_count" in requirements:
                if match_data.get("mentorship_provided", False):
                    progress.current_progress["mentorship_count"] = progress.current_progress.get("mentorship_count", 0) + 1
                    updated = True
        
        # Milestone achievements
        elif achievement.type == AchievementType.MILESTONE:
            # Handle match counting milestones
            progress.current_progress["total_matches"] = progress.current_progress.get("total_matches", 0) + 1
            updated = True
        
        # Update progress percentage
        if updated:
            progress.progress_percentage = await self._calculate_progress_percentage(achievement, progress)
        
        return updated
    
    async def _is_achievement_completed(self, achievement: Achievement, progress: PlayerProgress) -> bool:
        """Check if achievement requirements are met."""
        
        requirements = achievement.requirements
        current = progress.current_progress
        
        # Check each requirement
        for req_key, req_value in requirements.items():
            if req_key == "mvp_count":
                if current.get("mvp_count", 0) < req_value:
                    return False
            
            elif req_key == "max_kda":
                if current.get("max_kda", 0) < req_value:
                    return False
            
            elif req_key == "max_hero_damage":
                if current.get("max_hero_damage", 0) < req_value:
                    return False
            
            elif req_key == "pentakill_count":
                if current.get("pentakill_count", 0) < req_value:
                    return False
            
            elif req_key == "win_streak":
                if current.get("max_streak", 0) < req_value:
                    return False
            
            elif req_key == "consistent_performance":
                if current.get("consistent_streak", 0) < req_value["matches"]:
                    return False
            
            elif req_key == "monthly_matches":
                current_month = datetime.now().strftime("%Y-%m")
                monthly_data = current.get("monthly_data", {})
                if monthly_data.get(current_month, 0) < req_value:
                    return False
            
            elif req_key == "hero_matches":
                if current.get("max_hero_matches", 0) < req_value:
                    return False
            
            elif req_key == "role_mastery":
                if current.get("best_role_performance", 0) < req_value["win_rate"]:
                    return False
            
            elif req_key == "role_versatility":
                if current.get("qualified_roles", 0) < req_value["roles"]:
                    return False
            
            elif req_key == "analyses_completed":
                if current.get("analyses_completed", 0) < req_value:
                    return False
            
            elif req_key == "coaching_follows":
                if current.get("coaching_follows", 0) < req_value:
                    return False
            
            elif req_key == "meta_hero_matches":
                if current.get("meta_hero_matches", 0) < req_value:
                    return False
            
            elif req_key == "team_matches":
                if current.get("team_matches", 0) < req_value:
                    return False
            
            elif req_key == "mentorship_count":
                if current.get("mentorship_count", 0) < req_value:
                    return False
            
            elif req_key == "early_adopter":
                # Special handling for early adopter achievement
                if not current.get("early_adopter", False):
                    return False
        
        return True
    
    async def _complete_achievement(self, player_id: str, achievement: Achievement, progress: PlayerProgress):
        """Complete an achievement for a player."""
        
        progress.is_completed = True
        progress.completion_date = datetime.now()
        progress.completion_count += 1
        progress.progress_percentage = 100.0
        
        # Update achievement statistics
        achievement.total_earned += 1
        if achievement.first_earned_date is None:
            achievement.first_earned_date = progress.completion_date
        achievement.last_earned_date = progress.completion_date
        
        # Add to milestone history
        milestone = {
            "completion_date": progress.completion_date.isoformat(),
            "completion_count": progress.completion_count,
            "final_progress": dict(progress.current_progress)
        }
        progress.milestone_history.append(milestone)
        
        # Log achievement completion
        logger.info(f"Achievement completed: {achievement.name} by player {player_id}")
        
        # If repeatable, reset progress for next completion
        if achievement.is_repeatable and progress.completion_count < achievement.max_completions:
            progress.is_completed = False
            progress.current_progress = {}
            progress.progress_percentage = 0.0
    
    async def _calculate_progress_percentage(self, achievement: Achievement, progress: PlayerProgress) -> float:
        """Calculate progress percentage for an achievement."""
        
        requirements = achievement.requirements
        current = progress.current_progress
        
        if not requirements:
            return 0.0
        
        total_progress = 0.0
        requirement_count = 0
        
        for req_key, req_value in requirements.items():
            requirement_count += 1
            
            if req_key in ["mvp_count", "pentakill_count", "analyses_completed", "coaching_follows", 
                          "meta_hero_matches", "team_matches", "mentorship_count"]:
                current_value = current.get(req_key, 0)
                progress_pct = min(100.0, (current_value / req_value) * 100)
                total_progress += progress_pct
            
            elif req_key in ["max_kda", "max_hero_damage"]:
                current_value = current.get(req_key, 0)
                progress_pct = min(100.0, (current_value / req_value) * 100)
                total_progress += progress_pct
            
            elif req_key == "win_streak":
                current_streak = current.get("max_streak", 0)
                progress_pct = min(100.0, (current_streak / req_value) * 100)
                total_progress += progress_pct
            
            elif req_key == "consistent_performance":
                current_streak = current.get("consistent_streak", 0)
                target_matches = req_value["matches"]
                progress_pct = min(100.0, (current_streak / target_matches) * 100)
                total_progress += progress_pct
            
            elif req_key == "monthly_matches":
                current_month = datetime.now().strftime("%Y-%m")
                monthly_data = current.get("monthly_data", {})
                current_count = monthly_data.get(current_month, 0)
                progress_pct = min(100.0, (current_count / req_value) * 100)
                total_progress += progress_pct
            
            elif req_key == "hero_matches":
                current_max = current.get("max_hero_matches", 0)
                progress_pct = min(100.0, (current_max / req_value) * 100)
                total_progress += progress_pct
            
            elif req_key == "role_mastery":
                current_performance = current.get("best_role_performance", 0)
                target_performance = req_value["win_rate"]
                progress_pct = min(100.0, (current_performance / target_performance) * 100)
                total_progress += progress_pct
            
            elif req_key == "role_versatility":
                current_roles = current.get("qualified_roles", 0)
                target_roles = req_value["roles"]
                progress_pct = min(100.0, (current_roles / target_roles) * 100)
                total_progress += progress_pct
            
            else:
                # For boolean or special requirements
                total_progress += 100.0 if current.get(req_key, False) else 0.0
        
        return total_progress / max(1, requirement_count)
    
    async def _update_player_summary(self, player_id: str):
        """Update player achievement summary."""
        
        if player_id not in self.player_progress:
            return
        
        player_achievements = self.player_progress[player_id]
        
        # Initialize summary
        summary = PlayerAchievementSummary(player_id=player_id)
        
        # Count achievements by status
        summary.total_achievements = len(self.achievements)
        summary.completed_achievements = sum(1 for progress in player_achievements.values() if progress.is_completed)
        summary.completion_rate = (summary.completed_achievements / max(1, summary.total_achievements)) * 100
        
        # Calculate total XP earned
        summary.total_xp_earned = sum(
            self.achievements[aid].xp_reward * progress.completion_count
            for aid, progress in player_achievements.items()
            if progress.is_completed
        )
        
        # Breakdown by tier and category
        for tier in AchievementTier:
            summary.tier_breakdown[tier] = 0
        for category in AchievementCategory:
            summary.category_breakdown[category] = 0
        
        for achievement_id, progress in player_achievements.items():
            if progress.is_completed:
                achievement = self.achievements[achievement_id]
                summary.tier_breakdown[achievement.tier] += 1
                summary.category_breakdown[achievement.category] += 1
        
        # Recent completions (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        summary.recent_completions = [
            achievement_id for achievement_id, progress in player_achievements.items()
            if progress.is_completed and progress.completion_date and progress.completion_date >= week_ago
        ]
        
        # Active progress (achievements with >0% progress but not completed)
        summary.active_progress = [
            achievement_id for achievement_id, progress in player_achievements.items()
            if not progress.is_completed and progress.progress_percentage > 0
        ]
        
        # Collect earned titles and badges
        summary.earned_titles = [
            self.achievements[aid].title_reward
            for aid, progress in player_achievements.items()
            if progress.is_completed and self.achievements[aid].title_reward
        ]
        
        summary.special_badges = [
            self.achievements[aid].badge_icon
            for aid, progress in player_achievements.items()
            if progress.is_completed and self.achievements[aid].tier in [AchievementTier.DIAMOND, AchievementTier.LEGENDARY]
        ]
        
        # Store summary
        self.player_summaries[player_id] = summary
        
        # Save to disk
        await self._save_player_summary(player_id, summary)
    
    async def get_player_achievements(self, player_id: str) -> Dict[str, Any]:
        """Get comprehensive achievement data for a player."""
        
        if player_id not in self.player_progress:
            # Initialize empty progress
            self.player_progress[player_id] = {}
            await self._update_player_summary(player_id)
        
        player_achievements = self.player_progress[player_id]
        summary = self.player_summaries.get(player_id)
        
        # Organize achievements by category and status
        achievements_data = {
            "summary": asdict(summary) if summary else {},
            "completed": [],
            "in_progress": [],
            "available": [],
            "locked": []
        }
        
        for achievement_id, achievement in self.achievements.items():
            achievement_data = {
                "achievement": asdict(achievement),
                "progress": None
            }
            
            # Get progress if exists
            if achievement_id in player_achievements:
                progress = player_achievements[achievement_id]
                achievement_data["progress"] = asdict(progress)
                
                if progress.is_completed:
                    achievements_data["completed"].append(achievement_data)
                elif progress.progress_percentage > 0:
                    achievements_data["in_progress"].append(achievement_data)
                else:
                    achievements_data["available"].append(achievement_data)
            else:
                # Check if prerequisites are met
                prereqs_met = await self._check_prerequisites(player_id, achievement.prerequisites)
                
                if prereqs_met and not achievement.is_hidden:
                    achievements_data["available"].append(achievement_data)
                else:
                    achievements_data["locked"].append(achievement_data)
        
        return achievements_data
    
    async def get_leaderboards(self, category: Optional[AchievementCategory] = None, 
                             limit: int = 100) -> Dict[str, Any]:
        """Get achievement leaderboards."""
        
        leaderboards = {
            "total_achievements": [],
            "total_xp": [],
            "completion_rate": [],
            "recent_achievements": []
        }
        
        # Collect player data
        player_data = []
        for player_id, summary in self.player_summaries.items():
            if category:
                # Filter by category if specified
                category_count = summary.category_breakdown.get(category, 0)
                player_data.append({
                    "player_id": player_id,
                    "total_achievements": category_count,
                    "total_xp": summary.total_xp_earned,
                    "completion_rate": summary.completion_rate,
                    "recent_count": len(summary.recent_completions)
                })
            else:
                player_data.append({
                    "player_id": player_id,
                    "total_achievements": summary.completed_achievements,
                    "total_xp": summary.total_xp_earned,
                    "completion_rate": summary.completion_rate,
                    "recent_count": len(summary.recent_completions)
                })
        
        # Sort and create leaderboards
        leaderboards["total_achievements"] = sorted(
            player_data, key=lambda x: x["total_achievements"], reverse=True
        )[:limit]
        
        leaderboards["total_xp"] = sorted(
            player_data, key=lambda x: x["total_xp"], reverse=True
        )[:limit]
        
        leaderboards["completion_rate"] = sorted(
            player_data, key=lambda x: x["completion_rate"], reverse=True
        )[:limit]
        
        leaderboards["recent_achievements"] = sorted(
            player_data, key=lambda x: x["recent_count"], reverse=True
        )[:limit]
        
        return leaderboards
    
    async def _load_achievements(self):
        """Load achievements from disk."""
        achievements_file = self.achievements_dir / "achievements.json"
        
        if achievements_file.exists():
            try:
                with open(achievements_file, 'r') as f:
                    data = json.load(f)
                
                for achievement_data in data:
                    achievement = Achievement(**achievement_data)
                    self.achievements[achievement.achievement_id] = achievement
                
                logger.info(f"Loaded {len(self.achievements)} achievements")
            except Exception as e:
                logger.error(f"Failed to load achievements: {e}")
    
    async def _save_achievements(self):
        """Save achievements to disk."""
        achievements_file = self.achievements_dir / "achievements.json"
        
        try:
            achievements_data = []
            for achievement in self.achievements.values():
                data = asdict(achievement)
                # Handle datetime serialization
                if achievement.first_earned_date:
                    data['first_earned_date'] = achievement.first_earned_date.isoformat()
                if achievement.last_earned_date:
                    data['last_earned_date'] = achievement.last_earned_date.isoformat()
                achievements_data.append(data)
            
            with open(achievements_file, 'w') as f:
                json.dump(achievements_data, f, indent=2)
            
            logger.info(f"Saved {len(achievements_data)} achievements")
        except Exception as e:
            logger.error(f"Failed to save achievements: {e}")
    
    async def _save_player_summary(self, player_id: str, summary: PlayerAchievementSummary):
        """Save player summary to disk."""
        summary_file = self.progress_dir / f"{player_id}_summary.json"
        
        try:
            data = asdict(summary)
            data['last_updated'] = summary.last_updated.isoformat()
            
            with open(summary_file, 'w') as f:
                json.dump(data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save player summary: {e}")
    
    async def process(self, request: Dict[str, Any]) -> ServiceResult:
        """Process achievement system requests."""
        try:
            action = request.get('action', 'get_player_achievements')
            
            if action == 'check_achievements':
                player_id = request.get('player_id')
                match_data = request.get('match_data', {})
                
                newly_earned = await self.check_player_achievements(player_id, match_data)
                
                return ServiceResult(
                    success=True,
                    data={'newly_earned': newly_earned},
                    metadata={'action': 'check_achievements', 'player_id': player_id}
                )
                
            elif action == 'get_player_achievements':
                player_id = request.get('player_id')
                achievements_data = await self.get_player_achievements(player_id)
                
                return ServiceResult(
                    success=True,
                    data=achievements_data,
                    metadata={'action': 'get_player_achievements', 'player_id': player_id}
                )
                
            elif action == 'get_leaderboards':
                category = request.get('category')
                if category:
                    category = AchievementCategory(category)
                limit = request.get('limit', 100)
                
                leaderboards = await self.get_leaderboards(category, limit)
                
                return ServiceResult(
                    success=True,
                    data=leaderboards,
                    metadata={'action': 'get_leaderboards', 'category': category}
                )
                
            else:
                return ServiceResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            logger.error(f"Achievement engine error: {str(e)}")
            return ServiceResult(
                success=False,
                error=str(e)
            )


# Global achievement engine instance
_achievement_engine = None

def get_achievement_engine() -> AchievementEngine:
    """Get global achievement engine instance."""
    global _achievement_engine
    if _achievement_engine is None:
        _achievement_engine = AchievementEngine()
    return _achievement_engine
