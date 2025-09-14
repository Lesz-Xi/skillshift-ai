"""
Fallback and Role-Based Evaluators
==================================

This module provides robust fallback mechanisms to ensure the coaching system
never returns "no logic found" errors. It integrates with existing role-based
rules and provides graceful degradation when hero-specific configurations
are unavailable.

Fallback hierarchy:
1. Hero-specific YAML config + multi-layer evaluators
2. Existing hero-specific Python rules (legacy compatibility)
3. Role-based generic evaluators  
4. Universal fallback evaluator

All fallbacks return structured CoachingTip objects for consistent UI output.
"""

import logging
import importlib.util
import os
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path

from .enhanced_coaching import (
    CoachingTip, CoachingSeverity, CoachingCategory, FocusArea,
    ExpectedImpact, RankTier, EnhancedMatchAnalysis, format_coaching_message,
    humanize_number, CoachingResult
)
from .hero_config_loader import HeroConfig, get_hero_config_loader
from .multi_layer_evaluators import MultiLayerCoachingOrchestrator


logger = logging.getLogger(__name__)


class LegacyRuleAdapter:
    """
    Adapter to convert legacy tuple-based hero rules to new CoachingTip format.
    
    Maintains backward compatibility with existing hero rule files while
    providing consistent structured output.
    """
    
    def __init__(self):
        self._loaded_modules = {}
        self.rules_base_path = Path("rules")
        
    def load_legacy_rule(self, hero_name: str) -> Optional[Any]:
        """Load a legacy hero rule module if it exists."""
        module_key = hero_name.lower()
        
        if module_key in self._loaded_modules:
            return self._loaded_modules[module_key]
            
        # Search for hero rule file in role directories
        for role_dir in self.rules_base_path.glob("roles/*/"):
            if not role_dir.is_dir():
                continue
                
            hero_file = role_dir / f"{hero_name.lower()}.py"
            if hero_file.exists():
                try:
                    spec = importlib.util.spec_from_file_location(
                        f"rules.roles.{role_dir.name}.{hero_name.lower()}",
                        hero_file
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    self._loaded_modules[module_key] = module
                    logger.info(f"Loaded legacy rule for {hero_name}")
                    return module
                    
                except Exception as e:
                    logger.error(f"Error loading legacy rule for {hero_name}: {e}")
                    return None
                    
        return None
        
    def evaluate_with_legacy_rule(self, hero_name: str, match_data: Dict[str, Any]) -> Optional[List[CoachingTip]]:
        """Evaluate using legacy rule and convert to CoachingTip format."""
        module = self.load_legacy_rule(hero_name)
        if not module or not hasattr(module, 'evaluate'):
            return None
            
        try:
            # Call legacy evaluate function
            minutes = match_data.get('match_duration', 15.0)
            try:
                # Try new format with minutes parameter
                legacy_feedback = module.evaluate(match_data, minutes)
            except TypeError:
                # Fall back to old format
                legacy_feedback = module.evaluate(match_data)
                
            if not legacy_feedback:
                return None
                
            # Convert legacy feedback to CoachingTip objects
            coaching_tips = []
            for item in legacy_feedback:
                tip = self._convert_legacy_feedback(item, hero_name, match_data)
                if tip:
                    coaching_tips.append(tip)
                    
            return coaching_tips
            
        except Exception as e:
            logger.error(f"Error evaluating with legacy rule for {hero_name}: {e}")
            return None
            
    def _convert_legacy_feedback(self, legacy_item: Union[str, Tuple[str, str]], 
                                hero_name: str, match_data: Dict[str, Any]) -> Optional[CoachingTip]:
        """Convert legacy feedback item to CoachingTip format."""
        try:
            if isinstance(legacy_item, tuple) and len(legacy_item) == 2:
                # New format: (severity, message)
                severity_str, message = legacy_item
                severity = self._parse_severity(severity_str)
            elif isinstance(legacy_item, str):
                # Old format: just message, infer severity
                message = legacy_item
                severity = self._infer_severity(message)
            else:
                logger.warning(f"Unknown legacy feedback format: {legacy_item}")
                return None
                
            # Infer category and focus area from message content
            category, focus_area = self._infer_category_and_focus(message)
            
            # Create CoachingTip with reasonable defaults
            return CoachingTip(
                severity=severity,
                message=message,
                category=category,
                focus_area=focus_area,
                confidence=0.75,  # Reasonable confidence for legacy rules
                action_items=self._extract_action_items(message),
                expected_impact=ExpectedImpact.MEDIUM,
                hero_specificity=0.8,  # Legacy rules are hero-specific
                improvement_metric=self._infer_improvement_metric(focus_area),
                timeline_estimate="3-5 games",
                source_evaluator=f"Legacy_{hero_name}"
            )
            
        except Exception as e:
            logger.error(f"Error converting legacy feedback: {e}")
            return None
            
    def _parse_severity(self, severity_str: str) -> CoachingSeverity:
        """Parse severity string from legacy format."""
        severity_map = {
            'success': CoachingSeverity.SUCCESS,
            'info': CoachingSeverity.INFO,
            'warning': CoachingSeverity.WARNING,
            'critical': CoachingSeverity.CRITICAL
        }
        return severity_map.get(severity_str.lower(), CoachingSeverity.INFO)
        
    def _infer_severity(self, message: str) -> CoachingSeverity:
        """Infer severity from message content."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['excellent', 'great', 'outstanding', 'perfect']):
            return CoachingSeverity.SUCCESS
        elif any(word in message_lower for word in ['critical', 'urgent', 'too high', 'very low']):
            return CoachingSeverity.CRITICAL
        elif any(word in message_lower for word in ['low', 'poor', 'improve', 'focus', 'should', 'need']):
            return CoachingSeverity.WARNING
        else:
            return CoachingSeverity.INFO
            
    def _infer_category_and_focus(self, message: str) -> Tuple[CoachingCategory, FocusArea]:
        """Infer category and focus area from message content.""" 
        message_lower = message.lower()
        
        # Focus area detection
        if 'kda' in message_lower or 'kill' in message_lower or 'death' in message_lower:
            return CoachingCategory.PERFORMANCE, FocusArea.KDA
        elif 'gpm' in message_lower or 'gold' in message_lower or 'farm' in message_lower:
            return CoachingCategory.PERFORMANCE, FocusArea.GPM
        elif 'damage' in message_lower:
            return CoachingCategory.PERFORMANCE, FocusArea.DAMAGE_OUTPUT
        elif 'teamfight' in message_lower or 'participation' in message_lower:
            return CoachingCategory.PERFORMANCE, FocusArea.TEAMFIGHTING
        elif 'position' in message_lower or 'stay behind' in message_lower:
            return CoachingCategory.TACTICAL, FocusArea.POSITIONING
        elif 'ultimate' in message_lower or 'skill' in message_lower or 'combo' in message_lower:
            return CoachingCategory.TACTICAL, FocusArea.SKILL_USAGE
        else:
            return CoachingCategory.PERFORMANCE, FocusArea.SKILL_DEVELOPMENT
            
    def _extract_action_items(self, message: str) -> List[str]:
        """Extract actionable advice from message text."""
        # Simple extraction of actionable phrases
        action_items = []
        
        # Look for imperative phrases
        if 'focus on' in message.lower():
            start = message.lower().find('focus on')
            end = message.find('.', start)
            if end == -1:
                end = len(message)
            action = message[start:end].strip()
            action_items.append(action.capitalize())
            
        if 'use ' in message.lower() and ' to ' in message.lower():
            start = message.lower().find('use ')
            end = message.find('.', start)
            if end == -1:
                end = len(message)
            action = message[start:end].strip()
            action_items.append(action.capitalize())
            
        # Fallback: use first sentence as action if no specific actions found
        if not action_items:
            first_sentence = message.split('.')[0].strip()
            if len(first_sentence) < 100:  # Reasonable length check
                action_items.append(first_sentence)
                
        return action_items[:2]  # Maximum 2 action items
        
    def _infer_improvement_metric(self, focus_area: FocusArea) -> str:
        """Infer improvement metric from focus area."""
        metric_map = {
            FocusArea.KDA: 'kda_ratio',
            FocusArea.GPM: 'gold_per_min', 
            FocusArea.DAMAGE_OUTPUT: 'hero_damage',
            FocusArea.TEAMFIGHTING: 'teamfight_participation',
            FocusArea.POSITIONING: 'damage_ratio',
            FocusArea.SKILL_USAGE: 'ult_usage_effectiveness'
        }
        return metric_map.get(focus_area, 'performance_score')


class RoleBasedEvaluator:
    """
    Generic role-based evaluator that provides coaching when hero-specific
    configurations are unavailable.
    
    Uses role-appropriate thresholds and advice to ensure useful feedback
    for any hero in the game.
    """
    
    def __init__(self):
        self.role_configs = self._initialize_role_configs()
        
    def _initialize_role_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize role-based coaching configurations."""
        return {
            'tank': {
                'kda_thresholds': {'excellent': 3.5, 'good': 2.2, 'poor': 1.2},
                'gpm_thresholds': {'excellent': 450, 'good': 380, 'poor': 320},
                'damage_per_minute': {'excellent': 2800, 'good': 2200, 'poor': 1600},
                'teamfight_participation': {'excellent': 85, 'good': 70, 'poor': 55},
                'primary_focus': 'Team engagement and protection',
                'key_advice': [
                    "Initiate team fights with good timing",
                    "Protect your carries from enemy threats",
                    "Control vision and objectives"
                ]
            },
            'fighter': {
                'kda_thresholds': {'excellent': 4.0, 'good': 2.8, 'poor': 1.8},
                'gpm_thresholds': {'excellent': 580, 'good': 500, 'poor': 420},
                'damage_per_minute': {'excellent': 4200, 'good': 3400, 'poor': 2600},
                'teamfight_participation': {'excellent': 75, 'good': 60, 'poor': 45},
                'primary_focus': 'Balanced damage and survivability',
                'key_advice': [
                    "Split-push side lanes when team doesn't need you",
                    "Focus on enemy backline in team fights",
                    "Balance aggression with survival"
                ]
            },
            'assassin': {
                'kda_thresholds': {'excellent': 5.5, 'good': 3.8, 'poor': 2.2},
                'gpm_thresholds': {'excellent': 600, 'good': 520, 'poor': 440},
                'damage_per_minute': {'excellent': 5000, 'good': 3800, 'poor': 2800},
                'teamfight_participation': {'excellent': 70, 'good': 55, 'poor': 40},
                'primary_focus': 'Elimination of priority targets',
                'key_advice': [
                    "Focus on isolated enemy carries",
                    "Master your escape combos and timing",
                    "Avoid team fights until you spot your target"
                ]
            },
            'mage': {
                'kda_thresholds': {'excellent': 4.5, 'good': 3.0, 'poor': 2.0},
                'gpm_thresholds': {'excellent': 580, 'good': 500, 'poor': 420},
                'damage_per_minute': {'excellent': 6000, 'good': 4500, 'poor': 3200},
                'teamfight_participation': {'excellent': 80, 'good': 65, 'poor': 50},
                'primary_focus': 'AoE damage and zone control',
                'key_advice': [
                    "Position safely behind your frontline",
                    "Focus on landing AoE abilities on multiple enemies", 
                    "Control team fight positioning with zone abilities"
                ]
            },
            'marksman': {
                'kda_thresholds': {'excellent': 5.0, 'good': 3.5, 'poor': 2.0},
                'gpm_thresholds': {'excellent': 650, 'good': 560, 'poor': 480},
                'damage_per_minute': {'excellent': 7500, 'good': 5800, 'poor': 4200},
                'teamfight_participation': {'excellent': 75, 'good': 60, 'poor': 45},
                'primary_focus': 'Consistent DPS and positioning',
                'key_advice': [
                    "Prioritize farming safely in early game",
                    "Maintain maximum auto-attack range in fights",
                    "Focus on staying alive over dealing damage"
                ]
            },
            'support': {
                'kda_thresholds': {'excellent': 4.8, 'good': 3.2, 'poor': 2.0},
                'gpm_thresholds': {'excellent': 420, 'good': 350, 'poor': 280},
                'damage_per_minute': {'excellent': 2200, 'good': 1600, 'poor': 1000},
                'teamfight_participation': {'excellent': 85, 'good': 70, 'poor': 55},
                'primary_focus': 'Team enablement and protection',
                'key_advice': [
                    "Prioritize keeping your carries alive",
                    "Control vision and provide map information",
                    "Enable team fights with crowd control"
                ]
            }
        }
        
    def evaluate(self, match_data: EnhancedMatchAnalysis, role: str) -> List[CoachingTip]:
        """Generate role-based coaching tips."""
        tips = []
        role_config = self.role_configs.get(role.lower())
        
        if not role_config:
            # Unknown role - use generic advice
            return self._generate_generic_tips(match_data)
            
        tips.extend(self._evaluate_role_performance(match_data, role, role_config))
        tips.extend(self._add_role_specific_advice(match_data, role, role_config))
        
        return tips
        
    def _evaluate_role_performance(self, match_data: EnhancedMatchAnalysis, 
                                  role: str, role_config: Dict[str, Any]) -> List[CoachingTip]:
        """Evaluate performance using role-based thresholds."""
        tips = []
        
        # KDA evaluation
        kda = match_data.kda_ratio
        kda_thresholds = role_config['kda_thresholds']
        
        if kda >= kda_thresholds['excellent']:
            tips.append(CoachingTip(
                severity=CoachingSeverity.SUCCESS,
                message=format_coaching_message(
                    "Excellent {role} performance! KDA {kda:.1f} shows strong impact with good survival.",
                    role=role, kda=kda
                ),
                category=CoachingCategory.PERFORMANCE,
                focus_area=FocusArea.KDA,
                confidence=0.8,
                action_items=["Maintain this level of performance"],
                hero_specificity=0.3,
                source_evaluator=f"RoleBased_{role}"
            ))
        elif kda < kda_thresholds['poor']:
            tips.append(CoachingTip(
                severity=CoachingSeverity.WARNING,
                message=format_coaching_message(
                    "KDA {kda:.1f} is low for a {role}. Focus on safer positioning and {focus}.",
                    kda=kda, role=role, focus=role_config['primary_focus'].lower()
                ),
                category=CoachingCategory.PERFORMANCE,
                focus_area=FocusArea.KDA,
                confidence=0.8,
                action_items=["Improve positioning", "Focus on role fundamentals"],
                improvement_metric="kda_ratio",
                target_threshold=kda_thresholds['good'],
                timeline_estimate="5-8 games",
                hero_specificity=0.3,
                source_evaluator=f"RoleBased_{role}"
            ))
            
        # GPM evaluation
        gpm = match_data.gold_per_min
        gpm_thresholds = role_config['gpm_thresholds']
        
        if gpm < gpm_thresholds['poor']:
            gpm_advice = self._get_role_gpm_advice(role)
            tips.append(CoachingTip(
                severity=CoachingSeverity.WARNING,
                message=format_coaching_message(
                    "Gold income {gpm} is low for {role}. {advice}",
                    gpm=gpm, role=role, advice=gpm_advice
                ),
                category=CoachingCategory.PERFORMANCE,
                focus_area=FocusArea.GPM,
                confidence=0.75,
                action_items=["Improve farming efficiency"],
                improvement_metric="gold_per_min",
                target_threshold=gpm_thresholds['good'],
                timeline_estimate="3-5 games",
                hero_specificity=0.2,
                source_evaluator=f"RoleBased_{role}"
            ))
            
        return tips
        
    def _get_role_gpm_advice(self, role: str) -> str:
        """Get role-specific GPM improvement advice."""
        advice_map = {
            'tank': "Focus on assist gold from team engagements",
            'fighter': "Balance farming with team fight participation",
            'assassin': "Secure kills and farm jungle efficiently",
            'mage': "Clear minion waves and jungle camps between fights",
            'marksman': "Prioritize safe farming and last-hitting",
            'support': "Focus on shared gold and assist income"
        }
        return advice_map.get(role.lower(), "Focus on efficient farming")
        
    def _add_role_specific_advice(self, match_data: EnhancedMatchAnalysis,
                                 role: str, role_config: Dict[str, Any]) -> List[CoachingTip]:
        """Add role-specific strategic advice."""
        tips = []
        key_advice = role_config['key_advice']
        primary_focus = role_config['primary_focus']
        
        # Add one piece of role-specific advice
        advice_message = f"As a {role}, {primary_focus.lower()}. {key_advice[0]}"
        
        tips.append(CoachingTip(
            severity=CoachingSeverity.INFO,
            message=advice_message,
            category=CoachingCategory.STRATEGIC,
            focus_area=FocusArea.SKILL_DEVELOPMENT,
            confidence=0.7,
            action_items=[key_advice[0]],
            practice_suggestions=[f"Study {role} gameplay guides"],
            expected_impact=ExpectedImpact.MEDIUM,
            timeline_estimate="1-2 weeks",
            hero_specificity=0.2,
            source_evaluator=f"RoleBased_{role}"
        ))
        
        return tips
        
    def _generate_generic_tips(self, match_data: EnhancedMatchAnalysis) -> List[CoachingTip]:
        """Generate generic tips when role is unknown."""
        tips = []
        kda = match_data.kda_ratio
        
        # Basic KDA feedback
        if kda >= 3.0:
            tips.append(CoachingTip(
                severity=CoachingSeverity.SUCCESS,
                message=f"Good performance with {kda:.1f} KDA! Keep up the consistent play.",
                category=CoachingCategory.PERFORMANCE,
                focus_area=FocusArea.KDA,
                confidence=0.6,
                hero_specificity=0.0,
                source_evaluator="Generic"
            ))
        elif kda < 2.0:
            tips.append(CoachingTip(
                severity=CoachingSeverity.WARNING,
                message=f"KDA {kda:.1f} could be improved. Focus on positioning and safer plays.",
                category=CoachingCategory.PERFORMANCE,
                focus_area=FocusArea.KDA,
                confidence=0.6,
                action_items=["Improve positioning", "Play more safely"],
                improvement_metric="kda_ratio",
                target_threshold=2.5,
                timeline_estimate="5-10 games",
                hero_specificity=0.0,
                source_evaluator="Generic"
            ))
            
        # Generic advice
        tips.append(CoachingTip(
            severity=CoachingSeverity.INFO,
            message="Focus on core gameplay fundamentals: positioning, farming, and team coordination.",
            category=CoachingCategory.TACTICAL,
            focus_area=FocusArea.SKILL_DEVELOPMENT,
            confidence=0.5,
            action_items=["Practice positioning", "Improve map awareness"],
            timeline_estimate="ongoing",
            hero_specificity=0.0,
            source_evaluator="Generic"
        ))
        
        return tips


class FallbackCoachingOrchestrator:
    """
    Master orchestrator that implements the complete fallback hierarchy:
    
    1. Enhanced multi-layer system (YAML + 4-layer evaluators)
    2. Legacy hero-specific rules (existing .py files)
    3. Role-based generic evaluators
    4. Universal fallback
    
    Guarantees useful feedback in all scenarios while maintaining consistency.
    """
    
    def __init__(self):
        self.multi_layer_orchestrator = MultiLayerCoachingOrchestrator()
        self.legacy_adapter = LegacyRuleAdapter()
        self.role_evaluator = RoleBasedEvaluator()
        self.config_loader = get_hero_config_loader()
        
    def generate_coaching(self, match_data: Union[EnhancedMatchAnalysis, Dict[str, Any]], 
                         include_severity: bool = False) -> Union[CoachingResult, List[Union[str, tuple]]]:
        """
        Generate coaching feedback using the complete fallback hierarchy.
        
        Args:
            match_data: Match data (enhanced or legacy format)
            include_severity: Return legacy format with severity tuples
            
        Returns:
            CoachingResult for new system, legacy format for backward compatibility
        """
        # Convert legacy format to enhanced format if needed
        if isinstance(match_data, dict):
            enhanced_match = self._convert_to_enhanced_format(match_data)
        else:
            enhanced_match = match_data
            
        hero_name = enhanced_match.hero
        coaching_tips = []
        evaluator_chain = []
        
        # Level 1: Try enhanced multi-layer system
        try:
            coaching_tips = self.multi_layer_orchestrator.generate_coaching(enhanced_match)
            if coaching_tips:
                evaluator_chain.append("MultiLayer")
                logger.info(f"Generated coaching using multi-layer system for {hero_name}")
            else:
                raise Exception("Multi-layer system returned no tips")
                
        except Exception as e:
            logger.warning(f"Multi-layer system failed for {hero_name}: {e}")
            
            # Level 2: Try legacy hero-specific rules
            try:
                legacy_tips = self.legacy_adapter.evaluate_with_legacy_rule(
                    hero_name, enhanced_match.get_basic_stats()
                )
                if legacy_tips:
                    coaching_tips = legacy_tips
                    evaluator_chain.append(f"Legacy_{hero_name}")
                    logger.info(f"Generated coaching using legacy rules for {hero_name}")
                else:
                    raise Exception("Legacy rules returned no tips")
                    
            except Exception as e2:
                logger.warning(f"Legacy rules failed for {hero_name}: {e2}")
                
                # Level 3: Try role-based evaluation
                try:
                    role = self._detect_hero_role(hero_name) or "unknown"
                    role_tips = self.role_evaluator.evaluate(enhanced_match, role)
                    if role_tips:
                        coaching_tips = role_tips
                        evaluator_chain.append(f"RoleBased_{role}")
                        logger.info(f"Generated coaching using role-based system for {hero_name} ({role})")
                    else:
                        raise Exception("Role-based evaluation returned no tips")
                        
                except Exception as e3:
                    logger.warning(f"Role-based evaluation failed for {hero_name}: {e3}")
                    
                    # Level 4: Universal fallback (guaranteed to work)
                    coaching_tips = self._generate_universal_fallback(enhanced_match)
                    evaluator_chain.append("UniversalFallback")
                    logger.info(f"Generated coaching using universal fallback for {hero_name}")
        
        # Create result object
        result = CoachingResult(
            tips=coaching_tips,
            analysis_metadata={
                "hero": hero_name,
                "evaluator_chain": evaluator_chain,
                "fallback_level": len(evaluator_chain)
            },
            processing_time=0.0,  # Would be measured in production
            evaluator_chain=evaluator_chain
        )
        
        # Return format based on legacy compatibility needs
        if include_severity or isinstance(match_data, dict):
            # Legacy format requested
            return result.get_legacy_format(include_severity)
        else:
            # New format
            return result
            
    def _convert_to_enhanced_format(self, legacy_data: Dict[str, Any]) -> EnhancedMatchAnalysis:
        """Convert legacy match data format to enhanced format."""
        from .enhanced_coaching import EnhancedMatchAnalysis, MatchContext
        
        # Apply the same conversion logic as the original coach.py
        def _with_defaults(d: dict) -> dict:
            # Extract from combined kda if present
            kills = d.get('kills')
            deaths = d.get('deaths') 
            assists = d.get('assists')
            kda_str = d.get('kda')
            if (kills is None or deaths is None or assists is None) and isinstance(kda_str, str) and '/' in kda_str:
                parts = kda_str.split('/')
                try:
                    if kills is None:
                        kills = int(parts[0])
                    if deaths is None:
                        deaths = int(parts[1])
                    if assists is None:
                        assists = int(parts[2])
                except Exception:
                    pass

            # Compute gold_per_min if we only have gold + duration
            gpm = d.get('gold_per_min')
            if gpm is None:
                gold = d.get('gold')
                duration = d.get('match_duration') or d.get('minutes')
                try:
                    if gold is not None and duration and float(duration) > 0:
                        gpm = int(round(float(gold) / float(duration)))
                except Exception:
                    gpm = None

            # Map common aliases
            positioning = d.get('positioning_rating') or d.get('positioning')
            ult_usage = d.get('ult_usage') or d.get('ult_usage_rating')
            tfp = d.get('teamfight_participation') or d.get('tps') or d.get('teamfight_participation_pct')
            try:
                if isinstance(tfp, float):
                    tfp = int(round(tfp))
            except Exception:
                pass

            safe = {
                'hero': d.get('hero') or 'unknown',
                'kills': kills if kills is not None else 0,
                'deaths': deaths if deaths is not None else 0,
                'assists': assists if assists is not None else 0,
                'gold_per_min': gpm if gpm is not None else 0,
                'hero_damage': d.get('hero_damage') or d.get('damage') or 0,
                'turret_damage': d.get('turret_damage') or 0,
                'damage_taken': d.get('damage_taken') or 0,
                'teamfight_participation': tfp if tfp is not None else 0,
                'positioning_rating': (positioning or 'average'),
                'ult_usage': (ult_usage or 'average'),
                'match_duration': float(d.get('match_duration') or 0.0),
                'hooks_landed': d.get('hooks_landed') or 0,
                'team_engages': d.get('team_engages') or 0,
                'vision_score': d.get('vision_score') or 0,
            }
            return {**safe, **d}
        
        # Apply defaults and create enhanced match
        safe_data = _with_defaults(legacy_data)
        
        try:
            return EnhancedMatchAnalysis(
                hero=safe_data['hero'],
                kills=safe_data['kills'],
                deaths=safe_data['deaths'],
                assists=safe_data['assists'],
                gold_per_min=safe_data['gold_per_min'],
                hero_damage=safe_data['hero_damage'],
                turret_damage=safe_data['turret_damage'],
                damage_taken=safe_data['damage_taken'],
                teamfight_participation=safe_data['teamfight_participation'],
                positioning_rating=safe_data['positioning_rating'],
                ult_usage=safe_data['ult_usage'],
                match_duration=safe_data['match_duration'],
                hooks_landed=safe_data['hooks_landed'],
                team_engages=safe_data['team_engages'],
                vision_score=safe_data['vision_score'],
                match_context=MatchContext()  # Default context
            )
        except Exception as e:
            logger.error(f"Error creating enhanced match format: {e}")
            # Return minimal valid object
            return EnhancedMatchAnalysis(
                hero=safe_data.get('hero', 'Unknown'),
                kills=0, deaths=1, assists=0, gold_per_min=0,
                hero_damage=0, turret_damage=0, damage_taken=1,
                teamfight_participation=0
            )
            
    def _detect_hero_role(self, hero_name: str) -> Optional[str]:
        """Detect hero role from existing rules directory or config."""
        # First try to get role from hero config
        try:
            hero_config = self.config_loader.load_hero_config(hero_name)
            if hero_config.role != "unknown":
                return hero_config.role
        except:
            pass
            
        # Fall back to directory detection
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
        
    def _generate_universal_fallback(self, match_data: EnhancedMatchAnalysis) -> List[CoachingTip]:
        """Generate universal fallback tips that always work."""
        tips = []
        hero_name = match_data.hero
        kda = match_data.kda_ratio
        
        # Always provide at least one success or improvement tip
        if kda >= 2.5:
            tips.append(CoachingTip(
                severity=CoachingSeverity.SUCCESS,
                message=f"Solid performance with {hero_name}! KDA {kda:.1f} shows good impact.",
                category=CoachingCategory.PERFORMANCE,
                focus_area=FocusArea.KDA,
                confidence=0.7,
                action_items=["Continue this performance level"],
                hero_specificity=0.1,
                source_evaluator="UniversalFallback"
            ))
        else:
            tips.append(CoachingTip(
                severity=CoachingSeverity.WARNING,
                message=f"Focus on improving {hero_name} fundamentals. KDA {kda:.1f} has room for growth.",
                category=CoachingCategory.PERFORMANCE,
                focus_area=FocusArea.KDA,
                confidence=0.7,
                action_items=["Practice hero mechanics", "Improve positioning"],
                improvement_metric="kda_ratio",
                target_threshold=3.0,
                timeline_estimate="1-2 weeks",
                hero_specificity=0.1,
                source_evaluator="UniversalFallback"
            ))
        
        # Always provide general improvement advice
        tips.append(CoachingTip(
            severity=CoachingSeverity.INFO,
            message="Focus on core fundamentals: positioning, map awareness, and team coordination.",
            category=CoachingCategory.TACTICAL,
            focus_area=FocusArea.SKILL_DEVELOPMENT,
            confidence=0.6,
            action_items=["Study replays", "Practice positioning"],
            practice_suggestions=["Watch professional gameplay", "Focus on minimap awareness"],
            expected_impact=ExpectedImpact.MEDIUM,
            timeline_estimate="ongoing",
            hero_specificity=0.0,
            source_evaluator="UniversalFallback"
        ))
        
        return tips


# === EXAMPLE USAGE ===
if __name__ == "__main__":
    # Test the fallback system
    orchestrator = FallbackCoachingOrchestrator()
    
    # Test with various scenarios
    test_cases = [
        {"hero": "Kagura", "kills": 8, "deaths": 3, "assists": 12, "gold_per_min": 580},
        {"hero": "UnknownHero", "kills": 5, "deaths": 5, "assists": 8, "gold_per_min": 450},
        {"hero": "Franco", "kills": 2, "deaths": 4, "assists": 15, "gold_per_min": 380}
    ]
    
    for i, test_data in enumerate(test_cases, 1):
        print(f"\n=== Test Case {i}: {test_data['hero']} ===")
        result = orchestrator.generate_coaching(test_data)
        
        if isinstance(result, CoachingResult):
            print(f"Evaluator chain: {result.evaluator_chain}")
            for tip in result.tips:
                print(f"- {tip.format_for_display()}")
        else:
            print(f"Legacy result: {result}")