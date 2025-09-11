"""
Personalized Learning Paths - Adaptive learning system for skill development
==========================================================================

Provides personalized learning paths with role-specific improvement tracks,
adaptive difficulty progression, and intelligent coaching recommendations.
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
from ..analytics import get_behavior_analyzer

logger = logging.getLogger(__name__)


class SkillLevel(Enum):
    """Player skill levels."""
    BEGINNER = "beginner"
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"


class LearningPathType(Enum):
    """Types of learning paths."""
    ROLE_MASTERY = "role_mastery"
    HERO_SPECIALIZATION = "hero_specialization"
    SKILL_IMPROVEMENT = "skill_improvement"
    META_ADAPTATION = "meta_adaptation"
    TEAM_COORDINATION = "team_coordination"
    STRATEGIC_THINKING = "strategic_thinking"


class ModuleType(Enum):
    """Types of learning modules."""
    THEORETICAL = "theoretical"
    PRACTICAL = "practical"
    ANALYSIS = "analysis"
    CHALLENGE = "challenge"
    ASSESSMENT = "assessment"


class DifficultyLevel(Enum):
    """Difficulty levels for learning modules."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class LearningModule:
    """Individual learning module within a path."""
    # Basic Information
    module_id: str
    name: str
    description: str
    type: ModuleType
    difficulty: DifficultyLevel
    
    # Content
    objectives: List[str] = field(default_factory=list)
    content: Dict[str, Any] = field(default_factory=dict)
    resources: List[str] = field(default_factory=list)
    
    # Requirements
    prerequisites: List[str] = field(default_factory=list)
    estimated_duration: int = 30  # minutes
    
    # Assessment
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    practice_requirements: Dict[str, int] = field(default_factory=dict)
    
    # Rewards
    xp_reward: int = 50
    skill_points: Dict[str, int] = field(default_factory=dict)
    
    # Metadata
    is_mandatory: bool = True
    is_repeatable: bool = False
    tags: List[str] = field(default_factory=list)
    
    # Tracking
    completion_count: int = 0
    average_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class LearningPath:
    """Complete learning path for skill development."""
    # Basic Information
    path_id: str
    name: str
    description: str
    path_type: LearningPathType
    target_role: Optional[str] = None
    target_hero: Optional[str] = None
    
    # Structure
    modules: List[str] = field(default_factory=list)  # Module IDs in order
    total_modules: int = 0
    estimated_duration: int = 0  # Total minutes
    
    # Requirements
    min_skill_level: SkillLevel = SkillLevel.BEGINNER
    max_skill_level: SkillLevel = SkillLevel.MASTER
    prerequisites: List[str] = field(default_factory=list)
    
    # Rewards
    completion_rewards: Dict[str, Any] = field(default_factory=dict)
    milestone_rewards: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    
    # Adaptive Features
    adaptive_difficulty: bool = True
    personalization_enabled: bool = True
    
    # Metadata
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    is_active: bool = True
    
    # Statistics
    enrollment_count: int = 0
    completion_count: int = 0
    average_rating: float = 0.0
    success_rate: float = 0.0
    
    # Tracking
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class PlayerProgress:
    """Player's progress through a learning path."""
    player_id: str
    path_id: str
    
    # Progress Tracking
    enrolled_date: datetime = field(default_factory=datetime.now)
    current_module: int = 0
    completed_modules: Set[str] = field(default_factory=set)
    
    # Performance
    overall_score: float = 0.0
    module_scores: Dict[str, float] = field(default_factory=dict)
    skill_improvements: Dict[str, float] = field(default_factory=dict)
    
    # Status
    is_active: bool = True
    is_completed: bool = False
    completion_date: Optional[datetime] = None
    
    # Adaptive Learning
    current_difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    learning_pace: str = "normal"  # slow, normal, fast
    preferred_learning_style: str = "balanced"  # visual, practical, analytical
    
    # Personalization
    weak_areas: List[str] = field(default_factory=list)
    strong_areas: List[str] = field(default_factory=list)
    recommended_focus: List[str] = field(default_factory=list)
    
    # Engagement
    study_streak: int = 0
    total_study_time: int = 0  # minutes
    last_activity: datetime = field(default_factory=datetime.now)
    
    # Feedback
    module_feedback: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    path_rating: Optional[float] = None
    completion_feedback: str = ""


@dataclass
class PersonalizedRecommendation:
    """Personalized learning recommendation for a player."""
    player_id: str
    
    # Recommendation Details
    recommendation_type: str
    priority: str  # high, medium, low
    title: str
    description: str
    
    # Action Items
    suggested_paths: List[str] = field(default_factory=list)
    suggested_modules: List[str] = field(default_factory=list)
    practice_recommendations: List[str] = field(default_factory=list)
    
    # Reasoning
    analysis_basis: Dict[str, Any] = field(default_factory=dict)
    improvement_potential: float = 0.0
    confidence_score: float = 0.0
    
    # Timing
    created_date: datetime = field(default_factory=datetime.now)
    expires_date: Optional[datetime] = None
    
    # Status
    is_accepted: bool = False
    is_dismissed: bool = False
    acceptance_date: Optional[datetime] = None


class LearningPathManager(BaseService):
    """Manages personalized learning paths and adaptive progression."""
    
    def __init__(self,
                 paths_dir: str = "data/learning_paths",
                 progress_dir: str = "data/learning_progress"):
        super().__init__()
        
        # Directory setup
        self.paths_dir = Path(paths_dir)
        self.progress_dir = Path(progress_dir)
        
        # Create directories
        for dir_path in [self.paths_dir, self.progress_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Storage
        self.learning_paths: Dict[str, LearningPath] = {}
        self.learning_modules: Dict[str, LearningModule] = {}
        self.player_progress: Dict[str, Dict[str, PlayerProgress]] = {}  # player_id -> path_id -> progress
        self.recommendations: Dict[str, List[PersonalizedRecommendation]] = {}  # player_id -> recommendations
        
        # Configuration
        self.adaptive_threshold = 0.7  # Threshold for difficulty adjustment
        self.recommendation_refresh_hours = 24
        
        # Initialize learning content
        asyncio.create_task(self._initialize_learning_content())
        
        logger.info("Learning Path Manager initialized")
    
    async def _initialize_learning_content(self):
        """Initialize learning paths and modules."""
        await self._load_learning_content()
        
        if not self.learning_paths:
            await self._create_default_learning_content()
            await self._save_learning_content()
    
    async def _create_default_learning_content(self):
        """Create default learning paths and modules."""
        
        # Create learning modules first
        await self._create_default_modules()
        
        # Create learning paths
        await self._create_default_paths()
    
    async def _create_default_modules(self):
        """Create default learning modules."""
        
        # Basic Combat Modules
        combat_modules = [
            LearningModule(
                module_id="combat_basics",
                name="Combat Fundamentals",
                description="Learn the basics of MLBB combat mechanics",
                type=ModuleType.THEORETICAL,
                difficulty=DifficultyLevel.EASY,
                objectives=[
                    "Understand damage types and calculations",
                    "Learn about crowd control effects",
                    "Master basic positioning concepts"
                ],
                content={
                    "theory": "Combat mechanics overview",
                    "examples": ["Physical vs Magic damage", "CC types and counters"],
                    "tips": ["Stay behind minions", "Watch enemy cooldowns"]
                },
                success_criteria={"quiz_score": 80, "understanding_check": True},
                practice_requirements={"matches_played": 5},
                xp_reward=100,
                skill_points={"combat": 2, "positioning": 1}
            ),
            LearningModule(
                module_id="advanced_positioning",
                name="Advanced Positioning",
                description="Master advanced positioning techniques for different roles",
                type=ModuleType.PRACTICAL,
                difficulty=DifficultyLevel.MEDIUM,
                objectives=[
                    "Learn role-specific positioning",
                    "Understand team fight positioning",
                    "Master map awareness positioning"
                ],
                prerequisites=["combat_basics"],
                success_criteria={"positioning_score": 7.0, "deaths_per_match": 4},
                practice_requirements={"matches_played": 10, "good_positioning_matches": 7},
                xp_reward=200,
                skill_points={"positioning": 3, "awareness": 2}
            ),
            LearningModule(
                module_id="team_fight_mastery",
                name="Team Fight Mastery",
                description="Excel in team fight situations and coordination",
                type=ModuleType.PRACTICAL,
                difficulty=DifficultyLevel.HARD,
                objectives=[
                    "Master team fight initiation and timing",
                    "Learn target prioritization",
                    "Coordinate with team effectively"
                ],
                prerequisites=["advanced_positioning"],
                success_criteria={"team_fight_participation": 0.8, "kda_in_teamfights": 2.5},
                practice_requirements={"team_fights_won": 15, "good_coordination_matches": 10},
                xp_reward=300,
                skill_points={"teamwork": 4, "combat": 2}
            )
        ]
        
        # Strategic Thinking Modules
        strategy_modules = [
            LearningModule(
                module_id="map_awareness",
                name="Map Awareness Fundamentals",
                description="Develop superior map awareness and game sense",
                type=ModuleType.ANALYSIS,
                difficulty=DifficultyLevel.EASY,
                objectives=[
                    "Learn to read the minimap effectively",
                    "Understand vision control importance",
                    "Predict enemy movements"
                ],
                success_criteria={"map_awareness_score": 7.0, "wards_placed": 3},
                practice_requirements={"matches_with_good_awareness": 8},
                xp_reward=150,
                skill_points={"awareness": 3, "strategy": 1}
            ),
            LearningModule(
                module_id="objective_control",
                name="Objective Control",
                description="Master the art of objective timing and control",
                type=ModuleType.STRATEGIC,
                difficulty=DifficultyLevel.MEDIUM,
                objectives=[
                    "Learn objective priority and timing",
                    "Understand risk vs reward for objectives",
                    "Coordinate team for objective control"
                ],
                prerequisites=["map_awareness"],
                success_criteria={"objective_participation": 0.7, "objective_success_rate": 0.6},
                practice_requirements={"objectives_secured": 20},
                xp_reward=250,
                skill_points={"strategy": 3, "teamwork": 2}
            )
        ]
        
        # Role-Specific Modules
        role_modules = []
        
        # Tank Modules
        tank_modules = [
            LearningModule(
                module_id="tank_fundamentals",
                name="Tank Role Fundamentals",
                description="Master the tank role and protection mechanics",
                type=ModuleType.PRACTICAL,
                difficulty=DifficultyLevel.MEDIUM,
                objectives=[
                    "Learn tank positioning and engagement",
                    "Master crowd control timing",
                    "Protect carry teammates effectively"
                ],
                success_criteria={"damage_taken_ratio": 0.3, "cc_effectiveness": 0.6},
                practice_requirements={"tank_matches": 15, "successful_engages": 10},
                xp_reward=200,
                skill_points={"tanking": 4, "teamwork": 2},
                tags=["tank", "role_specific"]
            ),
            LearningModule(
                module_id="advanced_tanking",
                name="Advanced Tanking Techniques",
                description="Advanced tank strategies and team coordination",
                type=ModuleType.EXPERT,
                difficulty=DifficultyLevel.HARD,
                objectives=[
                    "Master advanced engagement techniques",
                    "Learn peel and disengage strategies",
                    "Coordinate team fights as tank"
                ],
                prerequisites=["tank_fundamentals", "team_fight_mastery"],
                success_criteria={"team_fight_win_rate": 0.7, "peel_effectiveness": 0.8},
                practice_requirements={"advanced_tank_matches": 20},
                xp_reward=400,
                skill_points={"tanking": 5, "leadership": 3},
                tags=["tank", "advanced"]
            )
        ]
        
        # Marksman Modules
        marksman_modules = [
            LearningModule(
                module_id="adc_fundamentals",
                name="Marksman Fundamentals",
                description="Master the marksman role and damage dealing",
                type=ModuleType.PRACTICAL,
                difficulty=DifficultyLevel.MEDIUM,
                objectives=[
                    "Learn optimal farming patterns",
                    "Master positioning for maximum DPS",
                    "Understand power spikes and itemization"
                ],
                success_criteria={"damage_per_minute": 1000, "farming_efficiency": 0.8},
                practice_requirements={"marksman_matches": 15, "high_damage_matches": 10},
                xp_reward=200,
                skill_points={"damage": 4, "farming": 2},
                tags=["marksman", "role_specific"]
            )
        ]
        
        # Combine all modules
        all_modules = combat_modules + strategy_modules + tank_modules + marksman_modules
        
        # Store modules
        for module in all_modules:
            self.learning_modules[module.module_id] = module
        
        logger.info(f"Created {len(all_modules)} default learning modules")
    
    async def _create_default_paths(self):
        """Create default learning paths."""
        
        # Beginner Path
        beginner_path = LearningPath(
            path_id="beginner_fundamentals",
            name="MLBB Fundamentals",
            description="Complete beginner's guide to Mobile Legends: Bang Bang",
            path_type=LearningPathType.SKILL_IMPROVEMENT,
            modules=["combat_basics", "map_awareness", "advanced_positioning"],
            total_modules=3,
            estimated_duration=180,  # 3 hours
            min_skill_level=SkillLevel.BEGINNER,
            max_skill_level=SkillLevel.NOVICE,
            completion_rewards={
                "xp": 500,
                "title": "MLBB Graduate",
                "badge": "🎓"
            },
            milestone_rewards={
                1: {"xp": 100, "message": "Great start!"},
                2: {"xp": 200, "message": "You're improving!"},
                3: {"xp": 300, "message": "Fundamentals mastered!"}
            },
            category="fundamentals",
            tags=["beginner", "essential"]
        )
        
        # Tank Mastery Path
        tank_path = LearningPath(
            path_id="tank_mastery",
            name="Tank Role Mastery",
            description="Become an expert tank player",
            path_type=LearningPathType.ROLE_MASTERY,
            target_role="Tank",
            modules=["combat_basics", "tank_fundamentals", "team_fight_mastery", "advanced_tanking"],
            total_modules=4,
            estimated_duration=300,  # 5 hours
            min_skill_level=SkillLevel.NOVICE,
            max_skill_level=SkillLevel.EXPERT,
            prerequisites=["beginner_fundamentals"],
            completion_rewards={
                "xp": 1000,
                "title": "Tank Master",
                "badge": "🛡️",
                "special_recognition": "Tank Specialist"
            },
            category="role_mastery",
            tags=["tank", "advanced", "mastery"]
        )
        
        # Strategic Thinking Path
        strategy_path = LearningPath(
            path_id="strategic_mastery",
            name="Strategic Thinking Mastery",
            description="Develop advanced strategic thinking and game sense",
            path_type=LearningPathType.STRATEGIC_THINKING,
            modules=["map_awareness", "objective_control", "team_fight_mastery"],
            total_modules=3,
            estimated_duration=240,  # 4 hours
            min_skill_level=SkillLevel.INTERMEDIATE,
            max_skill_level=SkillLevel.MASTER,
            completion_rewards={
                "xp": 800,
                "title": "Strategic Mastermind",
                "badge": "🧠"
            },
            category="strategy",
            tags=["strategy", "advanced", "thinking"]
        )
        
        # Meta Adaptation Path
        meta_path = LearningPath(
            path_id="meta_adaptation",
            name="Meta Game Adaptation",
            description="Learn to adapt to changing meta and stay competitive",
            path_type=LearningPathType.META_ADAPTATION,
            modules=["map_awareness", "objective_control"],  # Will be expanded with meta-specific modules
            total_modules=2,
            estimated_duration=120,  # 2 hours
            min_skill_level=SkillLevel.INTERMEDIATE,
            adaptive_difficulty=True,
            personalization_enabled=True,
            completion_rewards={
                "xp": 600,
                "title": "Meta Adaptor",
                "badge": "📈"
            },
            category="meta",
            tags=["meta", "adaptation", "competitive"]
        )
        
        # Store paths
        paths = [beginner_path, tank_path, strategy_path, meta_path]
        for path in paths:
            self.learning_paths[path.path_id] = path
        
        logger.info(f"Created {len(paths)} default learning paths")
    
    async def enroll_player(self, player_id: str, path_id: str) -> bool:
        """Enroll a player in a learning path."""
        
        if path_id not in self.learning_paths:
            logger.error(f"Learning path not found: {path_id}")
            return False
        
        path = self.learning_paths[path_id]
        
        # Check prerequisites
        if not await self._check_path_prerequisites(player_id, path.prerequisites):
            logger.warning(f"Prerequisites not met for path {path_id} by player {player_id}")
            return False
        
        # Initialize player progress if needed
        if player_id not in self.player_progress:
            self.player_progress[player_id] = {}
        
        # Check if already enrolled
        if path_id in self.player_progress[player_id]:
            existing_progress = self.player_progress[player_id][path_id]
            if existing_progress.is_active:
                logger.info(f"Player {player_id} already enrolled in path {path_id}")
                return True
        
        # Create progress tracking
        progress = PlayerProgress(
            player_id=player_id,
            path_id=path_id,
            enrolled_date=datetime.now()
        )
        
        # Personalize learning based on player data
        await self._personalize_learning_path(player_id, progress)
        
        # Store progress
        self.player_progress[player_id][path_id] = progress
        
        # Update path statistics
        path.enrollment_count += 1
        
        # Save progress
        await self._save_player_progress(player_id, path_id, progress)
        
        logger.info(f"Player {player_id} enrolled in learning path {path_id}")
        return True
    
    async def _check_path_prerequisites(self, player_id: str, prerequisites: List[str]) -> bool:
        """Check if player meets path prerequisites."""
        if not prerequisites:
            return True
        
        player_paths = self.player_progress.get(player_id, {})
        
        for prereq_path in prerequisites:
            if prereq_path not in player_paths:
                return False
            if not player_paths[prereq_path].is_completed:
                return False
        
        return True
    
    async def _personalize_learning_path(self, player_id: str, progress: PlayerProgress):
        """Personalize learning path based on player's behavioral profile."""
        
        try:
            # Get player's behavioral analysis
            behavior_analyzer = get_behavior_analyzer()
            
            # Check if we have cached behavioral profile
            if player_id in behavior_analyzer.behavior_profiles:
                profile = behavior_analyzer.behavior_profiles[player_id]
                
                # Adjust difficulty based on skill level
                if profile.behavior_metrics.consistency_score > 8.0:
                    progress.current_difficulty = DifficultyLevel.HARD
                elif profile.behavior_metrics.consistency_score > 6.0:
                    progress.current_difficulty = DifficultyLevel.MEDIUM
                else:
                    progress.current_difficulty = DifficultyLevel.EASY
                
                # Determine learning pace
                if profile.behavior_metrics.decision_quality > 7.0:
                    progress.learning_pace = "fast"
                elif profile.behavior_metrics.decision_quality < 4.0:
                    progress.learning_pace = "slow"
                else:
                    progress.learning_pace = "normal"
                
                # Identify weak areas for focus
                metrics = profile.behavior_metrics
                if metrics.positioning_score < 5.0:
                    progress.weak_areas.append("positioning")
                if metrics.team_coordination < 5.0:
                    progress.weak_areas.append("teamwork")
                if metrics.map_awareness < 5.0:
                    progress.weak_areas.append("awareness")
                if metrics.aggression_score > 8.0 or metrics.aggression_score < 3.0:
                    progress.weak_areas.append("aggression_balance")
                
                # Identify strong areas
                if metrics.avg_kda > 3.0:
                    progress.strong_areas.append("combat")
                if metrics.consistency_score > 7.0:
                    progress.strong_areas.append("consistency")
                if metrics.leadership_score > 6.0:
                    progress.strong_areas.append("leadership")
                
                # Set learning style based on playstyle
                if profile.primary_playstyle.value in ["aggressive_carry", "roaming_support"]:
                    progress.preferred_learning_style = "practical"
                elif profile.primary_playstyle.value in ["objective_focused", "balanced_player"]:
                    progress.preferred_learning_style = "analytical"
                else:
                    progress.preferred_learning_style = "visual"
                
                logger.info(f"Personalized learning for {player_id}: difficulty={progress.current_difficulty.value}, pace={progress.learning_pace}")
                
        except Exception as e:
            logger.warning(f"Failed to personalize learning path: {e}")
            # Use default settings if personalization fails
            progress.current_difficulty = DifficultyLevel.MEDIUM
            progress.learning_pace = "normal"
            progress.preferred_learning_style = "balanced"
    
    async def update_progress(self, player_id: str, path_id: str, 
                            module_id: str, completion_data: Dict[str, Any]) -> bool:
        """Update player's progress in a learning module."""
        
        if player_id not in self.player_progress:
            return False
        
        if path_id not in self.player_progress[player_id]:
            return False
        
        progress = self.player_progress[player_id][path_id]
        
        if not progress.is_active:
            return False
        
        # Get module
        if module_id not in self.learning_modules:
            return False
        
        module = self.learning_modules[module_id]
        
        # Update module completion
        score = completion_data.get('score', 0.0)
        progress.module_scores[module_id] = score
        
        # Check if module is completed
        if await self._is_module_completed(module, completion_data):
            progress.completed_modules.add(module_id)
            
            # Update study time
            study_time = completion_data.get('study_time', module.estimated_duration)
            progress.total_study_time += study_time
            
            # Update streak
            progress.study_streak += 1
            progress.last_activity = datetime.now()
            
            # Check if path is completed
            path = self.learning_paths[path_id]
            required_modules = set(path.modules)
            
            if required_modules.issubset(progress.completed_modules):
                await self._complete_learning_path(player_id, path_id)
            else:
                # Move to next module
                progress.current_module = min(progress.current_module + 1, len(path.modules) - 1)
            
            # Adaptive difficulty adjustment
            if module.difficulty == progress.current_difficulty:
                if score >= 90:  # Excellent performance
                    await self._adjust_difficulty(progress, increase=True)
                elif score < 60:  # Poor performance
                    await self._adjust_difficulty(progress, increase=False)
            
            logger.info(f"Module {module_id} completed by player {player_id} with score {score}")
        
        # Update overall progress
        await self._update_overall_progress(progress)
        
        # Save progress
        await self._save_player_progress(player_id, path_id, progress)
        
        return True
    
    async def _is_module_completed(self, module: LearningModule, completion_data: Dict[str, Any]) -> bool:
        """Check if module completion criteria are met."""
        
        # Check score requirements
        if "quiz_score" in module.success_criteria:
            required_score = module.success_criteria["quiz_score"]
            actual_score = completion_data.get("quiz_score", 0)
            if actual_score < required_score:
                return False
        
        # Check understanding requirements
        if "understanding_check" in module.success_criteria:
            if not completion_data.get("understanding_confirmed", False):
                return False
        
        # Check practical requirements
        for req_key, req_value in module.practice_requirements.items():
            actual_value = completion_data.get(req_key, 0)
            if actual_value < req_value:
                return False
        
        return True
    
    async def _adjust_difficulty(self, progress: PlayerProgress, increase: bool):
        """Adjust difficulty level based on performance."""
        
        current_level = progress.current_difficulty
        
        if increase:
            if current_level == DifficultyLevel.EASY:
                progress.current_difficulty = DifficultyLevel.MEDIUM
            elif current_level == DifficultyLevel.MEDIUM:
                progress.current_difficulty = DifficultyLevel.HARD
            elif current_level == DifficultyLevel.HARD:
                progress.current_difficulty = DifficultyLevel.EXPERT
        else:
            if current_level == DifficultyLevel.EXPERT:
                progress.current_difficulty = DifficultyLevel.HARD
            elif current_level == DifficultyLevel.HARD:
                progress.current_difficulty = DifficultyLevel.MEDIUM
            elif current_level == DifficultyLevel.MEDIUM:
                progress.current_difficulty = DifficultyLevel.EASY
        
        logger.info(f"Adjusted difficulty for player {progress.player_id}: {current_level.value} -> {progress.current_difficulty.value}")
    
    async def _complete_learning_path(self, player_id: str, path_id: str):
        """Complete a learning path for a player."""
        
        progress = self.player_progress[player_id][path_id]
        path = self.learning_paths[path_id]
        
        # Mark as completed
        progress.is_completed = True
        progress.completion_date = datetime.now()
        
        # Calculate overall score
        if progress.module_scores:
            progress.overall_score = sum(progress.module_scores.values()) / len(progress.module_scores)
        
        # Update path statistics
        path.completion_count += 1
        path.success_rate = path.completion_count / max(1, path.enrollment_count)
        
        # Award completion rewards
        rewards = path.completion_rewards
        total_xp = rewards.get("xp", 0)
        
        logger.info(f"Learning path {path_id} completed by player {player_id} with score {progress.overall_score:.1f}")
        
        # Generate completion certificate/badge
        completion_data = {
            "player_id": player_id,
            "path_name": path.name,
            "completion_date": progress.completion_date.isoformat(),
            "final_score": progress.overall_score,
            "study_time": progress.total_study_time,
            "rewards": rewards
        }
        
        # Save completion record
        await self._save_completion_record(player_id, path_id, completion_data)
    
    async def _update_overall_progress(self, progress: PlayerProgress):
        """Update overall progress metrics."""
        
        path = self.learning_paths[progress.path_id]
        
        # Calculate completion percentage
        total_modules = len(path.modules)
        completed_count = len(progress.completed_modules)
        completion_percentage = (completed_count / max(1, total_modules)) * 100
        
        # Update skill improvements based on completed modules
        for module_id in progress.completed_modules:
            if module_id in self.learning_modules:
                module = self.learning_modules[module_id]
                for skill, points in module.skill_points.items():
                    current_skill = progress.skill_improvements.get(skill, 0)
                    progress.skill_improvements[skill] = current_skill + points
    
    async def generate_recommendations(self, player_id: str) -> List[PersonalizedRecommendation]:
        """Generate personalized learning recommendations for a player."""
        
        recommendations = []
        
        try:
            # Get player's behavioral profile
            behavior_analyzer = get_behavior_analyzer()
            
            if player_id not in behavior_analyzer.behavior_profiles:
                # Generate basic recommendations for new players
                return await self._generate_basic_recommendations(player_id)
            
            profile = behavior_analyzer.behavior_profiles[player_id]
            player_paths = self.player_progress.get(player_id, {})
            
            # Analyze weaknesses and suggest improvements
            metrics = profile.behavior_metrics
            
            # Combat improvement recommendations
            if metrics.avg_kda < 2.0:
                rec = PersonalizedRecommendation(
                    player_id=player_id,
                    recommendation_type="skill_improvement",
                    priority="high",
                    title="Improve Combat Performance",
                    description="Your KDA could use improvement. Focus on positioning and decision-making.",
                    suggested_modules=["combat_basics", "advanced_positioning"],
                    analysis_basis={"current_kda": metrics.avg_kda, "target_kda": 2.5},
                    improvement_potential=0.8,
                    confidence_score=0.9
                )
                recommendations.append(rec)
            
            # Positioning recommendations
            if metrics.positioning_score < 5.0:
                rec = PersonalizedRecommendation(
                    player_id=player_id,
                    recommendation_type="skill_improvement",
                    priority="high",
                    title="Master Positioning",
                    description="Better positioning will significantly improve your survival and impact.",
                    suggested_modules=["advanced_positioning", "map_awareness"],
                    analysis_basis={"current_positioning": metrics.positioning_score, "target": 7.0},
                    improvement_potential=0.9,
                    confidence_score=0.85
                )
                recommendations.append(rec)
            
            # Team coordination recommendations
            if metrics.team_coordination < 6.0:
                rec = PersonalizedRecommendation(
                    player_id=player_id,
                    recommendation_type="skill_improvement",
                    priority="medium",
                    title="Enhance Team Coordination",
                    description="Improve your teamwork and communication skills for better match outcomes.",
                    suggested_modules=["team_fight_mastery", "objective_control"],
                    analysis_basis={"current_teamwork": metrics.team_coordination, "target": 8.0},
                    improvement_potential=0.7,
                    confidence_score=0.8
                )
                recommendations.append(rec)
            
            # Role mastery recommendations
            if profile.primary_playstyle:
                role_paths = [path_id for path_id, path in self.learning_paths.items() 
                             if path.path_type == LearningPathType.ROLE_MASTERY]
                
                incomplete_role_paths = [path_id for path_id in role_paths 
                                       if path_id not in player_paths or not player_paths[path_id].is_completed]
                
                if incomplete_role_paths:
                    rec = PersonalizedRecommendation(
                        player_id=player_id,
                        recommendation_type="role_mastery",
                        priority="medium",
                        title=f"Master Your {profile.primary_playstyle.value.title()} Style",
                        description=f"Complete role mastery training for {profile.primary_playstyle.value} playstyle.",
                        suggested_paths=incomplete_role_paths[:2],
                        analysis_basis={"playstyle": profile.primary_playstyle.value},
                        improvement_potential=0.6,
                        confidence_score=0.75
                    )
                    recommendations.append(rec)
            
            # Consistency recommendations
            if metrics.consistency_score < 6.0:
                rec = PersonalizedRecommendation(
                    player_id=player_id,
                    recommendation_type="skill_improvement",
                    priority="low",
                    title="Improve Consistency",
                    description="Work on maintaining consistent performance across matches.",
                    suggested_modules=["strategic_thinking", "mental_game"],
                    practice_recommendations=[
                        "Review your replays after each match",
                        "Focus on one improvement area per session",
                        "Practice the same hero for multiple matches"
                    ],
                    analysis_basis={"consistency": metrics.consistency_score, "target": 7.5},
                    improvement_potential=0.5,
                    confidence_score=0.7
                )
                recommendations.append(rec)
            
            # Sort by priority and confidence
            recommendations.sort(key=lambda x: (
                {"high": 3, "medium": 2, "low": 1}[x.priority], 
                x.confidence_score
            ), reverse=True)
            
            # Store recommendations
            self.recommendations[player_id] = recommendations
            
            logger.info(f"Generated {len(recommendations)} recommendations for player {player_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return await self._generate_basic_recommendations(player_id)
        
        return recommendations
    
    async def _generate_basic_recommendations(self, player_id: str) -> List[PersonalizedRecommendation]:
        """Generate basic recommendations for new players."""
        
        basic_recommendations = [
            PersonalizedRecommendation(
                player_id=player_id,
                recommendation_type="getting_started",
                priority="high",
                title="Start with Fundamentals",
                description="Begin your MLBB journey with our comprehensive fundamentals course.",
                suggested_paths=["beginner_fundamentals"],
                improvement_potential=1.0,
                confidence_score=1.0
            ),
            PersonalizedRecommendation(
                player_id=player_id,
                recommendation_type="skill_assessment",
                priority="medium",
                title="Complete Skill Assessment",
                description="Play 10 matches to get personalized recommendations based on your playstyle.",
                practice_recommendations=[
                    "Play different roles to find your preference",
                    "Focus on learning rather than winning",
                    "Try various heroes to understand the game"
                ],
                improvement_potential=0.8,
                confidence_score=0.9
            )
        ]
        
        return basic_recommendations
    
    async def get_player_learning_status(self, player_id: str) -> Dict[str, Any]:
        """Get comprehensive learning status for a player."""
        
        status = {
            "active_paths": [],
            "completed_paths": [],
            "available_paths": [],
            "recommendations": [],
            "overall_progress": {
                "total_study_time": 0,
                "paths_completed": 0,
                "current_streak": 0,
                "skill_improvements": {}
            }
        }
        
        # Get player progress
        player_paths = self.player_progress.get(player_id, {})
        
        total_study_time = 0
        paths_completed = 0
        max_streak = 0
        combined_skills = {}
        
        # Process each path
        for path_id, progress in player_paths.items():
            path = self.learning_paths[path_id]
            
            path_data = {
                "path": asdict(path),
                "progress": asdict(progress)
            }
            
            if progress.is_completed:
                status["completed_paths"].append(path_data)
                paths_completed += 1
            elif progress.is_active:
                status["active_paths"].append(path_data)
            
            # Aggregate statistics
            total_study_time += progress.total_study_time
            max_streak = max(max_streak, progress.study_streak)
            
            # Combine skill improvements
            for skill, points in progress.skill_improvements.items():
                combined_skills[skill] = combined_skills.get(skill, 0) + points
        
        # Find available paths
        for path_id, path in self.learning_paths.items():
            if path_id not in player_paths and path.is_active:
                # Check prerequisites
                if await self._check_path_prerequisites(player_id, path.prerequisites):
                    status["available_paths"].append(asdict(path))
        
        # Get recommendations
        if player_id in self.recommendations:
            status["recommendations"] = [asdict(rec) for rec in self.recommendations[player_id]]
        
        # Overall progress
        status["overall_progress"] = {
            "total_study_time": total_study_time,
            "paths_completed": paths_completed,
            "current_streak": max_streak,
            "skill_improvements": combined_skills
        }
        
        return status
    
    async def _load_learning_content(self):
        """Load learning paths and modules from disk."""
        # Implementation for loading from disk
        pass
    
    async def _save_learning_content(self):
        """Save learning paths and modules to disk."""
        # Implementation for saving to disk
        pass
    
    async def _save_player_progress(self, player_id: str, path_id: str, progress: PlayerProgress):
        """Save player progress to disk."""
        progress_file = self.progress_dir / f"{player_id}_{path_id}_progress.json"
        
        try:
            data = asdict(progress)
            # Handle datetime serialization
            data['enrolled_date'] = progress.enrolled_date.isoformat()
            data['last_activity'] = progress.last_activity.isoformat()
            if progress.completion_date:
                data['completion_date'] = progress.completion_date.isoformat()
            
            # Convert set to list
            data['completed_modules'] = list(progress.completed_modules)
            
            with open(progress_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save player progress: {e}")
    
    async def _save_completion_record(self, player_id: str, path_id: str, completion_data: Dict[str, Any]):
        """Save completion record."""
        record_file = self.progress_dir / f"{player_id}_{path_id}_completion.json"
        
        try:
            with open(record_file, 'w') as f:
                json.dump(completion_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save completion record: {e}")
    
    async def process(self, request: Dict[str, Any]) -> ServiceResult:
        """Process learning path requests."""
        try:
            action = request.get('action', 'get_learning_status')
            
            if action == 'enroll_player':
                player_id = request.get('player_id')
                path_id = request.get('path_id')
                
                success = await self.enroll_player(player_id, path_id)
                
                return ServiceResult(
                    success=success,
                    data={'enrolled': success},
                    metadata={'action': 'enroll_player', 'player_id': player_id, 'path_id': path_id}
                )
                
            elif action == 'update_progress':
                player_id = request.get('player_id')
                path_id = request.get('path_id')
                module_id = request.get('module_id')
                completion_data = request.get('completion_data', {})
                
                success = await self.update_progress(player_id, path_id, module_id, completion_data)
                
                return ServiceResult(
                    success=success,
                    data={'updated': success},
                    metadata={'action': 'update_progress'}
                )
                
            elif action == 'get_learning_status':
                player_id = request.get('player_id')
                status = await self.get_player_learning_status(player_id)
                
                return ServiceResult(
                    success=True,
                    data=status,
                    metadata={'action': 'get_learning_status', 'player_id': player_id}
                )
                
            elif action == 'generate_recommendations':
                player_id = request.get('player_id')
                recommendations = await self.generate_recommendations(player_id)
                
                return ServiceResult(
                    success=True,
                    data=[asdict(rec) for rec in recommendations],
                    metadata={'action': 'generate_recommendations', 'count': len(recommendations)}
                )
                
            elif action == 'get_available_paths':
                available_paths = [asdict(path) for path in self.learning_paths.values() if path.is_active]
                
                return ServiceResult(
                    success=True,
                    data=available_paths,
                    metadata={'action': 'get_available_paths', 'count': len(available_paths)}
                )
                
            else:
                return ServiceResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            logger.error(f"Learning path manager error: {str(e)}")
            return ServiceResult(
                success=False,
                error=str(e)
            )


# Global learning path manager instance
_learning_manager = None

def get_learning_manager() -> LearningPathManager:
    """Get global learning path manager instance."""
    global _learning_manager
    if _learning_manager is None:
        _learning_manager = LearningPathManager()
    return _learning_manager
