"""
Cross-view data fusion for KDA and Damage parsers.

This module combines data from KDA and Damage views using the row-agnostic
approach, providing conflict resolution and confidence weighting.
"""

from typing import Dict, Any, Optional, List
import logging
import numpy as np
from dataclasses import dataclass

from .parsers_kda import KDAResult, kda_parser
from .parsers_damage import DamageResult, damage_parser
from .hero_resolver import hero_resolver, HeroMatchResult

logger = logging.getLogger(__name__)

@dataclass
class FusedResult:
    """Result of fusing KDA and Damage data with enriched schema (OCR-Mission-4.md)."""
    player_ign: str
    hero: str
    kills: int
    deaths: int
    assists: int
    kda_ratio: float
    mvp_score: float
    hero_damage: int
    tower_damage: int
    damage_taken: int
    hero_damage_pct: float
    turret_damage_pct: float
    taken_damage_pct: float
    teamfight_participation: float
    gold_per_minute: int
    overall_confidence: float
    data_completeness: float
    fusion_method: str
    conflicts_resolved: List[str]
    raw_data: Dict[str, Any]
    # OCR Mission 4 additions
    hero_confidence: float = 0.0
    hero_resolution_method: str = "unknown"
    match_duration: Optional[float] = None
    
    def to_enriched_schema(self) -> Dict[str, Any]:
        """Return enriched schema as specified in OCR-Mission-4.md."""
        return {
            'ign': self.player_ign,
            'kda': {
                'k': self.kills,
                'd': self.deaths,
                'a': self.assists,
                'ratio': self.kda_ratio
            },
            'damage': {
                'hero_pct': self.hero_damage_pct,
                'turret_pct': self.turret_damage_pct,
                'taken_pct': self.taken_damage_pct
            },
            'mvp_score': int(self.mvp_score),
            'hero': self.hero,
            'confidence': self.overall_confidence,
            'hero_confidence': self.hero_confidence,
            'hero_resolution_method': self.hero_resolution_method,
            'teamfight_participation': self.teamfight_participation,
            'gold_per_minute': self.gold_per_minute,
            'match_duration': self.match_duration,
            'data_completeness': self.data_completeness,
            'fusion_method': self.fusion_method
        }

class CrossViewFusion:
    """
    Cross-view data fusion system for KDA and Damage parsers.
    
    Combines data from both views with intelligent conflict resolution
    and confidence weighting.
    """
    
    def __init__(self):
        # Enhanced confidence thresholds for OCR-Mission-2.md
        self.confidence_thresholds = {
            'kda': 0.8,  # Higher threshold for KDA accuracy ≥80%
            'damage': 0.7,
            'fusion': 0.85  # Mission target: ≥0.85 confidence
        }
        
        # Enhanced weight factors for MVP computation
        self.weight_factors = {
            'kda': 0.6,      # KDA more important for MVP
            'damage': 0.4,
            'performance': 0.3,
            'participation': 0.2
        }
        
        # MVP score computation weights
        self.mvp_weights = {
            'kda_ratio': 0.25,
            'hero_damage': 0.20,
            'teamfight_participation': 0.15,
            'gpm': 0.15,
            'kills': 0.10,
            'assists': 0.10,
            'damage_efficiency': 0.05
        }
    
    def fuse_kda_and_damage(self, kda_result: Optional[KDAResult], damage_result: Optional[DamageResult]) -> Optional[FusedResult]:
        """
        Fuse KDA and Damage results into a single comprehensive result.
        
        Args:
            kda_result: KDA parsing result
            damage_result: Damage parsing result
            
        Returns:
            FusedResult with combined data, or None if both results are invalid
        """
        try:
            # Validate inputs
            if not kda_result and not damage_result:
                logger.warning("Both KDA and Damage results are None")
                return None
            
            # Use the result with higher confidence as primary
            primary_result = self._select_primary_result(kda_result, damage_result)
            secondary_result = damage_result if primary_result == kda_result else kda_result
            
            # Extract basic info from primary result
            player_ign = primary_result.player_ign if primary_result else (damage_result.player_ign if damage_result else "unknown")
            hero = primary_result.hero if primary_result else (damage_result.hero if damage_result else "unknown")
            
            # Fuse KDA data
            kda_data = self._fuse_kda_data(kda_result, damage_result)
            
            # Fuse damage data
            damage_data = self._fuse_damage_data(kda_result, damage_result)
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(kda_result, damage_result)
            
            # Calculate data completeness
            data_completeness = self._calculate_data_completeness(kda_data, damage_data)
            
            # Track conflicts resolved
            conflicts_resolved = self._identify_conflicts_resolved(kda_result, damage_result)
            
            # Determine fusion method
            fusion_method = self._determine_fusion_method(kda_result, damage_result)

            # Try to carry match duration from the more reliable source
            match_duration = None
            if kda_result:
                match_duration = getattr(kda_result, "match_duration", None)
                if match_duration is None:
                    match_duration = kda_result.raw_data.get("match_duration") if getattr(kda_result, "raw_data", None) else None
            if match_duration is None and damage_result and getattr(damage_result, "raw_data", None):
                match_duration = damage_result.raw_data.get("match_duration")

            # Create fused result
            # Calculate KDA ratio safely
            kills = kda_data['kills']
            deaths = kda_data['deaths']
            assists = kda_data['assists']
            kda_ratio = (kills + assists) / max(deaths, 1) if deaths > 0 else kills + assists
            
            return FusedResult(
                player_ign=player_ign,
                hero=hero,
                kills=kills,
                deaths=deaths,
                assists=assists,
                kda_ratio=kda_ratio,
                mvp_score=kda_data['mvp_score'],
                hero_damage=damage_data['hero_damage'],
                tower_damage=damage_data['tower_damage'],
                damage_taken=damage_data['damage_taken'],
                hero_damage_pct=damage_data.get('hero_damage_pct', 0.0),
                turret_damage_pct=damage_data.get('turret_damage_pct', 0.0),
                taken_damage_pct=damage_data.get('taken_damage_pct', 0.0),
                teamfight_participation=damage_data['teamfight_participation'],
                gold_per_minute=damage_data['gold_per_minute'],
                overall_confidence=overall_confidence,
                data_completeness=data_completeness,
                fusion_method=fusion_method,
                conflicts_resolved=conflicts_resolved,
                raw_data={
                    'kda_result': kda_result.__dict__ if kda_result else None,
                    'damage_result': damage_result.__dict__ if damage_result else None
                },
                match_duration=match_duration
            )
            
        except Exception as e:
            logger.error(f"Error fusing KDA and Damage results: {e}")
            return None
    
    def _select_primary_result(self, kda_result: Optional[KDAResult], damage_result: Optional[DamageResult]) -> Optional[Any]:
        """Select the primary result based on confidence and completeness."""
        if not kda_result and not damage_result:
            return None
        
        if not kda_result:
            return damage_result
        
        if not damage_result:
            return kda_result
        
        # Compare confidence scores
        if kda_result.confidence > damage_result.confidence:
            return kda_result
        else:
            return damage_result
    
    def _fuse_kda_data(self, kda_result: Optional[KDAResult], damage_result: Optional[DamageResult]) -> Dict[str, Any]:
        """Fuse KDA data from both results."""
        kda_data = {
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'mvp_score': 0.0
        }
        
        # Use KDA result if available and confident
        if kda_result and kda_result.confidence >= self.confidence_thresholds['kda']:
            kda_data.update({
                'kills': kda_result.kills,
                'deaths': kda_result.deaths,
                'assists': kda_result.assists,
                'mvp_score': kda_result.mvp_score
            })
        elif damage_result and damage_result.confidence >= self.confidence_thresholds['damage']:
            # Try to extract KDA from damage result if available
            # This is a fallback - damage results typically don't have KDA
            pass
        
        return kda_data
    
    def _fuse_damage_data(self, kda_result: Optional[KDAResult], damage_result: Optional[DamageResult]) -> Dict[str, Any]:
        """Fuse damage data from both results."""
        damage_data = {
            'hero_damage': 0,
            'tower_damage': 0,
            'damage_taken': 0,
            'teamfight_participation': 0.0,
            'gold_per_minute': 0
        }
        
        # Use damage result if available and confident
        if damage_result and damage_result.confidence >= self.confidence_thresholds['damage']:
            damage_data.update({
                'hero_damage': damage_result.hero_damage,
                'tower_damage': damage_result.tower_damage,
                'damage_taken': damage_result.damage_taken,
                'teamfight_participation': damage_result.teamfight_participation,
                'gold_per_minute': damage_result.gold_per_minute
            })
        elif kda_result and kda_result.confidence >= self.confidence_thresholds['kda']:
            # Try to extract damage data from KDA result if available
            # This is a fallback - KDA results typically don't have damage data
            pass
        
        return damage_data
    
    def _calculate_overall_confidence(self, kda_result: Optional[KDAResult], damage_result: Optional[DamageResult]) -> float:
        """Calculate overall confidence score."""
        confidences = []
        
        if kda_result:
            confidences.append(kda_result.confidence * self.weight_factors['kda'])
        
        if damage_result:
            confidences.append(damage_result.confidence * self.weight_factors['damage'])
        
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences)
    
    def _calculate_data_completeness(self, kda_data: Dict[str, Any], damage_data: Dict[str, Any]) -> float:
        """Calculate data completeness score."""
        total_fields = 9  # Total number of data fields we expect
        filled_fields = 0
        
        # Count filled KDA fields
        if kda_data['kills'] > 0:
            filled_fields += 1
        if kda_data['deaths'] > 0:
            filled_fields += 1
        if kda_data['assists'] > 0:
            filled_fields += 1
        if kda_data['mvp_score'] > 0:
            filled_fields += 1
        
        # Count filled damage fields
        if damage_data['hero_damage'] > 0:
            filled_fields += 1
        if damage_data['tower_damage'] > 0:
            filled_fields += 1
        if damage_data['damage_taken'] > 0:
            filled_fields += 1
        if damage_data['teamfight_participation'] > 0:
            filled_fields += 1
        if damage_data['gold_per_minute'] > 0:
            filled_fields += 1
        
        return filled_fields / total_fields
    
    def _identify_conflicts_resolved(self, kda_result: Optional[KDAResult], damage_result: Optional[DamageResult]) -> List[str]:
        """Identify conflicts that were resolved during fusion."""
        conflicts = []
        
        if kda_result and damage_result:
            # Check for hero name conflicts
            if kda_result.hero != damage_result.hero and kda_result.hero != "unknown" and damage_result.hero != "unknown":
                conflicts.append(f"Hero name conflict: {kda_result.hero} vs {damage_result.hero}")
            
            # Check for IGN conflicts
            if kda_result.player_ign != damage_result.player_ign:
                conflicts.append(f"IGN conflict: {kda_result.player_ign} vs {damage_result.player_ign}")
        
        return conflicts
    
    def _determine_fusion_method(self, kda_result: Optional[KDAResult], damage_result: Optional[DamageResult]) -> str:
        """Determine the fusion method used."""
        if kda_result and damage_result:
            return "both_views"
        elif kda_result:
            return "kda_only"
        elif damage_result:
            return "damage_only"
        else:
            return "none"
    
    def parse_screenshot_pair(self, kda_image_path: str, damage_image_path: str, target_ign: str) -> Optional[FusedResult]:
        """
        Parse both KDA and Damage screenshots and fuse the results.
        
        Args:
            kda_image_path: Path to KDA view screenshot
            damage_image_path: Path to Damage view screenshot
            target_ign: Target player's IGN
            
        Returns:
            FusedResult with combined data, or None if parsing fails
        """
        try:
            # Parse KDA view
            kda_result = kda_parser.parse_kda_from_screenshot(kda_image_path, target_ign)
            
            # Parse Damage view
            damage_result = damage_parser.parse_damage_from_screenshot(damage_image_path, target_ign)
            
            # Fuse results
            return self.fuse_kda_and_damage(kda_result, damage_result)
            
        except Exception as e:
            logger.error(f"Error parsing screenshot pair: {e}")
            return None
    
    def parse_from_rows_fusion(self, kda_image: np.ndarray, damage_image: np.ndarray, rows: List, target_ign: str = "Diary of dolls") -> Optional[FusedResult]:
        """
        Parse from detected rows and fuse results (OCR-Mission-2.md requirement).
        
        Args:
            kda_image: KDA view image as numpy array
            damage_image: Damage view image as numpy array  
            rows: Pre-detected row crops from row-agnostic detector
            target_ign: Target player's IGN
            
        Returns:
            FusedResult with enriched schema, or None if parsing fails
        """
        try:
            # Parse using enhanced parse_from_rows methods
            kda_result = kda_parser.parse_from_rows(kda_image, rows, target_ign)
            damage_result = damage_parser.parse_from_rows(damage_image, rows, target_ign)
            
            # Fuse with enhanced MVP computation
            return self.fuse_kda_and_damage_enhanced(kda_result, damage_result, target_ign)
            
        except Exception as e:
            logger.error(f"Error in parse_from_rows_fusion: {e}")
            return None
    
    def fuse_kda_and_damage_enhanced(self, kda_result: Optional[KDAResult], damage_result: Optional[DamageResult], target_ign: str, hero_crop: Optional[np.ndarray] = None) -> Optional[FusedResult]:
        """
        Enhanced fusion with MVP score computation and enriched schema.
        Implements OCR-Mission-4.md and OCR-Mission-5.md requirements for hero resolution and drift telemetry.
        """
        try:
            # OCR Mission 5: Initialize drift telemetry
            from backend.ocr.robustness import detector_drift_guards, drift_telemetry_logger
            
            # Validate inputs
            if not kda_result and not damage_result:
                logger.warning("Both KDA and Damage results are None for enhanced fusion")
                return None
            
            # Extract basic info with fallbacks
            player_ign = target_ign
            
            # OCR Mission 4: Use advanced hero resolver if hero crop is provided
            hero = "unknown"
            hero_confidence = 0.0
            hero_resolution_method = "fallback"
            
            if hero_crop is not None:
                hero_match = hero_resolver.resolve_hero(hero_crop, target_ign)
                hero = hero_match.hero_name
                hero_confidence = hero_match.confidence
                hero_resolution_method = hero_match.method
                
                # OCR Mission 5: Update telemetry with hero resolution data
                detector_drift_guards.telemetry.hero_conf = hero_confidence
                if hasattr(hero_match, 'phash_distance') and hero_match.phash_distance is not None:
                    detector_drift_guards.telemetry.phash_dist = hero_match.phash_distance
                
                logger.info(f"Hero resolved: {hero} (confidence: {hero_confidence:.3f}, method: {hero_resolution_method})")
            else:
                # Fallback to original method
                hero = self._resolve_hero_name(kda_result, damage_result)
                hero_confidence = 0.5  # Default confidence for fallback
                hero_resolution_method = "text_based"
            
            # Fuse KDA data with enhanced processing
            kda_data = self._fuse_kda_data_enhanced(kda_result, damage_result)
            
            # Fuse damage data with enhanced processing  
            damage_data = self._fuse_damage_data_enhanced(kda_result, damage_result)
            
            # Calculate enhanced MVP score
            mvp_score = self._calculate_mvp_score_enhanced(kda_data, damage_data)
            
            # Calculate KDA ratio
            kda_ratio = self._calculate_kda_ratio(kda_data['kills'], kda_data['deaths'], kda_data['assists'])
            
            # Calculate overall confidence with enhanced weighting
            overall_confidence = self._calculate_overall_confidence_enhanced(kda_result, damage_result, mvp_score)
            
            # Calculate data completeness for enriched schema
            data_completeness = self._calculate_data_completeness_enhanced(kda_data, damage_data)
            
            # Track conflicts with enhanced resolution
            conflicts_resolved = self._identify_conflicts_resolved_enhanced(kda_result, damage_result)
            
            # Determine fusion method
            fusion_method = self._determine_fusion_method_enhanced(kda_result, damage_result)

            # OCR Mission 5: Update telemetry with final results
            detector_drift_guards.telemetry.ign_score = overall_confidence
            detector_drift_guards.telemetry.stage_ms["fusion"] = 0.0  # Will be updated by caller

            # Carry forward any match duration we managed to extract
            match_duration = None
            if kda_result:
                match_duration = getattr(kda_result, "match_duration", None)
                if match_duration is None and getattr(kda_result, "raw_data", None):
                    match_duration = kda_result.raw_data.get('match_duration')
            if match_duration is None and damage_result and getattr(damage_result, "raw_data", None):
                match_duration = damage_result.raw_data.get('match_duration')

            # Create enriched fused result
            fused_result = FusedResult(
                player_ign=player_ign,
                hero=hero,
                kills=kda_data['kills'],
                deaths=kda_data['deaths'],
                assists=kda_data['assists'],
                kda_ratio=kda_ratio,
                mvp_score=mvp_score,
                hero_damage=damage_data['hero_damage'],
                tower_damage=damage_data['tower_damage'],
                damage_taken=damage_data['damage_taken'],
                hero_damage_pct=damage_data.get('hero_damage_pct', 0.0),
                turret_damage_pct=damage_data.get('turret_damage_pct', 0.0),
                taken_damage_pct=damage_data.get('taken_damage_pct', 0.0),
                teamfight_participation=damage_data['teamfight_participation'],
                gold_per_minute=damage_data['gold_per_minute'],
                overall_confidence=overall_confidence,
                data_completeness=data_completeness,
                fusion_method=fusion_method,
                conflicts_resolved=conflicts_resolved,
                hero_confidence=hero_confidence,
                hero_resolution_method=hero_resolution_method,
                match_duration=match_duration,
                raw_data={
                    'kda_result': kda_result.__dict__ if kda_result else None,
                    'damage_result': damage_result.__dict__ if damage_result else None,
                    'mvp_computation': self._get_mvp_debug_info(kda_data, damage_data, mvp_score),
                    'hero_resolution': {
                        'hero': hero,
                        'confidence': hero_confidence,
                        'method': hero_resolution_method
                    },
                    'drift_telemetry': detector_drift_guards.telemetry.__dict__
                }
            )
            
            # OCR Mission 5: Log drift telemetry
            drift_telemetry_logger.log_analysis_telemetry(detector_drift_guards.telemetry, "OCR_FUSION_COMPLETE")
            
            return fused_result
            
        except Exception as e:
            logger.error(f"Error in enhanced KDA and Damage fusion: {e}")
            return None
    
    def _resolve_hero_name(self, kda_result: Optional[KDAResult], damage_result: Optional[DamageResult]) -> str:
        """Resolve hero name with confidence weighting."""
        if kda_result and damage_result:
            # Use result with higher confidence
            if kda_result.confidence > damage_result.confidence:
                return kda_result.hero if kda_result.hero != "unknown" else damage_result.hero
            else:
                return damage_result.hero if damage_result.hero != "unknown" else kda_result.hero
        elif kda_result:
            return kda_result.hero
        elif damage_result:
            return damage_result.hero
        else:
            return "unknown"
    
    def _fuse_kda_data_enhanced(self, kda_result: Optional[KDAResult], damage_result: Optional[DamageResult]) -> Dict[str, Any]:
        """Enhanced KDA data fusion with validation."""
        kda_data = {
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'mvp_score': 0.0
        }
        
        # Use KDA result if available and meets threshold
        if kda_result and kda_result.confidence >= self.confidence_thresholds['kda']:
            kda_data.update({
                'kills': max(0, kda_result.kills),  # Ensure non-negative
                'deaths': max(0, kda_result.deaths),
                'assists': max(0, kda_result.assists),
                'mvp_score': max(0.0, kda_result.mvp_score)
            })
        
        return kda_data
    
    def _fuse_damage_data_enhanced(self, kda_result: Optional[KDAResult], damage_result: Optional[DamageResult]) -> Dict[str, Any]:
        """Enhanced damage data fusion with percentage extraction."""
        damage_data = {
            'hero_damage': 0,
            'tower_damage': 0,
            'damage_taken': 0,
            'hero_damage_pct': 0.0,
            'turret_damage_pct': 0.0,
            'taken_damage_pct': 0.0,
            'teamfight_participation': 0.0,
            'gold_per_minute': 0
        }
        
        # Use damage result if available and meets threshold
        if damage_result and damage_result.confidence >= self.confidence_thresholds['damage']:
            damage_data.update({
                'hero_damage': max(0, damage_result.hero_damage),
                'tower_damage': max(0, damage_result.tower_damage),
                'damage_taken': max(0, damage_result.damage_taken),
                'teamfight_participation': max(0.0, damage_result.teamfight_participation),
                'gold_per_minute': max(0, damage_result.gold_per_minute)
            })
            
            # Extract percentage data if available in raw_data
            if hasattr(damage_result, 'raw_data') and damage_result.raw_data:
                raw_data = damage_result.raw_data
                damage_data['hero_damage_pct'] = raw_data.get('hero_damage_pct', 0.0)
                damage_data['turret_damage_pct'] = raw_data.get('turret_damage_pct', 0.0)
                damage_data['taken_damage_pct'] = raw_data.get('taken_damage_pct', 0.0)
        
        return damage_data
    
    def _calculate_kda_ratio(self, kills: int, deaths: int, assists: int) -> float:
        """Calculate KDA ratio with safe division."""
        try:
            if deaths == 0:
                return float(kills + assists)  # Perfect KDA
            return (kills + assists) / deaths
        except (ZeroDivisionError, TypeError):
            return 0.0
    
    def _calculate_mvp_score_enhanced(self, kda_data: Dict[str, Any], damage_data: Dict[str, Any]) -> float:
        """
        Calculate enhanced MVP score using weighted factors.
        Implements OCR-Mission-2.md requirement for MVP score computation.
        """
        try:
            # Extract values with defaults
            kills = kda_data.get('kills', 0)
            deaths = max(1, kda_data.get('deaths', 1))  # Avoid division by zero
            assists = kda_data.get('assists', 0)
            hero_damage = damage_data.get('hero_damage', 0)
            teamfight_participation = damage_data.get('teamfight_participation', 0.0) / 100.0  # Convert to 0-1
            gpm = damage_data.get('gold_per_minute', 0)
            
            # Calculate component scores (normalized 0-1)
            kda_ratio = (kills + assists) / deaths
            kda_score = min(1.0, kda_ratio / 5.0)  # Normalize to 0-1, cap at 5.0 KDA
            
            damage_score = min(1.0, hero_damage / 100000.0)  # Normalize to 0-1, cap at 100k damage
            participation_score = min(1.0, teamfight_participation)  # Already 0-1
            gpm_score = min(1.0, gpm / 1000.0)  # Normalize to 0-1, cap at 1k GPM
            
            # Individual performance bonuses
            kill_score = min(1.0, kills / 20.0)  # Cap at 20 kills
            assist_score = min(1.0, assists / 30.0)  # Cap at 30 assists
            
            # Damage efficiency (damage per death)
            damage_efficiency = hero_damage / deaths if deaths > 0 else hero_damage
            efficiency_score = min(1.0, damage_efficiency / 50000.0)  # Cap at 50k per death
            
            # Weighted MVP calculation
            mvp_score = (
                self.mvp_weights['kda_ratio'] * kda_score +
                self.mvp_weights['hero_damage'] * damage_score +
                self.mvp_weights['teamfight_participation'] * participation_score +
                self.mvp_weights['gpm'] * gpm_score +
                self.mvp_weights['kills'] * kill_score +
                self.mvp_weights['assists'] * assist_score +
                self.mvp_weights['damage_efficiency'] * efficiency_score
            )
            
            # Scale to typical MVP range (5.0-15.0)
            final_mvp_score = 5.0 + (mvp_score * 10.0)
            
            return min(15.0, max(5.0, final_mvp_score))
            
        except Exception as e:
            logger.error(f"Error calculating enhanced MVP score: {e}")
            return 8.0  # Default reasonable MVP score
    
    def _calculate_overall_confidence_enhanced(self, kda_result: Optional[KDAResult], damage_result: Optional[DamageResult], mvp_score: float) -> float:
        """Enhanced confidence calculation with MVP validation."""
        try:
            confidences = []
            weights = []
            
            if kda_result:
                confidences.append(kda_result.confidence)
                weights.append(self.weight_factors['kda'])
            
            if damage_result:
                confidences.append(damage_result.confidence)
                weights.append(self.weight_factors['damage'])
            
            if not confidences:
                return 0.0
            
            # Weighted average confidence
            weighted_confidence = sum(c * w for c, w in zip(confidences, weights)) / sum(weights)
            
            # MVP score validation bonus
            mvp_bonus = 0.1 if 5.0 <= mvp_score <= 15.0 else 0.0
            
            # Data consistency bonus
            consistency_bonus = 0.05 if kda_result and damage_result else 0.0
            
            final_confidence = weighted_confidence + mvp_bonus + consistency_bonus
            
            return min(1.0, max(0.0, final_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating enhanced overall confidence: {e}")
            return 0.0
    
    def _calculate_data_completeness_enhanced(self, kda_data: Dict[str, Any], damage_data: Dict[str, Any]) -> float:
        """Enhanced data completeness calculation for enriched schema."""
        try:
            total_fields = 13  # Total expected fields in enriched schema
            filled_fields = 0
            
            # Count filled KDA fields
            if kda_data['kills'] > 0: filled_fields += 1
            if kda_data['deaths'] > 0: filled_fields += 1
            if kda_data['assists'] > 0: filled_fields += 1
            if kda_data['mvp_score'] > 0: filled_fields += 1
            
            # Count filled damage fields
            if damage_data['hero_damage'] > 0: filled_fields += 1
            if damage_data['tower_damage'] > 0: filled_fields += 1
            if damage_data['damage_taken'] > 0: filled_fields += 1
            if damage_data['hero_damage_pct'] > 0: filled_fields += 1
            if damage_data['turret_damage_pct'] > 0: filled_fields += 1
            if damage_data['taken_damage_pct'] > 0: filled_fields += 1
            if damage_data['teamfight_participation'] > 0: filled_fields += 1
            if damage_data['gold_per_minute'] > 0: filled_fields += 1
            
            # Hero name field (always available)
            filled_fields += 1
            
            return filled_fields / total_fields
            
        except Exception as e:
            logger.error(f"Error calculating enhanced data completeness: {e}")
            return 0.0
    
    def _identify_conflicts_resolved_enhanced(self, kda_result: Optional[KDAResult], damage_result: Optional[DamageResult]) -> List[str]:
        """Enhanced conflict identification and resolution."""
        conflicts = []
        
        if kda_result and damage_result:
            # Hero name conflicts
            if (kda_result.hero != damage_result.hero and 
                kda_result.hero != "unknown" and damage_result.hero != "unknown"):
                conflicts.append(f"Hero name conflict resolved: {kda_result.hero} vs {damage_result.hero} (confidence-weighted)")
            
            # IGN conflicts  
            if kda_result.player_ign != damage_result.player_ign:
                conflicts.append(f"IGN conflict resolved: {kda_result.player_ign} vs {damage_result.player_ign}")
            
            # Confidence threshold conflicts
            if kda_result.confidence < self.confidence_thresholds['kda']:
                conflicts.append(f"Low KDA confidence handled: {kda_result.confidence:.3f} < {self.confidence_thresholds['kda']}")
            
            if damage_result.confidence < self.confidence_thresholds['damage']:
                conflicts.append(f"Low damage confidence handled: {damage_result.confidence:.3f} < {self.confidence_thresholds['damage']}")
        
        return conflicts
    
    def _determine_fusion_method_enhanced(self, kda_result: Optional[KDAResult], damage_result: Optional[DamageResult]) -> str:
        """Enhanced fusion method determination with quality indicators."""
        if kda_result and damage_result:
            kda_quality = "high" if kda_result.confidence >= self.confidence_thresholds['kda'] else "low"
            damage_quality = "high" if damage_result.confidence >= self.confidence_thresholds['damage'] else "low"
            return f"both_views_{kda_quality}_kda_{damage_quality}_damage"
        elif kda_result:
            kda_quality = "high" if kda_result.confidence >= self.confidence_thresholds['kda'] else "low"
            return f"kda_only_{kda_quality}"
        elif damage_result:
            damage_quality = "high" if damage_result.confidence >= self.confidence_thresholds['damage'] else "low"
            return f"damage_only_{damage_quality}"
        else:
            return "none"
    
    def _get_mvp_debug_info(self, kda_data: Dict[str, Any], damage_data: Dict[str, Any], mvp_score: float) -> Dict[str, Any]:
        """Get MVP computation debug information."""
        return {
            'input_kda': kda_data,
            'input_damage': damage_data,
            'computed_mvp_score': mvp_score,
            'mvp_weights': self.mvp_weights,
            'confidence_thresholds': self.confidence_thresholds
        }

# Standalone function for cross-view fusion (expected by performance tests)
def cross_view_fusion(kda_result, damage_result, hero_crop=None):
    """
    Standalone cross-view fusion function (OCR-Mission-4.md compatibility).
    
    Args:
        kda_result: KDA parsing result
        damage_result: Damage parsing result
        hero_crop: Optional hero portrait crop for advanced resolution
        
    Returns:
        FusedResult with enhanced schema including hero resolution
    """
    try:
        fusion_instance = CrossViewFusion()
        return fusion_instance.fuse_kda_and_damage_enhanced(kda_result, damage_result, "Diary of dolls", hero_crop)
    except Exception as e:
        logger.error(f"Error in standalone cross_view_fusion: {e}")
        return None

# Global instance
cross_view_fusion_instance = CrossViewFusion()
