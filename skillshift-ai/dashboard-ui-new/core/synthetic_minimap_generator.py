#!/usr/bin/env python3
"""
Synthetic Minimap Data Generator - Task 9: Minimap Movement Tracking
====================================================================

This module generates synthetic minimap data and movement patterns for testing
and training minimap tracking algorithms WITHOUT requiring real video datasets.

Features:
- Generate realistic MLBB minimap layouts
- Simulate player movement patterns
- Create synthetic video sequences
- Generate training data for movement tracking
- Provide realistic game scenarios
"""

import cv2
import numpy as np
import json
import random
import math
import time
from typing import Dict, List, Any, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

# Import existing components
from .minimap_tracker import LaneType, MinimapRegion, Position, MovementEvent
from .video_reader import TimestampedFrame

logger = logging.getLogger(__name__)


class MovementPattern(Enum):
    """Types of movement patterns to simulate"""
    LANING = "laning"           # Staying in lane
    ROAMING = "roaming"         # Moving between lanes
    JUNGLE_CLEAR = "jungle_clear"  # Clearing jungle camps
    TEAM_FIGHT = "team_fight"   # Group fighting
    RETREAT = "retreat"         # Falling back
    PUSH = "push"              # Advancing/pushing
    GANK = "gank"              # Ganking enemy
    RECALL = "recall"          # Going back to base


class HeroRole(Enum):
    """MLBB hero roles with typical movement patterns"""
    TANK = "tank"
    MARKSMAN = "marksman"
    ASSASSIN = "assassin"
    MAGE = "mage"
    SUPPORT = "support"
    FIGHTER = "fighter"


@dataclass
class SyntheticPlayer:
    """Synthetic player with movement characteristics"""
    player_id: str
    role: HeroRole
    team: str  # "ally" or "enemy"
    color: Tuple[int, int, int]  # BGR color for visualization
    current_position: Position
    target_position: Optional[Position] = None
    movement_pattern: MovementPattern = MovementPattern.LANING
    speed: float = 1.0  # Movement speed multiplier
    last_seen: float = 0.0  # Timestamp when last visible


@dataclass
class MinimapLayout:
    """MLBB minimap layout configuration"""
    width: int = 200
    height: int = 200
    
    # Lane positions (normalized 0-1)
    top_lane: List[Tuple[float, float]] = field(default_factory=lambda: [
        (0.1, 0.1), (0.3, 0.2), (0.5, 0.3), (0.7, 0.4), (0.9, 0.5)
    ])
    mid_lane: List[Tuple[float, float]] = field(default_factory=lambda: [
        (0.1, 0.5), (0.3, 0.4), (0.5, 0.5), (0.7, 0.6), (0.9, 0.9)
    ])
    bot_lane: List[Tuple[float, float]] = field(default_factory=lambda: [
        (0.1, 0.9), (0.3, 0.8), (0.5, 0.7), (0.7, 0.6), (0.9, 0.5)
    ])
    
    # Jungle camps
    jungle_camps: List[Tuple[float, float]] = field(default_factory=lambda: [
        (0.25, 0.25), (0.75, 0.75), (0.25, 0.75), (0.75, 0.25),
        (0.4, 0.4), (0.6, 0.6), (0.35, 0.65), (0.65, 0.35)
    ])
    
    # Important objectives
    lord_position: Tuple[float, float] = (0.5, 0.2)
    turtle_position: Tuple[float, float] = (0.5, 0.8)
    
    # Bases
    ally_base: Tuple[float, float] = (0.1, 0.9)
    enemy_base: Tuple[float, float] = (0.9, 0.1)


class SyntheticMinimapGenerator:
    """Generates synthetic minimap data and movement sequences"""
    
    def __init__(self, output_dir: str = "temp/synthetic_minimap"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.layout = MinimapLayout()
        self.players = []
        
        # Movement simulation parameters
        self.time_step = 1.0  # 1 second per frame
        self.max_simulation_time = 600  # 10 minutes
        self.visibility_probability = 0.8  # Probability player is visible
        
        logger.info("🎮 Synthetic Minimap Generator initialized")
    
    def create_base_minimap(self) -> np.ndarray:
        """Create base minimap image with lanes and objectives"""
        
        # Create black background
        minimap = np.zeros((self.layout.height, self.layout.width, 3), dtype=np.uint8)
        
        # Draw lanes
        self._draw_lane(minimap, self.layout.top_lane, (100, 100, 100))  # Gray
        self._draw_lane(minimap, self.layout.mid_lane, (100, 100, 100))
        self._draw_lane(minimap, self.layout.bot_lane, (100, 100, 100))
        
        # Draw jungle camps
        for camp_pos in self.layout.jungle_camps:
            x = int(camp_pos[0] * self.layout.width)
            y = int(camp_pos[1] * self.layout.height)
            cv2.circle(minimap, (x, y), 3, (0, 100, 0), -1)  # Dark green
        
        # Draw objectives
        lord_x = int(self.layout.lord_position[0] * self.layout.width)
        lord_y = int(self.layout.lord_position[1] * self.layout.height)
        cv2.circle(minimap, (lord_x, lord_y), 8, (0, 0, 200), 2)  # Red circle
        
        turtle_x = int(self.layout.turtle_position[0] * self.layout.width)
        turtle_y = int(self.layout.turtle_position[1] * self.layout.height)
        cv2.circle(minimap, (turtle_x, turtle_y), 6, (200, 0, 0), 2)  # Blue circle
        
        # Draw bases
        ally_x = int(self.layout.ally_base[0] * self.layout.width)
        ally_y = int(self.layout.ally_base[1] * self.layout.height)
        cv2.rectangle(minimap, (ally_x-10, ally_y-10), (ally_x+10, ally_y+10), (255, 0, 0), -1)
        
        enemy_x = int(self.layout.enemy_base[0] * self.layout.width)
        enemy_y = int(self.layout.enemy_base[1] * self.layout.height)
        cv2.rectangle(minimap, (enemy_x-10, enemy_y-10), (enemy_x+10, enemy_y+10), (0, 0, 255), -1)
        
        return minimap
    
    def _draw_lane(self, minimap: np.ndarray, lane_points: List[Tuple[float, float]], color: Tuple[int, int, int]):
        """Draw a lane on the minimap"""
        points = []
        for point in lane_points:
            x = int(point[0] * self.layout.width)
            y = int(point[1] * self.layout.height)
            points.append((x, y))
        
        # Draw connected lines
        for i in range(len(points) - 1):
            cv2.line(minimap, points[i], points[i+1], color, 2)
    
    def initialize_players(self) -> List[SyntheticPlayer]:
        """Initialize synthetic players with realistic starting positions"""
        
        players = []
        
        # Ally team (blue side)
        ally_roles = [HeroRole.TANK, HeroRole.MARKSMAN, HeroRole.SUPPORT, HeroRole.MAGE, HeroRole.ASSASSIN]
        ally_colors = [(255, 100, 100), (255, 150, 100), (255, 200, 100), (255, 255, 100), (200, 255, 100)]
        
        for i, (role, color) in enumerate(zip(ally_roles, ally_colors)):
            # Start near ally base
            start_x = random.uniform(0.1, 0.3)
            start_y = random.uniform(0.7, 0.9)
            
            player = SyntheticPlayer(
                player_id=f"ally_{i+1}",
                role=role,
                team="ally",
                color=color,
                current_position=Position(start_x, start_y),
                movement_pattern=MovementPattern.LANING
            )
            players.append(player)
        
        # Enemy team (red side)
        enemy_roles = [HeroRole.TANK, HeroRole.MARKSMAN, HeroRole.SUPPORT, HeroRole.MAGE, HeroRole.FIGHTER]
        enemy_colors = [(100, 100, 255), (100, 150, 255), (100, 200, 255), (100, 255, 255), (200, 100, 255)]
        
        for i, (role, color) in enumerate(zip(enemy_roles, enemy_colors)):
            # Start near enemy base
            start_x = random.uniform(0.7, 0.9)
            start_y = random.uniform(0.1, 0.3)
            
            player = SyntheticPlayer(
                player_id=f"enemy_{i+1}",
                role=role,
                team="enemy",
                color=color,
                current_position=Position(start_x, start_y),
                movement_pattern=MovementPattern.LANING
            )
            players.append(player)
        
        self.players = players
        logger.info(f"🎭 Initialized {len(players)} synthetic players")
        return players
    
    def simulate_movement_step(self, timestamp: float) -> List[MovementEvent]:
        """Simulate one step of player movement"""
        
        events = []
        
        for player in self.players:
            # Randomly change movement patterns
            if random.random() < 0.1:  # 10% chance to change pattern
                player.movement_pattern = random.choice(list(MovementPattern))
            
            # Update position based on movement pattern
            new_position = self._get_next_position(player, timestamp)
            
            # Create movement event if position changed significantly
            if self._distance(player.current_position, new_position) > 0.02:
                distance = self._distance(player.current_position, new_position)
                event = MovementEvent(
                    timestamp=timestamp,
                    frame_number=int(timestamp),
                    from_position=player.current_position,
                    to_position=new_position,
                    from_region=self._position_to_region(player.current_position),
                    to_region=self._position_to_region(new_position),
                    movement_type=player.movement_pattern.value,
                    distance=distance,
                    duration=1.0,  # 1 second per frame
                    confidence=0.95,
                    player_ign=player.player_id
                )
                events.append(event)
            
            # Update player position
            player.current_position = new_position
            player.last_seen = timestamp if random.random() < self.visibility_probability else player.last_seen
        
        return events
    
    def _get_next_position(self, player: SyntheticPlayer, timestamp: float) -> Position:
        """Calculate next position based on movement pattern"""
        
        current = player.current_position
        
        if player.movement_pattern == MovementPattern.LANING:
            # Stay in assigned lane with small movements
            noise_x = random.uniform(-0.02, 0.02)
            noise_y = random.uniform(-0.02, 0.02)
            return Position(
                max(0, min(1, current.x + noise_x)),
                max(0, min(1, current.y + noise_y))
            )
        
        elif player.movement_pattern == MovementPattern.ROAMING:
            # Move toward random lane position
            target_lane = random.choice([self.layout.top_lane, self.layout.mid_lane, self.layout.bot_lane])
            target_point = random.choice(target_lane)
            
            # Move toward target
            dx = target_point[0] - current.x
            dy = target_point[1] - current.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 0:
                move_distance = min(distance, 0.05 * player.speed)
                new_x = current.x + (dx / distance) * move_distance
                new_y = current.y + (dy / distance) * move_distance
                return Position(max(0, min(1, new_x)), max(0, min(1, new_y)))
        
        elif player.movement_pattern == MovementPattern.JUNGLE_CLEAR:
            # Move toward nearest jungle camp
            nearest_camp = min(self.layout.jungle_camps, 
                             key=lambda camp: self._distance(current, Position(camp[0], camp[1])))
            
            dx = nearest_camp[0] - current.x
            dy = nearest_camp[1] - current.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 0.03:  # Move toward camp
                move_distance = min(distance, 0.04 * player.speed)
                new_x = current.x + (dx / distance) * move_distance
                new_y = current.y + (dy / distance) * move_distance
                return Position(max(0, min(1, new_x)), max(0, min(1, new_y)))
        
        elif player.movement_pattern == MovementPattern.RECALL:
            # Move toward base
            if player.team == "ally":
                target = self.layout.ally_base
            else:
                target = self.layout.enemy_base
            
            dx = target[0] - current.x
            dy = target[1] - current.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 0.05:
                move_distance = min(distance, 0.06 * player.speed)
                new_x = current.x + (dx / distance) * move_distance
                new_y = current.y + (dy / distance) * move_distance
                return Position(max(0, min(1, new_x)), max(0, min(1, new_y)))
        
        # Default: small random movement
        noise_x = random.uniform(-0.01, 0.01)
        noise_y = random.uniform(-0.01, 0.01)
        return Position(
            max(0, min(1, current.x + noise_x)),
            max(0, min(1, current.y + noise_y))
        )
    
    def _distance(self, pos1: Position, pos2: Position) -> float:
        """Calculate distance between two positions"""
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        return math.sqrt(dx*dx + dy*dy)
    
    def _position_to_region(self, position: Position) -> MinimapRegion:
        """Convert position to minimap region"""
        x, y = position.x, position.y
        
        # Simple region mapping based on position
        if y < 0.4:
            if x < 0.5:
                return MinimapRegion.TOP_JUNGLE
            else:
                return MinimapRegion.TOP_LANE
        elif y > 0.6:
            if x < 0.5:
                return MinimapRegion.BOT_LANE
            else:
                return MinimapRegion.BOT_JUNGLE
        elif 0.4 <= x <= 0.6:
            return MinimapRegion.MID_LANE
        else:
            return MinimapRegion.RIVER
    
    def render_minimap_frame(self, timestamp: float) -> np.ndarray:
        """Render minimap frame with current player positions"""
        
        # Start with base minimap
        minimap = self.create_base_minimap()
        
        # Draw players
        for player in self.players:
            # Only draw if recently seen
            if timestamp - player.last_seen < 5.0:  # Visible within last 5 seconds
                x = int(player.current_position.x * self.layout.width)
                y = int(player.current_position.y * self.layout.height)
                
                # Draw player dot
                cv2.circle(minimap, (x, y), 4, player.color, -1)
                
                # Draw player ID
                cv2.putText(minimap, player.player_id[-1], (x+6, y+3), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        
        # Add timestamp
        cv2.putText(minimap, f"T: {timestamp:.1f}s", (5, 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return minimap
    
    def generate_movement_sequence(
        self, 
        duration: float = 300,  # 5 minutes
        fps: float = 1.0
    ) -> Tuple[List[TimestampedFrame], List[MovementEvent]]:
        """Generate complete movement sequence with frames and events"""
        
        logger.info(f"🎬 Generating {duration}s movement sequence at {fps} FPS")
        
        # Initialize players
        self.initialize_players()
        
        frames = []
        all_events = []
        
        current_time = 0.0
        frame_number = 0
        
        while current_time < duration:
            # Simulate movement step
            events = self.simulate_movement_step(current_time)
            all_events.extend(events)
            
            # Render frame
            minimap_image = self.render_minimap_frame(current_time)
            
            # Save frame
            frame_path = self.output_dir / f"frame_{frame_number:06d}.png"
            cv2.imwrite(str(frame_path), minimap_image)
            
            # Create timestamped frame
            timestamped_frame = TimestampedFrame(
                frame_path=str(frame_path),
                timestamp=current_time,
                frame_number=frame_number,
                confidence=1.0,
                metadata={
                    "synthetic": True,
                    "player_count": len(self.players),
                    "visible_players": len([p for p in self.players if current_time - p.last_seen < 5.0])
                }
            )
            frames.append(timestamped_frame)
            
            # Advance time
            current_time += 1.0 / fps
            frame_number += 1
        
        logger.info(f"✅ Generated {len(frames)} frames and {len(all_events)} movement events")
        
        return frames, all_events
    
    def save_movement_data(
        self, 
        frames: List[TimestampedFrame], 
        events: List[MovementEvent],
        filename: str = "synthetic_movement_data.json"
    ):
        """Save movement data to JSON file"""
        
        data = {
            "metadata": {
                "generated_at": time.time(),
                "frame_count": len(frames),
                "event_count": len(events),
                "duration": frames[-1].timestamp if frames else 0,
                "minimap_layout": {
                    "width": self.layout.width,
                    "height": self.layout.height,
                    "top_lane": self.layout.top_lane,
                    "mid_lane": self.layout.mid_lane,
                    "bot_lane": self.layout.bot_lane,
                    "jungle_camps": self.layout.jungle_camps
                }
            },
            "frames": [
                {
                    "frame_path": frame.frame_path,
                    "timestamp": frame.timestamp,
                    "frame_number": frame.frame_number,
                    "metadata": frame.metadata
                }
                for frame in frames
            ],
            "events": [
                {
                    "timestamp": event.timestamp,
                    "frame_number": event.frame_number,
                    "player_ign": event.player_ign,
                    "from_position": {"x": event.from_position.x, "y": event.from_position.y},
                    "to_position": {"x": event.to_position.x, "y": event.to_position.y},
                    "from_region": event.from_region.value,
                    "to_region": event.to_region.value,
                    "movement_type": event.movement_type,
                    "distance": event.distance,
                    "duration": event.duration,
                    "confidence": event.confidence
                }
                for event in events
            ],
            "players": [
                {
                    "player_id": player.player_id,
                    "role": player.role.value,
                    "team": player.team,
                    "color": player.color
                }
                for player in self.players
            ]
        }
        
        output_path = self.output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"💾 Saved movement data to {output_path}")
    
    def create_training_dataset(
        self, 
        num_sequences: int = 10,
        sequence_duration: float = 180  # 3 minutes each
    ) -> Dict[str, Any]:
        """Create comprehensive training dataset"""
        
        logger.info(f"🏗️ Creating training dataset with {num_sequences} sequences")
        
        dataset = {
            "sequences": [],
            "total_frames": 0,
            "total_events": 0
        }
        
        for i in range(num_sequences):
            logger.info(f"📹 Generating sequence {i+1}/{num_sequences}")
            
            # Create new output directory for this sequence
            sequence_dir = self.output_dir / f"sequence_{i+1:03d}"
            sequence_dir.mkdir(exist_ok=True)
            
            # Temporarily change output directory
            original_output_dir = self.output_dir
            self.output_dir = sequence_dir
            
            # Generate sequence
            frames, events = self.generate_movement_sequence(
                duration=sequence_duration,
                fps=1.0
            )
            
            # Save sequence data
            self.save_movement_data(frames, events, f"sequence_{i+1:03d}_data.json")
            
            # Add to dataset
            dataset["sequences"].append({
                "sequence_id": i+1,
                "directory": str(sequence_dir),
                "frame_count": len(frames),
                "event_count": len(events),
                "duration": sequence_duration
            })
            
            dataset["total_frames"] += len(frames)
            dataset["total_events"] += len(events)
            
            # Restore output directory
            self.output_dir = original_output_dir
        
        # Save dataset metadata
        dataset_path = self.output_dir / "training_dataset.json"
        with open(dataset_path, 'w') as f:
            json.dump(dataset, f, indent=2)
        
        logger.info(f"🎉 Training dataset created: {dataset['total_frames']} frames, {dataset['total_events']} events")
        
        return dataset


def create_synthetic_minimap_dataset():
    """Create synthetic minimap dataset for training and testing"""
    
    logger.info("🚀 Starting synthetic minimap dataset generation")
    
    generator = SyntheticMinimapGenerator()
    
    # Create training dataset
    dataset = generator.create_training_dataset(
        num_sequences=20,  # 20 sequences
        sequence_duration=300  # 5 minutes each
    )
    
    logger.info("✅ Synthetic minimap dataset generation completed")
    return dataset


if __name__ == "__main__":
    # Generate synthetic dataset
    dataset = create_synthetic_minimap_dataset()
    print(f"Generated dataset with {dataset['total_frames']} frames and {dataset['total_events']} events")
