"""
Social Features - Community engagement and collaboration system
==============================================================

Provides comprehensive social features including friend systems,
mentorship programs, community challenges, and team collaboration tools.
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
from collections import defaultdict

from ..core.services.base_service import BaseService, ServiceResult

logger = logging.getLogger(__name__)


class FriendshipStatus(Enum):
    """Friendship status types."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    DECLINED = "declined"


class MentorshipStatus(Enum):
    """Mentorship relationship status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ChallengeType(Enum):
    """Types of community challenges."""
    INDIVIDUAL = "individual"
    TEAM = "team"
    COMMUNITY = "community"
    SEASONAL = "seasonal"
    TOURNAMENT = "tournament"


class ChallengeStatus(Enum):
    """Challenge status types."""
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LeaderboardType(Enum):
    """Types of leaderboards."""
    GLOBAL = "global"
    FRIENDS = "friends"
    REGION = "region"
    ROLE = "role"
    HERO = "hero"
    MONTHLY = "monthly"
    WEEKLY = "weekly"


@dataclass
class Friend:
    """Friend relationship data."""
    requester_id: str
    recipient_id: str
    status: FriendshipStatus
    
    # Timestamps
    request_date: datetime = field(default_factory=datetime.now)
    accepted_date: Optional[datetime] = None
    
    # Interaction Stats
    matches_together: int = 0
    coaching_sessions: int = 0
    last_interaction: Optional[datetime] = None
    
    # Preferences
    can_invite: bool = True
    can_coach: bool = True
    notifications_enabled: bool = True
    
    # Metadata
    notes: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class MentorshipRelation:
    """Mentorship relationship between players."""
    mentor_id: str
    mentee_id: str
    status: MentorshipStatus
    
    # Program Details
    focus_areas: List[str] = field(default_factory=list)
    target_skills: List[str] = field(default_factory=list)
    duration_weeks: int = 4
    
    # Progress Tracking
    sessions_completed: int = 0
    sessions_planned: int = 8
    mentee_improvement: Dict[str, float] = field(default_factory=dict)
    
    # Scheduling
    start_date: datetime = field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    next_session: Optional[datetime] = None
    
    # Feedback
    mentor_rating: Optional[float] = None
    mentee_rating: Optional[float] = None
    mentor_feedback: str = ""
    mentee_feedback: str = ""
    
    # Goals and Milestones
    goals: List[Dict[str, Any]] = field(default_factory=list)
    milestones_achieved: List[str] = field(default_factory=list)
    
    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class CommunityChallenge:
    """Community challenge or event."""
    challenge_id: str
    name: str
    description: str
    challenge_type: ChallengeType
    status: ChallengeStatus
    
    # Timing
    start_date: datetime
    end_date: datetime
    registration_deadline: Optional[datetime] = None
    
    # Requirements
    requirements: Dict[str, Any] = field(default_factory=dict)
    min_participants: int = 1
    max_participants: Optional[int] = None
    
    # Rewards
    rewards: Dict[str, Any] = field(default_factory=dict)
    participation_rewards: Dict[str, Any] = field(default_factory=dict)
    
    # Progress Tracking
    participants: Set[str] = field(default_factory=set)
    teams: Dict[str, List[str]] = field(default_factory=dict)  # team_id -> player_ids
    leaderboard: List[Dict[str, Any]] = field(default_factory=list)
    
    # Rules and Settings
    rules: List[str] = field(default_factory=list)
    scoring_method: str = "points"  # points, ranking, achievement
    is_recurring: bool = False
    
    # Social Features
    allow_teams: bool = False
    max_team_size: int = 5
    public_leaderboard: bool = True
    
    # Metadata
    created_by: str = "system"
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    
    # Statistics
    total_registrations: int = 0
    completion_rate: float = 0.0
    average_score: float = 0.0


@dataclass
class LeaderboardEntry:
    """Entry in a leaderboard."""
    player_id: str
    player_name: str
    score: float
    rank: int
    
    # Additional Data
    secondary_scores: Dict[str, float] = field(default_factory=dict)
    achievements_count: int = 0
    recent_activity: List[str] = field(default_factory=list)
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    trend: str = "stable"  # rising, falling, stable


@dataclass
class TeamData:
    """Team information and statistics."""
    team_id: str
    team_name: str
    members: List[str] = field(default_factory=list)
    
    # Leadership
    captain_id: str = ""
    co_captains: List[str] = field(default_factory=list)
    
    # Statistics
    matches_played: int = 0
    matches_won: int = 0
    win_rate: float = 0.0
    average_performance: float = 0.0
    
    # Team Dynamics
    synergy_score: float = 0.0
    communication_rating: float = 0.0
    strategy_rating: float = 0.0
    
    # Activity
    created_date: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    activity_level: str = "active"  # active, inactive, disbanded
    
    # Settings
    is_public: bool = True
    recruitment_open: bool = False
    max_members: int = 10
    
    # Achievements
    team_achievements: List[str] = field(default_factory=list)
    tournament_participations: List[str] = field(default_factory=list)


class SocialEngine(BaseService):
    """Main social features engine."""
    
    def __init__(self,
                 social_dir: str = "data/social",
                 challenges_dir: str = "data/challenges"):
        super().__init__()
        
        # Directory setup
        self.social_dir = Path(social_dir)
        self.challenges_dir = Path(challenges_dir)
        
        # Create directories
        for dir_path in [self.social_dir, self.challenges_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize sub-systems
        self.friend_system = FriendSystem(self.social_dir)
        self.mentorship_system = MentorshipSystem(self.social_dir)
        self.leaderboard_manager = LeaderboardManager(self.social_dir)
        
        # Storage
        self.challenges: Dict[str, CommunityChallenge] = {}
        self.teams: Dict[str, TeamData] = {}
        
        # Load existing data
        asyncio.create_task(self._initialize_social_data())
        
        logger.info("Social Engine initialized")
    
    async def _initialize_social_data(self):
        """Initialize social data."""
        await self._load_challenges()
        await self._load_teams()
        
        if not self.challenges:
            await self._create_default_challenges()
    
    async def _create_default_challenges(self):
        """Create default community challenges."""
        
        # Weekly Performance Challenge
        weekly_challenge = CommunityChallenge(
            challenge_id="weekly_performance",
            name="Weekly Performance Challenge",
            description="Achieve the highest average performance score this week",
            challenge_type=ChallengeType.COMMUNITY,
            status=ChallengeStatus.ACTIVE,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            requirements={"min_matches": 10, "min_performance": 5.0},
            rewards={
                "1st": {"xp": 1000, "badge": "🥇", "title": "Weekly Champion"},
                "2nd": {"xp": 750, "badge": "🥈"},
                "3rd": {"xp": 500, "badge": "🥉"},
                "participation": {"xp": 100}
            },
            scoring_method="average_performance",
            is_recurring=True,
            public_leaderboard=True
        )
        
        # Team Coordination Challenge
        team_challenge = CommunityChallenge(
            challenge_id="team_coordination",
            name="Team Coordination Masters",
            description="Form teams and achieve the highest team coordination score",
            challenge_type=ChallengeType.TEAM,
            status=ChallengeStatus.UPCOMING,
            start_date=datetime.now() + timedelta(days=3),
            end_date=datetime.now() + timedelta(days=10),
            requirements={"team_size": 5, "min_matches_together": 15},
            rewards={
                "winning_team": {"xp_per_member": 800, "team_badge": "🏆", "team_title": "Coordination Masters"}
            },
            allow_teams=True,
            max_team_size=5,
            scoring_method="team_coordination"
        )
        
        # Improvement Challenge
        improvement_challenge = CommunityChallenge(
            challenge_id="monthly_improvement",
            name="Monthly Improvement Challenge",
            description="Show the most improvement in performance over the month",
            challenge_type=ChallengeType.INDIVIDUAL,
            status=ChallengeStatus.ACTIVE,
            start_date=datetime.now().replace(day=1),
            end_date=(datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
            requirements={"min_matches_start": 10, "min_matches_end": 10},
            rewards={
                "most_improved": {"xp": 1500, "badge": "📈", "title": "Most Improved Player"},
                "top_10": {"xp": 300, "badge": "⬆️"}
            },
            scoring_method="improvement_rate"
        )
        
        # Store challenges
        challenges = [weekly_challenge, team_challenge, improvement_challenge]
        for challenge in challenges:
            self.challenges[challenge.challenge_id] = challenge
        
        logger.info(f"Created {len(challenges)} default challenges")
    
    async def create_team(self, team_name: str, captain_id: str, 
                         initial_members: List[str] = None) -> str:
        """Create a new team."""
        
        team_id = f"team_{len(self.teams):06d}"
        
        team = TeamData(
            team_id=team_id,
            team_name=team_name,
            captain_id=captain_id,
            members=[captain_id] + (initial_members or [])
        )
        
        self.teams[team_id] = team
        
        # Save team data
        await self._save_team_data(team_id, team)
        
        logger.info(f"Team created: {team_name} (ID: {team_id}) by captain {captain_id}")
        return team_id
    
    async def join_challenge(self, player_id: str, challenge_id: str, 
                           team_id: Optional[str] = None) -> bool:
        """Join a community challenge."""
        
        if challenge_id not in self.challenges:
            return False
        
        challenge = self.challenges[challenge_id]
        
        # Check if challenge is accepting participants
        if challenge.status != ChallengeStatus.ACTIVE:
            if challenge.status == ChallengeStatus.UPCOMING:
                # Allow registration for upcoming challenges
                pass
            else:
                return False
        
        # Check registration deadline
        if challenge.registration_deadline and datetime.now() > challenge.registration_deadline:
            return False
        
        # Check if already participating
        if player_id in challenge.participants:
            return True
        
        # Check participant limits
        if challenge.max_participants and len(challenge.participants) >= challenge.max_participants:
            return False
        
        # Add participant
        challenge.participants.add(player_id)
        challenge.total_registrations += 1
        
        # Handle team challenges
        if challenge.allow_teams and team_id:
            if team_id not in challenge.teams:
                challenge.teams[team_id] = []
            
            if len(challenge.teams[team_id]) < challenge.max_team_size:
                challenge.teams[team_id].append(player_id)
        
        # Save challenge data
        await self._save_challenge_data(challenge_id, challenge)
        
        logger.info(f"Player {player_id} joined challenge {challenge_id}")
        return True
    
    async def update_challenge_progress(self, challenge_id: str, 
                                      progress_data: Dict[str, Any]) -> bool:
        """Update progress for a challenge."""
        
        if challenge_id not in self.challenges:
            return False
        
        challenge = self.challenges[challenge_id]
        
        # Update leaderboard based on scoring method
        if challenge.scoring_method == "points":
            await self._update_points_leaderboard(challenge, progress_data)
        elif challenge.scoring_method == "average_performance":
            await self._update_performance_leaderboard(challenge, progress_data)
        elif challenge.scoring_method == "improvement_rate":
            await self._update_improvement_leaderboard(challenge, progress_data)
        elif challenge.scoring_method == "team_coordination":
            await self._update_team_leaderboard(challenge, progress_data)
        
        # Save updated challenge
        await self._save_challenge_data(challenge_id, challenge)
        
        return True
    
    async def _update_performance_leaderboard(self, challenge: CommunityChallenge, 
                                            progress_data: Dict[str, Any]):
        """Update performance-based leaderboard."""
        
        player_id = progress_data.get("player_id")
        performance_score = progress_data.get("performance_score", 0)
        
        if not player_id or player_id not in challenge.participants:
            return
        
        # Find existing entry or create new one
        existing_entry = None
        for entry in challenge.leaderboard:
            if entry.get("player_id") == player_id:
                existing_entry = entry
                break
        
        if existing_entry:
            # Update existing entry
            existing_entry["total_score"] += performance_score
            existing_entry["match_count"] += 1
            existing_entry["average_score"] = existing_entry["total_score"] / existing_entry["match_count"]
        else:
            # Create new entry
            challenge.leaderboard.append({
                "player_id": player_id,
                "player_name": progress_data.get("player_name", f"Player_{player_id}"),
                "total_score": performance_score,
                "match_count": 1,
                "average_score": performance_score,
                "last_updated": datetime.now().isoformat()
            })
        
        # Sort leaderboard by average score
        challenge.leaderboard.sort(key=lambda x: x["average_score"], reverse=True)
        
        # Update ranks
        for i, entry in enumerate(challenge.leaderboard):
            entry["rank"] = i + 1
    
    async def _update_improvement_leaderboard(self, challenge: CommunityChallenge, 
                                            progress_data: Dict[str, Any]):
        """Update improvement-based leaderboard."""
        
        player_id = progress_data.get("player_id")
        current_performance = progress_data.get("current_performance", 0)
        baseline_performance = progress_data.get("baseline_performance", 0)
        
        if not player_id or player_id not in challenge.participants:
            return
        
        improvement_rate = ((current_performance - baseline_performance) / max(1, baseline_performance)) * 100
        
        # Find existing entry or create new one
        existing_entry = None
        for entry in challenge.leaderboard:
            if entry.get("player_id") == player_id:
                existing_entry = entry
                break
        
        if existing_entry:
            existing_entry["improvement_rate"] = improvement_rate
            existing_entry["current_performance"] = current_performance
            existing_entry["baseline_performance"] = baseline_performance
        else:
            challenge.leaderboard.append({
                "player_id": player_id,
                "player_name": progress_data.get("player_name", f"Player_{player_id}"),
                "improvement_rate": improvement_rate,
                "current_performance": current_performance,
                "baseline_performance": baseline_performance,
                "last_updated": datetime.now().isoformat()
            })
        
        # Sort by improvement rate
        challenge.leaderboard.sort(key=lambda x: x["improvement_rate"], reverse=True)
        
        # Update ranks
        for i, entry in enumerate(challenge.leaderboard):
            entry["rank"] = i + 1
    
    async def get_active_challenges(self, player_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active challenges, optionally filtered for a player."""
        
        active_challenges = []
        
        for challenge in self.challenges.values():
            if challenge.status in [ChallengeStatus.ACTIVE, ChallengeStatus.UPCOMING]:
                challenge_data = asdict(challenge)
                
                # Convert sets to lists for JSON serialization
                challenge_data["participants"] = list(challenge.participants)
                
                # Add player-specific data if requested
                if player_id:
                    challenge_data["is_participating"] = player_id in challenge.participants
                    challenge_data["player_rank"] = None
                    
                    # Find player's rank in leaderboard
                    for entry in challenge.leaderboard:
                        if entry.get("player_id") == player_id:
                            challenge_data["player_rank"] = entry.get("rank")
                            break
                
                active_challenges.append(challenge_data)
        
        return active_challenges
    
    async def get_player_social_summary(self, player_id: str) -> Dict[str, Any]:
        """Get comprehensive social summary for a player."""
        
        summary = {
            "friends": await self.friend_system.get_friends_summary(player_id),
            "mentorship": await self.mentorship_system.get_mentorship_summary(player_id),
            "challenges": {
                "active_participations": 0,
                "completed_challenges": 0,
                "total_rewards_earned": 0,
                "best_rankings": []
            },
            "teams": [],
            "leaderboards": await self.leaderboard_manager.get_player_rankings(player_id),
            "social_stats": {
                "reputation_score": 0.0,
                "helpfulness_rating": 0.0,
                "community_contributions": 0
            }
        }
        
        # Count challenge participations
        active_participations = 0
        completed_challenges = 0
        best_rankings = []
        
        for challenge in self.challenges.values():
            if player_id in challenge.participants:
                if challenge.status == ChallengeStatus.ACTIVE:
                    active_participations += 1
                elif challenge.status == ChallengeStatus.COMPLETED:
                    completed_challenges += 1
                    
                    # Find player's final rank
                    for entry in challenge.leaderboard:
                        if entry.get("player_id") == player_id:
                            rank = entry.get("rank", 999)
                            if rank <= 10:  # Top 10 finishes
                                best_rankings.append({
                                    "challenge_name": challenge.name,
                                    "rank": rank,
                                    "total_participants": len(challenge.participants)
                                })
                            break
        
        summary["challenges"]["active_participations"] = active_participations
        summary["challenges"]["completed_challenges"] = completed_challenges
        summary["challenges"]["best_rankings"] = sorted(best_rankings, key=lambda x: x["rank"])[:5]
        
        # Find teams the player is in
        player_teams = []
        for team in self.teams.values():
            if player_id in team.members:
                team_data = {
                    "team_id": team.team_id,
                    "team_name": team.team_name,
                    "role": "captain" if team.captain_id == player_id else "member",
                    "win_rate": team.win_rate,
                    "matches_played": team.matches_played
                }
                player_teams.append(team_data)
        
        summary["teams"] = player_teams
        
        return summary
    
    async def _load_challenges(self):
        """Load challenges from disk."""
        challenges_file = self.challenges_dir / "challenges.json"
        
        if challenges_file.exists():
            try:
                with open(challenges_file, 'r') as f:
                    data = json.load(f)
                
                for challenge_data in data:
                    # Convert participants list back to set
                    if "participants" in challenge_data:
                        challenge_data["participants"] = set(challenge_data["participants"])
                    
                    challenge = CommunityChallenge(**challenge_data)
                    self.challenges[challenge.challenge_id] = challenge
                
                logger.info(f"Loaded {len(self.challenges)} challenges")
            except Exception as e:
                logger.error(f"Failed to load challenges: {e}")
    
    async def _load_teams(self):
        """Load teams from disk."""
        teams_file = self.social_dir / "teams.json"
        
        if teams_file.exists():
            try:
                with open(teams_file, 'r') as f:
                    data = json.load(f)
                
                for team_data in data:
                    team = TeamData(**team_data)
                    self.teams[team.team_id] = team
                
                logger.info(f"Loaded {len(self.teams)} teams")
            except Exception as e:
                logger.error(f"Failed to load teams: {e}")
    
    async def _save_challenge_data(self, challenge_id: str, challenge: CommunityChallenge):
        """Save individual challenge data."""
        challenge_file = self.challenges_dir / f"{challenge_id}.json"
        
        try:
            data = asdict(challenge)
            # Handle datetime and set serialization
            data['start_date'] = challenge.start_date.isoformat()
            data['end_date'] = challenge.end_date.isoformat()
            if challenge.registration_deadline:
                data['registration_deadline'] = challenge.registration_deadline.isoformat()
            data['participants'] = list(challenge.participants)
            
            with open(challenge_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save challenge data: {e}")
    
    async def _save_team_data(self, team_id: str, team: TeamData):
        """Save individual team data."""
        team_file = self.social_dir / f"{team_id}.json"
        
        try:
            data = asdict(team)
            # Handle datetime serialization
            data['created_date'] = team.created_date.isoformat()
            data['last_activity'] = team.last_activity.isoformat()
            
            with open(team_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save team data: {e}")
    
    async def process(self, request: Dict[str, Any]) -> ServiceResult:
        """Process social engine requests."""
        try:
            action = request.get('action', 'get_social_summary')
            
            if action == 'create_team':
                team_name = request.get('team_name')
                captain_id = request.get('captain_id')
                initial_members = request.get('initial_members', [])
                
                team_id = await self.create_team(team_name, captain_id, initial_members)
                
                return ServiceResult(
                    success=True,
                    data={'team_id': team_id},
                    metadata={'action': 'create_team'}
                )
                
            elif action == 'join_challenge':
                player_id = request.get('player_id')
                challenge_id = request.get('challenge_id')
                team_id = request.get('team_id')
                
                success = await self.join_challenge(player_id, challenge_id, team_id)
                
                return ServiceResult(
                    success=success,
                    data={'joined': success},
                    metadata={'action': 'join_challenge'}
                )
                
            elif action == 'get_active_challenges':
                player_id = request.get('player_id')
                challenges = await self.get_active_challenges(player_id)
                
                return ServiceResult(
                    success=True,
                    data=challenges,
                    metadata={'action': 'get_active_challenges', 'count': len(challenges)}
                )
                
            elif action == 'get_social_summary':
                player_id = request.get('player_id')
                summary = await self.get_player_social_summary(player_id)
                
                return ServiceResult(
                    success=True,
                    data=summary,
                    metadata={'action': 'get_social_summary', 'player_id': player_id}
                )
                
            elif action == 'update_challenge_progress':
                challenge_id = request.get('challenge_id')
                progress_data = request.get('progress_data', {})
                
                success = await self.update_challenge_progress(challenge_id, progress_data)
                
                return ServiceResult(
                    success=success,
                    data={'updated': success},
                    metadata={'action': 'update_challenge_progress'}
                )
                
            else:
                return ServiceResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            logger.error(f"Social engine error: {str(e)}")
            return ServiceResult(
                success=False,
                error=str(e)
            )


class FriendSystem:
    """Friend system management."""
    
    def __init__(self, social_dir: Path):
        self.social_dir = social_dir
        self.friendships: Dict[str, List[Friend]] = defaultdict(list)
    
    async def send_friend_request(self, requester_id: str, recipient_id: str) -> bool:
        """Send a friend request."""
        
        # Check if friendship already exists
        existing = await self._get_friendship(requester_id, recipient_id)
        if existing:
            return False
        
        # Create friend request
        friendship = Friend(
            requester_id=requester_id,
            recipient_id=recipient_id,
            status=FriendshipStatus.PENDING
        )
        
        self.friendships[requester_id].append(friendship)
        self.friendships[recipient_id].append(friendship)
        
        return True
    
    async def accept_friend_request(self, requester_id: str, recipient_id: str) -> bool:
        """Accept a friend request."""
        
        friendship = await self._get_friendship(requester_id, recipient_id)
        if not friendship or friendship.status != FriendshipStatus.PENDING:
            return False
        
        friendship.status = FriendshipStatus.ACCEPTED
        friendship.accepted_date = datetime.now()
        
        return True
    
    async def _get_friendship(self, player1_id: str, player2_id: str) -> Optional[Friend]:
        """Get friendship between two players."""
        
        for friendship in self.friendships[player1_id]:
            if ((friendship.requester_id == player1_id and friendship.recipient_id == player2_id) or
                (friendship.requester_id == player2_id and friendship.recipient_id == player1_id)):
                return friendship
        
        return None
    
    async def get_friends_summary(self, player_id: str) -> Dict[str, Any]:
        """Get friends summary for a player."""
        
        friends_list = []
        pending_requests = []
        sent_requests = []
        
        for friendship in self.friendships[player_id]:
            if friendship.status == FriendshipStatus.ACCEPTED:
                friend_id = (friendship.recipient_id if friendship.requester_id == player_id 
                           else friendship.requester_id)
                friends_list.append({
                    "friend_id": friend_id,
                    "matches_together": friendship.matches_together,
                    "last_interaction": friendship.last_interaction.isoformat() if friendship.last_interaction else None
                })
            elif friendship.status == FriendshipStatus.PENDING:
                if friendship.recipient_id == player_id:
                    pending_requests.append(friendship.requester_id)
                else:
                    sent_requests.append(friendship.recipient_id)
        
        return {
            "friends": friends_list,
            "pending_requests": pending_requests,
            "sent_requests": sent_requests,
            "total_friends": len(friends_list)
        }


class MentorshipSystem:
    """Mentorship system management."""
    
    def __init__(self, social_dir: Path):
        self.social_dir = social_dir
        self.mentorships: Dict[str, List[MentorshipRelation]] = defaultdict(list)
    
    async def create_mentorship(self, mentor_id: str, mentee_id: str, 
                              focus_areas: List[str]) -> str:
        """Create a new mentorship relationship."""
        
        mentorship = MentorshipRelation(
            mentor_id=mentor_id,
            mentee_id=mentee_id,
            status=MentorshipStatus.ACTIVE,
            focus_areas=focus_areas,
            end_date=datetime.now() + timedelta(weeks=4)
        )
        
        relation_id = f"{mentor_id}_{mentee_id}_{datetime.now().strftime('%Y%m%d')}"
        
        self.mentorships[mentor_id].append(mentorship)
        self.mentorships[mentee_id].append(mentorship)
        
        return relation_id
    
    async def get_mentorship_summary(self, player_id: str) -> Dict[str, Any]:
        """Get mentorship summary for a player."""
        
        as_mentor = []
        as_mentee = []
        
        for mentorship in self.mentorships[player_id]:
            if mentorship.mentor_id == player_id:
                as_mentor.append({
                    "mentee_id": mentorship.mentee_id,
                    "status": mentorship.status.value,
                    "sessions_completed": mentorship.sessions_completed,
                    "focus_areas": mentorship.focus_areas
                })
            else:
                as_mentee.append({
                    "mentor_id": mentorship.mentor_id,
                    "status": mentorship.status.value,
                    "sessions_completed": mentorship.sessions_completed,
                    "focus_areas": mentorship.focus_areas
                })
        
        return {
            "as_mentor": as_mentor,
            "as_mentee": as_mentee,
            "total_mentorships": len(as_mentor) + len(as_mentee)
        }


class LeaderboardManager:
    """Leaderboard management system."""
    
    def __init__(self, social_dir: Path):
        self.social_dir = social_dir
        self.leaderboards: Dict[LeaderboardType, List[LeaderboardEntry]] = {}
    
    async def get_player_rankings(self, player_id: str) -> Dict[str, Any]:
        """Get player's rankings across all leaderboards."""
        
        rankings = {}
        
        for leaderboard_type, entries in self.leaderboards.items():
            for entry in entries:
                if entry.player_id == player_id:
                    rankings[leaderboard_type.value] = {
                        "rank": entry.rank,
                        "score": entry.score,
                        "trend": entry.trend
                    }
                    break
        
        return rankings


# Global social engine instance
_social_engine = None

def get_social_engine() -> SocialEngine:
    """Get global social engine instance."""
    global _social_engine
    if _social_engine is None:
        _social_engine = SocialEngine()
    return _social_engine
