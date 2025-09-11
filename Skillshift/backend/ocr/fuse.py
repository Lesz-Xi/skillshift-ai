"""
Cross-view data fusion for MLBB OCR results
Combines KDA view and Damage view data with conflict resolution
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class FusionConflict:
    """Represents a conflict between data from different views"""
    field: str
    kda_value: Any
    damage_value: Any
    resolved_value: Any
    confidence_diff: float


@dataclass
class CrossViewFusionResult:
    """Unified result from fusing KDA and Damage view data"""
    player_located: bool = False
    player_ign: Optional[str] = None
    hero: Optional[str] = None
    kda: Optional[Dict[str, int]] = None
    mvp_score: Optional[float] = None
    damage_stats: Optional[Dict[str, Any]] = None
    data_completeness: float = 0.0
    overall_confidence: float = 0.0
    warnings: List[str] = field(default_factory=list)
    conflicts: List[FusionConflict] = field(default_factory=list)


def fuse_cross_view_data(
    kda_result, 
    damage_result, 
    target_ign: str
) -> CrossViewFusionResult:
    """
    Fuse data from KDA and Damage views into unified result
    
    Args:
        kda_result: Result from KDA view parsing
        damage_result: Result from Damage view parsing
        target_ign: Target player IGN
        
    Returns:
        Unified CrossViewFusionResult
    """
    result = CrossViewFusionResult()
    
    # Handle case where only one view is available
    if kda_result is None and damage_result is None:
        result.warnings.append("No data from either view")
        return result
    
    if damage_result is None:
        return _fuse_single_view(kda_result, target_ign, is_kda=True)
    
    if kda_result is None:
        return _fuse_single_view(damage_result, target_ign, is_kda=False)
    
    # Both views available - perform full fusion
    return _fuse_both_views(kda_result, damage_result, target_ign)


def _fuse_single_view(view_result, target_ign: str, is_kda: bool) -> CrossViewFusionResult:
    """Fuse data from single view only"""
    result = CrossViewFusionResult()
    
    if hasattr(view_result, 'player_located'):
        result.player_located = view_result.player_located
    if hasattr(view_result, 'player_ign'):
        result.player_ign = view_result.player_ign
    if hasattr(view_result, 'hero'):
        result.hero = view_result.hero
    if hasattr(view_result, 'confidence'):
        result.overall_confidence = view_result.confidence
    
    if is_kda:
        if hasattr(view_result, 'kda'):
            result.kda = view_result.kda
        if hasattr(view_result, 'mvp_score'):
            result.mvp_score = view_result.mvp_score
        result.warnings.append("Damage data missing - only KDA view available")
    else:
        if hasattr(view_result, 'hero_damage_pct') or hasattr(view_result, 'teamfight_participation'):
            result.damage_stats = {}
            if hasattr(view_result, 'hero_damage_pct'):
                result.damage_stats['hero_damage_pct'] = view_result.hero_damage_pct
            if hasattr(view_result, 'teamfight_participation'):
                result.damage_stats['teamfight_pct'] = view_result.teamfight_participation
        result.warnings.append("KDA data missing - only Damage view available")
    
    # Calculate reduced completeness for single view
    result.data_completeness = 0.6  # Reduced since missing one view
    result.overall_confidence = min(0.8, result.overall_confidence)  # Cap confidence
    
    return result


def _fuse_both_views(kda_result, damage_result, target_ign: str) -> CrossViewFusionResult:
    """Fuse data from both KDA and Damage views"""
    result = CrossViewFusionResult()
    
    # Player location - both should agree for high confidence
    kda_located = getattr(kda_result, 'player_located', False)
    damage_located = getattr(damage_result, 'player_located', False)
    result.player_located = kda_located or damage_located
    
    # IGN - prefer exact match or higher confidence
    result.player_ign = target_ign if result.player_located else None
    
    # Hero resolution with conflict detection
    kda_hero = getattr(kda_result, 'hero', None)
    damage_hero = getattr(damage_result, 'hero', None)
    kda_conf = getattr(kda_result, 'confidence', 0.0)
    damage_conf = getattr(damage_result, 'confidence', 0.0)
    
    if kda_hero and damage_hero and kda_hero != damage_hero:
        # Conflict detected
        resolved_hero = kda_hero if kda_conf > damage_conf else damage_hero
        conflict = FusionConflict(
            field="hero",
            kda_value=kda_hero,
            damage_value=damage_hero,
            resolved_value=resolved_hero,
            confidence_diff=abs(kda_conf - damage_conf)
        )
        result.conflicts.append(conflict)
        result.hero = resolved_hero
    else:
        # No conflict - use available value
        result.hero = kda_hero or damage_hero
    
    # KDA data (only from KDA view)
    if hasattr(kda_result, 'kda'):
        result.kda = kda_result.kda
    
    # MVP score (only from KDA view)
    if hasattr(kda_result, 'mvp_score'):
        result.mvp_score = kda_result.mvp_score
    
    # Damage stats (only from Damage view)
    if hasattr(damage_result, 'hero_damage_pct') or hasattr(damage_result, 'teamfight_participation'):
        result.damage_stats = {}
        if hasattr(damage_result, 'hero_damage_pct'):
            result.damage_stats['hero_damage_pct'] = damage_result.hero_damage_pct
        if hasattr(damage_result, 'teamfight_participation'):
            result.damage_stats['teamfight_pct'] = damage_result.teamfight_participation
        # Add gold_earned if available
        if hasattr(damage_result, 'gold_earned'):
            result.damage_stats['gold_earned'] = damage_result.gold_earned
    
    # Calculate overall confidence (weighted average)
    if kda_conf > 0 and damage_conf > 0:
        result.overall_confidence = (kda_conf * 0.6 + damage_conf * 0.4)
    elif kda_conf > 0:
        result.overall_confidence = kda_conf * 0.8  # Reduced for missing damage
    elif damage_conf > 0:
        result.overall_confidence = damage_conf * 0.7  # Reduced for missing KDA
    
    # Calculate data completeness
    # If player not located in either view, completeness should be very low
    if not result.player_located:
        result.data_completeness = 0.2  # Very low for no player match
    else:
        completeness_factors = []
        if result.hero:
            completeness_factors.append(0.2)
        if result.kda:
            completeness_factors.append(0.3)
        if result.mvp_score:
            completeness_factors.append(0.2)
        if result.damage_stats:
            completeness_factors.append(0.3)
        
        result.data_completeness = sum(completeness_factors)
    
    # Add warnings for missing data
    if not result.kda:
        result.warnings.append("KDA data missing")
    if not result.damage_stats:
        result.warnings.append("Damage data missing")
    if not result.hero:
        result.warnings.append("Hero identification failed")
    
    return result


def resolve_data_conflicts(kda_data: Dict[str, Any], damage_data: Dict[str, Any]) -> List[FusionConflict]:
    """
    Resolve conflicts between KDA and Damage view data
    
    Args:
        kda_data: Data from KDA view with confidence scores
        damage_data: Data from Damage view with confidence scores
        
    Returns:
        List of detected and resolved conflicts
    """
    conflicts = []
    
    # Check for hero conflicts
    if "hero" in kda_data and "hero" in damage_data:
        kda_hero = kda_data["hero"]
        damage_hero = damage_data["hero"]
        kda_conf = kda_data.get("confidence", 0.0)
        damage_conf = damage_data.get("confidence", 0.0)
        
        if kda_hero != damage_hero:
            resolved = kda_hero if kda_conf > damage_conf else damage_hero
            conflict = FusionConflict(
                field="hero",
                kda_value=kda_hero,
                damage_value=damage_hero,
                resolved_value=resolved,
                confidence_diff=abs(kda_conf - damage_conf)
            )
            conflicts.append(conflict)
    
    # Check for KDA conflicts (if damage view also extracts KDA)
    if "kda" in kda_data and "kda" in damage_data:
        kda_vals = kda_data["kda"]
        damage_vals = damage_data["kda"]
        
        if kda_vals != damage_vals:
            kda_conf = kda_data.get("confidence", 0.0)
            damage_conf = damage_data.get("confidence", 0.0)
            resolved = kda_vals if kda_conf > damage_conf else damage_vals
            
            conflict = FusionConflict(
                field="kda",
                kda_value=kda_vals,
                damage_value=damage_vals,
                resolved_value=resolved,
                confidence_diff=abs(kda_conf - damage_conf)
            )
            conflicts.append(conflict)
    
    return conflicts


def validate_fused_result(result: CrossViewFusionResult) -> Tuple[bool, List[str]]:
    """
    Validate fused result meets quality requirements
    
    Args:
        result: CrossViewFusionResult to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check minimum confidence threshold
    if result.overall_confidence < 0.85:
        errors.append(f"Overall confidence {result.overall_confidence:.2f} below required 0.85")
    
    # Check minimum data completeness
    if result.data_completeness < 0.85:
        errors.append(f"Data completeness {result.data_completeness:.2f} below required 0.85")
    
    # Check player location
    if not result.player_located:
        errors.append("Player not located in either view")
    
    # Check critical data presence
    if not result.hero:
        errors.append("Hero identification missing")
    if not result.kda:
        errors.append("KDA data missing")
    
    is_valid = len(errors) == 0
    return is_valid, errors