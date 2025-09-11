#!/usr/bin/env python3
"""
Quality Assessment Integration Module
====================================

Integration layer connecting the Intelligent Quality Assessment Engine
with existing MLBB Coach AI systems for seamless quality-aware processing.

Features:
- Integration with Enhanced Data Collector
- Quality-aware OCR processing
- Adaptive YOLO-OCR coordination
- Performance optimization integration
- Quality-based caching strategies
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

# Import existing systems
try:
    from .quality_assessor import IntelligentQualityAssessmentEngine, QualityLevel, ProcessingStrategy
    from .enhanced_data_collector import DataCollector
    from .enhanced_ocr_processor import EnhancedOCRProcessor, PreprocessingMethod
    from .yolo_ocr_integration import YOLOOCRIntegrator, IntegrationMode
    from .performance_optimizer_v2 import PerformanceOptimizerV2
    IMPORTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Some imports not available: {e}")
    IMPORTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class QualityAwareDataCollector(DataCollector):
    """Enhanced DataCollector with quality assessment integration."""
    
    def __init__(self):
        """Initialize quality-aware data collector."""
        super().__init__()
        
        if IMPORTS_AVAILABLE:
            self.quality_engine = IntelligentQualityAssessmentEngine()
        else:
            self.quality_engine = None
            
        logger.info("📊 Quality-Aware Data Collector initialized")
    
    async def from_screenshot_quality_aware(self, 
                                          ign: str, 
                                          image_path: str, 
                                          hero_override: str = None,
                                          user_id: str = "anonymous") -> Dict[str, Any]:
        """
        Process screenshot with quality assessment and adaptive optimization.
        
        Args:
            ign: Player IGN
            image_path: Path to screenshot
            hero_override: Manual hero override
            user_id: User ID for personalized guidance
            
        Returns:
            Enhanced processing result with quality information
        """
        logger.info(f"📊 Quality-aware processing for IGN: {ign}")
        
        if not self.quality_engine:
            logger.warning("⚠️ Quality engine not available, using standard processing")
            return self.from_screenshot(ign, image_path, hero_override)
        
        try:
            # Step 1: Assess screenshot quality
            quality_assessment = await self.quality_engine.assess_screenshot_quality(
                image_path=image_path,
                user_id=user_id,
                include_guidance=True,
                include_adaptive_config=True
            )
            
            quality_metrics = quality_assessment.quality_metrics
            adaptive_config = quality_assessment.adaptive_processing_config
            
            logger.info(f"📊 Quality assessment: {quality_metrics.quality_level.name} "
                       f"(score: {quality_metrics.overall_score:.3f})")
            
            # Step 2: Check quality gates
            user_guidance = quality_assessment.user_guidance
            quality_gates = user_guidance.get('quality_gates', {})
            
            if quality_gates.get('block_processing', False):
                return {
                    'success': False,
                    'error': 'Screenshot quality too low for reliable analysis',
                    'quality_assessment': quality_assessment,
                    'user_guidance': user_guidance,
                    'recommendations': ['Please retake the screenshot with better quality']
                }
            
            # Step 3: Select processing method based on quality
            if quality_metrics.overall_score >= 0.8:
                # High quality - use efficient processing
                result = self.from_screenshot(ign, image_path, hero_override)
            else:
                # Lower quality - use enhanced processing
                if hasattr(self, 'from_screenshot_enhanced'):
                    result = await self.from_screenshot_enhanced(
                        ign=ign, 
                        image_path=image_path,
                        hero_override=hero_override,
                        use_ensemble=True
                    )
                else:
                    result = self.from_screenshot(ign, image_path, hero_override)
            
            # Step 4: Enhance result with quality information
            if isinstance(result, dict):
                result['quality_assessment'] = {
                    'overall_score': quality_metrics.overall_score,
                    'quality_level': quality_metrics.quality_level.name,
                    'processing_strategy': quality_metrics.processing_strategy.name,
                    'confidence_adjustment': self._calculate_confidence_adjustment(quality_metrics),
                    'user_guidance': user_guidance,
                    'adaptive_config': adaptive_config
                }
                
                # Adjust confidence based on quality
                if 'confidence' in result:
                    original_confidence = result['confidence']
                    adjusted_confidence = original_confidence * quality_metrics.confidence
                    result['quality_adjusted_confidence'] = adjusted_confidence
                    
                    # Add quality warnings to existing warnings
                    if 'warnings' not in result:
                        result['warnings'] = []
                    
                    if quality_metrics.overall_score < 0.6:
                        result['warnings'].append(f"Low image quality may affect analysis accuracy (score: {quality_metrics.overall_score:.3f})")
                    
                    if quality_gates.get('warn_reduced_accuracy', False):
                        result['warnings'].append("Reduced analysis accuracy expected due to image quality")
            
            logger.info(f"✅ Quality-aware processing completed")
            return result
            
        except Exception as e:
            logger.error(f"❌ Quality-aware processing failed: {e}")
            # Fallback to standard processing
            return self.from_screenshot(ign, image_path, hero_override)
    
    def _calculate_confidence_adjustment(self, quality_metrics: QualityMetrics) -> float:
        """Calculate confidence adjustment factor based on quality."""
        base_adjustment = quality_metrics.confidence
        
        # Additional adjustments based on specific dimensions
        critical_dimensions = [
            'text_clarity', 'ui_visibility', 'sharpness'
        ]
        
        critical_scores = [
            quality_metrics.dimension_scores.get(dim, 1.0) 
            for dim in critical_dimensions
        ]
        
        critical_avg = sum(critical_scores) / len(critical_scores)
        
        # Combine base adjustment with critical dimension performance
        final_adjustment = (base_adjustment * 0.7 + critical_avg * 0.3)
        
        return max(0.3, min(1.0, final_adjustment))  # Clamp between 0.3 and 1.0


class QualityAwareOCRProcessor:
    """OCR processor enhanced with quality assessment integration."""
    
    def __init__(self):
        """Initialize quality-aware OCR processor."""
        if IMPORTS_AVAILABLE:
            self.ocr_processor = EnhancedOCRProcessor()
            self.quality_engine = IntelligentQualityAssessmentEngine()
        else:
            self.ocr_processor = None
            self.quality_engine = None
        
        logger.info("📝 Quality-Aware OCR Processor initialized")
    
    async def process_with_quality_optimization(self, 
                                              image_path: str,
                                              user_id: str = "anonymous") -> Dict[str, Any]:
        """
        Process image with quality-optimized OCR pipeline.
        
        Args:
            image_path: Path to image
            user_id: User ID for guidance
            
        Returns:
            OCR results with quality optimization
        """
        if not self.quality_engine or not self.ocr_processor:
            logger.warning("⚠️ Quality-aware components not available")
            return {'error': 'Components not available'}
        
        # Step 1: Assess quality
        quality_assessment = await self.quality_engine.assess_screenshot_quality(image_path, user_id)
        quality_metrics = quality_assessment.quality_metrics
        
        # Step 2: Select optimal OCR method based on quality
        ocr_method = self._select_ocr_method(quality_metrics)
        ocr_engine = self._select_ocr_engine(quality_metrics)
        
        # Step 3: Process with selected configuration
        ocr_result = await self.ocr_processor.process_image(
            image_path=image_path,
            preprocessing_method=ocr_method,
            ocr_engine=ocr_engine,
            confidence_threshold=self._get_confidence_threshold(quality_metrics)
        )
        
        # Step 4: Apply quality-based post-processing
        enhanced_result = self._apply_quality_post_processing(ocr_result, quality_metrics)
        
        # Step 5: Add quality information
        enhanced_result['quality_assessment'] = {
            'overall_score': quality_metrics.overall_score,
            'quality_level': quality_metrics.quality_level.name,
            'processing_strategy': quality_metrics.processing_strategy.name,
            'user_guidance': quality_assessment.user_guidance,
            'recommendations': quality_assessment.preprocessing_recommendations
        }
        
        return enhanced_result
    
    def _select_ocr_method(self, quality_metrics: QualityMetrics) -> PreprocessingMethod:
        """Select OCR preprocessing method based on quality."""
        strategy = quality_metrics.processing_strategy
        
        method_mapping = {
            ProcessingStrategy.MINIMAL: PreprocessingMethod.BASIC,
            ProcessingStrategy.STANDARD: PreprocessingMethod.ADVANCED,
            ProcessingStrategy.ENHANCED: PreprocessingMethod.GAME_SPECIFIC,
            ProcessingStrategy.AGGRESSIVE: PreprocessingMethod.ENSEMBLE,
            ProcessingStrategy.RECOVERY: PreprocessingMethod.ENSEMBLE
        }
        
        return method_mapping.get(strategy, PreprocessingMethod.ADVANCED)
    
    def _select_ocr_engine(self, quality_metrics: QualityMetrics):
        """Select OCR engine based on quality."""
        if quality_metrics.overall_score >= 0.8:
            return "easyocr"  # Fast processing for high quality
        else:
            return "ensemble"  # More robust processing for lower quality
    
    def _get_confidence_threshold(self, quality_metrics: QualityMetrics) -> float:
        """Get confidence threshold based on quality."""
        base_threshold = 0.7
        
        # Lower threshold for poor quality images
        quality_adjustment = quality_metrics.overall_score * 0.3
        adjusted_threshold = base_threshold - quality_adjustment
        
        return max(0.3, min(0.9, adjusted_threshold))
    
    def _apply_quality_post_processing(self, ocr_result, quality_metrics: QualityMetrics) -> Dict[str, Any]:
        """Apply quality-based post-processing to OCR results."""
        enhanced_result = {
            'success': ocr_result.success,
            'results': ocr_result.results,
            'processing_time': ocr_result.processing_time,
            'quality_enhanced': True
        }
        
        if ocr_result.success:
            # Apply confidence adjustments based on quality
            confidence_adjustment = quality_metrics.confidence
            
            adjusted_results = []
            for result in ocr_result.results:
                if hasattr(result, 'confidence'):
                    adjusted_confidence = result.confidence * confidence_adjustment
                    # Create adjusted result (simplified for demo)
                    adjusted_results.append({
                        'text': result.text,
                        'confidence': adjusted_confidence,
                        'bbox': result.bbox,
                        'quality_adjusted': True
                    })
                else:
                    adjusted_results.append(result)
            
            enhanced_result['quality_adjusted_results'] = adjusted_results
            enhanced_result['confidence_adjustment_factor'] = confidence_adjustment
        
        return enhanced_result


class QualityAwareIntegrationManager:
    """Manager for integrating quality assessment across all systems."""
    
    def __init__(self):
        """Initialize quality-aware integration manager."""
        self.quality_engine = IntelligentQualityAssessmentEngine() if IMPORTS_AVAILABLE else None
        self.quality_data_collector = QualityAwareDataCollector()
        self.quality_ocr_processor = QualityAwareOCRProcessor()
        
        # Integration statistics
        self.integration_stats = {
            'quality_assessments_performed': 0,
            'quality_improvements_applied': 0,
            'user_guidance_provided': 0,
            'adaptive_processing_used': 0,
            'quality_gates_triggered': 0
        }
        
        logger.info("🔗 Quality-Aware Integration Manager initialized")
    
    async def process_screenshot_with_quality_intelligence(self, 
                                                         image_path: str,
                                                         ign: str,
                                                         user_id: str = "anonymous",
                                                         processing_mode: str = "adaptive") -> Dict[str, Any]:
        """
        Process screenshot with full quality intelligence integration.
        
        Args:
            image_path: Path to screenshot
            ign: Player IGN
            user_id: User ID
            processing_mode: Processing mode (adaptive, quality_first, performance_first)
            
        Returns:
            Comprehensive processing result with quality intelligence
        """
        logger.info(f"🧠 Quality-intelligent processing: {Path(image_path).name}")
        
        if not self.quality_engine:
            logger.warning("⚠️ Quality engine not available")
            return await self._fallback_processing(image_path, ign)
        
        try:
            # Step 1: Comprehensive quality assessment
            quality_assessment = await self.quality_engine.assess_screenshot_quality(
                image_path=image_path,
                user_id=user_id,
                include_guidance=True,
                include_adaptive_config=True
            )
            
            self.integration_stats['quality_assessments_performed'] += 1
            
            # Step 2: Apply quality gates
            quality_gates = quality_assessment.user_guidance.get('quality_gates', {})
            
            if quality_gates.get('block_processing', False):
                self.integration_stats['quality_gates_triggered'] += 1
                return {
                    'success': False,
                    'blocked_by_quality': True,
                    'quality_assessment': quality_assessment,
                    'message': 'Screenshot quality too low for reliable analysis',
                    'user_guidance': quality_assessment.user_guidance
                }
            
            # Step 3: Select processing approach based on mode and quality
            if processing_mode == "quality_first":
                result = await self._quality_first_processing(image_path, ign, quality_assessment)
            elif processing_mode == "performance_first":
                result = await self._performance_first_processing(image_path, ign, quality_assessment)
            else:  # adaptive
                result = await self._adaptive_processing(image_path, ign, quality_assessment)
            
            # Step 4: Apply quality-based confidence adjustments
            result = self._apply_quality_adjustments(result, quality_assessment)
            
            # Step 5: Add comprehensive quality information
            result['quality_intelligence'] = {
                'assessment': quality_assessment,
                'processing_optimizations_applied': self._get_applied_optimizations(quality_assessment),
                'confidence_adjustments': self._get_confidence_adjustments(quality_assessment),
                'user_guidance': quality_assessment.user_guidance,
                'quality_score': quality_assessment.quality_metrics.overall_score,
                'processing_strategy': quality_assessment.quality_metrics.processing_strategy.name
            }
            
            self.integration_stats['quality_improvements_applied'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Quality-intelligent processing failed: {e}")
            return await self._fallback_processing(image_path, ign)
    
    async def _quality_first_processing(self, image_path: str, ign: str, 
                                      quality_assessment) -> Dict[str, Any]:
        """Process with quality as primary concern."""
        quality_metrics = quality_assessment.quality_metrics
        
        # Use the most appropriate method for the quality level
        if quality_metrics.quality_level in [QualityLevel.EXCELLENT, QualityLevel.GOOD]:
            # High quality - use efficient processing
            return await self.quality_data_collector.from_screenshot_quality_aware(
                ign=ign,
                image_path=image_path
            )
        else:
            # Lower quality - use enhanced processing
            return await self.quality_data_collector.from_screenshot_quality_aware(
                ign=ign,
                image_path=image_path
            )
    
    async def _performance_first_processing(self, image_path: str, ign: str,
                                          quality_assessment) -> Dict[str, Any]:
        """Process with performance as primary concern."""
        # Use fastest available processing regardless of quality
        return self.from_screenshot(ign, image_path)
    
    async def _adaptive_processing(self, image_path: str, ign: str,
                                 quality_assessment) -> Dict[str, Any]:
        """Process with adaptive balance of quality and performance."""
        quality_metrics = quality_assessment.quality_metrics
        adaptive_config = quality_assessment.adaptive_processing_config
        
        # Balance quality needs with performance requirements
        if quality_metrics.overall_score >= 0.7:
            # Good quality - prioritize performance
            processing_method = "standard_enhanced"
        elif quality_metrics.overall_score >= 0.5:
            # Fair quality - balance quality and performance
            processing_method = "quality_enhanced"
        else:
            # Poor quality - prioritize quality recovery
            processing_method = "quality_recovery"
        
        self.integration_stats['adaptive_processing_used'] += 1
        
        # Use quality-aware data collector
        return await self.quality_data_collector.from_screenshot_quality_aware(
            ign=ign,
            image_path=image_path
        )
    
    async def _fallback_processing(self, image_path: str, ign: str) -> Dict[str, Any]:
        """Fallback processing without quality assessment."""
        logger.info("🔄 Using fallback processing")
        return self.from_screenshot(ign, image_path)
    
    def _apply_quality_adjustments(self, result: Dict[str, Any], quality_assessment) -> Dict[str, Any]:
        """Apply quality-based adjustments to processing result."""
        quality_metrics = quality_assessment.quality_metrics
        
        # Adjust confidence scores based on quality
        if 'data' in result and isinstance(result['data'], dict):
            # Apply quality-based confidence scaling
            confidence_factor = quality_metrics.confidence
            
            # Add quality metadata to result data
            result['data']['quality_metadata'] = {
                'quality_score': quality_metrics.overall_score,
                'quality_level': quality_metrics.quality_level.name,
                'confidence_factor': confidence_factor,
                'processing_strategy': quality_metrics.processing_strategy.name
            }
        
        return result
    
    def _get_applied_optimizations(self, quality_assessment) -> List[str]:
        """Get list of optimizations applied based on quality."""
        optimizations = []
        
        quality_level = quality_assessment.quality_metrics.quality_level
        strategy = quality_assessment.quality_metrics.processing_strategy
        
        if strategy == ProcessingStrategy.ENHANCED:
            optimizations.append("Enhanced preprocessing applied")
        elif strategy == ProcessingStrategy.AGGRESSIVE:
            optimizations.append("Aggressive quality recovery applied")
        elif strategy == ProcessingStrategy.RECOVERY:
            optimizations.append("Maximum quality recovery attempted")
        
        if quality_level in [QualityLevel.POOR, QualityLevel.UNUSABLE]:
            optimizations.append("Low-quality image handling activated")
        
        return optimizations
    
    def _get_confidence_adjustments(self, quality_assessment) -> Dict[str, float]:
        """Get confidence adjustments applied."""
        quality_metrics = quality_assessment.quality_metrics
        
        return {
            'quality_confidence_factor': quality_metrics.confidence,
            'overall_quality_impact': quality_metrics.overall_score,
            'dimension_impacts': {
                dim: score for dim, score in quality_metrics.dimension_scores.items()
                if score < 0.7  # Only show dimensions that impact confidence
            }
        }
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration statistics."""
        stats = self.integration_stats.copy()
        
        # Add quality engine stats if available
        if self.quality_engine:
            stats['quality_engine'] = self.quality_engine.get_comprehensive_stats()
        
        return stats


# Global integration manager
quality_integration_manager = QualityAwareIntegrationManager()


def get_quality_integration_manager() -> QualityAwareIntegrationManager:
    """Get the global quality integration manager."""
    return quality_integration_manager


# Convenience functions for easy integration
async def assess_and_process_screenshot(image_path: str, 
                                      ign: str,
                                      user_id: str = "anonymous",
                                      processing_mode: str = "adaptive") -> Dict[str, Any]:
    """
    Convenience function for quality-aware screenshot processing.
    
    Args:
        image_path: Path to screenshot
        ign: Player IGN
        user_id: User ID
        processing_mode: Processing mode
        
    Returns:
        Processing result with quality intelligence
    """
    manager = get_quality_integration_manager()
    return await manager.process_screenshot_with_quality_intelligence(
        image_path=image_path,
        ign=ign,
        user_id=user_id,
        processing_mode=processing_mode
    )


def quality_gate_check(min_quality: float = 0.4):
    """Decorator for quality gate checking."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            image_path = kwargs.get('image_path') or (args[0] if args else None)
            
            if image_path and IMPORTS_AVAILABLE:
                engine = IntelligentQualityAssessmentEngine()
                assessment = await engine.assess_screenshot_quality(image_path)
                
                if assessment.quality_metrics.overall_score < min_quality:
                    return {
                        'success': False,
                        'blocked_by_quality_gate': True,
                        'quality_score': assessment.quality_metrics.overall_score,
                        'minimum_required': min_quality,
                        'user_guidance': assessment.user_guidance
                    }
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test quality integration
    async def test_quality_integration():
        """Test quality integration functionality."""
        logger.info("🧪 Testing Quality Assessment Integration")
        
        # Test integration manager
        manager = QualityAwareIntegrationManager()
        
        # Create test image
        import cv2
        import numpy as np
        
        test_image = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        test_path = "temp/test_integration_image.png"
        os.makedirs("temp", exist_ok=True)
        cv2.imwrite(test_path, test_image)
        
        # Test quality-aware processing
        result = await manager.process_screenshot_with_quality_intelligence(
            image_path=test_path,
            ign="TestPlayer",
            user_id="test_user",
            processing_mode="adaptive"
        )
        
        logger.info(f"📊 Integration test result: {result.get('success', False)}")
        
        if 'quality_intelligence' in result:
            qi = result['quality_intelligence']
            logger.info(f"   - Quality score: {qi['quality_score']:.3f}")
            logger.info(f"   - Processing strategy: {qi['processing_strategy']}")
        
        # Get statistics
        stats = manager.get_integration_stats()
        logger.info(f"📈 Integration stats: {json.dumps(stats, indent=2, default=str)}")
        
        # Cleanup
        if os.path.exists(test_path):
            os.remove(test_path)
    
    import json
    from functools import wraps
    asyncio.run(test_quality_integration())
