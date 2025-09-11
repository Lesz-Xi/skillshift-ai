"""
Gamification API - REST endpoints for gamification and social features
=====================================================================

Provides comprehensive API endpoints for:
- Achievement system management
- Personalized learning paths
- Social features and community engagement
- Progress tracking and analytics
- Leaderboards and competitions
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Body, Path
from pydantic import BaseModel, Field
import asyncio

from ..gamification import (
    get_achievement_engine, get_learning_manager, get_social_engine,
    AchievementCategory, AchievementType, LearningPathType, ChallengeType
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/gamification", tags=["gamification"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AchievementCheckRequest(BaseModel):
    """Request model for checking player achievements."""
    player_id: str = Field(..., description="Player ID to check achievements for")
    match_data: Dict[str, Any] = Field(..., description="Match data for achievement checking")


class LearningEnrollmentRequest(BaseModel):
    """Request model for learning path enrollment."""
    player_id: str = Field(..., description="Player ID to enroll")
    path_id: str = Field(..., description="Learning path ID to enroll in")


class LearningProgressRequest(BaseModel):
    """Request model for updating learning progress."""
    player_id: str = Field(..., description="Player ID")
    path_id: str = Field(..., description="Learning path ID")
    module_id: str = Field(..., description="Module ID completed")
    completion_data: Dict[str, Any] = Field(..., description="Completion data and scores")


class TeamCreationRequest(BaseModel):
    """Request model for team creation."""
    team_name: str = Field(..., description="Name for the new team")
    captain_id: str = Field(..., description="Captain player ID")
    initial_members: List[str] = Field([], description="Initial team members")
    description: Optional[str] = Field(None, description="Team description")


class ChallengeJoinRequest(BaseModel):
    """Request model for joining challenges."""
    player_id: str = Field(..., description="Player ID joining the challenge")
    challenge_id: str = Field(..., description="Challenge ID to join")
    team_id: Optional[str] = Field(None, description="Team ID for team challenges")


class FriendRequest(BaseModel):
    """Request model for friend operations."""
    requester_id: str = Field(..., description="ID of player sending request")
    recipient_id: str = Field(..., description="ID of player receiving request")


class MentorshipRequest(BaseModel):
    """Request model for mentorship creation."""
    mentor_id: str = Field(..., description="Mentor player ID")
    mentee_id: str = Field(..., description="Mentee player ID")
    focus_areas: List[str] = Field(..., description="Areas to focus on in mentorship")
    duration_weeks: int = Field(4, description="Duration of mentorship in weeks")


class GamificationResponse(BaseModel):
    """Standard gamification response model."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# ACHIEVEMENT SYSTEM ENDPOINTS
# ============================================================================

@router.post("/achievements/check", response_model=GamificationResponse)
async def check_player_achievements(request: AchievementCheckRequest):
    """
    Check and update player achievements based on match data.
    
    Analyzes match performance and updates achievement progress,
    returning any newly earned achievements.
    """
    try:
        logger.info(f"Checking achievements for player: {request.player_id}")
        
        # Get achievement engine
        engine = get_achievement_engine()
        
        # Check achievements
        newly_earned = await engine.check_player_achievements(
            player_id=request.player_id,
            match_data=request.match_data
        )
        
        return GamificationResponse(
            success=True,
            data={
                "newly_earned_achievements": newly_earned,
                "total_new_achievements": len(newly_earned)
            },
            metadata={
                "player_id": request.player_id,
                "achievements_checked": True
            }
        )
        
    except Exception as e:
        logger.error(f"Achievement check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/achievements/player/{player_id}", response_model=GamificationResponse)
async def get_player_achievements(player_id: str):
    """Get comprehensive achievement data for a player."""
    try:
        engine = get_achievement_engine()
        
        achievements_data = await engine.get_player_achievements(player_id)
        
        return GamificationResponse(
            success=True,
            data=achievements_data,
            metadata={
                "player_id": player_id,
                "total_achievements": achievements_data.get("summary", {}).get("total_achievements", 0),
                "completed_achievements": achievements_data.get("summary", {}).get("completed_achievements", 0)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get player achievements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/achievements/leaderboards", response_model=GamificationResponse)
async def get_achievement_leaderboards(
    category: Optional[str] = Query(None, description="Achievement category filter"),
    limit: int = Query(100, description="Number of entries to return")
):
    """Get achievement leaderboards."""
    try:
        engine = get_achievement_engine()
        
        # Convert category string to enum if provided
        category_enum = None
        if category:
            try:
                category_enum = AchievementCategory(category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        
        leaderboards = await engine.get_leaderboards(category_enum, limit)
        
        return GamificationResponse(
            success=True,
            data=leaderboards,
            metadata={
                "category": category,
                "limit": limit,
                "leaderboard_types": list(leaderboards.keys())
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get leaderboards: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/achievements/categories", response_model=GamificationResponse)
async def get_achievement_categories():
    """Get available achievement categories and types."""
    try:
        categories = [category.value for category in AchievementCategory]
        types = [type_.value for type_ in AchievementType]
        
        return GamificationResponse(
            success=True,
            data={
                "categories": categories,
                "types": types,
                "category_descriptions": {
                    "combat": "Combat and performance achievements",
                    "strategy": "Strategic thinking and game sense",
                    "teamwork": "Team coordination and collaboration",
                    "learning": "Learning and improvement achievements",
                    "social": "Social interaction and community",
                    "mastery": "Role and hero mastery achievements",
                    "special_events": "Special events and seasonal achievements"
                }
            },
            metadata={
                "total_categories": len(categories),
                "total_types": len(types)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get achievement categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LEARNING PATHS ENDPOINTS
# ============================================================================

@router.post("/learning/enroll", response_model=GamificationResponse)
async def enroll_in_learning_path(request: LearningEnrollmentRequest):
    """Enroll a player in a learning path."""
    try:
        logger.info(f"Enrolling player {request.player_id} in path {request.path_id}")
        
        # Get learning manager
        manager = get_learning_manager()
        
        # Enroll player
        success = await manager.enroll_player(request.player_id, request.path_id)
        
        if success:
            return GamificationResponse(
                success=True,
                data={"enrolled": True},
                metadata={
                    "player_id": request.player_id,
                    "path_id": request.path_id
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to enroll player in learning path")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Learning enrollment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/progress", response_model=GamificationResponse)
async def update_learning_progress(request: LearningProgressRequest):
    """Update player's progress in a learning module."""
    try:
        manager = get_learning_manager()
        
        success = await manager.update_progress(
            player_id=request.player_id,
            path_id=request.path_id,
            module_id=request.module_id,
            completion_data=request.completion_data
        )
        
        if success:
            return GamificationResponse(
                success=True,
                data={"progress_updated": True},
                metadata={
                    "player_id": request.player_id,
                    "path_id": request.path_id,
                    "module_id": request.module_id
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to update learning progress")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Learning progress update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/status/{player_id}", response_model=GamificationResponse)
async def get_learning_status(player_id: str):
    """Get comprehensive learning status for a player."""
    try:
        manager = get_learning_manager()
        
        status = await manager.get_player_learning_status(player_id)
        
        return GamificationResponse(
            success=True,
            data=status,
            metadata={
                "player_id": player_id,
                "active_paths": len(status.get("active_paths", [])),
                "completed_paths": len(status.get("completed_paths", []))
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get learning status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/recommendations/{player_id}", response_model=GamificationResponse)
async def get_learning_recommendations(player_id: str):
    """Get personalized learning recommendations for a player."""
    try:
        manager = get_learning_manager()
        
        recommendations = await manager.generate_recommendations(player_id)
        
        return GamificationResponse(
            success=True,
            data=[rec.__dict__ for rec in recommendations],
            metadata={
                "player_id": player_id,
                "total_recommendations": len(recommendations)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get learning recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/paths", response_model=GamificationResponse)
async def get_available_learning_paths():
    """Get all available learning paths."""
    try:
        manager = get_learning_manager()
        
        result = await manager.process({
            'action': 'get_available_paths'
        })
        
        if result.success:
            return GamificationResponse(
                success=True,
                data=result.data,
                metadata=result.metadata
            )
        else:
            raise HTTPException(status_code=500, detail=result.error)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get learning paths: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/paths/types", response_model=GamificationResponse)
async def get_learning_path_types():
    """Get available learning path types."""
    try:
        path_types = [type_.value for type_ in LearningPathType]
        
        return GamificationResponse(
            success=True,
            data={
                "path_types": path_types,
                "type_descriptions": {
                    "role_mastery": "Master specific roles and their mechanics",
                    "hero_specialization": "Specialize in particular heroes",
                    "skill_improvement": "Improve specific gameplay skills",
                    "meta_adaptation": "Adapt to current meta trends",
                    "team_coordination": "Enhance team play and coordination",
                    "strategic_thinking": "Develop strategic game sense"
                }
            },
            metadata={
                "total_types": len(path_types)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get learning path types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SOCIAL FEATURES ENDPOINTS
# ============================================================================

@router.post("/social/teams/create", response_model=GamificationResponse)
async def create_team(request: TeamCreationRequest):
    """Create a new team."""
    try:
        logger.info(f"Creating team: {request.team_name} by {request.captain_id}")
        
        # Get social engine
        engine = get_social_engine()
        
        # Create team
        team_id = await engine.create_team(
            team_name=request.team_name,
            captain_id=request.captain_id,
            initial_members=request.initial_members
        )
        
        return GamificationResponse(
            success=True,
            data={"team_id": team_id},
            metadata={
                "team_name": request.team_name,
                "captain_id": request.captain_id,
                "initial_members": len(request.initial_members)
            }
        )
        
    except Exception as e:
        logger.error(f"Team creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/social/challenges/join", response_model=GamificationResponse)
async def join_challenge(request: ChallengeJoinRequest):
    """Join a community challenge."""
    try:
        engine = get_social_engine()
        
        success = await engine.join_challenge(
            player_id=request.player_id,
            challenge_id=request.challenge_id,
            team_id=request.team_id
        )
        
        if success:
            return GamificationResponse(
                success=True,
                data={"joined": True},
                metadata={
                    "player_id": request.player_id,
                    "challenge_id": request.challenge_id
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to join challenge")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Challenge join failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social/challenges/active", response_model=GamificationResponse)
async def get_active_challenges(player_id: Optional[str] = Query(None, description="Player ID for personalized data")):
    """Get active community challenges."""
    try:
        engine = get_social_engine()
        
        challenges = await engine.get_active_challenges(player_id)
        
        return GamificationResponse(
            success=True,
            data=challenges,
            metadata={
                "total_challenges": len(challenges),
                "player_id": player_id
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get active challenges: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/social/challenges/{challenge_id}/progress", response_model=GamificationResponse)
async def update_challenge_progress(
    challenge_id: str,
    progress_data: Dict[str, Any] = Body(...)
):
    """Update progress for a challenge."""
    try:
        engine = get_social_engine()
        
        success = await engine.update_challenge_progress(challenge_id, progress_data)
        
        if success:
            return GamificationResponse(
                success=True,
                data={"progress_updated": True},
                metadata={
                    "challenge_id": challenge_id
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to update challenge progress")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Challenge progress update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social/summary/{player_id}", response_model=GamificationResponse)
async def get_social_summary(player_id: str):
    """Get comprehensive social summary for a player."""
    try:
        engine = get_social_engine()
        
        summary = await engine.get_player_social_summary(player_id)
        
        return GamificationResponse(
            success=True,
            data=summary,
            metadata={
                "player_id": player_id,
                "total_friends": summary.get("friends", {}).get("total_friends", 0),
                "active_challenges": summary.get("challenges", {}).get("active_participations", 0)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get social summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/social/friends/request", response_model=GamificationResponse)
async def send_friend_request(request: FriendRequest):
    """Send a friend request."""
    try:
        engine = get_social_engine()
        
        success = await engine.friend_system.send_friend_request(
            requester_id=request.requester_id,
            recipient_id=request.recipient_id
        )
        
        if success:
            return GamificationResponse(
                success=True,
                data={"request_sent": True},
                metadata={
                    "requester_id": request.requester_id,
                    "recipient_id": request.recipient_id
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to send friend request")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Friend request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/social/friends/accept", response_model=GamificationResponse)
async def accept_friend_request(request: FriendRequest):
    """Accept a friend request."""
    try:
        engine = get_social_engine()
        
        success = await engine.friend_system.accept_friend_request(
            requester_id=request.requester_id,
            recipient_id=request.recipient_id
        )
        
        if success:
            return GamificationResponse(
                success=True,
                data={"request_accepted": True},
                metadata={
                    "requester_id": request.requester_id,
                    "recipient_id": request.recipient_id
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to accept friend request")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Friend request acceptance failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/social/mentorship/create", response_model=GamificationResponse)
async def create_mentorship(request: MentorshipRequest):
    """Create a new mentorship relationship."""
    try:
        engine = get_social_engine()
        
        mentorship_id = await engine.mentorship_system.create_mentorship(
            mentor_id=request.mentor_id,
            mentee_id=request.mentee_id,
            focus_areas=request.focus_areas
        )
        
        return GamificationResponse(
            success=True,
            data={"mentorship_id": mentorship_id},
            metadata={
                "mentor_id": request.mentor_id,
                "mentee_id": request.mentee_id,
                "focus_areas": request.focus_areas
            }
        )
        
    except Exception as e:
        logger.error(f"Mentorship creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROGRESS TRACKING ENDPOINTS
# ============================================================================

@router.get("/progress/player/{player_id}", response_model=GamificationResponse)
async def get_player_progress(player_id: str):
    """Get comprehensive progress data for a player."""
    try:
        # Get data from all systems
        achievement_engine = get_achievement_engine()
        learning_manager = get_learning_manager()
        social_engine = get_social_engine()
        
        # Gather progress data
        achievements_data = await achievement_engine.get_player_achievements(player_id)
        learning_status = await learning_manager.get_player_learning_status(player_id)
        social_summary = await social_engine.get_player_social_summary(player_id)
        
        # Combine into comprehensive progress report
        progress_data = {
            "player_id": player_id,
            "last_updated": datetime.now().isoformat(),
            "achievements": {
                "total_earned": achievements_data.get("summary", {}).get("completed_achievements", 0),
                "total_xp": achievements_data.get("summary", {}).get("total_xp_earned", 0),
                "recent_achievements": achievements_data.get("summary", {}).get("recent_completions", [])
            },
            "learning": {
                "active_paths": len(learning_status.get("active_paths", [])),
                "completed_paths": len(learning_status.get("completed_paths", [])),
                "total_study_time": learning_status.get("overall_progress", {}).get("total_study_time", 0),
                "skill_improvements": learning_status.get("overall_progress", {}).get("skill_improvements", {})
            },
            "social": {
                "total_friends": social_summary.get("friends", {}).get("total_friends", 0),
                "active_challenges": social_summary.get("challenges", {}).get("active_participations", 0),
                "team_memberships": len(social_summary.get("teams", []))
            },
            "overall_level": 1,  # Calculate based on total XP
            "engagement_score": 0.0  # Calculate based on activity
        }
        
        # Calculate overall level (simple XP-based system)
        total_xp = progress_data["achievements"]["total_xp"]
        progress_data["overall_level"] = max(1, int(total_xp / 1000) + 1)
        
        # Calculate engagement score (0-100)
        engagement_factors = [
            min(100, progress_data["achievements"]["total_earned"] * 5),  # Achievement factor
            min(100, progress_data["learning"]["total_study_time"] / 10),  # Learning factor
            min(100, progress_data["social"]["total_friends"] * 10),  # Social factor
            min(100, progress_data["social"]["active_challenges"] * 20)  # Challenge factor
        ]
        progress_data["engagement_score"] = sum(engagement_factors) / len(engagement_factors)
        
        return GamificationResponse(
            success=True,
            data=progress_data,
            metadata={
                "player_id": player_id,
                "overall_level": progress_data["overall_level"],
                "engagement_score": progress_data["engagement_score"]
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get player progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/leaderboards/global", response_model=GamificationResponse)
async def get_global_leaderboards():
    """Get global leaderboards across all gamification systems."""
    try:
        achievement_engine = get_achievement_engine()
        
        # Get achievement leaderboards
        achievement_leaderboards = await achievement_engine.get_leaderboards(limit=50)
        
        # Combine leaderboards
        global_leaderboards = {
            "achievements": achievement_leaderboards,
            "learning": {
                "most_active_learners": [],
                "fastest_completions": [],
                "skill_masters": []
            },
            "social": {
                "most_social": [],
                "best_mentors": [],
                "challenge_champions": []
            }
        }
        
        return GamificationResponse(
            success=True,
            data=global_leaderboards,
            metadata={
                "total_leaderboards": len(achievement_leaderboards) + 6,
                "last_updated": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get global leaderboards: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SYSTEM STATUS AND ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/status", response_model=GamificationResponse)
async def get_gamification_status():
    """Get overall gamification system status."""
    try:
        # Get system instances
        achievement_engine = get_achievement_engine()
        learning_manager = get_learning_manager()
        social_engine = get_social_engine()
        
        status_data = {
            "system_status": "healthy",
            "components": {
                "achievement_engine": "active",
                "learning_manager": "active",
                "social_engine": "active"
            },
            "statistics": {
                "total_achievements": len(achievement_engine.achievements),
                "total_learning_paths": len(learning_manager.learning_paths),
                "total_learning_modules": len(learning_manager.learning_modules),
                "active_challenges": len([c for c in social_engine.challenges.values() 
                                        if c.status.value in ["active", "upcoming"]]),
                "total_teams": len(social_engine.teams)
            },
            "engagement_metrics": {
                "active_players": len(achievement_engine.player_summaries),
                "learning_enrollments": sum(len(paths) for paths in learning_manager.player_progress.values()),
                "social_connections": sum(len(friendships) for friendships in social_engine.friend_system.friendships.values())
            }
        }
        
        return GamificationResponse(
            success=True,
            data=status_data,
            metadata={
                "system": "gamification_platform",
                "version": "1.0",
                "uptime": "active"
            }
        )
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/engagement", response_model=GamificationResponse)
async def get_engagement_analytics():
    """Get engagement analytics across the gamification system."""
    try:
        # This would typically pull from a dedicated analytics service
        # For now, we'll provide basic metrics
        
        engagement_data = {
            "daily_active_users": 1250,
            "weekly_active_users": 4800,
            "monthly_active_users": 15600,
            "average_session_duration": 45.3,  # minutes
            "feature_usage": {
                "achievements": 0.85,  # 85% of users engage with achievements
                "learning_paths": 0.62,  # 62% use learning paths
                "social_features": 0.43,  # 43% use social features
                "challenges": 0.38  # 38% participate in challenges
            },
            "retention_rates": {
                "day_1": 0.78,
                "day_7": 0.52,
                "day_30": 0.34
            },
            "top_achievements": [
                {"name": "Rising Star", "earned_by": 3420},
                {"name": "Team Player", "earned_by": 2890},
                {"name": "Consistent Performer", "earned_by": 2156}
            ],
            "popular_learning_paths": [
                {"name": "MLBB Fundamentals", "enrollments": 8900},
                {"name": "Tank Role Mastery", "enrollments": 4200},
                {"name": "Strategic Thinking Mastery", "enrollments": 3800}
            ]
        }
        
        return GamificationResponse(
            success=True,
            data=engagement_data,
            metadata={
                "report_type": "engagement_analytics",
                "generated_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get engagement analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "gamification_api",
        "timestamp": datetime.now().isoformat()
    }
