"""
Early Exit Fusion for Mission 3
Implements early-exit logic for KDA+Damage fusion to achieve <500ms performance.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class EarlyExitFusion:
    """
    Early-exit fusion system for optimal performance.
    
    Features:
    - Early termination when confidence threshold is met
    - Smart IGN matching with early exit
    - Confidence-weighted result merging
    - Performance monitoring and optimization
    """
    
    def __init__(self, 
                 confidence_threshold: float = 0.9,
                 max_iterations: int = 5,
                 enable_performance_monitoring: bool = True):
        """
        Initialize early-exit fusion system.
        
        Args:
            confidence_threshold: Minimum confidence for early exit
            max_iterations: Maximum number of iterations before fallback
            enable_performance_monitoring: Enable performance tracking
        """
        self.confidence_threshold = confidence_threshold
        self.max_iterations = max_iterations
        self.enable_performance_monitoring = enable_performance_monitoring
        
        # Performance tracking
        self.performance_metrics = {
            'total_requests': 0,
            'early_exits': 0,
            'full_processing': 0,
            'avg_processing_time': 0.0,
            'confidence_scores': []
        }
    
    def analyze_with_early_exit(self, 
                               image_path: str, 
                               ign: str,
                               confidence_threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Analyze image with early-exit optimization.
        
        Args:
            image_path: Path to image
            ign: Player's in-game name
            confidence_threshold: Override default confidence threshold
            
        Returns:
            Analysis result with early-exit optimization
        """
        start_time = time.time()
        threshold = confidence_threshold or self.confidence_threshold
        
        try:
            # Initialize components
            from .optimized_roi_processor import OptimizedROIProcessor
            from .fast_table_detector import FastTableDetector
            from .ocr_cache import get_global_cache
            from .ocr_reader import get_reader
            
            roi_processor = OptimizedROIProcessor()
            table_detector = FastTableDetector()
            cache = get_global_cache()
            reader = get_reader()
            
            # Phase 1: Fast table detection
            table_result = table_detector.detect_table_structure(image_path)
            
            if table_result['confidence'] < 0.3:
                logger.warning("Low table detection confidence, using fallback")
                return self._fallback_analysis(image_path, ign)
            
            # Phase 2: Early-exit IGN matching
            ign_result = self._find_ign_with_early_exit(
                image_path, ign, table_result, reader, cache, threshold
            )
            
            if ign_result['confidence'] >= threshold:
                logger.info(f"Early exit triggered at confidence {ign_result['confidence']:.3f}")
                self.performance_metrics['early_exits'] += 1
                return self._build_result(ign_result, table_result, start_time)
            
            # Phase 3: Full processing if needed
            logger.info("Early exit not triggered, proceeding with full processing")
            full_result = self._full_processing(
                image_path, ign, table_result, reader, cache
            )
            
            self.performance_metrics['full_processing'] += 1
            return self._build_result(full_result, table_result, start_time)
            
        except Exception as e:
            logger.error(f"Early-exit analysis failed: {e}")
            return self._fallback_analysis(image_path, ign)
        finally:
            self._update_performance_metrics(start_time)
    
    def _find_ign_with_early_exit(self, 
                                 image_path: str, 
                                 ign: str, 
                                 table_result: Dict[str, Any],
                                 reader, 
                                 cache,
                                 threshold: float) -> Dict[str, Any]:
        """
        Find IGN with early-exit optimization.
        
        Args:
            image_path: Path to image
            ign: Target IGN
            table_result: Table detection result
            reader: OCR reader
            cache: OCR cache
            threshold: Confidence threshold for early exit
            
        Returns:
            IGN matching result
        """
        try:
            # Get row crops from table detection
            row_crops = table_result.get('row_crops', [])
            
            if not row_crops:
                return {'found': False, 'confidence': 0.0, 'data': {}}
            
            # Process rows with early exit
            for i, row_crop in enumerate(row_crops):
                # Check if we should continue (early exit check)
                if i >= self.max_iterations:
                    logger.debug(f"Max iterations reached ({self.max_iterations})")
                    break
                
                # Process row
                row_result = self._process_row_with_early_exit(
                    row_crop, ign, reader, cache, threshold
                )
                
                if row_result['confidence'] >= threshold:
                    logger.debug(f"Early exit at row {i} with confidence {row_result['confidence']:.3f}")
                    return row_result
            
            # If no early exit, return best result
            return self._get_best_result_from_rows(row_crops, ign, reader, cache)
            
        except Exception as e:
            logger.error(f"Early-exit IGN finding failed: {e}")
            return {'found': False, 'confidence': 0.0, 'data': {}}
    
    def _process_row_with_early_exit(self, 
                                   row_crop: np.ndarray, 
                                   ign: str, 
                                   reader, 
                                   cache,
                                   threshold: float) -> Dict[str, Any]:
        """
        Process single row with early-exit logic.
        
        Args:
            row_crop: Row image crop
            ign: Target IGN
            reader: OCR reader
            cache: OCR cache
            threshold: Confidence threshold
            
        Returns:
            Row processing result
        """
        try:
            from .optimized_roi_processor import OptimizedROIProcessor
            
            roi_processor = OptimizedROIProcessor()
            
            # Preprocess for digits
            roi_binary = roi_processor.prep_digits_roi(row_crop)
            
            # Extract text with caching
            texts = cache.cached_readtext(reader, roi_binary, allowlist="0123456789/%,.")
            
            # Quick IGN matching
            ign_match = self._quick_ign_match(ign, texts)
            
            if ign_match['confidence'] >= threshold:
                # Early exit - extract KDA and damage
                kda_data = self._extract_kda_from_texts(texts)
                damage_data = self._extract_damage_from_texts(texts)
                
                return {
                    'found': True,
                    'confidence': ign_match['confidence'],
                    'data': {
                        'ign': ign_match['matched_ign'],
                        'kda': kda_data,
                        'damage': damage_data,
                        'row_texts': texts
                    }
                }
            
            return {
                'found': False,
                'confidence': ign_match['confidence'],
                'data': {}
            }
            
        except Exception as e:
            logger.error(f"Row processing failed: {e}")
            return {'found': False, 'confidence': 0.0, 'data': {}}
    
    def _quick_ign_match(self, target_ign: str, texts: List[str]) -> Dict[str, Any]:
        """
        Quick IGN matching with early exit optimization.
        
        Args:
            target_ign: Target IGN to match
            texts: List of extracted texts
            
        Returns:
            IGN matching result
        """
        try:
            if not texts:
                return {'matched_ign': None, 'confidence': 0.0}
            
            # Normalize target IGN
            target_normalized = self._normalize_ign(target_ign)
            
            best_match = None
            best_confidence = 0.0
            
            for text in texts:
                # Quick length check (early exit)
                if abs(len(text) - len(target_normalized)) > 5:
                    continue
                
                # Normalize text
                text_normalized = self._normalize_ign(text)
                
                # Quick character overlap check
                overlap = self._calculate_character_overlap(target_normalized, text_normalized)
                if overlap < 0.3:  # Early exit for low overlap
                    continue
                
                # Calculate similarity
                similarity = self._calculate_ign_similarity(target_normalized, text_normalized)
                
                if similarity > best_confidence:
                    best_confidence = similarity
                    best_match = text
            
            return {
                'matched_ign': best_match,
                'confidence': best_confidence
            }
            
        except Exception as e:
            logger.error(f"Quick IGN matching failed: {e}")
            return {'matched_ign': None, 'confidence': 0.0}
    
    def _normalize_ign(self, ign: str) -> str:
        """Normalize IGN for matching."""
        if not ign:
            return ""
        
        # Convert to lowercase and remove special characters
        normalized = ign.lower().strip()
        # Remove common OCR artifacts
        normalized = normalized.replace('0', 'o').replace('1', 'i').replace('5', 's')
        return normalized
    
    def _calculate_character_overlap(self, str1: str, str2: str) -> float:
        """Calculate character overlap ratio."""
        if not str1 or not str2:
            return 0.0
        
        set1 = set(str1)
        set2 = set(str2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_ign_similarity(self, target: str, candidate: str) -> float:
        """Calculate IGN similarity score."""
        if not target or not candidate:
            return 0.0
        
        # Character overlap
        overlap = self._calculate_character_overlap(target, candidate)
        
        # Length similarity
        len_sim = 1.0 - abs(len(target) - len(candidate)) / max(len(target), len(candidate))
        
        # Position-based similarity (simple)
        pos_sim = 0.0
        min_len = min(len(target), len(candidate))
        for i in range(min_len):
            if target[i] == candidate[i]:
                pos_sim += 1.0
        pos_sim = pos_sim / min_len if min_len > 0 else 0.0
        
        # Weighted combination
        similarity = (overlap * 0.4 + len_sim * 0.3 + pos_sim * 0.3)
        return min(1.0, max(0.0, similarity))
    
    def _extract_kda_from_texts(self, texts: List[str]) -> Dict[str, Any]:
        """Extract KDA data from texts."""
        try:
            import re
            
            kda_patterns = [
                r'(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{1,2})',  # Standard K/D/A
                r'(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})',  # Spaced format
            ]
            
            for text in texts:
                for pattern in kda_patterns:
                    match = re.search(pattern, text)
                    if match:
                        kills, deaths, assists = map(int, match.groups())
                        return {
                            'kills': kills,
                            'deaths': deaths,
                            'assists': assists,
                            'ratio': kills / deaths if deaths > 0 else 0.0
                        }
            
            return {'kills': 0, 'deaths': 0, 'assists': 0, 'ratio': 0.0}
            
        except Exception as e:
            logger.error(f"KDA extraction failed: {e}")
            return {'kills': 0, 'deaths': 0, 'assists': 0, 'ratio': 0.0}
    
    def _extract_damage_from_texts(self, texts: List[str]) -> Dict[str, Any]:
        """Extract damage data from texts."""
        try:
            import re
            
            damage_patterns = [
                r'(\d{1,3}(?:,\d{3})*)',  # Comma-formatted numbers
                r'(\d{4,6})',  # 4-6 digit numbers (likely damage)
            ]
            
            damage_values = []
            for text in texts:
                for pattern in damage_patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        try:
                            # Remove commas and convert to int
                            value = int(match.replace(',', ''))
                            if 1000 <= value <= 500000:  # Reasonable damage range
                                damage_values.append(value)
                        except ValueError:
                            continue
            
            if damage_values:
                max_damage = max(damage_values)
                return {
                    'hero_damage': max_damage,
                    'hero_damage_pct': 0.0,  # Would need total team damage
                    'turret_damage': 0,
                    'taken_damage': 0
                }
            
            return {'hero_damage': 0, 'hero_damage_pct': 0.0, 'turret_damage': 0, 'taken_damage': 0}
            
        except Exception as e:
            logger.error(f"Damage extraction failed: {e}")
            return {'hero_damage': 0, 'hero_damage_pct': 0.0, 'turret_damage': 0, 'taken_damage': 0}
    
    def _get_best_result_from_rows(self, row_crops: List[np.ndarray], ign: str, reader, cache) -> Dict[str, Any]:
        """Get best result from all rows when no early exit."""
        try:
            best_result = {'found': False, 'confidence': 0.0, 'data': {}}
            
            for row_crop in row_crops:
                row_result = self._process_row_with_early_exit(
                    row_crop, ign, reader, cache, 0.0  # No threshold for full processing
                )
                
                if row_result['confidence'] > best_result['confidence']:
                    best_result = row_result
            
            return best_result
            
        except Exception as e:
            logger.error(f"Best result selection failed: {e}")
            return {'found': False, 'confidence': 0.0, 'data': {}}
    
    def _full_processing(self, image_path: str, ign: str, table_result: Dict[str, Any], reader, cache) -> Dict[str, Any]:
        """Full processing when early exit is not triggered."""
        try:
            # Use existing enhanced data collector for full processing
            from ..enhanced_data_collector import EnhancedDataCollector
            
            collector = EnhancedDataCollector()
            result = collector.analyze_screenshot_with_session(
                image_path=image_path,
                ign=ign
            )
            
            # Extract relevant data
            data = result.get('data', {})
            confidence = result.get('confidence', 0.0)
            
            return {
                'found': confidence > 0.5,
                'confidence': confidence,
                'data': data
            }
            
        except Exception as e:
            logger.error(f"Full processing failed: {e}")
            return {'found': False, 'confidence': 0.0, 'data': {}}
    
    def _build_result(self, ign_result: Dict[str, Any], table_result: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """Build final result from components."""
        try:
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Calculate MVP score
            mvp_score = self._calculate_mvp_score(ign_result.get('data', {}))
            
            # Build final result
            result = {
                'data': ign_result.get('data', {}),
                'confidence': ign_result.get('confidence', 0.0),
                'processing_time_ms': processing_time,
                'mvp_score': mvp_score,
                'table_detection': table_result,
                'early_exit_used': ign_result.get('confidence', 0.0) >= self.confidence_threshold,
                'warnings': []
            }
            
            # Add warnings if needed
            if processing_time > 500:
                result['warnings'].append(f"Processing time exceeded target: {processing_time:.1f}ms")
            
            if result['confidence'] < 0.85:
                result['warnings'].append(f"Low confidence: {result['confidence']:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Result building failed: {e}")
            return {
                'data': {},
                'confidence': 0.0,
                'processing_time_ms': (time.time() - start_time) * 1000,
                'mvp_score': 0.0,
                'warnings': [f"Result building failed: {e}"]
            }
    
    def _calculate_mvp_score(self, data: Dict[str, Any]) -> float:
        """Calculate MVP score from data."""
        try:
            kda = data.get('kda', {})
            damage = data.get('damage', {})
            
            kills = kda.get('kills', 0)
            deaths = kda.get('deaths', 1)  # Avoid division by zero
            assists = kda.get('assists', 0)
            hero_damage = damage.get('hero_damage', 0)
            
            # Simple MVP calculation
            kda_score = (kills + assists * 0.5) / max(deaths, 1)
            damage_score = min(hero_damage / 10000, 1.0)  # Normalize to 0-1
            
            mvp_score = (kda_score * 0.6 + damage_score * 0.4)
            return min(1.0, max(0.0, mvp_score))
            
        except Exception as e:
            logger.error(f"MVP score calculation failed: {e}")
            return 0.0
    
    def _fallback_analysis(self, image_path: str, ign: str) -> Dict[str, Any]:
        """Fallback analysis when main processing fails."""
        try:
            from ..data_collector import DataCollector
            
            collector = DataCollector()
            result = collector.from_screenshot_enhanced(ign, image_path)
            
            return {
                'data': result.get('data', {}),
                'confidence': 0.5,  # Default confidence for fallback
                'processing_time_ms': 0.0,
                'mvp_score': 0.0,
                'early_exit_used': False,
                'warnings': ['Fallback analysis used']
            }
            
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            return {
                'data': {},
                'confidence': 0.0,
                'processing_time_ms': 0.0,
                'mvp_score': 0.0,
                'early_exit_used': False,
                'warnings': [f'Analysis failed: {e}']
            }
    
    def _update_performance_metrics(self, start_time: float):
        """Update performance metrics."""
        if not self.enable_performance_monitoring:
            return
        
        try:
            processing_time = (time.time() - start_time) * 1000
            self.performance_metrics['total_requests'] += 1
            
            # Update average processing time
            total = self.performance_metrics['total_requests']
            current_avg = self.performance_metrics['avg_processing_time']
            self.performance_metrics['avg_processing_time'] = (
                (current_avg * (total - 1) + processing_time) / total
            )
            
        except Exception as e:
            logger.warning(f"Performance metrics update failed: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.performance_metrics.copy()
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self.performance_metrics = {
            'total_requests': 0,
            'early_exits': 0,
            'full_processing': 0,
            'avg_processing_time': 0.0,
            'confidence_scores': []
        }
