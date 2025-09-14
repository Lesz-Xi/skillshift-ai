"""
Multi-Layer Coaching Evaluators
===============================

This module implements the 4-layer coaching evaluation system:

Layer 1: Performance Analysis (KDA, GPM, damage output, teamfighting)
Layer 2: Tactical Analysis (positioning, farming, skill usage, objectives)  
Layer 3: Strategic Analysis (itemization, team synergy, meta awareness, matchups)
Layer 4: Progression Analysis (improvement trends, skill gaps, achievements)

Each layer provides increasingly sophisticated coaching insights.
"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import statistics
from datetime import datetime, timedelta

from .enhanced_coaching import (
    CoachingTip, CoachingSeverity, CoachingCategory, FocusArea, 
    ExpectedImpact, RankTier, EnhancedMatchAnalysis, format_coaching_message, 
    humanize_number
)
from .hero_config_loader import HeroConfig, get_hero_config_loader


logger = logging.getLogger(__name__)


class BaseEvaluator(ABC):
    """Base class for all coaching evaluators."""
    
    def __init__(self, category: CoachingCategory):
        self.category = category
        self.confidence_base = 0.8
        
    @abstractmethod
    def evaluate(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Generate coaching tips for this evaluation layer."""
        pass
        
    def _create_tip(self,
                   severity: CoachingSeverity,
                   message: str,
                   focus_area: FocusArea,
                   match_data: EnhancedMatchAnalysis = None,
                   confidence: float = None,
                   action_items: List[str] = None,
                   practice_suggestions: List[str] = None,
                   expected_impact: ExpectedImpact = ExpectedImpact.MEDIUM,
                   improvement_metric: str = None,
                   target_threshold: float = None,
                   timeline_estimate: str = "1-2 games",
                   hero_specificity: float = 0.5) -> CoachingTip:
        """Helper method to create standardized coaching tips."""
        
        # Get rank relevance from match data if available
        rank_relevance = [match_data.match_context.rank_tier] if match_data else [RankTier.EPIC]
        
        return CoachingTip(
            severity=severity,
            message=message,
            category=self.category,
            focus_area=focus_area,
            confidence=confidence or self.confidence_base,
            action_items=action_items or [],
            practice_suggestions=practice_suggestions or [],
            expected_impact=expected_impact,
            rank_relevance=rank_relevance,
            meta_relevance="current",
            hero_specificity=hero_specificity,
            improvement_metric=improvement_metric,
            target_threshold=target_threshold,
            timeline_estimate=timeline_estimate,
            source_evaluator=self.__class__.__name__
        )


class PerformanceEvaluator(BaseEvaluator):
    """
    Layer 1: Core Performance Analysis
    
    Analyzes fundamental gameplay metrics that are extractable from screenshots:
    - KDA ratios with contextual thresholds
    - Gold per minute with match duration scaling  
    - Hero damage output vs role expectations
    - Teamfight participation effectiveness
    """
    
    def __init__(self):
        super().__init__(CoachingCategory.PERFORMANCE)
        
    def evaluate(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Generate performance-focused coaching tips."""
        tips = []
        
        tips.extend(self._evaluate_kda(match_data, hero_config))
        tips.extend(self._evaluate_economy(match_data, hero_config))
        tips.extend(self._evaluate_damage_output(match_data, hero_config))
        tips.extend(self._evaluate_teamfighting(match_data, hero_config))
        
        return tips
        
    def _evaluate_kda(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Evaluate KDA performance with rank-aware thresholds."""
        tips = []
        kda = match_data.kda_ratio
        rank = match_data.match_context.rank_tier
        
        # Get hero-specific thresholds
        excellent_threshold = hero_config.performance_thresholds.get_threshold('kda', 'excellent', rank)
        good_threshold = hero_config.performance_thresholds.get_threshold('kda', 'good', rank)
        poor_threshold = hero_config.performance_thresholds.get_threshold('kda', 'poor', rank)
        
        if kda >= excellent_threshold:
            tips.append(self._create_tip(
                severity=CoachingSeverity.SUCCESS,
                message=format_coaching_message(
                    "Excellent KDA {kda:.1f} for {hero}! You're maximizing impact while minimizing deaths.",
                    kda=kda, hero=hero_config.name
                ),
                focus_area=FocusArea.KDA,
                confidence=0.9,
                action_items=["Maintain this performance level", "Focus on consistency"],
                expected_impact=ExpectedImpact.HIGH,
                hero_specificity=0.7
            ))
        elif kda >= good_threshold:
            tips.append(self._create_tip(
                severity=CoachingSeverity.INFO,
                message=format_coaching_message(
                    "Solid KDA {kda:.1f}. To reach excellence ({target:.1f}), focus on reducing unnecessary deaths.",
                    kda=kda, target=excellent_threshold
                ),
                focus_area=FocusArea.KDA,
                action_items=["Improve positioning", "Better escape timing"],
                improvement_metric="kda_ratio",
                target_threshold=excellent_threshold,
                timeline_estimate="3-5 games"
            ))
        elif kda >= poor_threshold:
            tips.append(self._create_tip(
                severity=CoachingSeverity.WARNING,
                message=format_coaching_message(
                    "KDA {kda:.1f} needs improvement. Focus on safer plays and better positioning to reduce deaths.",
                    kda=kda
                ),
                focus_area=FocusArea.KDA,
                confidence=0.85,
                action_items=["Play more defensively", "Improve map awareness", "Focus on assists over kills"],
                practice_suggestions=["Practice positioning in AI mode", "Watch replays of your deaths"],
                expected_impact=ExpectedImpact.HIGH,
                improvement_metric="kda_ratio", 
                target_threshold=good_threshold,
                timeline_estimate="5-10 games"
            ))
        else:
            # Critical KDA issues
            tips.append(self._create_tip(
                severity=CoachingSeverity.CRITICAL,
                message=format_coaching_message(
                    "Very low KDA {kda:.1f}. Prioritize survival over aggressive plays. Death reduction is critical.",
                    kda=kda
                ),
                focus_area=FocusArea.KDA,
                confidence=0.9,
                action_items=["Focus entirely on not dying", "Farm safely", "Stay behind teammates"],
                practice_suggestions=["Practice escape combos", "Learn enemy threat ranges"],
                expected_impact=ExpectedImpact.HIGH,
                improvement_metric="kda_ratio",
                target_threshold=poor_threshold,
                timeline_estimate="10-15 games"
            ))
            
        return tips
        
    def _evaluate_economy(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Evaluate gold per minute with match duration scaling.""" 
        tips = []
        gpm = match_data.gold_per_min
        duration = match_data.match_duration or 15.0  # Default if not provided
        
        # Get thresholds from hero config
        excellent_gpm = hero_config.performance_thresholds.get_threshold('gpm', 'excellent')
        good_gpm = hero_config.performance_thresholds.get_threshold('gpm', 'good')  
        poor_gpm = hero_config.performance_thresholds.get_threshold('gpm', 'poor')
        
        # Scale thresholds based on match duration
        if duration < 10:
            # Short games - lower expectations
            scale_factor = 0.85
        elif duration > 25:
            # Long games - higher expectations  
            scale_factor = 1.15
        else:
            scale_factor = 1.0
            
        scaled_excellent = excellent_gpm * scale_factor
        scaled_good = good_gpm * scale_factor
        scaled_poor = poor_gpm * scale_factor
        
        if gpm >= scaled_excellent:
            tips.append(self._create_tip(
                severity=CoachingSeverity.SUCCESS,
                message=format_coaching_message(
                    "Outstanding economy! {gpm} GPM shows excellent farming efficiency.",
                    gpm=gpm
                ),
                focus_area=FocusArea.GPM,
                confidence=0.85,
                action_items=["Maintain farming consistency"],
                hero_specificity=0.6
            ))
        elif gpm < scaled_poor:
            role_specific_advice = self._get_gpm_advice_by_role(hero_config.role)
            tips.append(self._create_tip(
                severity=CoachingSeverity.WARNING,
                message=format_coaching_message(
                    "Low GPM {gpm} (target: {target}). {advice}",
                    gpm=gpm, target=int(scaled_good), advice=role_specific_advice
                ),
                focus_area=FocusArea.GPM,
                confidence=0.8,
                action_items=["Improve farming efficiency", "Clear jungle camps between fights"],
                practice_suggestions=["Practice last-hitting minions", "Learn optimal farming routes"],
                expected_impact=ExpectedImpact.MEDIUM,
                improvement_metric="gold_per_min",
                target_threshold=scaled_good,
                timeline_estimate="3-5 games"
            ))
            
        return tips
        
    def _get_gpm_advice_by_role(self, role: str) -> str:
        """Get role-specific GPM improvement advice.""" 
        advice_map = {
            "mage": "Clear minion waves efficiently and secure jungle camps",
            "marksman": "Focus on last-hitting and safe farming in lane", 
            "assassin": "Balance farming with ganking - don't miss farm for failed ganks",
            "fighter": "Split-push side lanes and clear jungle when not grouping",
            "tank": "Help carries farm safely and secure assist gold from engagements",
            "support": "Focus on assist gold and shared farm with your carry"
        }
        return advice_map.get(role.lower(), "Improve farming consistency and objective participation")
        
    def _evaluate_damage_output(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Evaluate hero damage output versus role expectations."""
        tips = []
        damage = match_data.hero_damage
        duration = match_data.match_duration or 15.0
        dpm = damage / duration if duration > 0 else 0
        
        # Get expected damage thresholds
        excellent_dpm = hero_config.performance_thresholds.get_threshold('damage_per_minute', 'excellent')
        good_dpm = hero_config.performance_thresholds.get_threshold('damage_per_minute', 'good')
        poor_dpm = hero_config.performance_thresholds.get_threshold('damage_per_minute', 'poor')
        
        if dpm >= excellent_dpm:
            tips.append(self._create_tip(
                severity=CoachingSeverity.SUCCESS,
                message=format_coaching_message(
                    "Impressive damage output! {damage} total ({dpm} DPM) shows strong combat effectiveness.",
                    damage=damage, dpm=int(dpm)
                ),
                focus_area=FocusArea.DAMAGE_OUTPUT,
                confidence=0.8,
                hero_specificity=0.8
            ))
        elif dpm < poor_dpm:
            role_advice = self._get_damage_advice_by_role(hero_config.role, hero_config.name)
            tips.append(self._create_tip(
                severity=CoachingSeverity.WARNING, 
                message=format_coaching_message(
                    "Low damage output: {damage} total. {advice}",
                    damage=damage, advice=role_advice
                ),
                focus_area=FocusArea.DAMAGE_OUTPUT,
                confidence=0.8,
                action_items=["Participate more in team fights", "Improve skill accuracy"],
                practice_suggestions=["Practice combos in training mode", "Work on positioning for damage"],
                expected_impact=ExpectedImpact.HIGH,
                improvement_metric="hero_damage",
                target_threshold=good_dpm * duration,
                timeline_estimate="2-3 games",
                hero_specificity=0.9
            ))
            
        return tips
        
    def _get_damage_advice_by_role(self, role: str, hero_name: str) -> str:
        """Get role-specific damage improvement advice."""
        role_advice = {
            "mage": f"Focus on landing skill combos and positioning safely for sustained damage",
            "marksman": "Improve positioning to maximize auto-attack uptime in fights",
            "assassin": "Look for better pick opportunities and combo execution",
            "fighter": "Balance between tanking damage and dealing damage to priority targets",
            "tank": "Focus on initiating good team fights rather than personal damage",
            "support": "Damage is secondary - focus on enabling your carries"
        }
        return role_advice.get(role.lower(), "Focus on better positioning and skill usage in team fights")
        
    def _evaluate_teamfighting(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Evaluate teamfight participation effectiveness."""
        tips = []
        participation = match_data.teamfight_participation
        
        # Get thresholds
        excellent_tf = hero_config.performance_thresholds.get_threshold('teamfight_participation', 'excellent')
        good_tf = hero_config.performance_thresholds.get_threshold('teamfight_participation', 'good')
        poor_tf = hero_config.performance_thresholds.get_threshold('teamfight_participation', 'poor')
        
        if participation >= excellent_tf:
            tips.append(self._create_tip(
                severity=CoachingSeverity.SUCCESS,
                message=format_coaching_message(
                    "Excellent teamfight presence! {participation}% participation shows strong team coordination.",
                    participation=participation
                ),
                focus_area=FocusArea.TEAMFIGHTING,
                confidence=0.85
            ))
        elif participation < poor_tf:
            tips.append(self._create_tip(
                severity=CoachingSeverity.WARNING,
                message=format_coaching_message(
                    "Low teamfight participation ({participation}%). Join more team engagements to maximize impact.",
                    participation=participation
                ),
                focus_area=FocusArea.TEAMFIGHTING,
                confidence=0.8,
                action_items=["Improve map awareness", "Rotate faster to team fights"],
                practice_suggestions=["Watch minimap more frequently", "Learn team fight timing"],
                expected_impact=ExpectedImpact.HIGH,
                improvement_metric="teamfight_participation",
                target_threshold=good_tf,
                timeline_estimate="2-3 games"
            ))
            
        return tips


class TacticalEvaluator(BaseEvaluator):
    """
    Layer 2: Tactical Analysis
    
    Analyzes advanced tactical decisions and execution:
    - Positioning patterns and safety
    - Farming efficiency and patterns
    - Skill usage effectiveness  
    - Objective control participation
    """
    
    def __init__(self):
        super().__init__(CoachingCategory.TACTICAL)
        
    def evaluate(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Generate tactical coaching tips."""
        tips = []
        
        tips.extend(self._evaluate_positioning(match_data, hero_config))
        tips.extend(self._evaluate_farming_patterns(match_data, hero_config))
        tips.extend(self._evaluate_skill_usage(match_data, hero_config))
        
        return tips
        
    def _evaluate_positioning(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Evaluate positioning based on damage taken vs damage dealt ratios."""
        tips = []
        
        # Analyze damage ratio as positioning indicator
        damage_ratio = match_data.damage_ratio
        deaths = match_data.deaths
        
        # Role-specific positioning expectations
        expected_ratios = {
            "mage": 3.0,      # Should deal much more than taken
            "marksman": 4.0,  # Highest damage, lowest damage taken
            "assassin": 2.5,  # Burst damage but some risk
            "fighter": 1.5,   # Balanced damage dealer/tank
            "tank": 0.8,      # Takes more than deals
            "support": 1.2    # Moderate damage, focus on safety
        }
        
        expected_ratio = expected_ratios.get(hero_config.role.lower(), 2.0)
        positioning_advice = hero_config.positioning
        
        if damage_ratio < expected_ratio and deaths > 4:
            # Poor positioning indicated
            tips.append(self._create_tip(
                severity=CoachingSeverity.WARNING,
                message=format_coaching_message(
                    "Positioning needs work - damage ratio {ratio:.1f} with {deaths} deaths. {advice}",
                    ratio=damage_ratio, deaths=deaths, advice=positioning_advice.escape_routes
                ),
                focus_area=FocusArea.POSITIONING,
                confidence=0.75,
                action_items=[
                    f"Maintain {positioning_advice.ideal_range} distance from enemies",
                    "Focus on escape route planning"
                ],
                practice_suggestions=[
                    "Practice positioning in AI mode",
                    "Watch pro gameplay for positioning reference"
                ],
                expected_impact=ExpectedImpact.HIGH,
                improvement_metric="damage_ratio",
                target_threshold=expected_ratio,
                timeline_estimate="5-7 games",
                hero_specificity=0.8
            ))
        elif damage_ratio >= expected_ratio * 1.5:
            # Excellent positioning
            tips.append(self._create_tip(
                severity=CoachingSeverity.SUCCESS,
                message=format_coaching_message(
                    "Outstanding positioning! Damage ratio {ratio:.1f} shows excellent threat management.",
                    ratio=damage_ratio
                ),
                focus_area=FocusArea.POSITIONING,
                confidence=0.8,
                hero_specificity=0.7
            ))
            
        return tips
        
    def _evaluate_farming_patterns(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Evaluate farming efficiency (future enhancement for replay data).""" 
        tips = []
        
        # For now, use GPM as proxy for farming efficiency
        gpm = match_data.gold_per_min
        duration = match_data.match_duration or 15.0
        
        # Advanced metrics would come from replay analysis
        if hasattr(match_data.advanced_metrics, 'farming_efficiency') and match_data.advanced_metrics.farming_efficiency:
            efficiency = match_data.advanced_metrics.farming_efficiency
            if efficiency < 0.7:  # 70% farming efficiency threshold
                tips.append(self._create_tip(
                    severity=CoachingSeverity.WARNING,
                    message="Farming efficiency could be improved. Focus on consistent minion clearing and jungle timing.",
                    focus_area=FocusArea.FARMING,
                match_data=match_data,
                    action_items=["Improve last-hitting", "Clear jungle camps efficiently"],
                    practice_suggestions=["Practice farming patterns in training mode"],
                    expected_impact=ExpectedImpact.MEDIUM,
                    timeline_estimate="3-5 games"
                ))
        else:
            # Placeholder for future farming analysis
            if gpm > 0:  # Basic validation
                tips.append(self._create_tip(
                    severity=CoachingSeverity.INFO,
                    message="Farming analysis will be enhanced with replay data support.",
                    focus_area=FocusArea.FARMING,
                match_data=match_data,
                    confidence=0.3,
                    hero_specificity=0.0
                ))
            
        return tips
        
    def _evaluate_skill_usage(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Evaluate skill usage effectiveness."""
        tips = []
        
        # Check ultimate usage rating from basic stats
        ult_usage = match_data.ult_usage.lower()
        
        if ult_usage == "low":
            # Get hero-specific ultimate advice
            ult_config = hero_config.skills.get('ultimate')
            if ult_config:
                ult_tips = ult_config.coaching_tips
                advice = ult_tips.get('low_impact', 'Use ultimate more frequently in team fights')
                
                tips.append(self._create_tip(
                    severity=CoachingSeverity.WARNING,
                    message=f"Low ultimate usage detected. {advice}",
                    focus_area=FocusArea.SKILL_USAGE,
                match_data=match_data,
                    confidence=0.7,
                    action_items=["Look for more ultimate opportunities", "Practice ultimate timing"],
                    practice_suggestions=[f"Practice {ult_config.name} combos in training mode"],
                    expected_impact=ExpectedImpact.MEDIUM,
                    timeline_estimate="2-3 games",
                    hero_specificity=0.9
                ))
        elif ult_usage == "high":
            tips.append(self._create_tip(
                severity=CoachingSeverity.SUCCESS,
                message="Great ultimate usage! You're maximizing your impact with key abilities.",
                focus_area=FocusArea.SKILL_USAGE,
                match_data=match_data,
                confidence=0.8,
                hero_specificity=0.8
            ))
            
        # Future: Advanced skill accuracy analysis from replay data
        if match_data.advanced_metrics.skill_accuracy:
            for skill, accuracy in match_data.advanced_metrics.skill_accuracy.items():
                if accuracy < 0.6:  # 60% accuracy threshold
                    skill_config = hero_config.skills.get(skill)
                    if skill_config and skill_config.coaching_tips:
                        advice = skill_config.coaching_tips.get('low_accuracy', 'Practice skill shot accuracy')
                        tips.append(self._create_tip(
                            severity=CoachingSeverity.WARNING,
                            message=f"{skill_config.name} accuracy ({accuracy:.0%}) needs improvement. {advice}",
                            focus_area=FocusArea.SKILL_USAGE,
                match_data=match_data,
                            confidence=0.85,
                            action_items=[f"Practice {skill_config.name} accuracy"],
                            expected_impact=ExpectedImpact.HIGH,
                            hero_specificity=1.0
                        ))
                        
        return tips


class StrategicEvaluator(BaseEvaluator):
    """
    Layer 3: Strategic Analysis
    
    Analyzes high-level strategic decisions:
    - Itemization optimization based on team compositions
    - Team synergy and role fulfillment
    - Meta-game awareness and tier optimization
    - Counter-matchup strategies
    """
    
    def __init__(self):
        super().__init__(CoachingCategory.STRATEGIC)
        
    def evaluate(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Generate strategic coaching tips."""
        tips = []
        
        tips.extend(self._evaluate_meta_relevance(match_data, hero_config))
        tips.extend(self._evaluate_team_composition(match_data, hero_config))
        tips.extend(self._evaluate_itemization(match_data, hero_config))
        
        return tips
        
    def _evaluate_meta_relevance(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Evaluate hero choice relative to current meta."""
        tips = []
        
        meta_tier = hero_config.meta_tier
        rank_tier = match_data.match_context.rank_tier
        
        if meta_tier in ['S+', 'S']:
            tips.append(self._create_tip(
                severity=CoachingSeverity.SUCCESS,
                message=f"{hero_config.name} is currently {meta_tier.value}-tier in the meta. Great hero choice!",
                focus_area=FocusArea.META_AWARENESS,
                match_data=match_data,
                confidence=0.8,
                action_items=["Continue mastering this strong meta pick"],
                hero_specificity=1.0
            ))
        elif meta_tier in ['C']:
            tips.append(self._create_tip(
                severity=CoachingSeverity.INFO,
                message=f"{hero_config.name} is {meta_tier.value}-tier in current meta. Consider learning stronger alternatives for ranked climbing.",
                focus_area=FocusArea.META_AWARENESS,
                match_data=match_data,
                confidence=0.7,
                action_items=["Consider meta alternatives", "Perfect your gameplay to overcome tier disadvantage"],
                practice_suggestions=[f"Master {hero_config.name} mechanics to outplay meta picks"],
                expected_impact=ExpectedImpact.MEDIUM,
                timeline_estimate="1-2 weeks",
                hero_specificity=1.0
            ))
            
        return tips
        
    def _evaluate_team_composition(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Evaluate team composition synergy and role fulfillment."""
        tips = []
        
        team_comp = match_data.match_context.team_composition
        enemy_comp = match_data.match_context.enemy_composition
        
        if team_comp and enemy_comp:
            # Analyze team composition balance
            team_roles = self._analyze_team_roles(team_comp)
            enemy_roles = self._analyze_team_roles(enemy_comp)
            
            # Check for team composition issues
            if team_roles.get('tank', 0) == 0:
                tips.append(self._create_tip(
                    severity=CoachingSeverity.WARNING,
                    message="Team lacks a tank. Focus on defensive positioning and avoid initiating fights.",
                    focus_area=FocusArea.TEAM_SYNERGY,
                match_data=match_data,
                    confidence=0.8,
                    action_items=["Play more defensively", "Let enemies initiate"],
                    expected_impact=ExpectedImpact.MEDIUM,
                    hero_specificity=0.3
                ))
                
            if team_roles.get('marksman', 0) == 0 and team_roles.get('mage', 0) == 0:
                tips.append(self._create_tip(
                    severity=CoachingSeverity.WARNING, 
                    message="Team lacks consistent damage dealers. Games may be harder to close out.",
                    focus_area=FocusArea.TEAM_SYNERGY,
                match_data=match_data,
                    confidence=0.7,
                    action_items=["Focus on early game advantage", "End games quickly"],
                    expected_impact=ExpectedImpact.MEDIUM,
                    hero_specificity=0.3
                ))
        else:
            # Placeholder tip for future enhancement
            tips.append(self._create_tip(
                severity=CoachingSeverity.INFO,
                message="Team composition analysis will be enhanced with full team data.",
                focus_area=FocusArea.TEAM_SYNERGY,
                match_data=match_data,
                confidence=0.3,
                hero_specificity=0.0
            ))
            
        return tips
        
    def _analyze_team_roles(self, team_heroes: List[str]) -> Dict[str, int]:
        """Analyze team composition by roles (simplified)."""
        # This would be enhanced with a hero role database
        role_counts = {
            'tank': 0,
            'fighter': 0, 
            'assassin': 0,
            'mage': 0,
            'marksman': 0,
            'support': 0
        }
        
        # Simplified role detection based on common hero names
        # In production, this would use a comprehensive hero database
        for hero in team_heroes:
            hero_lower = hero.lower()
            if any(tank in hero_lower for tank in ['tigreal', 'franco', 'fredrinn', 'johnson']):
                role_counts['tank'] += 1
            elif any(mm in hero_lower for mm in ['miya', 'layla', 'bruno', 'granger']):
                role_counts['marksman'] += 1
            elif any(mage in hero_lower for mage in ['kagura', 'eudora', 'aurora', 'chang']):
                role_counts['mage'] += 1
            # Add more detection logic as needed
                
        return role_counts
        
    def _evaluate_itemization(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Evaluate itemization choices (future enhancement)."""
        tips = []
        
        # Placeholder for itemization analysis
        # This would require item build data from match analysis
        enemy_comp = match_data.match_context.enemy_composition
        item_config = hero_config.items
        
        if enemy_comp and item_config.coaching_tips:
            # Basic enemy composition analysis for item suggestions
            has_burst = any('assassin' in hero.lower() or 'mage' in hero.lower() for hero in enemy_comp)
            has_cc = any('tank' in hero.lower() for hero in enemy_comp)
            
            if has_burst and 'vs_burst' in item_config.coaching_tips:
                tips.append(self._create_tip(
                    severity=CoachingSeverity.INFO,
                    message=item_config.coaching_tips['vs_burst'],
                    focus_area=FocusArea.ITEMIZATION,
                match_data=match_data,
                    confidence=0.6,
                    action_items=["Consider defensive items"],
                    expected_impact=ExpectedImpact.MEDIUM,
                    hero_specificity=0.8
                ))
                
            if has_cc and 'vs_cc' in item_config.coaching_tips:
                tips.append(self._create_tip(
                    severity=CoachingSeverity.INFO,
                    message=item_config.coaching_tips['vs_cc'],
                    focus_area=FocusArea.ITEMIZATION,
                match_data=match_data,
                    confidence=0.6,
                    action_items=["Consider CC reduction items"],
                    expected_impact=ExpectedImpact.MEDIUM,
                    hero_specificity=0.8
                ))
        else:
            tips.append(self._create_tip(
                severity=CoachingSeverity.INFO,
                message="Itemization analysis will be enhanced with build tracking.",
                focus_area=FocusArea.ITEMIZATION,
                match_data=match_data,
                confidence=0.2,
                hero_specificity=0.0
            ))
            
        return tips


class ProgressionEvaluator(BaseEvaluator):
    """
    Layer 4: Progression Analysis
    
    Analyzes player development and improvement patterns:
    - Performance trends over recent matches
    - Skill gap identification and targeted improvement
    - Achievement recognition and motivation
    - Personalized coaching focus areas
    """
    
    def __init__(self):
        super().__init__(CoachingCategory.PROGRESSION)
        
    def evaluate(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Generate progression-focused coaching tips."""
        tips = []
        
        if match_data.progression:
            tips.extend(self._evaluate_improvement_trends(match_data, hero_config))
            tips.extend(self._evaluate_skill_gaps(match_data, hero_config))
            tips.extend(self._evaluate_achievements(match_data, hero_config))
        else:
            # First-time analysis - provide foundational guidance
            tips.extend(self._provide_foundational_guidance(match_data, hero_config))
            
        return tips
        
    def _evaluate_improvement_trends(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Analyze improvement trends from recent matches."""
        tips = []
        trends = match_data.progression.improvement_trends
        
        for metric, trend_value in trends.items():
            if trend_value > 0.1:  # Positive trend threshold
                tips.append(self._create_tip(
                    severity=CoachingSeverity.SUCCESS,
                    message=f"Great improvement in {metric.replace('_', ' ')}! Keep up the consistent progress.",
                    focus_area=FocusArea.SKILL_DEVELOPMENT,
                    confidence=0.8,
                    action_items=["Maintain current practice routine"],
                    timeline_estimate="ongoing",
                    hero_specificity=0.5
                ))
            elif trend_value < -0.1:  # Negative trend threshold
                tips.append(self._create_tip(
                    severity=CoachingSeverity.WARNING,
                    message=f"{metric.replace('_', ' ').title()} has been declining recently. Consider focused practice in this area.",
                    focus_area=FocusArea.WEAKNESS_PATTERNS,
                    confidence=0.7,
                    action_items=[f"Focus practice sessions on {metric.replace('_', ' ')}"],
                    practice_suggestions=["Review recent replays to identify the cause"],
                    expected_impact=ExpectedImpact.MEDIUM,
                    timeline_estimate="1-2 weeks",
                    hero_specificity=0.4
                ))
                
        return tips
        
    def _evaluate_skill_gaps(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Identify skill gaps based on rank tier and performance."""
        tips = []
        rank = match_data.match_context.rank_tier
        weaknesses = match_data.progression.weakness_patterns
        
        # Rank-specific skill expectations
        rank_skills = {
            RankTier.EPIC: ["positioning", "farming", "team fighting"],
            RankTier.LEGEND: ["positioning", "team fighting", "objective control", "meta awareness"],
            RankTier.MYTHIC: ["positioning", "team fighting", "objective control", "meta awareness", "team coordination"]
        }
        
        expected_skills = rank_skills.get(rank, ["positioning", "farming"])
        
        for skill in expected_skills:
            if skill in weaknesses:
                tips.append(self._create_tip(
                    severity=CoachingSeverity.WARNING,
                    message=f"{skill.title()} is crucial for {rank.value} rank. Focus on improving this area for consistent climbing.",
                    focus_area=FocusArea.SKILL_DEVELOPMENT,
                match_data=match_data,
                    confidence=0.8,
                    action_items=[f"Dedicate practice time to {skill}"],
                    practice_suggestions=[f"Study high-level gameplay focusing on {skill}"],
                    expected_impact=ExpectedImpact.HIGH,
                    timeline_estimate="2-3 weeks",
                    hero_specificity=0.3
                ))
                
        return tips
        
    def _evaluate_achievements(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Recognize achievements and provide motivation."""
        tips = []
        personal_bests = match_data.progression.personal_bests
        current_kda = match_data.kda_ratio
        current_damage = match_data.hero_damage
        
        # Check for personal records
        if personal_bests.get('kda', 0) < current_kda:
            tips.append(self._create_tip(
                severity=CoachingSeverity.SUCCESS,
                message=f"New personal best KDA of {current_kda:.1f}! Excellent performance improvement.",
                focus_area=FocusArea.ACHIEVEMENT_RECOGNITION,
                match_data=match_data,
                confidence=0.9,
                action_items=["Build on this success", "Analyze what worked well"],
                hero_specificity=0.6
            ))
            
        if personal_bests.get('hero_damage', 0) < current_damage:
            tips.append(self._create_tip(
                severity=CoachingSeverity.SUCCESS,
                message=f"Personal record damage output of {humanize_number(current_damage)}! Your combat effectiveness is improving.",
                focus_area=FocusArea.ACHIEVEMENT_RECOGNITION,
                match_data=match_data,
                confidence=0.9,
                action_items=["Continue focusing on damage positioning"],
                hero_specificity=0.7
            ))
            
        return tips
        
    def _provide_foundational_guidance(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Provide foundational coaching for first-time analysis."""
        tips = []
        
        # Basic improvement guidance
        tips.append(self._create_tip(
            severity=CoachingSeverity.INFO,
            message=f"Welcome to enhanced coaching for {hero_config.name}! Focus on consistency to establish your baseline performance.",
            focus_area=FocusArea.SKILL_DEVELOPMENT,
                match_data=match_data,
            confidence=0.7,
            action_items=["Play 5-10 more games to establish performance trends"],
            timeline_estimate="1-2 weeks",
            hero_specificity=0.8
        ))
        
        # Role-specific foundational advice
        role_foundations = {
            "mage": "Master your skill combos and positioning fundamentals",
            "marksman": "Focus on farming safely and positioning in team fights",
            "tank": "Learn engagement timing and team coordination",
            "support": "Practice enabling teammates and vision control", 
            "assassin": "Work on target selection and escape timing",
            "fighter": "Balance between damage dealing and survivability"
        }
        
        foundation_advice = role_foundations.get(hero_config.role.lower(), "Focus on core gameplay fundamentals")
        tips.append(self._create_tip(
            severity=CoachingSeverity.INFO,
            message=f"As a {hero_config.role}, {foundation_advice.lower()}.",
            focus_area=FocusArea.SKILL_DEVELOPMENT,
            confidence=0.8,
            action_items=["Focus on role fundamentals"],
            expected_impact=ExpectedImpact.HIGH,
            timeline_estimate="2-3 weeks",
            hero_specificity=0.7
        ))
        
        return tips


# === MULTI-LAYER EVALUATOR ORCHESTRATOR ===

class MultiLayerCoachingOrchestrator:
    """
    Orchestrates all 4 coaching evaluation layers and combines results.
    
    Provides intelligent tip prioritization, deduplication, and formatting
    to deliver the most valuable coaching insights.
    """
    
    def __init__(self):
        self.evaluators = [
            PerformanceEvaluator(),  # Layer 1
            TacticalEvaluator(),     # Layer 2  
            StrategicEvaluator(),    # Layer 3
            ProgressionEvaluator()   # Layer 4
        ]
        self.config_loader = get_hero_config_loader()
        
    def generate_coaching(self, match_data: EnhancedMatchAnalysis) -> List[CoachingTip]:
        """Generate comprehensive coaching tips from all evaluation layers."""
        all_tips = []
        hero_config = self.config_loader.load_hero_config(match_data.hero)
        
        # Run all evaluators
        for evaluator in self.evaluators:
            try:
                layer_tips = evaluator.evaluate(match_data, hero_config)
                all_tips.extend(layer_tips)
            except Exception as e:
                logger.error(f"Error in {evaluator.__class__.__name__}: {e}")
                continue
                
        # Prioritize and filter tips
        prioritized_tips = self._prioritize_tips(all_tips)
        
        # Ensure we always return at least some feedback
        if not prioritized_tips:
            prioritized_tips = self._generate_fallback_tips(match_data, hero_config)
            
        return prioritized_tips[:4]  # Maximum 4 tips as specified
        
    def _prioritize_tips(self, tips: List[CoachingTip]) -> List[CoachingTip]:
        """Prioritize coaching tips for optimal user experience."""
        if not tips:
            return tips
            
        # Define priority scoring
        severity_priority = {
            CoachingSeverity.CRITICAL: 4,
            CoachingSeverity.SUCCESS: 3,
            CoachingSeverity.WARNING: 2,
            CoachingSeverity.INFO: 1
        }
        
        # Score tips by multiple factors
        def score_tip(tip):
            score = 0
            score += severity_priority.get(tip.severity, 1) * 10  # Severity weight
            score += tip.confidence * 5  # Confidence weight
            score += tip.hero_specificity * 3  # Hero-specific weight
            score += {'high': 3, 'medium': 2, 'low': 1}.get(tip.expected_impact.value, 2)
            return score
            
        # Sort by score (descending)
        sorted_tips = sorted(tips, key=score_tip, reverse=True)
        
        # Ensure balanced tip distribution
        balanced_tips = self._balance_tip_categories(sorted_tips)
        
        return balanced_tips
        
    def _balance_tip_categories(self, tips: List[CoachingTip]) -> List[CoachingTip]:
        """Ensure balanced representation across tip categories and severities."""
        balanced = []
        
        # Aim for: 1 success, 2 improvement areas (warning/critical), 1 strategic/progression
        success_tips = [t for t in tips if t.severity == CoachingSeverity.SUCCESS]
        improvement_tips = [t for t in tips if t.severity in [CoachingSeverity.WARNING, CoachingSeverity.CRITICAL]]
        info_tips = [t for t in tips if t.severity == CoachingSeverity.INFO]
        
        # Add 1 success tip if available
        if success_tips:
            balanced.append(success_tips[0])
            
        # Add 2 improvement tips
        for tip in improvement_tips[:2]:
            balanced.append(tip)
            
        # Fill remaining slots with highest priority tips
        remaining_slots = 4 - len(balanced)
        remaining_tips = [t for t in tips if t not in balanced]
        balanced.extend(remaining_tips[:remaining_slots])
        
        return balanced
        
    def _generate_fallback_tips(self, match_data: EnhancedMatchAnalysis, hero_config: HeroConfig) -> List[CoachingTip]:
        """Generate fallback tips if no evaluator produces results."""
        fallback_evaluator = PerformanceEvaluator()
        
        try:
            tips = fallback_evaluator.evaluate(match_data, hero_config)
            if tips:
                return tips
        except Exception as e:
            logger.error(f"Fallback evaluator failed: {e}")
            
        # Final fallback - generic tip
        return [CoachingTip(
            severity=CoachingSeverity.INFO,
            message=f"Keep practicing with {hero_config.name} to improve your performance!",
            category=CoachingCategory.PERFORMANCE,
            focus_area=FocusArea.SKILL_DEVELOPMENT,
            confidence=0.5,
            action_items=["Continue playing to gather more performance data"],
            timeline_estimate="ongoing",
            source_evaluator="FallbackGenerator"
        )]


# === EXAMPLE USAGE ===
if __name__ == "__main__":
    # Example usage of the multi-layer coaching system
    from .enhanced_coaching import EnhancedMatchAnalysis, MatchContext
    
    # Create sample match data
    sample_match = EnhancedMatchAnalysis(
        hero="Kagura",
        kills=8,
        deaths=3,
        assists=12,
        gold_per_min=580,
        hero_damage=45000,
        turret_damage=8000,
        damage_taken=18000,
        teamfight_participation=75,
        positioning_rating="average",
        ult_usage="high",
        match_duration=18.5,
        match_context=MatchContext(
            rank_tier=RankTier.EPIC,
            match_type="ranked"
        )
    )
    
    # Generate coaching
    orchestrator = MultiLayerCoachingOrchestrator()
    coaching_tips = orchestrator.generate_coaching(sample_match)
    
    print(f"Generated {len(coaching_tips)} coaching tips:")
    for i, tip in enumerate(coaching_tips, 1):
        print(f"\n{i}. {tip.format_for_display()}")
        print(f"   Category: {tip.category.value}")
        print(f"   Confidence: {tip.confidence:.2f}")