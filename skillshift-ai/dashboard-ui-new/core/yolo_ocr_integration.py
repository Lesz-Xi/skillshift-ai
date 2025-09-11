#!/usr/bin/env python3
"""
YOLO-OCR Integration System
===========================

Task 4: Custom YOLO Model Training - Integration Module

This module provides seamless integration between the custom YOLO model and
the existing OCR system, implementing fallback mechanisms and performance
optimization for 95%+ detection accuracy.

Features:
- Intelligent YOLO-OCR coordination
- Region-of-interest optimization using YOLO detections
- Fallback mechanisms to traditional CV methods
- Performance monitoring and A/B testing
- Real-time inference optimization
"""

import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import json

import cv2
import numpy as np
from pathlib import Path

# Import existing systems
try:
    from .enhanced_ocr_processor import EnhancedOCRProcessor, PreprocessingMethod, OCREngine
    from .services.yolo_detection_service import YOLODetectionService
    from ..models.mlbb_detection_v2 import DetectionClass, EnhancedMLBBYOLOTrainer
    IMPORTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Some imports not available: {e}")
    IMPORTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class IntegrationMode(Enum):
    """Integration modes for YOLO-OCR coordination."""
    YOLO_FIRST = "yolo_first"  # Use YOLO for region detection, then OCR
    OCR_FIRST = "ocr_first"    # Use OCR first, YOLO as fallback
    PARALLEL = "parallel"      # Run both simultaneously
    ADAPTIVE = "adaptive"      # Choose based on conditions
    ENSEMBLE = "ensemble"      # Combine results from both


@dataclass
class DetectionRegion:
    """Region of interest for OCR processing."""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    class_name: str
    confidence: float
    priority: int = 1  # Higher = more important
    ocr_method: str = "advanced"  # OCR preprocessing method to use


@dataclass
class IntegrationResult:
    """Combined YOLO-OCR result."""
    success: bool
    yolo_detections: List[Dict[str, Any]]
    ocr_results: List[Dict[str, Any]]
    combined_confidence: float
    processing_time: float
    method_used: str
    regions_processed: int
    fallback_triggered: bool = False
    error: Optional[str] = None


class YOLOOCRIntegrator:
    """
    Advanced integration system combining YOLO detection with OCR processing.
    
    This system implements intelligent coordination between YOLO object detection
    and OCR text recognition for optimal MLBB screenshot analysis.
    """
    
    def __init__(self, 
                 yolo_model_path: str = "models/mlbb_yolo_best.pt",
                 integration_mode: IntegrationMode = IntegrationMode.ADAPTIVE,
                 enable_fallback: bool = True):
        """
        Initialize the YOLO-OCR integration system.
        
        Args:
            yolo_model_path: Path to trained YOLO model
            integration_mode: How to coordinate YOLO and OCR
            enable_fallback: Whether to enable fallback mechanisms
        """
        self.yolo_model_path = yolo_model_path
        self.integration_mode = integration_mode
        self.enable_fallback = enable_fallback
        
        # Initialize components
        if IMPORTS_AVAILABLE:
            self.yolo_service = YOLODetectionService(
                model_path=yolo_model_path,
                confidence_threshold=0.5,
                enable_fallback=enable_fallback
            )
            self.ocr_processor = EnhancedOCRProcessor()
        else:
            self.yolo_service = None
            self.ocr_processor = None
            logger.warning("⚠️ Integration components not available")
        
        # Performance tracking
        self.integration_stats = {
            'total_processed': 0,
            'yolo_used': 0,
            'ocr_used': 0,
            'fallback_triggered': 0,
            'avg_processing_time': 0.0,
            'accuracy_improvements': [],
            'method_performance': {
                'yolo_first': {'count': 0, 'avg_time': 0.0, 'avg_confidence': 0.0},
                'ocr_first': {'count': 0, 'avg_time': 0.0, 'avg_confidence': 0.0},
                'parallel': {'count': 0, 'avg_time': 0.0, 'avg_confidence': 0.0},
                'adaptive': {'count': 0, 'avg_time': 0.0, 'avg_confidence': 0.0},
                'ensemble': {'count': 0, 'avg_time': 0.0, 'avg_confidence': 0.0}
            }
        }
        
        # Region mapping for OCR optimization
        self.region_ocr_mapping = {
            'hero_portrait': {'method': 'game_specific', 'region_type': 'hero_names'},
            'kda_box': {'method': 'advanced', 'region_type': 'stats'},
            'damage_box': {'method': 'advanced', 'region_type': 'stats'},
            'gold_box': {'method': 'advanced', 'region_type': 'stats'},
            'player_name': {'method': 'game_specific', 'region_type': 'player_names'},
            'hero_name': {'method': 'game_specific', 'region_type': 'hero_names'},
            'mvp_badge': {'method': 'basic', 'region_type': 'general'},
            'medal_bronze': {'method': 'basic', 'region_type': 'general'},
            'medal_silver': {'method': 'basic', 'region_type': 'general'},
            'medal_gold': {'method': 'basic', 'region_type': 'general'}
        }
        
        logger.info(f"🔗 YOLO-OCR Integration initialized")
        logger.info(f"📊 Mode: {integration_mode.value}")
        logger.info(f"🛡️ Fallback enabled: {enable_fallback}")
    
    async def process_screenshot(self, 
                               image_path: str,
                               target_ign: str = None,
                               force_mode: Optional[IntegrationMode] = None) -> IntegrationResult:
        """
        Process MLBB screenshot using integrated YOLO-OCR system.
        
        Args:
            image_path: Path to screenshot
            target_ign: Target player IGN for focused analysis
            force_mode: Override integration mode for this request
            
        Returns:
            Integration result with combined detections
        """
        start_time = time.time()
        mode = force_mode or self.integration_mode
        
        logger.info(f"🔍 Processing screenshot: {Path(image_path).name}")
        logger.info(f"🎯 Integration mode: {mode.value}")
        
        if not IMPORTS_AVAILABLE:
            return IntegrationResult(
                success=False,
                yolo_detections=[],
                ocr_results=[],
                combined_confidence=0.0,
                processing_time=time.time() - start_time,
                method_used="none",
                regions_processed=0,
                error="Integration components not available"
            )
        
        try:
            # Execute integration based on mode
            if mode == IntegrationMode.YOLO_FIRST:
                result = await self._process_yolo_first(image_path, target_ign)
            elif mode == IntegrationMode.OCR_FIRST:
                result = await self._process_ocr_first(image_path, target_ign)
            elif mode == IntegrationMode.PARALLEL:
                result = await self._process_parallel(image_path, target_ign)
            elif mode == IntegrationMode.ADAPTIVE:
                result = await self._process_adaptive(image_path, target_ign)
            elif mode == IntegrationMode.ENSEMBLE:
                result = await self._process_ensemble(image_path, target_ign)
            else:
                raise ValueError(f"Unknown integration mode: {mode}")
            
            # Update statistics
            self._update_integration_stats(result, mode)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Integration processing failed: {e}")
            return IntegrationResult(
                success=False,
                yolo_detections=[],
                ocr_results=[],
                combined_confidence=0.0,
                processing_time=time.time() - start_time,
                method_used=mode.value,
                regions_processed=0,
                error=str(e)
            )
    
    async def _process_yolo_first(self, image_path: str, target_ign: str) -> IntegrationResult:
        """Process using YOLO first, then targeted OCR."""
        start_time = time.time()
        
        # Step 1: YOLO detection
        yolo_results = self.yolo_service.detect_objects(image_path)
        yolo_detections = yolo_results.get('detections', [])
        
        # Step 2: Convert YOLO detections to OCR regions
        ocr_regions = self._convert_yolo_to_ocr_regions(yolo_detections, image_path)
        
        # Step 3: Process each region with appropriate OCR method
        ocr_results = []
        for region in ocr_regions:
            try:
                # Extract region from image
                region_image = self._extract_image_region(image_path, region.bbox)
                
                # Save region temporarily
                temp_path = f"temp/region_{int(time.time()*1000)}.jpg"
                os.makedirs("temp", exist_ok=True)
                cv2.imwrite(temp_path, region_image)
                
                # Process with appropriate OCR method
                preprocessing_method = getattr(PreprocessingMethod, region.ocr_method.upper(), PreprocessingMethod.ADVANCED)
                
                region_result = await self.ocr_processor.process_image(
                    image_path=temp_path,
                    preprocessing_method=preprocessing_method,
                    region_type=self.region_ocr_mapping.get(region.class_name, {}).get('region_type', 'general')
                )
                
                if region_result.success:
                    # Enhance result with region context
                    enhanced_result = {
                        'region_class': region.class_name,
                        'region_confidence': region.confidence,
                        'region_bbox': region.bbox,
                        'ocr_results': region_result.results,
                        'ocr_confidence': region_result.ensemble_confidence,
                        'quality_score': region_result.quality_score
                    }
                    ocr_results.append(enhanced_result)
                
                # Cleanup
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
            except Exception as e:
                logger.error(f"❌ Region OCR failed for {region.class_name}: {e}")
        
        # Calculate combined confidence
        combined_confidence = self._calculate_combined_confidence(yolo_detections, ocr_results)
        
        return IntegrationResult(
            success=True,
            yolo_detections=yolo_detections,
            ocr_results=ocr_results,
            combined_confidence=combined_confidence,
            processing_time=time.time() - start_time,
            method_used="yolo_first",
            regions_processed=len(ocr_regions)
        )
    
    async def _process_ocr_first(self, image_path: str, target_ign: str) -> IntegrationResult:
        """Process using OCR first, then YOLO as fallback if needed."""
        start_time = time.time()
        
        # Step 1: Full image OCR
        ocr_result = await self.ocr_processor.process_image(
            image_path=image_path,
            preprocessing_method=PreprocessingMethod.GAME_SPECIFIC,
            ocr_engine=OCREngine.ENSEMBLE
        )
        
        fallback_triggered = False
        yolo_detections = []
        
        # Step 2: Check if YOLO fallback is needed
        if (ocr_result.ensemble_confidence < 0.7 or 
            len(ocr_result.results) < 5):  # Low confidence or few detections
            
            logger.info("🔄 Triggering YOLO fallback due to low OCR performance")
            fallback_triggered = True
            
            # Run YOLO for additional context
            yolo_results = self.yolo_service.detect_objects(image_path)
            yolo_detections = yolo_results.get('detections', [])
        
        # Combine results
        ocr_results = [{
            'full_image_ocr': True,
            'ocr_results': ocr_result.results,
            'ocr_confidence': ocr_result.ensemble_confidence,
            'quality_score': ocr_result.quality_score,
            'preprocessing_applied': ocr_result.preprocessing_applied
        }]
        
        combined_confidence = ocr_result.ensemble_confidence
        if fallback_triggered and yolo_detections:
            # Boost confidence if YOLO confirms detections
            yolo_confidence = np.mean([d['confidence'] for d in yolo_detections])
            combined_confidence = min(1.0, combined_confidence + yolo_confidence * 0.2)
        
        return IntegrationResult(
            success=True,
            yolo_detections=yolo_detections,
            ocr_results=ocr_results,
            combined_confidence=combined_confidence,
            processing_time=time.time() - start_time,
            method_used="ocr_first",
            regions_processed=1,
            fallback_triggered=fallback_triggered
        )
    
    async def _process_parallel(self, image_path: str, target_ign: str) -> IntegrationResult:
        """Process using YOLO and OCR in parallel."""
        start_time = time.time()
        
        # Run both systems simultaneously
        yolo_task = asyncio.create_task(self._run_yolo_async(image_path))
        ocr_task = asyncio.create_task(self._run_ocr_async(image_path))
        
        # Wait for both to complete
        yolo_results, ocr_result = await asyncio.gather(yolo_task, ocr_task)
        
        yolo_detections = yolo_results.get('detections', [])
        
        # Combine and cross-validate results
        combined_results = self._cross_validate_results(yolo_detections, ocr_result.results)
        combined_confidence = self._calculate_cross_validated_confidence(yolo_detections, ocr_result)
        
        ocr_results = [{
            'parallel_ocr': True,
            'ocr_results': ocr_result.results,
            'ocr_confidence': ocr_result.ensemble_confidence,
            'quality_score': ocr_result.quality_score,
            'cross_validated': True,
            'validation_score': combined_results.get('validation_score', 0.0)
        }]
        
        return IntegrationResult(
            success=True,
            yolo_detections=yolo_detections,
            ocr_results=ocr_results,
            combined_confidence=combined_confidence,
            processing_time=time.time() - start_time,
            method_used="parallel",
            regions_processed=len(yolo_detections) + 1
        )
    
    async def _process_adaptive(self, image_path: str, target_ign: str) -> IntegrationResult:
        """Adaptively choose processing method based on image characteristics."""
        start_time = time.time()
        
        # Analyze image to determine best approach
        image_analysis = self._analyze_image_characteristics(image_path)
        
        # Choose method based on analysis
        if image_analysis['text_density'] > 0.3:
            # High text density - OCR first
            chosen_method = IntegrationMode.OCR_FIRST
        elif image_analysis['ui_elements_detected'] > 5:
            # Many UI elements - YOLO first
            chosen_method = IntegrationMode.YOLO_FIRST
        elif image_analysis['quality_score'] > 0.8:
            # High quality - parallel processing
            chosen_method = IntegrationMode.PARALLEL
        else:
            # Default to ensemble for difficult cases
            chosen_method = IntegrationMode.ENSEMBLE
        
        logger.info(f"🧠 Adaptive choice: {chosen_method.value} (quality: {image_analysis['quality_score']:.3f})")
        
        # Process using chosen method
        if chosen_method == IntegrationMode.OCR_FIRST:
            result = await self._process_ocr_first(image_path, target_ign)
        elif chosen_method == IntegrationMode.YOLO_FIRST:
            result = await self._process_yolo_first(image_path, target_ign)
        elif chosen_method == IntegrationMode.PARALLEL:
            result = await self._process_parallel(image_path, target_ign)
        else:
            result = await self._process_ensemble(image_path, target_ign)
        
        # Update method used
        result.method_used = f"adaptive_{chosen_method.value}"
        
        return result
    
    async def _process_ensemble(self, image_path: str, target_ign: str) -> IntegrationResult:
        """Process using ensemble of all methods."""
        start_time = time.time()
        
        # Run multiple processing methods
        methods = [
            self._process_yolo_first(image_path, target_ign),
            self._process_ocr_first(image_path, target_ign),
            self._process_parallel(image_path, target_ign)
        ]
        
        results = await asyncio.gather(*methods, return_exceptions=True)
        
        # Filter successful results
        successful_results = [r for r in results if isinstance(r, IntegrationResult) and r.success]
        
        if not successful_results:
            return IntegrationResult(
                success=False,
                yolo_detections=[],
                ocr_results=[],
                combined_confidence=0.0,
                processing_time=time.time() - start_time,
                method_used="ensemble",
                regions_processed=0,
                error="All ensemble methods failed"
            )
        
        # Combine results using ensemble voting
        ensemble_result = self._ensemble_vote(successful_results)
        ensemble_result.processing_time = time.time() - start_time
        ensemble_result.method_used = "ensemble"
        
        return ensemble_result
    
    def _convert_yolo_to_ocr_regions(self, yolo_detections: List[Dict], image_path: str) -> List[DetectionRegion]:
        """Convert YOLO detections to OCR processing regions."""
        regions = []
        
        for detection in yolo_detections:
            class_name = detection['class_name']
            confidence = detection['confidence']
            bbox_xyxy = detection['bbox_xyxy']
            
            # Skip non-text regions
            if class_name not in self.region_ocr_mapping:
                continue
            
            # Determine OCR method and priority
            ocr_config = self.region_ocr_mapping[class_name]
            
            # Set priority based on class importance
            priority = 1
            if class_name in ['player_name', 'kda_box', 'damage_box']:
                priority = 3  # High priority
            elif class_name in ['hero_name', 'gold_box']:
                priority = 2  # Medium priority
            
            region = DetectionRegion(
                bbox=tuple(map(int, bbox_xyxy)),
                class_name=class_name,
                confidence=confidence,
                priority=priority,
                ocr_method=ocr_config['method']
            )
            
            regions.append(region)
        
        # Sort by priority and confidence
        regions.sort(key=lambda r: (r.priority, r.confidence), reverse=True)
        
        return regions
    
    def _extract_image_region(self, image_path: str, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """Extract region from image."""
        image = cv2.imread(image_path)
        x1, y1, x2, y2 = bbox
        
        # Add padding
        padding = 5
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(image.shape[1], x2 + padding)
        y2 = min(image.shape[0], y2 + padding)
        
        return image[y1:y2, x1:x2]
    
    def _calculate_combined_confidence(self, yolo_detections: List[Dict], ocr_results: List[Dict]) -> float:
        """Calculate combined confidence from YOLO and OCR results."""
        if not yolo_detections and not ocr_results:
            return 0.0
        
        yolo_confidence = np.mean([d['confidence'] for d in yolo_detections]) if yolo_detections else 0.0
        ocr_confidence = np.mean([r.get('ocr_confidence', 0.0) for r in ocr_results]) if ocr_results else 0.0
        
        # Weighted combination
        if yolo_detections and ocr_results:
            return (yolo_confidence * 0.4 + ocr_confidence * 0.6)
        elif yolo_detections:
            return yolo_confidence * 0.8  # Slight penalty for missing OCR
        else:
            return ocr_confidence * 0.8  # Slight penalty for missing YOLO
    
    async def _run_yolo_async(self, image_path: str) -> Dict[str, Any]:
        """Run YOLO detection asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.yolo_service.detect_objects, image_path)
    
    async def _run_ocr_async(self, image_path: str):
        """Run OCR processing asynchronously."""
        return await self.ocr_processor.process_image(
            image_path=image_path,
            preprocessing_method=PreprocessingMethod.GAME_SPECIFIC,
            ocr_engine=OCREngine.ENSEMBLE
        )
    
    def _cross_validate_results(self, yolo_detections: List[Dict], ocr_results: List[Dict]) -> Dict[str, Any]:
        """Cross-validate YOLO and OCR results."""
        # Simple cross-validation based on spatial overlap and content matching
        validation_score = 0.0
        matches = 0
        
        # Check if YOLO detections align with OCR text regions
        for yolo_det in yolo_detections:
            yolo_bbox = yolo_det['bbox_xyxy']
            
            for ocr_result in ocr_results:
                if 'bbox' in ocr_result:
                    ocr_bbox = ocr_result['bbox']
                    
                    # Calculate IoU
                    iou = self._calculate_iou(yolo_bbox, ocr_bbox)
                    if iou > 0.3:  # Significant overlap
                        matches += 1
                        validation_score += iou
        
        if matches > 0:
            validation_score /= matches
        
        return {
            'validation_score': validation_score,
            'matches': matches,
            'total_yolo': len(yolo_detections),
            'total_ocr': len(ocr_results)
        }
    
    def _calculate_cross_validated_confidence(self, yolo_detections: List[Dict], ocr_result) -> float:
        """Calculate confidence with cross-validation boost."""
        base_confidence = self._calculate_combined_confidence(yolo_detections, [{'ocr_confidence': ocr_result.ensemble_confidence}])
        
        # Boost confidence if both systems agree
        if yolo_detections and ocr_result.results:
            agreement_bonus = min(0.2, len(yolo_detections) * 0.05)
            return min(1.0, base_confidence + agreement_bonus)
        
        return base_confidence
    
    def _analyze_image_characteristics(self, image_path: str) -> Dict[str, Any]:
        """Analyze image characteristics for adaptive processing."""
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate various characteristics
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])
        
        # Estimate text density (high edge density in regular patterns)
        text_density = min(edge_density * 3, 1.0)  # Rough approximation
        
        # Estimate UI elements (using simple blob detection)
        params = cv2.SimpleBlobDetector_Params()
        detector = cv2.SimpleBlobDetector_create(params)
        keypoints = detector.detect(gray)
        ui_elements_detected = len(keypoints)
        
        # Overall quality score
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        quality_score = min(laplacian_var / 1000, 1.0)
        
        return {
            'text_density': text_density,
            'ui_elements_detected': ui_elements_detected,
            'quality_score': quality_score,
            'edge_density': edge_density,
            'resolution': f"{image.shape[1]}x{image.shape[0]}"
        }
    
    def _ensemble_vote(self, results: List[IntegrationResult]) -> IntegrationResult:
        """Combine multiple integration results using ensemble voting."""
        if not results:
            return IntegrationResult(
                success=False,
                yolo_detections=[],
                ocr_results=[],
                combined_confidence=0.0,
                processing_time=0.0,
                method_used="ensemble",
                regions_processed=0
            )
        
        # Use the result with highest combined confidence
        best_result = max(results, key=lambda r: r.combined_confidence)
        
        # Combine all YOLO detections and remove duplicates
        all_yolo_detections = []
        for result in results:
            all_yolo_detections.extend(result.yolo_detections)
        
        # Simple deduplication based on class and spatial overlap
        unique_detections = self._deduplicate_detections(all_yolo_detections)
        
        # Combine OCR results
        all_ocr_results = []
        for result in results:
            all_ocr_results.extend(result.ocr_results)
        
        # Calculate ensemble confidence
        confidences = [r.combined_confidence for r in results]
        ensemble_confidence = np.mean(confidences) + (np.std(confidences) * 0.1)  # Boost for agreement
        ensemble_confidence = min(1.0, ensemble_confidence)
        
        return IntegrationResult(
            success=True,
            yolo_detections=unique_detections,
            ocr_results=all_ocr_results,
            combined_confidence=ensemble_confidence,
            processing_time=max(r.processing_time for r in results),
            method_used="ensemble",
            regions_processed=sum(r.regions_processed for r in results)
        )
    
    def _deduplicate_detections(self, detections: List[Dict]) -> List[Dict]:
        """Remove duplicate detections."""
        if not detections:
            return []
        
        unique = []
        for detection in detections:
            is_duplicate = False
            
            for existing in unique:
                if (detection['class_name'] == existing['class_name'] and
                    self._calculate_iou(detection['bbox_xyxy'], existing['bbox_xyxy']) > 0.5):
                    # Keep the one with higher confidence
                    if detection['confidence'] > existing['confidence']:
                        unique.remove(existing)
                        unique.append(detection)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(detection)
        
        return unique
    
    def _calculate_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate Intersection over Union of two bounding boxes."""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _update_integration_stats(self, result: IntegrationResult, mode: IntegrationMode):
        """Update integration statistics."""
        self.integration_stats['total_processed'] += 1
        
        if result.yolo_detections:
            self.integration_stats['yolo_used'] += 1
        
        if result.ocr_results:
            self.integration_stats['ocr_used'] += 1
        
        if result.fallback_triggered:
            self.integration_stats['fallback_triggered'] += 1
        
        # Update average processing time
        current_avg = self.integration_stats['avg_processing_time']
        new_avg = (current_avg + result.processing_time) / 2
        self.integration_stats['avg_processing_time'] = new_avg
        
        # Update method performance
        method_key = mode.value
        if method_key in self.integration_stats['method_performance']:
            method_stats = self.integration_stats['method_performance'][method_key]
            method_stats['count'] += 1
            method_stats['avg_time'] = (method_stats['avg_time'] + result.processing_time) / 2
            method_stats['avg_confidence'] = (method_stats['avg_confidence'] + result.combined_confidence) / 2
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get comprehensive integration statistics."""
        stats = self.integration_stats.copy()
        
        # Calculate usage percentages
        total = stats['total_processed']
        if total > 0:
            stats['yolo_usage_rate'] = stats['yolo_used'] / total
            stats['ocr_usage_rate'] = stats['ocr_used'] / total
            stats['fallback_rate'] = stats['fallback_triggered'] / total
        
        # Add configuration info
        stats['integration_mode'] = self.integration_mode.value
        stats['yolo_model_path'] = self.yolo_model_path
        stats['fallback_enabled'] = self.enable_fallback
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of integration system."""
        health_status = {
            'integration_system': 'healthy',
            'components': {},
            'last_check': time.time()
        }
        
        # Check YOLO service
        if self.yolo_service:
            yolo_health = self.yolo_service.health_check()
            health_status['components']['yolo'] = yolo_health
        else:
            health_status['components']['yolo'] = {'status': 'unavailable'}
        
        # Check OCR processor
        if self.ocr_processor:
            ocr_stats = self.ocr_processor.get_performance_stats()
            health_status['components']['ocr'] = {
                'status': 'healthy' if not ocr_stats.get('no_data') else 'unused',
                'stats': ocr_stats
            }
        else:
            health_status['components']['ocr'] = {'status': 'unavailable'}
        
        # Overall health
        component_statuses = [comp.get('status', 'unknown') for comp in health_status['components'].values()]
        if all(status in ['healthy', 'unused'] for status in component_statuses):
            health_status['integration_system'] = 'healthy'
        elif any(status == 'healthy' for status in component_statuses):
            health_status['integration_system'] = 'degraded'
        else:
            health_status['integration_system'] = 'unhealthy'
        
        return health_status


# Global integration instance
yolo_ocr_integrator = YOLOOCRIntegrator()


def get_yolo_ocr_integrator() -> YOLOOCRIntegrator:
    """Get the global YOLO-OCR integration instance."""
    return yolo_ocr_integrator


async def process_mlbb_screenshot_integrated(image_path: str, 
                                          target_ign: str = None,
                                          integration_mode: str = "adaptive") -> Dict[str, Any]:
    """
    Convenience function for integrated MLBB screenshot processing.
    
    Args:
        image_path: Path to MLBB screenshot
        target_ign: Target player IGN
        integration_mode: Integration mode to use
        
    Returns:
        Processing results
    """
    integrator = get_yolo_ocr_integrator()
    
    # Convert string mode to enum
    mode_mapping = {
        'yolo_first': IntegrationMode.YOLO_FIRST,
        'ocr_first': IntegrationMode.OCR_FIRST,
        'parallel': IntegrationMode.PARALLEL,
        'adaptive': IntegrationMode.ADAPTIVE,
        'ensemble': IntegrationMode.ENSEMBLE
    }
    
    mode = mode_mapping.get(integration_mode, IntegrationMode.ADAPTIVE)
    
    result = await integrator.process_screenshot(
        image_path=image_path,
        target_ign=target_ign,
        force_mode=mode
    )
    
    # Convert to legacy format for compatibility
    return {
        'success': result.success,
        'yolo_detections': result.yolo_detections,
        'ocr_results': result.ocr_results,
        'combined_confidence': result.combined_confidence,
        'processing_time': result.processing_time,
        'method_used': result.method_used,
        'regions_processed': result.regions_processed,
        'fallback_triggered': result.fallback_triggered,
        'error': result.error
    }
