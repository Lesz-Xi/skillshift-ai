"""
Gamification System for MLBB Coach AI
====================================

Comprehensive gamification platform providing:
- Skill-based achievement system
- Progress tracking and analytics
- Social leaderboards and competitions
- Personalized learning paths
- Community engagement features
"""

from .achievement_system import (
    AchievementEngine, Achievement, AchievementType, AchievementTier,
    PlayerProgress, AchievementCategory, get_achievement_engine
)
from .learning_paths import (
    LearningPathManager, LearningPath, LearningModule, SkillLevel,
    PersonalizedRecommendation, get_learning_manager
)
from .social_features import (
    SocialEngine, FriendSystem, MentorshipSystem, CommunityChallenge,
    LeaderboardManager, get_social_engine
)
from .progress_tracking import (
    ProgressTracker, ProgressMetrics, MilestoneTracker,
    PerformanceAnalyzer, get_progress_tracker
)
from .gamification_engine import GamificationEngine, get_gamification_engine

__all__ = [
    # Achievement System
    'AchievementEngine',
    'Achievement', 
    'AchievementType',
    'AchievementTier',
    'PlayerProgress',
    'AchievementCategory',
    'get_achievement_engine',
    
    # Learning Paths
    'LearningPathManager',
    'LearningPath',
    'LearningModule', 
    'SkillLevel',
    'PersonalizedRecommendation',
    'get_learning_manager',
    
    # Social Features
    'SocialEngine',
    'FriendSystem',
    'MentorshipSystem',
    'CommunityChallenge',
    'LeaderboardManager',
    'get_social_engine',
    
    # Progress Tracking
    'ProgressTracker',
    'ProgressMetrics',
    'MilestoneTracker',
    'PerformanceAnalyzer',
    'get_progress_tracker',
    
    # Main Engine
    'GamificationEngine',
    'get_gamification_engine'
]
