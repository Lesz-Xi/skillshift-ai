"""
YAML Hero Configuration Loader System
====================================

This module provides a flexible, maintainable way to define hero-specific
coaching parameters, thresholds, and advice using YAML configuration files.

Supports hot-reloading, validation, and fallback to default values.
"""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from .enhanced_coaching import RankTier, FocusArea


logger = logging.getLogger(__name__)


class MetaTier(str, Enum):
    """Current meta tier rankings for heroes."""
    S_PLUS = "S+"
    S = "S" 
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C = "C"


@dataclass
class PerformanceThresholds:
    """Performance thresholds with rank-aware scaling."""
    kda: Dict[str, Dict[str, float]] = field(default_factory=dict)
    damage_per_minute: Dict[str, float] = field(default_factory=dict) 
    gpm: Dict[str, float] = field(default_factory=dict)
    teamfight_participation: Dict[str, float] = field(default_factory=dict)
    
    def get_threshold(self, metric: str, level: str, rank: RankTier = RankTier.EPIC) -> float:
        """Get threshold value with rank scaling."""
        base_thresholds = getattr(self, metric, {})
        
        if isinstance(base_thresholds, dict) and level in base_thresholds:
            if isinstance(base_thresholds[level], dict):
                # Rank-specific thresholds
                return base_thresholds[level].get(rank.value, base_thresholds[level].get('default', 0))
            else:
                # Simple threshold value
                return base_thresholds[level]
        return 0.0


@dataclass 
class SkillConfig:
    """Individual skill configuration with coaching parameters."""
    name: str
    key_metrics: List[str] = field(default_factory=list)
    coaching_tips: Dict[str, str] = field(default_factory=dict)
    cooldown: Optional[float] = None
    mana_cost: Optional[int] = None


@dataclass
class ItemRecommendations:
    """Item build recommendations and situational coaching."""
    core_items: List[str] = field(default_factory=list)
    boots_options: List[str] = field(default_factory=list)
    situational_items: Dict[str, List[str]] = field(default_factory=dict)
    coaching_tips: Dict[str, str] = field(default_factory=dict)
    
    def get_build_advice(self, situation: str) -> Optional[str]:
        """Get build advice for specific game situations."""
        return self.coaching_tips.get(situation)


@dataclass
class PositioningGuidance:
    """Positioning and tactical guidance for the hero."""
    ideal_range: str = "medium"  # "close", "medium", "long"
    priority_targets: List[str] = field(default_factory=list)
    escape_routes: str = ""
    teamfight_role: str = ""
    early_game_focus: str = ""
    late_game_focus: str = ""


@dataclass
class MatchupAdvice:
    """Hero matchup-specific coaching advice.""" 
    counters: List[str] = field(default_factory=list)  # Heroes that counter this hero
    strong_against: List[str] = field(default_factory=list)  # Heroes this hero counters
    advice: Dict[str, str] = field(default_factory=dict)  # Specific matchup advice


@dataclass
class HeroConfig:
    """Complete hero configuration loaded from YAML."""
    # Basic hero info
    name: str
    role: str
    difficulty: int = 3
    meta_tier: MetaTier = MetaTier.B
    
    # Performance parameters
    performance_thresholds: PerformanceThresholds = field(default_factory=PerformanceThresholds)
    
    # Skills configuration
    skills: Dict[str, SkillConfig] = field(default_factory=dict)
    
    # Build recommendations
    items: ItemRecommendations = field(default_factory=ItemRecommendations)
    
    # Tactical guidance
    positioning: PositioningGuidance = field(default_factory=PositioningGuidance)
    
    # Matchup information
    matchups: MatchupAdvice = field(default_factory=MatchupAdvice)
    
    # Custom coaching messages
    custom_tips: Dict[str, List[str]] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HeroConfig':
        """Create HeroConfig from dictionary (loaded from YAML)."""
        config = cls(
            name=data.get('name', 'Unknown'),
            role=data.get('role', 'unknown'),
            difficulty=data.get('difficulty', 3),
            meta_tier=MetaTier(data.get('meta_tier', 'B'))
        )
        
        # Load performance thresholds
        if 'performance_thresholds' in data:
            thresholds_data = data['performance_thresholds']
            config.performance_thresholds = PerformanceThresholds(
                kda=thresholds_data.get('kda', {}),
                damage_per_minute=thresholds_data.get('damage_per_minute', {}),
                gpm=thresholds_data.get('gpm', {}),
                teamfight_participation=thresholds_data.get('teamfight_participation', {})
            )
        
        # Load skills
        if 'skills' in data:
            for skill_key, skill_data in data['skills'].items():
                config.skills[skill_key] = SkillConfig(
                    name=skill_data.get('name', skill_key),
                    key_metrics=skill_data.get('key_metrics', []),
                    coaching_tips=skill_data.get('coaching_tips', {}),
                    cooldown=skill_data.get('cooldown'),
                    mana_cost=skill_data.get('mana_cost')
                )
        
        # Load items
        if 'items' in data:
            items_data = data['items']
            config.items = ItemRecommendations(
                core_items=items_data.get('core_items', []),
                boots_options=items_data.get('boots_options', []),
                situational_items=items_data.get('situational_items', {}),
                coaching_tips=items_data.get('coaching_tips', {})
            )
        
        # Load positioning
        if 'positioning' in data:
            pos_data = data['positioning']
            config.positioning = PositioningGuidance(
                ideal_range=pos_data.get('ideal_range', 'medium'),
                priority_targets=pos_data.get('priority_targets', []),
                escape_routes=pos_data.get('escape_routes', ''),
                teamfight_role=pos_data.get('teamfight_role', ''),
                early_game_focus=pos_data.get('early_game_focus', ''),
                late_game_focus=pos_data.get('late_game_focus', '')
            )
        
        # Load matchups
        if 'matchups' in data:
            matchup_data = data['matchups']
            config.matchups = MatchupAdvice(
                counters=matchup_data.get('counters', []),
                strong_against=matchup_data.get('strong_against', []),
                advice=matchup_data.get('advice', {})
            )
        
        # Load custom tips
        config.custom_tips = data.get('custom_tips', {})
        
        return config


class HeroConfigLoader:
    """
    YAML-based hero configuration loader with caching and hot-reload support.
    
    Provides fallback mechanisms and validation for robust operation.
    """
    
    def __init__(self, config_dir: str = "config/heroes"):
        """Initialize the configuration loader."""
        self.config_dir = Path(config_dir)
        self._config_cache: Dict[str, HeroConfig] = {}
        self._file_timestamps: Dict[str, float] = {}
        self._ensure_config_dir()
        
    def _ensure_config_dir(self):
        """Ensure the configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_config_path(self, hero_name: str) -> Path:
        """Get the configuration file path for a hero."""
        return self.config_dir / f"{hero_name.lower().replace(' ', '_')}.yml"
        
    def _load_yaml_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load and parse a YAML configuration file."""
        try:
            if not file_path.exists():
                logger.warning(f"Config file not found: {file_path}")
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading config file {file_path}: {e}")
            return None
            
    def _is_file_modified(self, file_path: Path) -> bool:
        """Check if file has been modified since last load."""
        if not file_path.exists():
            return False
            
        current_mtime = file_path.stat().st_mtime
        cached_mtime = self._file_timestamps.get(str(file_path), 0)
        return current_mtime > cached_mtime
        
    def _update_timestamp(self, file_path: Path):
        """Update the cached timestamp for a file."""
        if file_path.exists():
            self._file_timestamps[str(file_path)] = file_path.stat().st_mtime
            
    def load_hero_config(self, hero_name: str, force_reload: bool = False) -> HeroConfig:
        """
        Load hero configuration from YAML file with caching.
        
        Args:
            hero_name: Name of the hero (case-insensitive)
            force_reload: Force reload from file, ignoring cache
            
        Returns:
            HeroConfig object with hero-specific settings
        """
        hero_key = hero_name.lower()
        config_path = self._get_config_path(hero_name)
        
        # Check if we need to reload
        should_reload = (
            force_reload or 
            hero_key not in self._config_cache or 
            self._is_file_modified(config_path)
        )
        
        if should_reload:
            yaml_data = self._load_yaml_file(config_path)
            if yaml_data:
                try:
                    config = HeroConfig.from_dict(yaml_data)
                    self._config_cache[hero_key] = config
                    self._update_timestamp(config_path)
                    logger.info(f"Loaded config for {hero_name}")
                except Exception as e:
                    logger.error(f"Error parsing config for {hero_name}: {e}")
                    return self._get_default_config(hero_name)
            else:
                logger.warning(f"Could not load config for {hero_name}, using defaults")
                return self._get_default_config(hero_name)
        
        return self._config_cache.get(hero_key, self._get_default_config(hero_name))
        
    def _get_default_config(self, hero_name: str) -> HeroConfig:
        """Generate default configuration for heroes without config files."""
        # Determine role from existing rules directory structure
        role = self._detect_hero_role(hero_name) or "unknown"
        
        default_config = HeroConfig(
            name=hero_name,
            role=role,
            difficulty=3,
            meta_tier=MetaTier.B
        )
        
        # Set role-based default thresholds
        if role == "mage":
            default_config.performance_thresholds.kda = {"excellent": 4.0, "good": 2.5, "poor": 1.5}
            default_config.performance_thresholds.damage_per_minute = {"excellent": 6000, "good": 4500, "poor": 3000}
        elif role == "fighter":
            default_config.performance_thresholds.kda = {"excellent": 4.5, "good": 3.0, "poor": 2.0}
            default_config.performance_thresholds.damage_per_minute = {"excellent": 4500, "good": 3500, "poor": 2500}
        elif role == "tank":
            default_config.performance_thresholds.kda = {"excellent": 3.0, "good": 2.0, "poor": 1.2}
            default_config.performance_thresholds.damage_per_minute = {"excellent": 2500, "good": 1800, "poor": 1200}
        elif role == "support":
            default_config.performance_thresholds.kda = {"excellent": 5.0, "good": 3.5, "poor": 2.0}
            default_config.performance_thresholds.damage_per_minute = {"excellent": 2000, "good": 1500, "poor": 1000}
        elif role == "marksman":
            default_config.performance_thresholds.kda = {"excellent": 5.0, "good": 3.5, "poor": 2.0}
            default_config.performance_thresholds.damage_per_minute = {"excellent": 8000, "good": 6000, "poor": 4000}
        elif role == "assassin":
            default_config.performance_thresholds.kda = {"excellent": 6.0, "good": 4.0, "poor": 2.5}
            default_config.performance_thresholds.damage_per_minute = {"excellent": 5500, "good": 4000, "poor": 2800}
        
        return default_config
        
    def _detect_hero_role(self, hero_name: str) -> Optional[str]:
        """Detect hero role from existing rules directory structure."""
        rules_base = Path("rules/roles")
        if not rules_base.exists():
            return None
            
        hero_file_name = f"{hero_name.lower()}.py"
        for role_dir in rules_base.iterdir():
            if role_dir.is_dir():
                hero_file = role_dir / hero_file_name
                if hero_file.exists():
                    return role_dir.name
        return None
        
    def list_available_configs(self) -> List[str]:
        """List all available hero configuration files."""
        if not self.config_dir.exists():
            return []
            
        configs = []
        for config_file in self.config_dir.glob("*.yml"):
            hero_name = config_file.stem.replace('_', ' ').title()
            configs.append(hero_name)
        return sorted(configs)
        
    def validate_config(self, hero_name: str) -> Dict[str, Any]:
        """Validate a hero configuration file and return validation results."""
        config_path = self._get_config_path(hero_name)
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "config_exists": config_path.exists()
        }
        
        if not config_path.exists():
            result["errors"].append(f"Configuration file not found: {config_path}")
            return result
            
        yaml_data = self._load_yaml_file(config_path)
        if not yaml_data:
            result["errors"].append("Could not parse YAML file")
            return result
            
        # Validate required fields
        required_fields = ["name", "role"]
        for field in required_fields:
            if field not in yaml_data:
                result["errors"].append(f"Missing required field: {field}")
                
        # Validate thresholds
        if "performance_thresholds" in yaml_data:
            thresholds = yaml_data["performance_thresholds"]
            for metric, values in thresholds.items():
                if isinstance(values, dict):
                    for level, value in values.items():
                        if not isinstance(value, (int, float, dict)):
                            result["warnings"].append(f"Threshold {metric}.{level} should be numeric")
        
        result["valid"] = len(result["errors"]) == 0
        return result
        
    def create_template_config(self, hero_name: str, role: str, overwrite: bool = False) -> bool:
        """Create a template configuration file for a hero."""
        config_path = self._get_config_path(hero_name)
        
        if config_path.exists() and not overwrite:
            logger.warning(f"Config file already exists: {config_path}")
            return False
            
        template_data = self._generate_config_template(hero_name, role)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, default_flow_style=False, indent=2)
            logger.info(f"Created template config for {hero_name} at {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating template config: {e}")
            return False
            
    def _generate_config_template(self, hero_name: str, role: str) -> Dict[str, Any]:
        """Generate a configuration template for a hero."""
        return {
            "name": hero_name,
            "role": role,
            "difficulty": 3,
            "meta_tier": "B",
            "performance_thresholds": {
                "kda": {
                    "excellent": {"epic": 4.0, "legend": 4.5, "mythic": 5.0, "default": 4.0},
                    "good": {"epic": 2.5, "legend": 3.0, "mythic": 3.5, "default": 2.5},
                    "poor": {"epic": 1.5, "legend": 1.8, "mythic": 2.0, "default": 1.5}
                },
                "damage_per_minute": {
                    "excellent": 6000,
                    "good": 4500,
                    "poor": 3000
                },
                "gpm": {
                    "excellent": 600,
                    "good": 500,
                    "poor": 400
                },
                "teamfight_participation": {
                    "excellent": 80,
                    "good": 65,
                    "poor": 50
                }
            },
            "skills": {
                "s1": {
                    "name": "First Skill",
                    "key_metrics": ["accuracy", "timing"],
                    "coaching_tips": {
                        "low_accuracy": "Focus on skill shot prediction and positioning"
                    }
                },
                "s2": {
                    "name": "Second Skill", 
                    "key_metrics": ["effectiveness", "timing"],
                    "coaching_tips": {
                        "poor_timing": "Use this skill reactively rather than proactively"
                    }
                },
                "ultimate": {
                    "name": "Ultimate",
                    "key_metrics": ["impact", "timing"],
                    "coaching_tips": {
                        "low_impact": "Save ultimate for key team fights and picks"
                    }
                }
            },
            "items": {
                "core_items": ["Item 1", "Item 2", "Item 3"],
                "boots_options": ["Magic Shoes", "Warrior Boots", "Tough Boots"],
                "situational_items": {
                    "vs_burst": ["Immortality", "Athena's Shield"],
                    "vs_cc": ["Purify Spell", "Tough Boots"]
                },
                "coaching_tips": {
                    "vs_burst": "Consider defensive items against burst teams",
                    "early_game": "Focus on core items for power spikes"
                }
            },
            "positioning": {
                "ideal_range": "medium",
                "priority_targets": ["marksman", "mage"],
                "escape_routes": "Keep mobility skills available for escape",
                "teamfight_role": "Damage dealer with positioning focus",
                "early_game_focus": "Farming and safe laning",
                "late_game_focus": "Team fight positioning and target selection"
            },
            "matchups": {
                "counters": ["Counter Hero 1", "Counter Hero 2"],
                "strong_against": ["Weak Hero 1", "Weak Hero 2"], 
                "advice": {
                    "vs_counters": "Play defensively and focus on farming",
                    "vs_weak": "Be aggressive and look for early kills"
                }
            },
            "custom_tips": {
                "general": [
                    f"Master {hero_name}'s core combos in practice mode",
                    f"Watch professional {hero_name} gameplay for positioning tips"
                ],
                "early_game": [
                    "Focus on farming and reaching power spikes safely"
                ],
                "late_game": [
                    "Position behind frontline and focus priority targets"
                ]
            }
        }


# Global instance
_hero_config_loader = None

def get_hero_config_loader() -> HeroConfigLoader:
    """Get the global hero configuration loader instance."""
    global _hero_config_loader
    if _hero_config_loader is None:
        _hero_config_loader = HeroConfigLoader()
    return _hero_config_loader


# === EXAMPLE USAGE ===
if __name__ == "__main__":
    loader = HeroConfigLoader()
    
    # Create template for Kagura
    if loader.create_template_config("Kagura", "mage"):
        print("Created Kagura template config")
    
    # Load configuration
    kagura_config = loader.load_hero_config("Kagura")
    print(f"Loaded config for {kagura_config.name} ({kagura_config.role})")
    print(f"KDA thresholds: {kagura_config.performance_thresholds.kda}")
    
    # Validate configuration
    validation = loader.validate_config("Kagura")
    print(f"Config valid: {validation['valid']}")
    if validation['errors']:
        print(f"Errors: {validation['errors']}")