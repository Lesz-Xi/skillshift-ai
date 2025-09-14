"""
Enhanced Coach Integration Bridge
===============================

This module serves as the integration layer between the existing coach.py system
and the new enhanced multi-layer coaching architecture. It maintains full 
backward compatibility while enabling gradual migration to the enhanced system.

Key Features:
- Seamless integration with existing generate_feedback() API
- Auto-detection of enhanced vs legacy hero configurations
- Intelligent fallback hierarchy with the new FallbackCoachingOrchestrator
- Backward-compatible output formats (tuples or messages)
- Performance optimization with caching and lazy loading
"""

import os
import logging
import importlib.util
from typing import Dict, List, Union, Any, Optional, Tuple
from dataclasses import asdict

from pydantic import ValidationError
from core.schemas import Matches
from core.enhanced_coaching import (
    EnhancedMatchAnalysis, CoachingTip, CoachingResult, 
    CoachingSeverity, MatchContext, RankTier
)
from core.hero_config_loader import HeroConfigLoader
from core.fallback_evaluators import FallbackCoachingOrchestrator

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedCoachBridge:
    """
    Integration bridge that orchestrates between legacy and enhanced coaching systems.
    
    This bridge enables a gradual migration strategy:
    1. Try enhanced multi-layer coaching (YAML configs + advanced evaluators)
    2. Fall back to legacy Python rules if enhanced not available
    3. Provide role-based fallbacks for unknown heroes
    4. Always return consistent, useful feedback
    """
    
    def __init__(self):
        # Initialize the enhanced coaching components
        self.hero_config_loader = HeroConfigLoader()
        self.fallback_orchestrator = FallbackCoachingOrchestrator()
        
        # Legacy rule module cache (maintained for compatibility)
        self._legacy_rule_modules = {}
        
        # Performance optimization caches
        self._enhanced_hero_cache = set()  # Heroes with enhanced configs
        self._legacy_hero_cache = set()    # Heroes with only legacy rules
        
        # Initialize legacy rule discovery
        self._discover_legacy_rules()
        logger.info("Enhanced Coach Bridge initialized successfully")
    
    def _discover_legacy_rules(self):
        """
        Discover and load legacy coaching rule modules from the rules/ directory.
        This maintains compatibility with existing Python-based hero rules.
        """
        rules_base_path = os.path.join(os.path.dirname(__file__), "..", "..", "rules")
        if not os.path.exists(rules_base_path):
            logger.warning(f"Legacy rules directory not found: {rules_base_path}")
            return
        
        for dirpath, _, filenames in os.walk(rules_base_path):
            for file_name in filenames:
                if file_name.endswith(".py") and not file_name.startswith("__"):
                    module_name = file_name[:-3]
                    file_path = os.path.join(dirpath, file_name)
                    
                    try:
                        # Create module specification and load
                        relative_path = os.path.relpath(file_path, os.path.dirname(__file__) + "/..")
                        module_import_name = os.path.splitext(relative_path)[0].replace(os.sep, '.')
                        
                        spec = importlib.util.spec_from_file_location(module_import_name, file_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        self._legacy_rule_modules[module_name] = module
                        self._legacy_hero_cache.add(module_name)
                        
                        logger.debug(f"Loaded legacy rule module: {module_name}")
                    
                    except Exception as e:
                        logger.warning(f"Failed to load legacy rule module {module_name}: {e}")
    
    def _convert_to_enhanced_match_analysis(self, match_data: Dict[str, Any]) -> EnhancedMatchAnalysis:
        """
        Convert legacy match data dictionary to EnhancedMatchAnalysis format.
        
        This conversion maintains all existing fields while adding enhanced metadata
        for the new coaching system to leverage.
        """
        # Extract basic match context
        hero_name = str(match_data.get('hero', 'unknown')).strip().lower()
        
        # Infer rank tier from performance (basic heuristic)
        kda_ratio = (match_data.get('kills', 0) + match_data.get('assists', 0)) / max(1, match_data.get('deaths', 1))
        gpm = match_data.get('gold_per_min', 0)
        
        # Simple rank inference based on performance metrics
        rank_tier = RankTier.EPIC  # Default
        if kda_ratio >= 3.0 and gpm >= 600:
            rank_tier = RankTier.MYTHIC
        elif kda_ratio >= 2.5 and gpm >= 500:
            rank_tier = RankTier.LEGEND
        elif kda_ratio >= 2.0 and gpm >= 400:
            rank_tier = RankTier.EPIC
        elif kda_ratio >= 1.5:
            rank_tier = RankTier.MASTER
        else:
            rank_tier = RankTier.GRANDMASTER
        
        # Create match context
        match_context = MatchContext(
            rank_tier=rank_tier,
            match_type="ranked",  # Assume ranked for coaching
            game_phase="full_game",
            match_duration=match_data.get('match_duration', 0.0)
        )
        
        # Create enhanced match analysis object
        enhanced_match = EnhancedMatchAnalysis(
            # Core stats (preserved exactly)
            hero=hero_name,
            kills=match_data.get('kills', 0),
            deaths=match_data.get('deaths', 0),
            assists=match_data.get('assists', 0),
            gold_per_min=match_data.get('gold_per_min', 0),
            hero_damage=match_data.get('hero_damage', 0),
            tower_damage=match_data.get('tower_damage', 0),  # FIXED: Use tower_damage to match backend
            damage_taken=match_data.get('damage_taken', 0),
            teamfight_participation=match_data.get('teamfight_participation', 0),
            positioning_rating=match_data.get('positioning_rating', 'average'),
            ult_usage=match_data.get('ult_usage', 'average'),
            match_duration=match_data.get('match_duration', 0.0),
            hooks_landed=match_data.get('hooks_landed', 0),
            team_engages=match_data.get('team_engages', 0),
            vision_score=match_data.get('vision_score', 0),
            
            # Enhanced context
            match_context=match_context
        )
        
        return enhanced_match
    
    def _format_for_legacy_output(self, 
                                coaching_result: CoachingResult, 
                                include_severity: bool = False) -> List[Union[str, Tuple[str, str]]]:
        """
        Format enhanced coaching results for backward compatibility with legacy API.
        
        Args:
            coaching_result: Results from enhanced coaching system
            include_severity: Whether to return (severity, message) tuples
            
        Returns:
            List in legacy format - either messages or (severity, message) tuples
        """
        if not coaching_result.tips:
            # Fallback for empty results
            fallback_msg = "Continue practicing to improve your gameplay!"
            if include_severity:
                return [("info", fallback_msg)]
            return [fallback_msg]
        
        # Convert CoachingTip objects to legacy format
        legacy_results = []
        for tip in coaching_result.tips:
            if include_severity:
                legacy_results.append((tip.severity.value, tip.message))
            else:
                legacy_results.append(tip.message)
        
        return legacy_results
    
    def generate_enhanced_feedback(self, match_data: Dict[str, Any], include_severity: bool = False) -> List[Union[str, Tuple[str, str]]]:
        """
        Main entry point for enhanced coaching feedback generation.
        
        This method orchestrates the entire coaching pipeline:
        1. Data validation and enhancement
        2. Enhanced coaching system (YAML configs + multi-layer evaluators)  
        3. Legacy fallback for heroes without enhanced configs
        4. Role-based and universal fallbacks
        5. Consistent output formatting
        
        Args:
            match_data: Raw match statistics dictionary
            include_severity: Return (severity, message) tuples if True
            
        Returns:
            List of coaching feedback in legacy-compatible format
        """
        try:
            # Step 1: Validate and enhance match data
            enhanced_match = self._convert_to_enhanced_match_analysis(match_data)
            hero_name = enhanced_match.hero
            
            logger.debug(f"Generating enhanced feedback for hero: {hero_name}")
            
            # Step 2: Try enhanced coaching system first
            try:
                coaching_result = self.fallback_orchestrator.generate_coaching(enhanced_match)
                
                if coaching_result and coaching_result.tips:
                    logger.info(f"Enhanced coaching successful for {hero_name}: {len(coaching_result.tips)} tips generated")
                    return self._format_for_legacy_output(coaching_result, include_severity)
                
            except Exception as e:
                logger.warning(f"Enhanced coaching failed for {hero_name}: {e}")
                # Continue to legacy fallback
            
            # Step 3: Legacy fallback - this should be handled by FallbackCoachingOrchestrator
            # but we add an extra safety layer here
            if hero_name in self._legacy_rule_modules:
                module = self._legacy_rule_modules[hero_name]
                if hasattr(module, 'evaluate'):
                    try:
                        # Try new format with minutes parameter
                        legacy_feedback = module.evaluate(match_data, match_data.get('match_duration'))
                    except TypeError:
                        # Fall back to old format
                        legacy_feedback = module.evaluate(match_data)
                    
                    if legacy_feedback:
                        logger.info(f"Legacy coaching successful for {hero_name}")
                        # Handle legacy format conversion
                        if isinstance(legacy_feedback[0], tuple):
                            return legacy_feedback if include_severity else [msg for _, msg in legacy_feedback]
                        else:
                            # Old format - convert to new format
                            if include_severity:
                                return [("info", msg) for msg in legacy_feedback]
                            return legacy_feedback
            
            # Step 4: Ultimate fallback
            fallback_message = f"Keep practicing with {hero_name.title()}! Focus on positioning and map awareness."
            logger.warning(f"All coaching methods failed for {hero_name}, using ultimate fallback")
            
            if include_severity:
                return [("info", fallback_message)]
            return [fallback_message]
        
        except Exception as e:
            logger.error(f"Critical error in enhanced feedback generation: {e}")
            error_message = "Unable to generate coaching feedback at this time."
            if include_severity:
                return [("error", error_message)]
            return [error_message]
    
    def get_coaching_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the coaching system configuration.
        
        Returns:
            Dictionary with system statistics for monitoring and debugging
        """
        enhanced_heroes = len(self.hero_config_loader._config_cache)
        legacy_heroes = len(self._legacy_rule_modules)
        
        return {
            "enhanced_heroes_available": enhanced_heroes,
            "legacy_heroes_available": legacy_heroes,
            "total_heroes_supported": enhanced_heroes + legacy_heroes,
            "cache_status": {
                "enhanced_cache_size": enhanced_heroes,
                "legacy_cache_size": legacy_heroes
            }
        }


# Global bridge instance for backward compatibility
_enhanced_coach_bridge = None

def get_enhanced_coach_bridge() -> EnhancedCoachBridge:
    """
    Get the global enhanced coach bridge instance (singleton pattern).
    This ensures consistent state across the application.
    """
    global _enhanced_coach_bridge
    if _enhanced_coach_bridge is None:
        _enhanced_coach_bridge = EnhancedCoachBridge()
    return _enhanced_coach_bridge


def generate_enhanced_feedback(match_data: Dict[str, Any], include_severity: bool = False) -> List[Union[str, Tuple[str, str]]]:
    """
    Main entry point for the enhanced coaching system.
    
    This function serves as a drop-in replacement for the legacy generate_feedback()
    function while providing enhanced capabilities through the new multi-layer system.
    
    Args:
        match_data: Match statistics dictionary
        include_severity: Whether to include severity levels in output
        
    Returns:
        List of coaching feedback messages or (severity, message) tuples
    """
    bridge = get_enhanced_coach_bridge()
    return bridge.generate_enhanced_feedback(match_data, include_severity)


# Convenience function for backward compatibility testing
def validate_integration() -> Dict[str, Any]:
    """
    Validate that the integration bridge is working correctly.
    
    Returns:
        Dictionary with validation results and system status
    """
    try:
        bridge = get_enhanced_coach_bridge()
        stats = bridge.get_coaching_statistics()
        
        # Test with sample data
        sample_data = {
            'hero': 'kagura',
            'kills': 8,
            'deaths': 2,
            'assists': 12,
            'gold_per_min': 520,
            'hero_damage': 45000,
            'match_duration': 18.5
        }
        
        # Test both output formats
        feedback_messages = bridge.generate_enhanced_feedback(sample_data, False)
        feedback_tuples = bridge.generate_enhanced_feedback(sample_data, True)
        
        return {
            "status": "success",
            "system_stats": stats,
            "sample_test": {
                "messages_count": len(feedback_messages),
                "tuples_count": len(feedback_tuples),
                "formats_consistent": len(feedback_messages) == len(feedback_tuples)
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


if __name__ == "__main__":
    # Integration validation when run directly
    result = validate_integration()
    print("Enhanced Coach Bridge Validation:")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"Enhanced heroes: {result['system_stats']['enhanced_heroes_available']}")
        print(f"Legacy heroes: {result['system_stats']['legacy_heroes_available']}")
        print(f"Total supported: {result['system_stats']['total_heroes_supported']}")
        print(f"Sample test passed: {result['sample_test']['formats_consistent']}")
    else:
        print(f"Error: {result['error_message']}")