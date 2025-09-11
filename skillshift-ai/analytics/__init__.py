"""
Advanced Analytics Engine for MLBB Coach AI
==========================================

Comprehensive analytics system providing:
- Player behavior analytics
- Meta game tracking
- Performance trend analysis
- Predictive modeling
- Business intelligence
"""

from .player_behavior_analyzer import PlayerBehaviorAnalyzer, BehaviorProfile
from .meta_game_tracker import MetaGameTracker, MetaGameInsights
from .predictive_analytics import PredictiveAnalytics, PredictionResult
from .performance_analyzer import PerformanceAnalyzer, PerformanceMetrics
from .analytics_engine import AnalyticsEngine

__all__ = [
    'PlayerBehaviorAnalyzer',
    'BehaviorProfile',
    'MetaGameTracker', 
    'MetaGameInsights',
    'PredictiveAnalytics',
    'PredictionResult',
    'PerformanceAnalyzer',
    'PerformanceMetrics',
    'AnalyticsEngine'
]
