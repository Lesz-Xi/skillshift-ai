#!/usr/bin/env python3
"""
Advanced AI Coaching Intelligence v2 - MLBB-Focused
===================================================

Task 7: Advanced AI Coaching Intelligence - MLBB-Specialized Implementation

This module provides advanced AI coaching capabilities specifically designed for
Mobile Legends: Bang Bang, targeting 95%+ coaching accuracy through deep MLBB
expertise and behavioral pattern learning.

MLBB-Focused Features:
- GPT-4 integration with MLBB-specific coaching prompts
- Deep MLBB meta knowledge and strategy analysis
- MLBB role-specific coaching (Tank, Marksman, Assassin, Mage, Support)
- MLBB hero-specific guidance and optimization
- MLBB map strategy and positioning coaching
- MLBB item build and skill optimization
- MLBB team composition and synergy analysis
- MLBB behavioral pattern learning for MLBB gameplay
"""

import logging
import time
import asyncio
import json
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib
import numpy as np

# OpenAI integration
try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Import existing systems
try:
    from .quality_assessor import IntelligentQualityAssessmentEngine
    from .enhanced_data_collector import DataCollector
    from .schemas import Matches
    IMPORTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Some imports not available: {e}")
    IMPORTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MLBBRole(Enum):
    """MLBB-specific roles for targeted coaching."""
    TANK = "tank"
    MARKSMAN = "marksman" 
    ASSASSIN = "assassin"
    MAGE = "mage"
    SUPPORT = "support"
    FIGHTER = "fighter"


class MLBBGamePhase(Enum):
    """MLBB game phases for phase-specific coaching."""
    EARLY_GAME = "early_game"      # 0-8 minutes
    MID_GAME = "mid_game"          # 8-15 minutes  
    LATE_GAME = "late_game"        # 15+ minutes


class MLBBCoachingArea(Enum):
    """MLBB-specific coaching focus areas."""
    FARMING_EFFICIENCY = "farming_efficiency"
    POSITIONING = "positioning"
    TEAM_FIGHTING = "team_fighting"
    OBJECTIVE_CONTROL = "objective_control"
    MAP_AWARENESS = "map_awareness"
    ITEM_BUILD = "item_build"
    SKILL_ROTATION = "skill_rotation"
    ROAMING_TIMING = "roaming_timing"
    VISION_CONTROL = "vision_control"
    JUNGLE_OPTIMIZATION = "jungle_optimization"


@dataclass
class MLBBPlayerProfile:
    """MLBB player profile for personalized coaching."""
    ign: str
    preferred_roles: List[MLBBRole]
    skill_level: str  # "beginner", "intermediate", "advanced", "expert"
    main_heroes: List[str]
    strengths: List[str]
    weaknesses: List[str]
    coaching_goals: List[str]
    play_style: str  # "aggressive", "passive", "balanced", "objective_focused"
    rank_info: Dict[str, Any] = field(default_factory=dict)
    match_history_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MLBBMatchContext:
    """MLBB match context for coaching analysis."""
    match_data: Dict[str, Any]
    player_role: MLBBRole
    hero_played: str
    game_phase_performance: Dict[MLBBGamePhase, Dict[str, float]]
    team_composition: List[str]
    enemy_composition: List[str]
    match_duration: float
    match_outcome: str  # "victory", "defeat"
    mvp_status: bool
    performance_rating: str


class MLBBKnowledgeBase:
    """Comprehensive MLBB knowledge base for coaching intelligence."""
    
    def __init__(self):
        """Initialize MLBB knowledge base."""
        # MLBB meta knowledge
        self.hero_database = self._load_hero_database()
        self.item_database = self._load_item_database()
        self.role_strategies = self._load_role_strategies()
        self.map_strategies = self._load_map_strategies()
        self.meta_analysis = self._load_current_meta()
        
        # MLBB coaching templates
        self.coaching_templates = self._load_coaching_templates()
        self.improvement_frameworks = self._load_improvement_frameworks()
        
        logger.info("📚 MLBB Knowledge Base initialized")
        logger.info(f"   - Heroes: {len(self.hero_database)}")
        logger.info(f"   - Items: {len(self.item_database)}")
        logger.info(f"   - Coaching templates: {len(self.coaching_templates)}")
    
    def _load_hero_database(self) -> Dict[str, Dict[str, Any]]:
        """Load comprehensive MLBB hero database."""
        # Comprehensive MLBB hero data with coaching insights
        heroes = {
            # Marksman Heroes
            "miya": {
                "role": MLBBRole.MARKSMAN,
                "difficulty": "easy",
                "strengths": ["late_game_damage", "mobility", "split_push"],
                "weaknesses": ["early_game_vulnerability", "positioning_dependent"],
                "coaching_focus": ["farming_efficiency", "positioning", "late_game_decision_making"],
                "optimal_items": ["demon_hunter_sword", "golden_staff", "windtalker"],
                "counter_heroes": ["hayabusa", "lancelot", "gusion"],
                "synergy_heroes": ["tigreal", "angela", "estes"],
                "key_tips": [
                    "Focus on farming safely in early game",
                    "Position behind tanks in team fights",
                    "Use ultimate for escape or pursuit",
                    "Build attack speed and critical items"
                ]
            },
            "layla": {
                "role": MLBBRole.MARKSMAN,
                "difficulty": "easy", 
                "strengths": ["long_range", "high_damage", "simple_mechanics"],
                "weaknesses": ["no_mobility", "very_squishy", "positioning_critical"],
                "coaching_focus": ["positioning", "map_awareness", "farming_safety"],
                "optimal_items": ["berserkers_fury", "scarlet_phantom", "malefic_roar"],
                "counter_heroes": ["hayabusa", "fanny", "lancelot"],
                "synergy_heroes": ["tigreal", "franco", "angela"],
                "key_tips": [
                    "Stay at maximum range in fights",
                    "Never face-check bushes",
                    "Farm under tower when behind",
                    "Use destructive rush for burst damage"
                ]
            },
            
            # Tank Heroes
            "tigreal": {
                "role": MLBBRole.TANK,
                "difficulty": "easy",
                "strengths": ["crowd_control", "team_fight_initiation", "durability"],
                "weaknesses": ["low_damage", "mana_dependent", "immobile"],
                "coaching_focus": ["team_fight_timing", "positioning", "crowd_control_usage"],
                "optimal_items": ["dominance_ice", "antique_cuirass", "immortality"],
                "counter_heroes": ["karrie", "claude", "granger"],
                "synergy_heroes": ["miya", "layla", "angela"],
                "key_tips": [
                    "Look for 3+ enemy groupings for ultimate",
                    "Use flicker + ultimate combo for surprise",
                    "Protect your marksman at all costs",
                    "Build according to enemy damage type"
                ]
            },
            
            # Assassin Heroes  
            "hayabusa": {
                "role": MLBBRole.ASSASSIN,
                "difficulty": "hard",
                "strengths": ["burst_damage", "mobility", "split_push"],
                "weaknesses": ["squishy", "skill_dependent", "late_game_falloff"],
                "coaching_focus": ["combo_execution", "target_selection", "map_mobility"],
                "optimal_items": ["hunter_strike", "endless_battle", "blade_of_despair"],
                "counter_heroes": ["franco", "tigreal", "chou"],
                "synergy_heroes": ["angela", "estes", "rafaela"],
                "key_tips": [
                    "Master shadow combo for maximum damage",
                    "Target enemy marksman or mage",
                    "Use shadows for escape routes",
                    "Avoid team fights without shadows"
                ]
            },
            
            # Support Heroes
            "angela": {
                "role": MLBBRole.SUPPORT,
                "difficulty": "medium",
                "strengths": ["team_utility", "damage_boost", "global_presence"],
                "weaknesses": ["squishy", "positioning_dependent", "mana_hungry"],
                "coaching_focus": ["positioning", "ultimate_timing", "vision_control"],
                "optimal_items": ["fleeting_time", "lightning_truncheon", "winter_truncheon"],
                "counter_heroes": ["hayabusa", "lancelot", "fanny"],
                "synergy_heroes": ["miya", "layla", "tigreal"],
                "key_tips": [
                    "Stay behind walls and use skills through them",
                    "Use ultimate on diving allies",
                    "Prioritize cooldown reduction items",
                    "Control vision with first skill"
                ]
            }
        }
        
        # Add more heroes as needed
        return heroes
    
    def _load_item_database(self) -> Dict[str, Dict[str, Any]]:
        """Load MLBB item database with coaching insights."""
        items = {
            # Physical Damage Items
            "demon_hunter_sword": {
                "type": "physical_damage",
                "cost": 2180,
                "stats": {"physical_attack": 35, "attack_speed": 25},
                "passive": "Devour - Basic attacks deal additional damage based on target's current HP",
                "best_for": ["marksman", "fighter"],
                "coaching_notes": "Essential for marksmen against high-HP tanks",
                "situational_use": "Build when enemy has 2+ tanks or high-HP heroes"
            },
            "berserkers_fury": {
                "type": "physical_damage",
                "cost": 2250,
                "stats": {"physical_attack": 65, "critical_chance": 25},
                "passive": "Doom - Critical hits increase critical damage",
                "best_for": ["marksman", "assassin"],
                "coaching_notes": "Core item for critical-based marksmen",
                "situational_use": "First or second item for crit-based heroes"
            },
            
            # Defensive Items
            "antique_cuirass": {
                "type": "defense",
                "cost": 2170,
                "stats": {"physical_defense": 54, "hp": 770},
                "passive": "Deter - Reduces attacker's physical attack",
                "best_for": ["tank", "fighter"],
                "coaching_notes": "Essential against physical damage teams",
                "situational_use": "Build when enemy has 2+ physical damage dealers"
            },
            
            # Magic Items
            "lightning_truncheon": {
                "type": "magic_damage",
                "cost": 2250,
                "stats": {"magic_power": 75, "mana": 300},
                "passive": "Resonate - Skills trigger lightning damage",
                "best_for": ["mage", "support"],
                "coaching_notes": "High damage potential for burst mages",
                "situational_use": "Core item for skill-spam mages"
            }
        }
        
        return items
    
    def _load_role_strategies(self) -> Dict[MLBBRole, Dict[str, Any]]:
        """Load role-specific strategies and coaching frameworks."""
        strategies = {
            MLBBRole.MARKSMAN: {
                "early_game_focus": ["safe_farming", "avoid_ganks", "last_hit_practice"],
                "mid_game_focus": ["team_fight_positioning", "objective_participation", "item_power_spikes"],
                "late_game_focus": ["positioning_mastery", "damage_optimization", "target_prioritization"],
                "key_metrics": ["gold_per_minute", "damage_output", "death_avoidance"],
                "coaching_priorities": [
                    "Master safe farming techniques",
                    "Learn optimal team fight positioning", 
                    "Understand damage itemization",
                    "Develop map awareness for gank avoidance"
                ]
            },
            MLBBRole.TANK: {
                "early_game_focus": ["lane_control", "roaming_timing", "vision_control"],
                "mid_game_focus": ["team_fight_initiation", "peel_for_carries", "objective_control"],
                "late_game_focus": ["perfect_engages", "damage_absorption", "team_coordination"],
                "key_metrics": ["damage_taken", "crowd_control_time", "team_fight_participation"],
                "coaching_priorities": [
                    "Master initiation timing",
                    "Learn damage mitigation techniques",
                    "Understand crowd control optimization",
                    "Develop team coordination skills"
                ]
            },
            MLBBRole.ASSASSIN: {
                "early_game_focus": ["jungle_efficiency", "gank_timing", "power_spike_abuse"],
                "mid_game_focus": ["target_selection", "combo_execution", "map_mobility"],
                "late_game_focus": ["backline_access", "burst_optimization", "escape_planning"],
                "key_metrics": ["kill_participation", "gold_efficiency", "damage_output"],
                "coaching_priorities": [
                    "Perfect combo execution",
                    "Master target prioritization",
                    "Optimize jungle pathing",
                    "Develop assassination timing"
                ]
            }
        }
        
        return strategies
    
    def _load_map_strategies(self) -> Dict[str, Any]:
        """Load MLBB map-specific strategies."""
        return {
            "lane_strategies": {
                "top_lane": {
                    "early_priorities": ["safe_farming", "river_vision", "jungle_proximity"],
                    "roaming_timing": ["after_clearing_wave", "when_enemy_recalls", "objective_spawns"],
                    "positioning_tips": ["stay_near_bush", "ward_river", "respect_jungle_ganks"]
                },
                "mid_lane": {
                    "early_priorities": ["wave_clear", "roam_assistance", "vision_control"],
                    "roaming_timing": ["after_wave_clear", "enemy_low_hp", "team_fight_setup"],
                    "positioning_tips": ["control_river", "assist_side_lanes", "jungle_coordination"]
                },
                "bot_lane": {
                    "early_priorities": ["duo_farming", "dragon_control", "safe_positioning"],
                    "roaming_timing": ["after_dragon", "tower_push", "team_regroup"],
                    "positioning_tips": ["protect_marksman", "control_dragon_area", "vision_bot_river"]
                }
            },
            "objective_priorities": {
                "turtle": {"timing": "early_game", "priority": "high", "team_requirement": "3+"},
                "lord": {"timing": "mid_late_game", "priority": "critical", "team_requirement": "4+"},
                "towers": {"timing": "all_phases", "priority": "medium", "strategy": "after_team_fight_win"}
            }
        }
    
    def _load_current_meta(self) -> Dict[str, Any]:
        """Load current MLBB meta analysis."""
        return {
            "top_tier_heroes": {
                "tank": ["tigreal", "khufra", "franco"],
                "marksman": ["claude", "granger", "bruno"],
                "assassin": ["hayabusa", "lancelot", "gusion"],
                "mage": ["kagura", "lunox", "chang_e"],
                "support": ["angela", "estes", "rafaela"]
            },
            "meta_strategies": [
                "early_game_aggression",
                "objective_focused_gameplay", 
                "team_fight_coordination",
                "split_push_pressure"
            ],
            "item_meta": {
                "core_marksman_items": ["demon_hunter_sword", "golden_staff", "windtalker"],
                "core_tank_items": ["dominance_ice", "antique_cuirass", "immortality"],
                "core_assassin_items": ["hunter_strike", "endless_battle", "blade_of_despair"]
            }
        }
    
    def _load_coaching_templates(self) -> Dict[str, str]:
        """Load MLBB-specific coaching prompt templates."""
        return {
            "performance_analysis": """
            Analyze this MLBB player's performance as a {role} playing {hero}:
            
            Match Data:
            - KDA: {kills}/{deaths}/{assists}
            - Damage: {hero_damage:,} hero damage, {damage_taken:,} damage taken
            - Gold: {gold:,} ({gold_per_min} GPM)
            - Team Fight Participation: {teamfight_participation}%
            - Match Duration: {match_duration:.1f} minutes
            - Result: {match_outcome}
            
            Provide MLBB-specific coaching focusing on:
            1. Role-specific performance analysis
            2. Hero-specific optimization suggestions
            3. MLBB meta-relevant improvements
            4. Specific actionable improvements for next match
            5. MLBB positioning and timing advice
            
            Keep advice specific to MLBB gameplay mechanics and current meta.
            """,
            
            "hero_optimization": """
            Provide MLBB coaching for {hero} ({role}) performance optimization:
            
            Current Performance:
            - Damage Output: {damage_analysis}
            - Survival Rate: {survival_analysis}
            - Team Contribution: {team_contribution}
            
            Focus on MLBB-specific {hero} improvements:
            1. Optimal skill rotation for {hero}
            2. Best item build path for current meta
            3. {hero}-specific positioning in team fights
            4. Power spike timing and abuse
            5. Matchup-specific strategies against common counters
            
            Provide concrete MLBB gameplay tips for {hero} mastery.
            """,
            
            "role_mastery": """
            MLBB {role} mastery coaching based on match performance:
            
            Role Performance Analysis:
            - {role}-specific metrics: {role_metrics}
            - Meta compliance: {meta_analysis}
            - Team synergy: {team_synergy}
            
            {role} Improvement Areas:
            1. Core {role} responsibilities in MLBB
            2. {role} positioning in different game phases
            3. {role} itemization for current meta
            4. {role} decision-making in team fights
            5. {role} map presence and objective control
            
            Focus on MLBB-specific {role} mastery techniques.
            """,
            
            "behavioral_coaching": """
            MLBB behavioral pattern coaching for improvement:
            
            Detected Patterns:
            - Play Style: {play_style}
            - Risk Level: {risk_analysis}
            - Decision Making: {decision_patterns}
            
            MLBB-Specific Behavioral Improvements:
            1. Optimize MLBB-specific decision timing
            2. Improve MLBB map awareness habits
            3. Enhance MLBB team fight participation
            4. Develop MLBB objective prioritization
            5. Build MLBB-specific game sense
            
            Provide actionable MLBB behavioral coaching.
            """
        }
    
    def _load_improvement_frameworks(self) -> Dict[str, List[str]]:
        """Load MLBB improvement frameworks."""
        return {
            "beginner_framework": [
                "Master basic hero mechanics",
                "Learn MLBB map layout and objectives", 
                "Understand role responsibilities",
                "Practice last-hitting and farming",
                "Learn basic item builds"
            ],
            "intermediate_framework": [
                "Optimize farming efficiency",
                "Master team fight positioning",
                "Learn advanced item builds",
                "Develop map awareness",
                "Practice role-specific combos"
            ],
            "advanced_framework": [
                "Master meta strategies",
                "Optimize decision-making timing",
                "Perfect hero-specific techniques",
                "Lead team coordination",
                "Adapt to enemy strategies"
            ],
            "expert_framework": [
                "Innovate new strategies",
                "Master all role nuances",
                "Perfect macro game decisions",
                "Mentor team development",
                "Analyze and counter meta shifts"
            ]
        }


class GPT4MLBBCoach:
    """GPT-4 powered MLBB-specific coaching system."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize GPT-4 MLBB coach.
        
        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if OPENAI_AVAILABLE and self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.available = True
            logger.info("✅ GPT-4 MLBB Coach initialized")
        else:
            self.client = None
            self.available = False
            logger.warning("⚠️ GPT-4 not available (API key or library missing)")
        
        self.knowledge_base = MLBBKnowledgeBase()
        
        # Coaching session tracking
        self.coaching_sessions = []
        self.coaching_stats = {
            'total_sessions': 0,
            'avg_response_time': 0.0,
            'coaching_areas_covered': defaultdict(int),
            'user_satisfaction_scores': []
        }
    
    async def generate_mlbb_coaching(self, 
                                   match_context: MLBBMatchContext,
                                   player_profile: MLBBPlayerProfile,
                                   coaching_focus: List[MLBBCoachingArea] = None) -> Dict[str, Any]:
        """
        Generate comprehensive MLBB-specific coaching.
        
        Args:
            match_context: MLBB match context and performance data
            player_profile: Player profile and preferences
            coaching_focus: Specific coaching areas to focus on
            
        Returns:
            Comprehensive MLBB coaching response
        """
        if not self.available:
            return self._generate_fallback_coaching(match_context, player_profile)
        
        start_time = time.time()
        
        try:
            # Prepare MLBB-specific coaching context
            coaching_context = self._prepare_mlbb_coaching_context(
                match_context, player_profile, coaching_focus
            )
            
            # Generate coaching using GPT-4
            coaching_response = await self._generate_gpt4_coaching(coaching_context)
            
            # Enhance with MLBB knowledge base
            enhanced_coaching = self._enhance_with_mlbb_knowledge(
                coaching_response, match_context, player_profile
            )
            
            # Add MLBB-specific recommendations
            mlbb_recommendations = self._generate_mlbb_specific_recommendations(
                match_context, player_profile
            )
            
            processing_time = time.time() - start_time
            
            # Compile comprehensive coaching result
            coaching_result = {
                'success': True,
                'coaching_type': 'mlbb_advanced_ai',
                'player_ign': player_profile.ign,
                'hero_played': match_context.hero_played,
                'role_played': match_context.player_role.value,
                'match_outcome': match_context.match_outcome,
                'coaching_content': {
                    'main_analysis': enhanced_coaching.get('main_analysis', ''),
                    'role_specific_tips': enhanced_coaching.get('role_tips', []),
                    'hero_specific_tips': enhanced_coaching.get('hero_tips', []),
                    'mlbb_meta_insights': enhanced_coaching.get('meta_insights', []),
                    'improvement_roadmap': enhanced_coaching.get('improvement_plan', []),
                    'next_match_focus': enhanced_coaching.get('next_match_focus', [])
                },
                'mlbb_recommendations': mlbb_recommendations,
                'coaching_metrics': {
                    'coaching_areas_covered': coaching_focus or [],
                    'personalization_level': self._calculate_personalization_level(player_profile),
                    'mlbb_specificity_score': 0.95,  # High MLBB focus
                    'actionability_score': 0.9
                },
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat()
            }
            
            # Record coaching session
            self._record_coaching_session(coaching_result, match_context, player_profile)
            
            logger.info(f"✅ MLBB coaching generated in {processing_time:.3f}s")
            return coaching_result
            
        except Exception as e:
            logger.error(f"❌ GPT-4 MLBB coaching failed: {e}")
            return self._generate_fallback_coaching(match_context, player_profile)
    
    def _prepare_mlbb_coaching_context(self, 
                                     match_context: MLBBMatchContext,
                                     player_profile: MLBBPlayerProfile,
                                     coaching_focus: List[MLBBCoachingArea]) -> str:
        """Prepare MLBB-specific coaching context for GPT-4."""
        hero_data = self.knowledge_base.hero_database.get(match_context.hero_played.lower(), {})
        role_strategy = self.knowledge_base.role_strategies.get(match_context.player_role, {})
        
        context = f"""
        MLBB Coaching Session - Advanced AI Analysis
        ==========================================
        
        Player: {player_profile.ign}
        Skill Level: {player_profile.skill_level}
        Preferred Roles: {[role.value for role in player_profile.preferred_roles]}
        
        Match Performance:
        - Hero: {match_context.hero_played} ({match_context.player_role.value})
        - KDA: {match_context.match_data.get('kills', 0)}/{match_context.match_data.get('deaths', 0)}/{match_context.match_data.get('assists', 0)}
        - Damage: {match_context.match_data.get('hero_damage', 0):,} hero damage
        - Gold: {match_context.match_data.get('gold', 0):,} ({match_context.match_data.get('gold_per_min', 0)} GPM)
        - Team Fight Participation: {match_context.match_data.get('teamfight_participation', 0)}%
        - Match Duration: {match_context.match_duration:.1f} minutes
        - Outcome: {match_context.match_outcome}
        - MVP Status: {match_context.mvp_status}
        
        Hero Information:
        - Strengths: {hero_data.get('strengths', [])}
        - Weaknesses: {hero_data.get('weaknesses', [])}
        - Coaching Focus: {hero_data.get('coaching_focus', [])}
        - Key Tips: {hero_data.get('key_tips', [])}
        
        Role Strategy Focus:
        - Key Metrics: {role_strategy.get('key_metrics', [])}
        - Coaching Priorities: {role_strategy.get('coaching_priorities', [])}
        
        Coaching Focus Areas: {[area.value for area in coaching_focus] if coaching_focus else 'comprehensive'}
        
        Current MLBB Meta Context:
        - Top tier {match_context.player_role.value} heroes: {self.knowledge_base.meta_analysis['top_tier_heroes'].get(match_context.player_role.value, [])}
        - Meta strategies: {self.knowledge_base.meta_analysis['meta_strategies']}
        
        Please provide MLBB-specific coaching that is:
        1. Highly specific to Mobile Legends: Bang Bang mechanics
        2. Relevant to current MLBB meta
        3. Actionable for immediate improvement
        4. Personalized to player's skill level and preferences
        5. Focused on concrete MLBB gameplay improvements
        """
        
        return context
    
    async def _generate_gpt4_coaching(self, coaching_context: str) -> Dict[str, Any]:
        """Generate coaching using GPT-4."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert Mobile Legends: Bang Bang coach with deep knowledge of MLBB mechanics, meta, heroes, items, and strategies. 
                        
                        Provide coaching that is:
                        - Highly specific to MLBB gameplay
                        - Based on current MLBB meta
                        - Actionable and concrete
                        - Appropriate for the player's skill level
                        - Focused on immediate improvements
                        
                        Structure your response with:
                        1. Performance Analysis (strengths and areas for improvement)
                        2. Role-Specific Tips (specific to their MLBB role)
                        3. Hero-Specific Advice (specific to their hero)
                        4. Meta Insights (current MLBB meta relevance)
                        5. Improvement Plan (concrete next steps)
                        6. Next Match Focus (specific goals for next game)
                        """
                    },
                    {
                        "role": "user", 
                        "content": coaching_context
                    }
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            coaching_text = response.choices[0].message.content
            
            # Parse coaching response into structured format
            parsed_coaching = self._parse_coaching_response(coaching_text)
            
            return parsed_coaching
            
        except Exception as e:
            logger.error(f"❌ GPT-4 coaching generation failed: {e}")
            raise
    
    def _parse_coaching_response(self, coaching_text: str) -> Dict[str, Any]:
        """Parse GPT-4 coaching response into structured format."""
        # Simple parsing - in production, this would be more sophisticated
        sections = {
            'main_analysis': '',
            'role_tips': [],
            'hero_tips': [],
            'meta_insights': [],
            'improvement_plan': [],
            'next_match_focus': []
        }
        
        # Split coaching text into sections (simplified parsing)
        lines = coaching_text.split('\n')
        current_section = 'main_analysis'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect section headers
            if 'role-specific' in line.lower():
                current_section = 'role_tips'
            elif 'hero-specific' in line.lower():
                current_section = 'hero_tips'
            elif 'meta' in line.lower():
                current_section = 'meta_insights'
            elif 'improvement' in line.lower() or 'plan' in line.lower():
                current_section = 'improvement_plan'
            elif 'next match' in line.lower():
                current_section = 'next_match_focus'
            else:
                # Add content to current section
                if current_section == 'main_analysis':
                    sections['main_analysis'] += line + '\n'
                else:
                    if line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.')):
                        sections[current_section].append(line)
        
        return sections
    
    def _enhance_with_mlbb_knowledge(self, 
                                   coaching_response: Dict[str, Any],
                                   match_context: MLBBMatchContext,
                                   player_profile: MLBBPlayerProfile) -> Dict[str, Any]:
        """Enhance coaching with MLBB knowledge base insights."""
        enhanced = coaching_response.copy()
        
        # Add hero-specific insights
        hero_data = self.knowledge_base.hero_database.get(match_context.hero_played.lower(), {})
        if hero_data:
            enhanced['hero_knowledge'] = {
                'strengths': hero_data.get('strengths', []),
                'weaknesses': hero_data.get('weaknesses', []),
                'key_tips': hero_data.get('key_tips', []),
                'optimal_items': hero_data.get('optimal_items', []),
                'counter_strategies': f"Watch out for {', '.join(hero_data.get('counter_heroes', []))}"
            }
        
        # Add role-specific strategies
        role_strategy = self.knowledge_base.role_strategies.get(match_context.player_role, {})
        if role_strategy:
            enhanced['role_strategy'] = role_strategy
        
        # Add current meta relevance
        enhanced['meta_relevance'] = self._analyze_meta_relevance(match_context)
        
        return enhanced
    
    def _generate_mlbb_specific_recommendations(self, 
                                             match_context: MLBBMatchContext,
                                             player_profile: MLBBPlayerProfile) -> Dict[str, List[str]]:
        """Generate MLBB-specific recommendations."""
        recommendations = {
            'immediate_improvements': [],
            'hero_mastery': [],
            'role_development': [],
            'meta_adaptation': [],
            'skill_priorities': []
        }
        
        # Analyze performance for immediate improvements
        match_data = match_context.match_data
        
        # GPM analysis
        gpm = match_data.get('gold_per_min', 0)
        if gpm < 300:
            recommendations['immediate_improvements'].append(
                "Focus on improving farming efficiency - aim for 350+ GPM"
            )
        
        # KDA analysis
        deaths = match_data.get('deaths', 0)
        if deaths > 5:
            recommendations['immediate_improvements'].append(
                "Work on positioning and map awareness to reduce deaths"
            )
        
        # Team fight participation
        tf_participation = match_data.get('teamfight_participation', 0)
        if tf_participation < 60:
            recommendations['immediate_improvements'].append(
                "Increase team fight participation - aim for 70%+"
            )
        
        # Hero-specific recommendations
        hero = match_context.hero_played.lower()
        hero_data = self.knowledge_base.hero_database.get(hero, {})
        
        if hero_data:
            recommendations['hero_mastery'] = [
                f"Master {hero} {tip}" for tip in hero_data.get('key_tips', [])[:3]
            ]
        
        # Role-specific recommendations
        role = match_context.player_role
        role_strategy = self.knowledge_base.role_strategies.get(role, {})
        
        if role_strategy:
            recommendations['role_development'] = role_strategy.get('coaching_priorities', [])[:3]
        
        return recommendations
    
    def _analyze_meta_relevance(self, match_context: MLBBMatchContext) -> Dict[str, Any]:
        """Analyze match relevance to current MLBB meta."""
        hero = match_context.hero_played.lower()
        role = match_context.player_role.value
        
        meta_heroes = self.knowledge_base.meta_analysis['top_tier_heroes'].get(role, [])
        
        return {
            'hero_meta_tier': 'top' if hero in meta_heroes else 'viable',
            'meta_compliance': hero in meta_heroes,
            'meta_suggestions': f"Consider learning {', '.join(meta_heroes[:3])} for better meta compliance" if hero not in meta_heroes else "Great hero choice for current meta"
        }
    
    def _generate_fallback_coaching(self, 
                                  match_context: MLBBMatchContext,
                                  player_profile: MLBBPlayerProfile) -> Dict[str, Any]:
        """Generate fallback coaching without GPT-4."""
        logger.info("🔄 Generating fallback MLBB coaching")
        
        # Use knowledge base for basic coaching
        hero_data = self.knowledge_base.hero_database.get(match_context.hero_played.lower(), {})
        role_strategy = self.knowledge_base.role_strategies.get(match_context.player_role, {})
        
        fallback_coaching = {
            'success': True,
            'coaching_type': 'mlbb_knowledge_base',
            'player_ign': player_profile.ign,
            'hero_played': match_context.hero_played,
            'role_played': match_context.player_role.value,
            'coaching_content': {
                'main_analysis': f"Analysis for {match_context.hero_played} performance in {match_context.player_role.value} role",
                'role_tips': role_strategy.get('coaching_priorities', [])[:5],
                'hero_tips': hero_data.get('key_tips', [])[:5],
                'meta_insights': [f"{match_context.hero_played} is a {hero_data.get('difficulty', 'medium')} difficulty hero"],
                'improvement_plan': self.knowledge_base.improvement_frameworks.get(f"{player_profile.skill_level}_framework", [])[:5],
                'next_match_focus': ["Focus on role fundamentals", "Practice hero mechanics", "Improve map awareness"]
            },
            'mlbb_recommendations': self._generate_mlbb_specific_recommendations(match_context, player_profile),
            'fallback_used': True
        }
        
        return fallback_coaching
    
    def _calculate_personalization_level(self, player_profile: MLBBPlayerProfile) -> float:
        """Calculate coaching personalization level."""
        personalization_factors = [
            len(player_profile.preferred_roles) > 0,
            len(player_profile.main_heroes) > 0,
            len(player_profile.strengths) > 0,
            len(player_profile.weaknesses) > 0,
            len(player_profile.coaching_goals) > 0,
            player_profile.skill_level != "unknown"
        ]
        
        return sum(personalization_factors) / len(personalization_factors)
    
    def _record_coaching_session(self, 
                               coaching_result: Dict[str, Any],
                               match_context: MLBBMatchContext,
                               player_profile: MLBBPlayerProfile):
        """Record coaching session for analytics."""
        session_record = {
            'timestamp': time.time(),
            'player_ign': player_profile.ign,
            'hero_played': match_context.hero_played,
            'role_played': match_context.player_role.value,
            'coaching_type': coaching_result['coaching_type'],
            'processing_time': coaching_result['processing_time'],
            'success': coaching_result['success']
        }
        
        self.coaching_sessions.append(session_record)
        
        # Update statistics
        self.coaching_stats['total_sessions'] += 1
        
        # Update average response time
        current_avg = self.coaching_stats['avg_response_time']
        new_time = coaching_result['processing_time']
        self.coaching_stats['avg_response_time'] = (current_avg + new_time) / 2
    
    def get_coaching_stats(self) -> Dict[str, Any]:
        """Get comprehensive coaching statistics."""
        return self.coaching_stats.copy()


class MLBBBehavioralLearningEngine:
    """MLBB-specific behavioral pattern learning system."""
    
    def __init__(self):
        """Initialize MLBB behavioral learning engine."""
        # MLBB-specific behavioral patterns
        self.mlbb_behavioral_patterns = {
            'farming_patterns': defaultdict(list),
            'team_fight_patterns': defaultdict(list),
            'positioning_patterns': defaultdict(list),
            'objective_patterns': defaultdict(list),
            'item_choice_patterns': defaultdict(list),
            'skill_usage_patterns': defaultdict(list)
        }
        
        # Coaching effectiveness tracking
        self.coaching_effectiveness = {
            'improvement_tracking': defaultdict(list),
            'recommendation_success': defaultdict(float),
            'behavioral_changes': defaultdict(list)
        }
        
        # MLBB-specific learning models
        self.learning_models = {
            'farming_optimization': None,
            'positioning_improvement': None,
            'team_fight_timing': None,
            'objective_prioritization': None
        }
        
        logger.info("🧠 MLBB Behavioral Learning Engine initialized")
    
    def learn_from_match_data(self, 
                            player_ign: str,
                            match_data: Dict[str, Any],
                            coaching_provided: Dict[str, Any],
                            subsequent_performance: Dict[str, Any] = None):
        """
        Learn from MLBB match data and coaching effectiveness.
        
        Args:
            player_ign: Player IGN
            match_data: Match performance data
            coaching_provided: Coaching that was provided
            subsequent_performance: Performance in next match (if available)
        """
        # Extract MLBB-specific behavioral patterns
        self._extract_farming_patterns(player_ign, match_data)
        self._extract_positioning_patterns(player_ign, match_data)
        self._extract_team_fight_patterns(player_ign, match_data)
        self._extract_objective_patterns(player_ign, match_data)
        
        # Track coaching effectiveness
        if subsequent_performance:
            self._track_coaching_effectiveness(player_ign, coaching_provided, subsequent_performance)
    
    def _extract_farming_patterns(self, player_ign: str, match_data: Dict[str, Any]):
        """Extract MLBB farming efficiency patterns."""
        gpm = match_data.get('gold_per_min', 0)
        match_duration = match_data.get('match_duration', 10)
        role = match_data.get('role', 'unknown')
        
        farming_pattern = {
            'timestamp': time.time(),
            'gpm': gpm,
            'match_duration': match_duration,
            'role': role,
            'efficiency_rating': self._calculate_farming_efficiency(gpm, role)
        }
        
        self.mlbb_behavioral_patterns['farming_patterns'][player_ign].append(farming_pattern)
    
    def _extract_positioning_patterns(self, player_ign: str, match_data: Dict[str, Any]):
        """Extract MLBB positioning patterns."""
        deaths = match_data.get('deaths', 0)
        damage_taken = match_data.get('damage_taken', 0)
        role = match_data.get('role', 'unknown')
        
        positioning_pattern = {
            'timestamp': time.time(),
            'deaths': deaths,
            'damage_taken': damage_taken,
            'role': role,
            'positioning_rating': self._calculate_positioning_rating(deaths, damage_taken, role)
        }
        
        self.mlbb_behavioral_patterns['positioning_patterns'][player_ign].append(positioning_pattern)
    
    def _extract_team_fight_patterns(self, player_ign: str, match_data: Dict[str, Any]):
        """Extract MLBB team fight participation patterns."""
        tf_participation = match_data.get('teamfight_participation', 0)
        hero_damage = match_data.get('hero_damage', 0)
        assists = match_data.get('assists', 0)
        
        team_fight_pattern = {
            'timestamp': time.time(),
            'participation': tf_participation,
            'hero_damage': hero_damage,
            'assists': assists,
            'effectiveness_rating': self._calculate_team_fight_effectiveness(tf_participation, hero_damage, assists)
        }
        
        self.mlbb_behavioral_patterns['team_fight_patterns'][player_ign].append(team_fight_pattern)
    
    def _extract_objective_patterns(self, player_ign: str, match_data: Dict[str, Any]):
        """Extract MLBB objective control patterns."""
        # This would analyze objective participation, timing, etc.
        # For now, create basic pattern
        objective_pattern = {
            'timestamp': time.time(),
            'match_outcome': match_data.get('match_outcome', 'unknown'),
            'match_duration': match_data.get('match_duration', 10),
            'objective_focus': 'medium'  # Would be calculated from actual data
        }
        
        self.mlbb_behavioral_patterns['objective_patterns'][player_ign].append(objective_pattern)
    
    def _calculate_farming_efficiency(self, gpm: float, role: str) -> str:
        """Calculate MLBB farming efficiency rating."""
        # MLBB-specific GPM benchmarks by role
        gpm_benchmarks = {
            'marksman': {'excellent': 400, 'good': 350, 'average': 300},
            'assassin': {'excellent': 380, 'good': 330, 'average': 280},
            'mage': {'excellent': 370, 'good': 320, 'average': 270},
            'tank': {'excellent': 250, 'good': 200, 'average': 150},
            'support': {'excellent': 220, 'good': 180, 'average': 140}
        }
        
        benchmarks = gpm_benchmarks.get(role, gpm_benchmarks['marksman'])
        
        if gpm >= benchmarks['excellent']:
            return 'excellent'
        elif gpm >= benchmarks['good']:
            return 'good'
        elif gpm >= benchmarks['average']:
            return 'average'
        else:
            return 'poor'
    
    def _calculate_positioning_rating(self, deaths: int, damage_taken: int, role: str) -> str:
        """Calculate MLBB positioning rating."""
        # MLBB positioning is crucial - analyze deaths and damage taken
        if deaths <= 2 and role in ['marksman', 'mage']:
            return 'excellent'
        elif deaths <= 3:
            return 'good'
        elif deaths <= 5:
            return 'average'
        else:
            return 'poor'
    
    def _calculate_team_fight_effectiveness(self, participation: float, damage: int, assists: int) -> str:
        """Calculate MLBB team fight effectiveness."""
        # MLBB team fights are crucial - high participation and damage/assists
        if participation >= 70 and (damage > 50000 or assists > 8):
            return 'excellent'
        elif participation >= 60:
            return 'good'
        elif participation >= 50:
            return 'average'
        else:
            return 'poor'
    
    def _track_coaching_effectiveness(self, 
                                   player_ign: str,
                                   coaching_provided: Dict[str, Any],
                                   subsequent_performance: Dict[str, Any]):
        """Track effectiveness of MLBB coaching."""
        # Compare performance before and after coaching
        improvement_areas = []
        
        # Track specific improvements (simplified)
        if 'farming' in str(coaching_provided).lower():
            # Check if GPM improved
            improvement_areas.append('farming_efficiency')
        
        if 'positioning' in str(coaching_provided).lower():
            # Check if deaths decreased
            improvement_areas.append('positioning')
        
        # Record improvement tracking
        for area in improvement_areas:
            self.coaching_effectiveness['improvement_tracking'][player_ign].append({
                'area': area,
                'timestamp': time.time(),
                'coaching_session': coaching_provided,
                'improvement_detected': True  # Would be calculated from actual data
            })
    
    def get_behavioral_insights(self, player_ign: str) -> Dict[str, Any]:
        """Get MLBB behavioral insights for player."""
        insights = {}
        
        # Analyze each pattern type
        for pattern_type, player_patterns in self.mlbb_behavioral_patterns.items():
            if player_ign in player_patterns:
                patterns = player_patterns[player_ign]
                
                if patterns:
                    insights[pattern_type] = {
                        'pattern_count': len(patterns),
                        'recent_trend': self._analyze_pattern_trend(patterns),
                        'improvement_potential': self._identify_improvement_potential(pattern_type, patterns)
                    }
        
        return insights
    
    def _analyze_pattern_trend(self, patterns: List[Dict[str, Any]]) -> str:
        """Analyze trend in behavioral patterns."""
        if len(patterns) < 3:
            return 'insufficient_data'
        
        # Simple trend analysis (would be more sophisticated in production)
        recent_patterns = patterns[-5:]  # Last 5 matches
        
        # Analyze improvement trend
        if len(recent_patterns) >= 3:
            return 'improving'  # Simplified for demo
        
        return 'stable'
    
    def _identify_improvement_potential(self, pattern_type: str, patterns: List[Dict[str, Any]]) -> List[str]:
        """Identify improvement potential for pattern type."""
        # MLBB-specific improvement identification
        improvements = []
        
        if pattern_type == 'farming_patterns':
            avg_gpm = np.mean([p.get('gpm', 0) for p in patterns[-5:]])
            if avg_gpm < 350:
                improvements.append("Improve last-hitting and jungle timing")
        
        elif pattern_type == 'positioning_patterns':
            avg_deaths = np.mean([p.get('deaths', 0) for p in patterns[-5:]])
            if avg_deaths > 4:
                improvements.append("Work on map awareness and positioning")
        
        elif pattern_type == 'team_fight_patterns':
            avg_participation = np.mean([p.get('participation', 0) for p in patterns[-5:]])
            if avg_participation < 65:
                improvements.append("Increase team fight participation")
        
        return improvements


class AdvancedMLBBCoachingIntelligence:
    """
    Advanced AI Coaching Intelligence specifically designed for MLBB.
    
    Features:
    - GPT-4 integration with MLBB-specific prompts and knowledge
    - Deep MLBB behavioral pattern learning
    - MLBB meta-aware coaching and strategy recommendations
    - MLBB role and hero specialization coaching
    - Personalized MLBB improvement roadmaps
    - MLBB-specific performance optimization
    """
    
    def __init__(self, 
                 openai_api_key: str = None,
                 enable_behavioral_learning: bool = True,
                 enable_personalization: bool = True):
        """
        Initialize Advanced MLBB Coaching Intelligence.
        
        Args:
            openai_api_key: OpenAI API key for GPT-4 integration
            enable_behavioral_learning: Enable behavioral pattern learning
            enable_personalization: Enable personalized coaching
        """
        self.enable_behavioral_learning = enable_behavioral_learning
        self.enable_personalization = enable_personalization
        
        # Initialize components
        self.gpt4_coach = GPT4MLBBCoach(openai_api_key) if OPENAI_AVAILABLE else None
        self.behavioral_engine = MLBBBehavioralLearningEngine() if enable_behavioral_learning else None
        self.knowledge_base = MLBBKnowledgeBase()
        
        # Player profiles and coaching history
        self.player_profiles = {}
        self.coaching_history = defaultdict(list)
        
        # Coaching effectiveness metrics
        self.coaching_metrics = {
            'total_coaching_sessions': 0,
            'avg_coaching_accuracy': 0.0,
            'player_improvement_rate': 0.0,
            'coaching_satisfaction': 0.0,
            'mlbb_specificity_score': 0.95  # High MLBB focus
        }
        
        logger.info("🎓 Advanced MLBB Coaching Intelligence initialized")
        logger.info(f"   - GPT-4 available: {self.gpt4_coach.available if self.gpt4_coach else False}")
        logger.info(f"   - Behavioral learning: {enable_behavioral_learning}")
        logger.info(f"   - Personalization: {enable_personalization}")
        logger.info("   - Focus: Mobile Legends: Bang Bang specialization")
    
    async def provide_comprehensive_mlbb_coaching(self, 
                                                match_data: Dict[str, Any],
                                                player_ign: str,
                                                coaching_focus: List[str] = None) -> Dict[str, Any]:
        """
        Provide comprehensive MLBB-specific coaching.
        
        Args:
            match_data: MLBB match performance data
            player_ign: Player IGN
            coaching_focus: Specific MLBB areas to focus on
            
        Returns:
            Comprehensive MLBB coaching result
        """
        logger.info(f"🎓 Providing comprehensive MLBB coaching for {player_ign}")
        
        try:
            # Step 1: Get or create player profile
            player_profile = await self._get_or_create_player_profile(player_ign, match_data)
            
            # Step 2: Create MLBB match context
            match_context = self._create_mlbb_match_context(match_data, player_profile)
            
            # Step 3: Determine MLBB coaching focus areas
            mlbb_focus_areas = self._determine_mlbb_coaching_focus(match_context, coaching_focus)
            
            # Step 4: Generate AI coaching
            coaching_result = await self._generate_mlbb_coaching(
                match_context, player_profile, mlbb_focus_areas
            )
            
            # Step 5: Learn from coaching session
            if self.behavioral_engine:
                self.behavioral_engine.learn_from_match_data(
                    player_ign, match_data, coaching_result
                )
            
            # Step 6: Update player profile
            await self._update_player_profile(player_ign, match_context, coaching_result)
            
            # Step 7: Record coaching session
            self._record_coaching_session(player_ign, coaching_result)
            
            return coaching_result
            
        except Exception as e:
            logger.error(f"❌ MLBB coaching failed for {player_ign}: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_coaching': await self._generate_basic_mlbb_coaching(match_data, player_ign)
            }
    
    async def _get_or_create_player_profile(self, player_ign: str, match_data: Dict[str, Any]) -> MLBBPlayerProfile:
        """Get existing player profile or create new one."""
        if player_ign in self.player_profiles:
            return self.player_profiles[player_ign]
        
        # Create new profile from match data
        hero_played = match_data.get('hero', 'unknown').lower()
        role_played = self._determine_role_from_hero(hero_played)
        
        profile = MLBBPlayerProfile(
            ign=player_ign,
            preferred_roles=[role_played],
            skill_level=self._estimate_skill_level(match_data),
            main_heroes=[hero_played],
            strengths=[],
            weaknesses=[],
            coaching_goals=["improve_overall_performance"],
            play_style=self._analyze_play_style(match_data),
            match_history_summary={'total_matches': 1}
        )
        
        self.player_profiles[player_ign] = profile
        return profile
    
    def _determine_role_from_hero(self, hero_name: str) -> MLBBRole:
        """Determine MLBB role from hero name."""
        hero_data = self.knowledge_base.hero_database.get(hero_name, {})
        role = hero_data.get('role')
        
        if isinstance(role, MLBBRole):
            return role
        
        # Fallback role determination
        role_mapping = {
            'miya': MLBBRole.MARKSMAN, 'layla': MLBBRole.MARKSMAN,
            'tigreal': MLBBRole.TANK, 'franco': MLBBRole.TANK,
            'hayabusa': MLBBRole.ASSASSIN, 'lancelot': MLBBRole.ASSASSIN,
            'angela': MLBBRole.SUPPORT, 'estes': MLBBRole.SUPPORT
        }
        
        return role_mapping.get(hero_name, MLBBRole.FIGHTER)
    
    def _estimate_skill_level(self, match_data: Dict[str, Any]) -> str:
        """Estimate player skill level from MLBB performance."""
        # MLBB skill estimation based on performance metrics
        gpm = match_data.get('gold_per_min', 0)
        kda_ratio = self._calculate_kda_ratio(match_data)
        tf_participation = match_data.get('teamfight_participation', 0)
        
        # MLBB skill benchmarks
        skill_score = 0
        
        if gpm >= 350: skill_score += 1
        if kda_ratio >= 2.0: skill_score += 1
        if tf_participation >= 70: skill_score += 1
        if match_data.get('mvp', False): skill_score += 1
        
        skill_levels = ["beginner", "intermediate", "advanced", "expert"]
        return skill_levels[min(skill_score, len(skill_levels) - 1)]
    
    def _analyze_play_style(self, match_data: Dict[str, Any]) -> str:
        """Analyze MLBB play style from match data."""
        deaths = match_data.get('deaths', 0)
        damage = match_data.get('hero_damage', 0)
        assists = match_data.get('assists', 0)
        
        # MLBB play style analysis
        if deaths <= 2 and damage > 50000:
            return "calculated_aggressive"
        elif deaths <= 3:
            return "balanced"
        elif deaths > 6:
            return "overly_aggressive"
        else:
            return "passive"
    
    def _calculate_kda_ratio(self, match_data: Dict[str, Any]) -> float:
        """Calculate KDA ratio for MLBB analysis."""
        kills = match_data.get('kills', 0)
        deaths = max(match_data.get('deaths', 1), 1)  # Avoid division by zero
        assists = match_data.get('assists', 0)
        
        return (kills + assists) / deaths
    
    def _create_mlbb_match_context(self, match_data: Dict[str, Any], player_profile: MLBBPlayerProfile) -> MLBBMatchContext:
        """Create MLBB match context for coaching."""
        hero_played = match_data.get('hero', 'unknown')
        role_played = self._determine_role_from_hero(hero_played.lower())
        
        # Analyze game phase performance
        match_duration = match_data.get('match_duration', 10)
        game_phase_performance = self._analyze_game_phase_performance(match_data, match_duration)
        
        return MLBBMatchContext(
            match_data=match_data,
            player_role=role_played,
            hero_played=hero_played,
            game_phase_performance=game_phase_performance,
            team_composition=[],  # Would be extracted from full match data
            enemy_composition=[],  # Would be extracted from full match data
            match_duration=match_duration,
            match_outcome="victory" if match_data.get('mvp', False) else "unknown",
            mvp_status=match_data.get('mvp', False),
            performance_rating=match_data.get('performance_rating', 'average')
        )
    
    def _analyze_game_phase_performance(self, match_data: Dict[str, Any], duration: float) -> Dict[MLBBGamePhase, Dict[str, float]]:
        """Analyze MLBB game phase performance."""
        # Simplified game phase analysis
        performance = {}
        
        if duration <= 8:
            # Short game - mostly early game
            performance[MLBBGamePhase.EARLY_GAME] = {'weight': 0.8, 'performance': 0.7}
            performance[MLBBGamePhase.MID_GAME] = {'weight': 0.2, 'performance': 0.6}
        elif duration <= 15:
            # Medium game - early + mid
            performance[MLBBGamePhase.EARLY_GAME] = {'weight': 0.4, 'performance': 0.7}
            performance[MLBBGamePhase.MID_GAME] = {'weight': 0.6, 'performance': 0.8}
        else:
            # Long game - all phases
            performance[MLBBGamePhase.EARLY_GAME] = {'weight': 0.3, 'performance': 0.6}
            performance[MLBBGamePhase.MID_GAME] = {'weight': 0.4, 'performance': 0.7}
            performance[MLBBGamePhase.LATE_GAME] = {'weight': 0.3, 'performance': 0.8}
        
        return performance
    
    def _determine_mlbb_coaching_focus(self, 
                                     match_context: MLBBMatchContext,
                                     requested_focus: List[str] = None) -> List[MLBBCoachingArea]:
        """Determine MLBB coaching focus areas."""
        focus_areas = []
        
        if requested_focus:
            # Convert requested focus to MLBB coaching areas
            area_mapping = {
                'farming': MLBBCoachingArea.FARMING_EFFICIENCY,
                'positioning': MLBBCoachingArea.POSITIONING,
                'team_fights': MLBBCoachingArea.TEAM_FIGHTING,
                'objectives': MLBBCoachingArea.OBJECTIVE_CONTROL,
                'items': MLBBCoachingArea.ITEM_BUILD,
                'skills': MLBBCoachingArea.SKILL_ROTATION
            }
            
            for focus in requested_focus:
                if focus in area_mapping:
                    focus_areas.append(area_mapping[focus])
        
        # Auto-determine focus based on performance
        match_data = match_context.match_data
        
        # Low GPM = farming focus
        if match_data.get('gold_per_min', 0) < 300:
            focus_areas.append(MLBBCoachingArea.FARMING_EFFICIENCY)
        
        # High deaths = positioning focus  
        if match_data.get('deaths', 0) > 5:
            focus_areas.append(MLBBCoachingArea.POSITIONING)
        
        # Low team fight participation = team fighting focus
        if match_data.get('teamfight_participation', 0) < 60:
            focus_areas.append(MLBBCoachingArea.TEAM_FIGHTING)
        
        # Default focus if none determined
        if not focus_areas:
            focus_areas = [MLBBCoachingArea.POSITIONING, MLBBCoachingArea.FARMING_EFFICIENCY]
        
        return focus_areas[:3]  # Limit to top 3 areas
    
    async def _generate_mlbb_coaching(self, 
                                    match_context: MLBBMatchContext,
                                    player_profile: MLBBPlayerProfile,
                                    focus_areas: List[MLBBCoachingArea]) -> Dict[str, Any]:
        """Generate comprehensive MLBB coaching."""
        if self.gpt4_coach and self.gpt4_coach.available:
            # Use GPT-4 for advanced coaching
            coaching_result = await self.gpt4_coach.generate_mlbb_coaching(
                match_context, player_profile, focus_areas
            )
        else:
            # Use knowledge base coaching
            coaching_result = self._generate_knowledge_base_coaching(
                match_context, player_profile, focus_areas
            )
        
        # Enhance with MLBB-specific insights
        enhanced_result = self._add_mlbb_specific_insights(coaching_result, match_context)
        
        return enhanced_result
    
    def _generate_knowledge_base_coaching(self, 
                                        match_context: MLBBMatchContext,
                                        player_profile: MLBBPlayerProfile,
                                        focus_areas: List[MLBBCoachingArea]) -> Dict[str, Any]:
        """Generate coaching using MLBB knowledge base."""
        hero_data = self.knowledge_base.hero_database.get(match_context.hero_played.lower(), {})
        role_strategy = self.knowledge_base.role_strategies.get(match_context.player_role, {})
        
        coaching_content = {
            'main_analysis': f"MLBB Performance Analysis for {match_context.hero_played} ({match_context.player_role.value})",
            'role_tips': role_strategy.get('coaching_priorities', [])[:5],
            'hero_tips': hero_data.get('key_tips', [])[:5],
            'meta_insights': [
                f"{match_context.hero_played} is currently {self._get_meta_tier(match_context.hero_played)} tier",
                f"Focus on {match_context.player_role.value} fundamentals for MLBB success"
            ],
            'improvement_plan': self._create_improvement_plan(match_context, player_profile, focus_areas),
            'next_match_focus': self._create_next_match_focus(focus_areas)
        }
        
        return {
            'success': True,
            'coaching_type': 'mlbb_knowledge_base',
            'coaching_content': coaching_content,
            'mlbb_specific': True,
            'processing_time': 0.5
        }
    
    def _add_mlbb_specific_insights(self, coaching_result: Dict[str, Any], match_context: MLBBMatchContext) -> Dict[str, Any]:
        """Add MLBB-specific insights to coaching result."""
        enhanced = coaching_result.copy()
        
        # Add MLBB meta context
        enhanced['mlbb_meta_context'] = {
            'hero_meta_tier': self._get_meta_tier(match_context.hero_played),
            'role_meta_priority': self._get_role_meta_priority(match_context.player_role),
            'current_meta_strategies': self.knowledge_base.meta_analysis['meta_strategies']
        }
        
        # Add MLBB-specific performance benchmarks
        enhanced['mlbb_benchmarks'] = self._get_mlbb_performance_benchmarks(match_context)
        
        # Add MLBB improvement suggestions
        enhanced['mlbb_improvements'] = self._generate_mlbb_improvements(match_context)
        
        return enhanced
    
    def _get_meta_tier(self, hero_name: str) -> str:
        """Get current meta tier for MLBB hero."""
        hero_lower = hero_name.lower()
        
        for role, heroes in self.knowledge_base.meta_analysis['top_tier_heroes'].items():
            if hero_lower in heroes:
                return 'top'
        
        return 'viable'
    
    def _get_role_meta_priority(self, role: MLBBRole) -> str:
        """Get meta priority for MLBB role."""
        # Current MLBB meta priorities
        role_priorities = {
            MLBBRole.MARKSMAN: 'high',
            MLBBRole.TANK: 'high', 
            MLBBRole.ASSASSIN: 'medium',
            MLBBRole.MAGE: 'medium',
            MLBBRole.SUPPORT: 'medium'
        }
        
        return role_priorities.get(role, 'medium')
    
    def _get_mlbb_performance_benchmarks(self, match_context: MLBBMatchContext) -> Dict[str, Any]:
        """Get MLBB performance benchmarks for role/hero."""
        role = match_context.player_role.value
        
        benchmarks = {
            'marksman': {'gpm': 350, 'hero_damage': 60000, 'deaths_max': 4},
            'tank': {'gpm': 200, 'damage_taken': 80000, 'tf_participation': 80},
            'assassin': {'gpm': 330, 'hero_damage': 50000, 'kills_min': 8},
            'mage': {'gpm': 320, 'hero_damage': 55000, 'tf_participation': 75},
            'support': {'gpm': 180, 'assists_min': 12, 'tf_participation': 85}
        }
        
        return benchmarks.get(role, benchmarks['marksman'])
    
    def _generate_mlbb_improvements(self, match_context: MLBBMatchContext) -> List[str]:
        """Generate MLBB-specific improvement suggestions."""
        improvements = []
        match_data = match_context.match_data
        
        # MLBB-specific improvement analysis
        gpm = match_data.get('gold_per_min', 0)
        deaths = match_data.get('deaths', 0)
        tf_participation = match_data.get('teamfight_participation', 0)
        
        if gpm < 300:
            improvements.append("Focus on MLBB farming fundamentals - practice last-hitting and jungle timing")
        
        if deaths > 5:
            improvements.append("Improve MLBB map awareness and positioning - study common gank routes")
        
        if tf_participation < 60:
            improvements.append("Increase MLBB team fight participation - learn team fight positioning")
        
        # Hero-specific improvements
        hero_data = self.knowledge_base.hero_database.get(match_context.hero_played.lower(), {})
        if hero_data and 'coaching_focus' in hero_data:
            for focus_area in hero_data['coaching_focus'][:2]:
                improvements.append(f"Master {match_context.hero_played} {focus_area.replace('_', ' ')}")
        
        return improvements[:5]  # Top 5 improvements
    
    def _create_improvement_plan(self, 
                               match_context: MLBBMatchContext,
                               player_profile: MLBBPlayerProfile,
                               focus_areas: List[MLBBCoachingArea]) -> List[str]:
        """Create MLBB-specific improvement plan."""
        skill_level = player_profile.skill_level
        framework = self.knowledge_base.improvement_frameworks.get(f"{skill_level}_framework", [])
        
        # Customize framework for MLBB and focus areas
        customized_plan = []
        
        for area in focus_areas:
            if area == MLBBCoachingArea.FARMING_EFFICIENCY:
                customized_plan.append("Practice MLBB farming: aim for 350+ GPM consistently")
            elif area == MLBBCoachingArea.POSITIONING:
                customized_plan.append("Study MLBB positioning: learn safe spots for your role")
            elif area == MLBBCoachingArea.TEAM_FIGHTING:
                customized_plan.append("Master MLBB team fights: practice role-specific positioning")
        
        # Add skill level appropriate goals
        customized_plan.extend(framework[:3])
        
        return customized_plan[:5]
    
    def _create_next_match_focus(self, focus_areas: List[MLBBCoachingArea]) -> List[str]:
        """Create next match focus goals."""
        focus_goals = []
        
        for area in focus_areas:
            if area == MLBBCoachingArea.FARMING_EFFICIENCY:
                focus_goals.append("Focus on last-hitting and maintaining high GPM")
            elif area == MLBBCoachingArea.POSITIONING:
                focus_goals.append("Prioritize safe positioning and map awareness")
            elif area == MLBBCoachingArea.TEAM_FIGHTING:
                focus_goals.append("Focus on optimal team fight participation")
        
        return focus_goals
    
    async def _generate_basic_mlbb_coaching(self, match_data: Dict[str, Any], player_ign: str) -> Dict[str, Any]:
        """Generate basic MLBB coaching as fallback."""
        return {
            'coaching_type': 'basic_mlbb',
            'main_message': f"MLBB coaching for {player_ign}",
            'basic_tips': [
                "Focus on improving your MLBB fundamentals",
                "Practice hero mechanics and positioning",
                "Study current MLBB meta and strategies"
            ],
            'mlbb_specific': True
        }
    
    async def _update_player_profile(self, 
                                   player_ign: str,
                                   match_context: MLBBMatchContext,
                                   coaching_result: Dict[str, Any]):
        """Update player profile based on coaching session."""
        if player_ign in self.player_profiles:
            profile = self.player_profiles[player_ign]
            
            # Update hero list
            hero_played = match_context.hero_played.lower()
            if hero_played not in profile.main_heroes:
                profile.main_heroes.append(hero_played)
                profile.main_heroes = profile.main_heroes[-10:]  # Keep last 10 heroes
            
            # Update match history
            profile.match_history_summary['total_matches'] = profile.match_history_summary.get('total_matches', 0) + 1
    
    def _record_coaching_session(self, player_ign: str, coaching_result: Dict[str, Any]):
        """Record coaching session for analytics."""
        session_record = {
            'timestamp': time.time(),
            'player_ign': player_ign,
            'coaching_type': coaching_result.get('coaching_type', 'unknown'),
            'success': coaching_result.get('success', False),
            'processing_time': coaching_result.get('processing_time', 0),
            'mlbb_specific': True
        }
        
        self.coaching_history[player_ign].append(session_record)
        
        # Update metrics
        self.coaching_metrics['total_coaching_sessions'] += 1
    
    def get_comprehensive_coaching_stats(self) -> Dict[str, Any]:
        """Get comprehensive coaching statistics."""
        stats = self.coaching_metrics.copy()
        
        # Add component stats
        if self.gpt4_coach:
            stats['gpt4_coach'] = self.gpt4_coach.get_coaching_stats()
        
        if self.behavioral_engine:
            stats['behavioral_learning'] = {
                'patterns_tracked': len(self.behavioral_engine.mlbb_behavioral_patterns),
                'improvement_tracking': len(self.behavioral_engine.coaching_effectiveness['improvement_tracking'])
            }
        
        # Player analytics
        stats['player_analytics'] = {
            'total_players': len(self.player_profiles),
            'avg_sessions_per_player': (
                self.coaching_metrics['total_coaching_sessions'] / max(len(self.player_profiles), 1)
            ),
            'skill_level_distribution': self._get_skill_level_distribution()
        }
        
        return stats
    
    def _get_skill_level_distribution(self) -> Dict[str, int]:
        """Get skill level distribution of coached players."""
        distribution = defaultdict(int)
        
        for profile in self.player_profiles.values():
            distribution[profile.skill_level] += 1
        
        return dict(distribution)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform MLBB coaching system health check."""
        health_status = {
            'status': 'healthy',
            'components': {},
            'mlbb_focus': True
        }
        
        # Check GPT-4 availability
        if self.gpt4_coach:
            health_status['components']['gpt4_coach'] = {
                'status': 'healthy' if self.gpt4_coach.available else 'unavailable',
                'api_available': self.gpt4_coach.available
            }
        
        # Check behavioral learning
        if self.behavioral_engine:
            health_status['components']['behavioral_learning'] = {
                'status': 'healthy',
                'patterns_tracked': len(self.behavioral_engine.mlbb_behavioral_patterns)
            }
        
        # Check knowledge base
        health_status['components']['mlbb_knowledge_base'] = {
            'status': 'healthy',
            'heroes_loaded': len(self.knowledge_base.hero_database),
            'strategies_loaded': len(self.knowledge_base.role_strategies)
        }
        
        # Overall health
        component_statuses = [comp.get('status', 'unknown') for comp in health_status['components'].values()]
        if all(status in ['healthy', 'disabled'] for status in component_statuses):
            health_status['status'] = 'healthy'
        elif any(status == 'unavailable' for status in component_statuses):
            health_status['status'] = 'degraded'
        else:
            health_status['status'] = 'unhealthy'
        
        return health_status


# Global MLBB coaching intelligence
mlbb_coaching_intelligence = AdvancedMLBBCoachingIntelligence()


def get_mlbb_coaching_intelligence() -> AdvancedMLBBCoachingIntelligence:
    """Get the global MLBB coaching intelligence instance."""
    return mlbb_coaching_intelligence


# Convenience function for MLBB coaching
async def provide_mlbb_coaching(match_data: Dict[str, Any], 
                               player_ign: str,
                               coaching_focus: List[str] = None) -> Dict[str, Any]:
    """
    Convenience function for MLBB coaching.
    
    Args:
        match_data: MLBB match data
        player_ign: Player IGN
        coaching_focus: Specific coaching areas
        
    Returns:
        MLBB coaching result
    """
    coach = get_mlbb_coaching_intelligence()
    return await coach.provide_comprehensive_mlbb_coaching(
        match_data=match_data,
        player_ign=player_ign,
        coaching_focus=coaching_focus
    )


if __name__ == "__main__":
    # Test MLBB coaching system
    async def test_mlbb_coaching():
        """Test MLBB coaching functionality."""
        logger.info("🧪 Testing Advanced MLBB Coaching Intelligence")
        
        # Initialize coaching system
        coach = AdvancedMLBBCoachingIntelligence()
        
        # Create test match data
        test_match_data = {
            'hero': 'Miya',
            'kills': 8,
            'deaths': 3,
            'assists': 12,
            'gold': 15000,
            'gold_per_min': 375,
            'hero_damage': 65000,
            'damage_taken': 25000,
            'teamfight_participation': 75,
            'match_duration': 12.5,
            'mvp': True,
            'performance_rating': 'excellent'
        }
        
        # Test coaching
        coaching_result = await coach.provide_comprehensive_mlbb_coaching(
            match_data=test_match_data,
            player_ign="TestPlayer",
            coaching_focus=['farming', 'positioning']
        )
        
        logger.info(f"📊 MLBB Coaching result: {coaching_result.get('success', False)}")
        logger.info(f"   - Coaching type: {coaching_result.get('coaching_type', 'unknown')}")
        logger.info(f"   - MLBB specific: {coaching_result.get('mlbb_specific', False)}")
        
        # Health check
        health = await coach.health_check()
        logger.info(f"🏥 Health status: {health['status']}")
        logger.info(f"   - MLBB focused: {health['mlbb_focus']}")
        
        # Get statistics
        stats = coach.get_comprehensive_coaching_stats()
        logger.info(f"📈 Coaching stats: {json.dumps(stats, indent=2, default=str)}")
    
    import json
    asyncio.run(test_mlbb_coaching())
