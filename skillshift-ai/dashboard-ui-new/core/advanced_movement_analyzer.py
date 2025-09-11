#!/usr/bin/env python3
"""
Advanced Movement Pattern Analyzer - Task 9: Minimap Movement Tracking
======================================================================

This module analyzes player movement patterns from both synthetic and real data,
providing tactical insights and behavioral analysis for MLBB coaching.

Features:
- Advanced movement pattern recognition
- Tactical positioning analysis
- Rotation timing optimization
- Map control assessment
- Team coordination evaluation
- Performance metrics generation
"""

import numpy as np
import cv2
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import math
import statistics
from collections import defaultdict, deque
import time

# Import existing components
from .minimap_tracker import Position, MovementEvent, LaneType, MinimapRegion
from .synthetic_minimap_generator import MovementPattern, HeroRole, SyntheticPlayer
from .video_reader import TimestampedFrame

logger = logging.getLogger(__name__)


class TacticalInsight(Enum):
    """Types of tactical insights"""
    POOR_POSITIONING = "poor_positioning"
    GOOD_ROTATION = "good_rotation"
    MISSED_OPPORTUNITY = "missed_opportunity"
    OVEREXTENDED = "overextended"
    GOOD_MAP_CONTROL = "good_map_control"
    POOR_TEAM_COORDINATION = "poor_team_coordination"
    EFFICIENT_FARMING = "efficient_farming"
    WASTED_TIME = "wasted_time"


@dataclass
class MovementMetrics:
    """Comprehensive movement metrics for a player"""
    player_id: str
    total_distance: float = 0.0
    average_speed: float = 0.0
    time_in_lanes: Dict[str, float] = field(default_factory=dict)
    rotation_count: int = 0
    rotation_efficiency: float = 0.0
    map_coverage: float = 0.0
    team_coordination_score: float = 0.0
    positioning_score: float = 0.0
    farming_efficiency: float = 0.0
    
    def __post_init__(self):
        if not self.time_in_lanes:
            self.time_in_lanes = {
                "top": 0.0, "mid": 0.0, "bot": 0.0, 
                "jungle": 0.0, "river": 0.0, "base": 0.0
            }


@dataclass
class TacticalRecommendation:
    """Tactical recommendation based on movement analysis"""
    insight_type: TacticalInsight
    severity: str  # "low", "medium", "high", "critical"
    description: str
    recommendation: str
    timestamp: float
    player_id: str
    confidence: float = 0.0
    impact_score: float = 0.0


@dataclass
class TeamMovementAnalysis:
    """Team-level movement analysis"""
    team_id: str
    coordination_score: float = 0.0
    map_control_percentage: float = 0.0
    rotation_synchronization: float = 0.0
    objective_control: float = 0.0
    positioning_quality: float = 0.0
    recommendations: List[TacticalRecommendation] = field(default_factory=list)


class AdvancedMovementAnalyzer:
    """Advanced analyzer for player movement patterns and tactical insights"""
    
    def __init__(self):
        self.movement_history = defaultdict(list)
        self.position_history = defaultdict(deque)
        self.tactical_insights = []
        
        # Analysis parameters
        self.analysis_window = 30.0  # 30 second analysis window
        self.position_history_limit = 100  # Keep last 100 positions
        self.rotation_threshold = 0.3  # Distance threshold for rotation detection
        self.team_coordination_radius = 0.2  # Radius for team coordination analysis
        
        # Lane boundaries (normalized coordinates)
        self.lane_boundaries = {
            "top": {"x_min": 0.0, "x_max": 1.0, "y_min": 0.0, "y_max": 0.4},
            "mid": {"x_min": 0.2, "x_max": 0.8, "y_min": 0.3, "y_max": 0.7},
            "bot": {"x_min": 0.0, "x_max": 1.0, "y_min": 0.6, "y_max": 1.0},
            "jungle": {"x_min": 0.1, "x_max": 0.9, "y_min": 0.1, "y_max": 0.9},
            "river": {"x_min": 0.4, "x_max": 0.6, "y_min": 0.0, "y_max": 1.0}
        }
        
        logger.info("🧠 Advanced Movement Analyzer initialized")
    
    def analyze_movement_sequence(
        self, 
        movement_events: List[MovementEvent],
        players: List[SyntheticPlayer] = None
    ) -> Dict[str, Any]:
        """Analyze complete movement sequence and generate insights"""
        
        logger.info(f"📊 Analyzing {len(movement_events)} movement events")
        
        # Group events by player
        player_events = defaultdict(list)
        for event in movement_events:
            player_events[event.player_ign].append(event)
        
        # Analyze each player
        player_metrics = {}
        for player_id, events in player_events.items():
            metrics = self._analyze_player_movements(player_id, events)
            player_metrics[player_id] = metrics
        
        # Team-level analysis
        team_analysis = self._analyze_team_coordination(movement_events, players)
        
        # Generate tactical insights
        tactical_insights = self._generate_tactical_insights(player_metrics, team_analysis)
        
        # Create comprehensive analysis result
        analysis_result = {
            "timestamp": time.time(),
            "total_events": len(movement_events),
            "analysis_duration": movement_events[-1].timestamp - movement_events[0].timestamp if movement_events else 0,
            "player_metrics": {pid: self._metrics_to_dict(metrics) for pid, metrics in player_metrics.items()},
            "team_analysis": {
                "ally_team": self._team_analysis_to_dict(team_analysis.get("ally", TeamMovementAnalysis("ally"))),
                "enemy_team": self._team_analysis_to_dict(team_analysis.get("enemy", TeamMovementAnalysis("enemy")))
            },
            "tactical_insights": [self._recommendation_to_dict(insight) for insight in tactical_insights],
            "summary_scores": self._calculate_summary_scores(player_metrics, team_analysis)
        }
        
        logger.info(f"✅ Movement analysis completed - {len(tactical_insights)} insights generated")
        
        return analysis_result
    
    def _analyze_player_movements(self, player_id: str, events: List[MovementEvent]) -> MovementMetrics:
        """Analyze movement patterns for a single player"""
        
        if not events:
            return MovementMetrics(player_id)
        
        metrics = MovementMetrics(player_id)
        
        # Calculate basic movement metrics
        total_distance = 0.0
        positions = []
        
        for event in events:
            # Calculate distance moved
            distance = self._calculate_distance(event.from_position, event.to_position)
            total_distance += distance
            positions.append(event.to_position)
        
        metrics.total_distance = total_distance
        
        # Calculate average speed
        if events:
            time_span = events[-1].timestamp - events[0].timestamp
            metrics.average_speed = total_distance / max(time_span, 1.0)
        
        # Analyze time spent in different lanes
        metrics.time_in_lanes = self._calculate_lane_time(events)
        
        # Count rotations
        metrics.rotation_count = self._count_rotations(events)
        
        # Calculate rotation efficiency
        metrics.rotation_efficiency = self._calculate_rotation_efficiency(events)
        
        # Calculate map coverage
        metrics.map_coverage = self._calculate_map_coverage(positions)
        
        # Calculate positioning score
        metrics.positioning_score = self._calculate_positioning_score(events)
        
        # Calculate farming efficiency
        metrics.farming_efficiency = self._calculate_farming_efficiency(events)
        
        return metrics
    
    def _calculate_distance(self, pos1: Position, pos2: Position) -> float:
        """Calculate Euclidean distance between two positions"""
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        return math.sqrt(dx*dx + dy*dy)
    
    def _calculate_lane_time(self, events: List[MovementEvent]) -> Dict[str, float]:
        """Calculate time spent in each lane"""
        
        lane_time = {"top": 0.0, "mid": 0.0, "bot": 0.0, "jungle": 0.0, "river": 0.0, "base": 0.0}
        
        for i, event in enumerate(events[:-1]):
            current_lane = self._get_lane_from_position(event.to_position)
            next_event = events[i + 1]
            time_diff = next_event.timestamp - event.timestamp
            
            lane_time[current_lane] += time_diff
        
        return lane_time
    
    def _get_lane_from_position(self, position: Position) -> str:
        """Determine which lane a position belongs to"""
        
        x, y = position.x, position.y
        
        # Check if in base area
        if (x < 0.2 and y > 0.8) or (x > 0.8 and y < 0.2):
            return "base"
        
        # Check river (middle area)
        if 0.4 <= x <= 0.6:
            return "river"
        
        # Check lanes
        if y < 0.4:
            return "top"
        elif y > 0.6:
            return "bot"
        else:
            return "mid"
    
    def _count_rotations(self, events: List[MovementEvent]) -> int:
        """Count significant rotations (lane changes)"""
        
        if len(events) < 2:
            return 0
        
        rotations = 0
        current_lane = self._get_lane_from_position(events[0].to_position)
        
        for event in events[1:]:
            new_lane = self._get_lane_from_position(event.to_position)
            if new_lane != current_lane and new_lane != "river":  # Ignore river transitions
                rotations += 1
                current_lane = new_lane
        
        return rotations
    
    def _calculate_rotation_efficiency(self, events: List[MovementEvent]) -> float:
        """Calculate rotation efficiency score (0-1)"""
        
        if len(events) < 5:
            return 0.5  # Neutral score for insufficient data
        
        # Look for efficient rotations (direct paths, good timing)
        efficient_rotations = 0
        total_rotations = 0
        
        for i in range(len(events) - 2):
            # Check if this is a rotation
            start_lane = self._get_lane_from_position(events[i].to_position)
            end_lane = self._get_lane_from_position(events[i + 2].to_position)
            
            if start_lane != end_lane:
                total_rotations += 1
                
                # Check efficiency factors
                distance = self._calculate_distance(events[i].to_position, events[i + 2].to_position)
                time_taken = events[i + 2].timestamp - events[i].timestamp
                
                # Efficient if reasonable speed and direct path
                if distance > 0 and time_taken > 0:
                    speed = distance / time_taken
                    if 0.02 <= speed <= 0.1:  # Reasonable movement speed
                        efficient_rotations += 1
        
        return efficient_rotations / max(total_rotations, 1)
    
    def _calculate_map_coverage(self, positions: List[Position]) -> float:
        """Calculate what percentage of the map the player has covered"""
        
        if not positions:
            return 0.0
        
        # Create a grid to track visited areas
        grid_size = 20
        visited = set()
        
        for pos in positions:
            grid_x = int(pos.x * grid_size)
            grid_y = int(pos.y * grid_size)
            visited.add((grid_x, grid_y))
        
        # Calculate coverage percentage
        total_cells = grid_size * grid_size
        coverage = len(visited) / total_cells
        
        return min(coverage, 1.0)
    
    def _calculate_positioning_score(self, events: List[MovementEvent]) -> float:
        """Calculate positioning quality score (0-1)"""
        
        if not events:
            return 0.5
        
        good_positions = 0
        total_positions = len(events)
        
        for event in events:
            pos = event.to_position
            
            # Good positioning criteria
            score = 0.0
            
            # Not too close to edges (avoid overextending)
            edge_distance = min(pos.x, 1-pos.x, pos.y, 1-pos.y)
            if edge_distance > 0.1:
                score += 0.3
            
            # Good lane positioning
            lane = self._get_lane_from_position(pos)
            if lane in ["top", "mid", "bot"]:
                score += 0.4
            elif lane == "jungle":
                score += 0.2
            
            # Not staying in base too long
            if lane != "base":
                score += 0.3
            
            if score > 0.6:
                good_positions += 1
        
        return good_positions / max(total_positions, 1)
    
    def _calculate_farming_efficiency(self, events: List[MovementEvent]) -> float:
        """Calculate farming efficiency based on jungle/lane presence"""
        
        if not events:
            return 0.5
        
        # Look for patterns indicating efficient farming
        jungle_time = 0.0
        lane_time = 0.0
        total_time = 0.0
        
        for i, event in enumerate(events[:-1]):
            next_event = events[i + 1]
            time_diff = next_event.timestamp - event.timestamp
            total_time += time_diff
            
            lane = self._get_lane_from_position(event.to_position)
            if lane == "jungle":
                jungle_time += time_diff
            elif lane in ["top", "mid", "bot"]:
                lane_time += time_diff
        
        if total_time > 0:
            # Good balance of jungle and lane farming
            jungle_ratio = jungle_time / total_time
            lane_ratio = lane_time / total_time
            
            # Optimal ratios depend on role, but generally 20-40% jungle is good
            if 0.2 <= jungle_ratio <= 0.4 and lane_ratio > 0.3:
                return 0.8
            elif jungle_ratio > 0.1 and lane_ratio > 0.2:
                return 0.6
            else:
                return 0.4
        
        return 0.5
    
    def _analyze_team_coordination(
        self, 
        movement_events: List[MovementEvent],
        players: List[SyntheticPlayer] = None
    ) -> Dict[str, TeamMovementAnalysis]:
        """Analyze team-level coordination and map control"""
        
        # Group events by team
        team_events = {"ally": [], "enemy": []}
        
        for event in movement_events:
            if "ally" in event.player_ign:
                team_events["ally"].append(event)
            elif "enemy" in event.player_ign:
                team_events["enemy"].append(event)
        
        team_analysis = {}
        
        for team_id, events in team_events.items():
            analysis = TeamMovementAnalysis(team_id)
            
            if events:
                # Calculate coordination score
                analysis.coordination_score = self._calculate_team_coordination_score(events)
                
                # Calculate map control
                analysis.map_control_percentage = self._calculate_map_control(events)
                
                # Calculate rotation synchronization
                analysis.rotation_synchronization = self._calculate_rotation_sync(events)
                
                # Calculate objective control
                analysis.objective_control = self._calculate_objective_control(events)
                
                # Calculate positioning quality
                analysis.positioning_quality = self._calculate_team_positioning_quality(events)
            
            team_analysis[team_id] = analysis
        
        return team_analysis
    
    def _calculate_team_coordination_score(self, events: List[MovementEvent]) -> float:
        """Calculate how well the team coordinates movements"""
        
        if len(events) < 10:
            return 0.5
        
        # Group events by timestamp windows
        time_windows = defaultdict(list)
        window_size = 10.0  # 10 second windows
        
        for event in events:
            window = int(event.timestamp / window_size)
            time_windows[window].append(event)
        
        coordination_scores = []
        
        for window, window_events in time_windows.items():
            if len(window_events) >= 2:
                # Check if players are moving in coordinated fashion
                positions = [event.to_position for event in window_events]
                
                # Calculate average distance between teammates
                distances = []
                for i in range(len(positions)):
                    for j in range(i + 1, len(positions)):
                        distance = self._calculate_distance(positions[i], positions[j])
                        distances.append(distance)
                
                if distances:
                    avg_distance = statistics.mean(distances)
                    # Good coordination if teammates are reasonably close (but not too close)
                    if 0.1 <= avg_distance <= 0.4:
                        coordination_scores.append(0.8)
                    elif 0.05 <= avg_distance <= 0.6:
                        coordination_scores.append(0.6)
                    else:
                        coordination_scores.append(0.3)
        
        return statistics.mean(coordination_scores) if coordination_scores else 0.5
    
    def _calculate_map_control(self, events: List[MovementEvent]) -> float:
        """Calculate team's map control percentage"""
        
        if not events:
            return 0.0
        
        # Create presence map
        grid_size = 10
        presence_grid = np.zeros((grid_size, grid_size))
        
        for event in events:
            grid_x = int(event.to_position.x * (grid_size - 1))
            grid_y = int(event.to_position.y * (grid_size - 1))
            presence_grid[grid_y, grid_x] += 1
        
        # Calculate controlled areas (areas with significant presence)
        controlled_cells = np.sum(presence_grid > 2)  # More than 2 visits
        total_cells = grid_size * grid_size
        
        return controlled_cells / total_cells
    
    def _calculate_rotation_sync(self, events: List[MovementEvent]) -> float:
        """Calculate how synchronized team rotations are"""
        
        # Group by players
        player_events = defaultdict(list)
        for event in events:
            player_events[event.player_ign].append(event)
        
        # Find rotation times for each player
        player_rotations = {}
        for player_id, player_events_list in player_events.items():
            rotations = []
            current_lane = None
            
            for event in player_events_list:
                lane = self._get_lane_from_position(event.to_position)
                if current_lane and lane != current_lane and lane != "river":
                    rotations.append(event.timestamp)
                current_lane = lane
            
            player_rotations[player_id] = rotations
        
        # Calculate synchronization score
        if len(player_rotations) < 2:
            return 0.5
        
        sync_scores = []
        rotation_lists = list(player_rotations.values())
        
        for i in range(len(rotation_lists)):
            for j in range(i + 1, len(rotation_lists)):
                # Find synchronized rotations (within 15 seconds)
                sync_count = 0
                total_rotations = max(len(rotation_lists[i]), len(rotation_lists[j]))
                
                for rot_time_i in rotation_lists[i]:
                    for rot_time_j in rotation_lists[j]:
                        if abs(rot_time_i - rot_time_j) <= 15.0:
                            sync_count += 1
                            break
                
                if total_rotations > 0:
                    sync_scores.append(sync_count / total_rotations)
        
        return statistics.mean(sync_scores) if sync_scores else 0.5
    
    def _calculate_objective_control(self, events: List[MovementEvent]) -> float:
        """Calculate team's objective area control"""
        
        # Define objective areas
        lord_area = Position(0.5, 0.2)
        turtle_area = Position(0.5, 0.8)
        objective_radius = 0.15
        
        objective_presence = 0
        total_events = len(events)
        
        for event in events:
            pos = event.to_position
            
            # Check if near lord
            if self._calculate_distance(pos, lord_area) <= objective_radius:
                objective_presence += 1
            # Check if near turtle
            elif self._calculate_distance(pos, turtle_area) <= objective_radius:
                objective_presence += 1
        
        return objective_presence / max(total_events, 1)
    
    def _calculate_team_positioning_quality(self, events: List[MovementEvent]) -> float:
        """Calculate overall team positioning quality"""
        
        if not events:
            return 0.5
        
        position_scores = []
        
        for event in events:
            pos = event.to_position
            
            # Individual positioning score
            score = 0.0
            
            # Good lane presence
            lane = self._get_lane_from_position(pos)
            if lane in ["top", "mid", "bot"]:
                score += 0.4
            elif lane == "jungle":
                score += 0.3
            elif lane == "river":
                score += 0.2
            
            # Not overextended
            edge_distance = min(pos.x, 1-pos.x, pos.y, 1-pos.y)
            if edge_distance > 0.1:
                score += 0.3
            
            # Map presence
            if 0.1 <= pos.x <= 0.9 and 0.1 <= pos.y <= 0.9:
                score += 0.3
            
            position_scores.append(score)
        
        return statistics.mean(position_scores) if position_scores else 0.5
    
    def _generate_tactical_insights(
        self, 
        player_metrics: Dict[str, MovementMetrics],
        team_analysis: Dict[str, TeamMovementAnalysis]
    ) -> List[TacticalRecommendation]:
        """Generate tactical recommendations based on analysis"""
        
        recommendations = []
        
        # Player-specific insights
        for player_id, metrics in player_metrics.items():
            
            # Poor positioning
            if metrics.positioning_score < 0.4:
                recommendations.append(TacticalRecommendation(
                    insight_type=TacticalInsight.POOR_POSITIONING,
                    severity="high",
                    description=f"Player {player_id} has poor positioning (score: {metrics.positioning_score:.2f})",
                    recommendation="Focus on safer positioning, avoid overextending, stay closer to team",
                    timestamp=time.time(),
                    player_id=player_id,
                    confidence=0.8,
                    impact_score=0.7
                ))
            
            # Low rotation efficiency
            if metrics.rotation_efficiency < 0.3:
                recommendations.append(TacticalRecommendation(
                    insight_type=TacticalInsight.WASTED_TIME,
                    severity="medium",
                    description=f"Player {player_id} has inefficient rotations (efficiency: {metrics.rotation_efficiency:.2f})",
                    recommendation="Plan rotations better, take more direct paths, improve timing",
                    timestamp=time.time(),
                    player_id=player_id,
                    confidence=0.7,
                    impact_score=0.5
                ))
            
            # Low map coverage
            if metrics.map_coverage < 0.2:
                recommendations.append(TacticalRecommendation(
                    insight_type=TacticalInsight.MISSED_OPPORTUNITY,
                    severity="medium",
                    description=f"Player {player_id} has limited map presence (coverage: {metrics.map_coverage:.2f})",
                    recommendation="Explore more areas of the map, help other lanes, control key areas",
                    timestamp=time.time(),
                    player_id=player_id,
                    confidence=0.6,
                    impact_score=0.4
                ))
            
            # Good performance recognition
            if metrics.positioning_score > 0.7 and metrics.rotation_efficiency > 0.6:
                recommendations.append(TacticalRecommendation(
                    insight_type=TacticalInsight.GOOD_ROTATION,
                    severity="low",
                    description=f"Player {player_id} shows excellent movement patterns",
                    recommendation="Keep up the good positioning and efficient rotations",
                    timestamp=time.time(),
                    player_id=player_id,
                    confidence=0.9,
                    impact_score=0.3
                ))
        
        # Team-level insights
        for team_id, analysis in team_analysis.items():
            
            # Poor team coordination
            if analysis.coordination_score < 0.4:
                recommendations.append(TacticalRecommendation(
                    insight_type=TacticalInsight.POOR_TEAM_COORDINATION,
                    severity="high",
                    description=f"Team {team_id} has poor coordination (score: {analysis.coordination_score:.2f})",
                    recommendation="Improve team communication, coordinate rotations, group for objectives",
                    timestamp=time.time(),
                    player_id=f"team_{team_id}",
                    confidence=0.8,
                    impact_score=0.8
                ))
            
            # Good map control
            if analysis.map_control_percentage > 0.6:
                recommendations.append(TacticalRecommendation(
                    insight_type=TacticalInsight.GOOD_MAP_CONTROL,
                    severity="low",
                    description=f"Team {team_id} has excellent map control ({analysis.map_control_percentage:.1%})",
                    recommendation="Maintain map presence and use it to secure objectives",
                    timestamp=time.time(),
                    player_id=f"team_{team_id}",
                    confidence=0.9,
                    impact_score=0.6
                ))
        
        # Sort by impact score
        recommendations.sort(key=lambda x: x.impact_score, reverse=True)
        
        return recommendations
    
    def _calculate_summary_scores(
        self, 
        player_metrics: Dict[str, MovementMetrics],
        team_analysis: Dict[str, TeamMovementAnalysis]
    ) -> Dict[str, float]:
        """Calculate overall summary scores"""
        
        summary = {
            "overall_movement_quality": 0.0,
            "team_coordination": 0.0,
            "map_control": 0.0,
            "tactical_awareness": 0.0
        }
        
        if player_metrics:
            # Overall movement quality
            positioning_scores = [m.positioning_score for m in player_metrics.values()]
            rotation_scores = [m.rotation_efficiency for m in player_metrics.values()]
            farming_scores = [m.farming_efficiency for m in player_metrics.values()]
            
            summary["overall_movement_quality"] = statistics.mean(
                positioning_scores + rotation_scores + farming_scores
            )
        
        if team_analysis:
            # Team coordination
            coord_scores = [t.coordination_score for t in team_analysis.values()]
            summary["team_coordination"] = statistics.mean(coord_scores) if coord_scores else 0.0
            
            # Map control
            map_scores = [t.map_control_percentage for t in team_analysis.values()]
            summary["map_control"] = statistics.mean(map_scores) if map_scores else 0.0
            
            # Tactical awareness
            positioning_scores = [t.positioning_quality for t in team_analysis.values()]
            objective_scores = [t.objective_control for t in team_analysis.values()]
            summary["tactical_awareness"] = statistics.mean(
                positioning_scores + objective_scores
            ) if (positioning_scores and objective_scores) else 0.0
        
        return summary
    
    # Helper methods for data serialization
    def _metrics_to_dict(self, metrics: MovementMetrics) -> Dict[str, Any]:
        """Convert MovementMetrics to dictionary"""
        return {
            "player_id": metrics.player_id,
            "total_distance": metrics.total_distance,
            "average_speed": metrics.average_speed,
            "time_in_lanes": metrics.time_in_lanes,
            "rotation_count": metrics.rotation_count,
            "rotation_efficiency": metrics.rotation_efficiency,
            "map_coverage": metrics.map_coverage,
            "team_coordination_score": metrics.team_coordination_score,
            "positioning_score": metrics.positioning_score,
            "farming_efficiency": metrics.farming_efficiency
        }
    
    def _team_analysis_to_dict(self, analysis: TeamMovementAnalysis) -> Dict[str, Any]:
        """Convert TeamMovementAnalysis to dictionary"""
        return {
            "team_id": analysis.team_id,
            "coordination_score": analysis.coordination_score,
            "map_control_percentage": analysis.map_control_percentage,
            "rotation_synchronization": analysis.rotation_synchronization,
            "objective_control": analysis.objective_control,
            "positioning_quality": analysis.positioning_quality
        }
    
    def _recommendation_to_dict(self, rec: TacticalRecommendation) -> Dict[str, Any]:
        """Convert TacticalRecommendation to dictionary"""
        return {
            "insight_type": rec.insight_type.value,
            "severity": rec.severity,
            "description": rec.description,
            "recommendation": rec.recommendation,
            "timestamp": rec.timestamp,
            "player_id": rec.player_id,
            "confidence": rec.confidence,
            "impact_score": rec.impact_score
        }
    
    def save_analysis_result(self, analysis_result: Dict[str, Any], filename: str):
        """Save analysis result to JSON file"""
        
        output_path = Path("temp/movement_analysis") / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(analysis_result, f, indent=2)
        
        logger.info(f"💾 Analysis result saved to {output_path}")


def analyze_synthetic_movement_data(data_file: str) -> Dict[str, Any]:
    """Analyze synthetic movement data from file"""
    
    logger.info(f"📊 Analyzing synthetic movement data from {data_file}")
    
    # Load data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    # Convert to MovementEvent objects
    movement_events = []
    for event_data in data["events"]:
        event = MovementEvent(
            timestamp=event_data["timestamp"],
            frame_number=event_data["frame_number"],
            from_position=Position(
                event_data["from_position"]["x"],
                event_data["from_position"]["y"]
            ),
            to_position=Position(
                event_data["to_position"]["x"],
                event_data["to_position"]["y"]
            ),
            from_region=MinimapRegion(event_data["from_region"]),
            to_region=MinimapRegion(event_data["to_region"]),
            movement_type=event_data["movement_type"],
            distance=event_data["distance"],
            duration=event_data["duration"],
            confidence=event_data["confidence"],
            player_ign=event_data["player_ign"]
        )
        movement_events.append(event)
    
    # Create analyzer and analyze
    analyzer = AdvancedMovementAnalyzer()
    analysis_result = analyzer.analyze_movement_sequence(movement_events)
    
    # Save analysis result
    analyzer.save_analysis_result(
        analysis_result, 
        f"analysis_{Path(data_file).stem}.json"
    )
    
    return analysis_result


if __name__ == "__main__":
    # Example usage
    print("🧠 Advanced Movement Analyzer - Task 9")
    print("Use analyze_synthetic_movement_data() to analyze movement data files")
