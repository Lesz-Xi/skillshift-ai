"""
Enhanced OCR Processor - Task 3: OCR Performance Enhancement

This module implements advanced OCR processing with:
- Advanced image preprocessing pipeline
- Multi-model OCR ensemble (EasyOCR + Tesseract)
- Game-specific optimization for MLBB screenshots
- Confidence scoring and quality validation
- Performance monitoring and caching

Target: 40% → 80%+ OCR reliability improvement
"""

import logging
import time
import hashlib
import os
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import threading
import json

import cv2
import numpy as np
import easyocr
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class PreprocessingMethod(Enum):
    """Available preprocessing methods for OCR enhancement."""
    BASIC = "basic"
    ADVANCED = "advanced"
    GAME_SPECIFIC = "game_specific"
    ADAPTIVE = "adaptive"
    ENSEMBLE = "ensemble"


class OCREngine(Enum):
    """Available OCR engines."""
    EASYOCR = "easyocr"
    TESSERACT = "tesseract"
    ENSEMBLE = "ensemble"


@dataclass
class OCRResult:
    """Enhanced OCR result with confidence and metadata."""
    text: str
    confidence: float
    bbox: List[List[int]]  # Bounding box coordinates
    engine: str
    preprocessing_method: str
    processing_time: float
    metadata: Dict[str, Any]


@dataclass
class EnhancedOCRResponse:
    """Complete OCR processing response."""
    success: bool
    results: List[OCRResult]
    ensemble_confidence: float
    processing_time: float
    preprocessing_applied: List[str]
    quality_score: float
    raw_engine_results: Dict[str, Any]
    error: Optional[str] = None


class GameSpecificProcessor:
    """MLBB-specific image preprocessing optimizations."""
    
    def __init__(self):
        self.mlbb_text_regions = {
            'player_names': {'y_range': (0.3, 0.8), 'font_size_range': (12, 24)},
            'stats': {'y_range': (0.3, 0.8), 'font_size_range': (10, 18)},
            'hero_names': {'y_range': (0.2, 0.9), 'font_size_range': (10, 16)},
            'damage_numbers': {'y_range': (0.3, 0.8), 'font_size_range': (8, 14)}
        }
    
    def detect_mlbb_ui_regions(self, image: np.ndarray) -> Dict[str, Tuple[int, int, int, int]]:
        """Detect MLBB-specific UI regions for targeted processing."""
        height, width = image.shape[:2]
        
        # Define MLBB post-match screenshot regions
        regions = {
            'scoreboard': (int(width * 0.1), int(height * 0.25), 
                          int(width * 0.9), int(height * 0.8)),
            'player_stats': (int(width * 0.15), int(height * 0.3), 
                           int(width * 0.85), int(height * 0.75)),
            'hero_section': (int(width * 0.05), int(height * 0.3), 
                           int(width * 0.25), int(height * 0.75)),
            'kda_section': (int(width * 0.25), int(height * 0.3), 
                          int(width * 0.45), int(height * 0.75)),
            'damage_section': (int(width * 0.45), int(height * 0.3), 
                             int(width * 0.85), int(height * 0.75))
        }
        
        return regions
    
    def enhance_for_mlbb_text(self, image: np.ndarray, region_type: str = "general") -> np.ndarray:
        """Apply MLBB-specific text enhancement."""
        
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # MLBB-specific optimizations
        if region_type == "player_names":
            # Player names often have specific font and background
            enhanced = self._enhance_player_names(gray)
        elif region_type == "stats":
            # Numbers and stats have different characteristics
            enhanced = self._enhance_stats_numbers(gray)
        elif region_type == "hero_names":
            # Hero names may have special styling
            enhanced = self._enhance_hero_names(gray)
        else:
            # General MLBB text enhancement
            enhanced = self._general_mlbb_enhancement(gray)
        
        return enhanced
    
    def _enhance_player_names(self, gray: np.ndarray) -> np.ndarray:
        """Enhance player name text regions."""
        # Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Morphological operations to clean text
        kernel = np.ones((1, 1), np.uint8)
        enhanced = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
        
        # Gaussian blur to smooth text
        enhanced = cv2.GaussianBlur(enhanced, (1, 1), 0)
        
        return enhanced
    
    def _enhance_stats_numbers(self, gray: np.ndarray) -> np.ndarray:
        """Enhance numeric statistics."""
        # Bilateral filter to preserve edges while reducing noise
        enhanced = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Adaptive threshold for better number recognition
        enhanced = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Invert if text is white on dark background
        if np.mean(enhanced) < 127:
            enhanced = cv2.bitwise_not(enhanced)
        
        return enhanced
    
    def _enhance_hero_names(self, gray: np.ndarray) -> np.ndarray:
        """Enhance hero name text."""
        # Unsharp masking for text sharpening
        gaussian = cv2.GaussianBlur(gray, (9, 9), 10.0)
        enhanced = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)
        
        # Morphological gradient to enhance text edges
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        enhanced = cv2.morphologyEx(enhanced, cv2.MORPH_GRADIENT, kernel)
        
        return enhanced
    
    def _general_mlbb_enhancement(self, gray: np.ndarray) -> np.ndarray:
        """General MLBB text enhancement."""
        # Multi-step enhancement pipeline
        
        # Step 1: Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # Step 2: Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(denoised)
        
        # Step 3: Sharpening
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(contrast_enhanced, -1, kernel)
        
        # Step 4: Final smoothing
        final = cv2.bilateralFilter(sharpened, 5, 80, 80)
        
        return final


class AdvancedImagePreprocessor:
    """Advanced image preprocessing pipeline for OCR enhancement."""
    
    def __init__(self):
        self.game_processor = GameSpecificProcessor()
        self.preprocessing_cache = {}
        self.cache_lock = threading.Lock()
    
    def preprocess_image(
        self, 
        image: np.ndarray, 
        method: PreprocessingMethod = PreprocessingMethod.ADVANCED,
        region_type: str = "general"
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Apply advanced preprocessing to enhance OCR accuracy.
        
        Returns:
            Tuple of (processed_image, metadata)
        """
        start_time = time.time()
        
        # Generate cache key
        image_hash = hashlib.md5(image.tobytes()).hexdigest()[:8]
        cache_key = f"{image_hash}_{method.value}_{region_type}"
        
        # Check cache
        with self.cache_lock:
            if cache_key in self.preprocessing_cache:
                cached_result, cached_metadata = self.preprocessing_cache[cache_key]
                cached_metadata['from_cache'] = True
                return cached_result.copy(), cached_metadata
        
        metadata = {
            'method': method.value,
            'region_type': region_type,
            'original_shape': image.shape,
            'processing_time': 0,
            'steps_applied': [],
            'from_cache': False
        }
        
        try:
            if method == PreprocessingMethod.BASIC:
                processed = self._basic_preprocessing(image, metadata)
            elif method == PreprocessingMethod.ADVANCED:
                processed = self._advanced_preprocessing(image, metadata)
            elif method == PreprocessingMethod.GAME_SPECIFIC:
                processed = self._game_specific_preprocessing(image, region_type, metadata)
            elif method == PreprocessingMethod.ADAPTIVE:
                processed = self._adaptive_preprocessing(image, metadata)
            elif method == PreprocessingMethod.ENSEMBLE:
                processed = self._ensemble_preprocessing(image, region_type, metadata)
            else:
                processed = image.copy()
                metadata['steps_applied'].append('no_preprocessing')
            
            metadata['processing_time'] = time.time() - start_time
            metadata['final_shape'] = processed.shape
            
            # Cache result
            with self.cache_lock:
                if len(self.preprocessing_cache) < 100:  # Limit cache size
                    self.preprocessing_cache[cache_key] = (processed.copy(), metadata.copy())
            
            return processed, metadata
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            metadata['error'] = str(e)
            return image.copy(), metadata
    
    def _basic_preprocessing(self, image: np.ndarray, metadata: Dict[str, Any]) -> np.ndarray:
        """Basic preprocessing pipeline."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            metadata['steps_applied'].append('grayscale_conversion')
        else:
            gray = image.copy()
        
        # Simple denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        metadata['steps_applied'].append('denoising')
        
        return denoised
    
    def _advanced_preprocessing(self, image: np.ndarray, metadata: Dict[str, Any]) -> np.ndarray:
        """Advanced preprocessing pipeline with multiple enhancement techniques."""
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            metadata['steps_applied'].append('grayscale_conversion')
        else:
            gray = image.copy()
        
        # Step 1: Noise reduction
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        metadata['steps_applied'].append('bilateral_filtering')
        
        # Step 2: Contrast enhancement using CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(denoised)
        metadata['steps_applied'].append('clahe_enhancement')
        
        # Step 3: Sharpening
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(contrast_enhanced, -1, kernel)
        metadata['steps_applied'].append('unsharp_masking')
        
        # Step 4: Morphological operations
        kernel = np.ones((2, 2), np.uint8)
        morph_enhanced = cv2.morphologyEx(sharpened, cv2.MORPH_CLOSE, kernel)
        metadata['steps_applied'].append('morphological_closing')
        
        # Step 5: Final smoothing
        final = cv2.GaussianBlur(morph_enhanced, (1, 1), 0)
        metadata['steps_applied'].append('gaussian_smoothing')
        
        return final
    
    def _game_specific_preprocessing(
        self, 
        image: np.ndarray, 
        region_type: str, 
        metadata: Dict[str, Any]
    ) -> np.ndarray:
        """MLBB-specific preprocessing."""
        processed = self.game_processor.enhance_for_mlbb_text(image, region_type)
        metadata['steps_applied'].append(f'mlbb_specific_{region_type}')
        return processed
    
    def _adaptive_preprocessing(self, image: np.ndarray, metadata: Dict[str, Any]) -> np.ndarray:
        """Adaptive preprocessing based on image characteristics."""
        
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Analyze image characteristics
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)
        
        metadata['image_analysis'] = {
            'mean_brightness': float(mean_brightness),
            'std_brightness': float(std_brightness)
        }
        
        # Adaptive processing based on image characteristics
        if mean_brightness < 100:  # Dark image
            # Enhance brightness and contrast
            enhanced = cv2.convertScaleAbs(gray, alpha=1.5, beta=30)
            metadata['steps_applied'].append('brightness_enhancement')
        elif mean_brightness > 200:  # Bright image
            # Reduce brightness, enhance contrast
            enhanced = cv2.convertScaleAbs(gray, alpha=1.2, beta=-20)
            metadata['steps_applied'].append('brightness_reduction')
        else:
            enhanced = gray.copy()
        
        # Apply contrast enhancement based on standard deviation
        if std_brightness < 50:  # Low contrast
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(enhanced)
            metadata['steps_applied'].append('high_contrast_enhancement')
        else:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(enhanced)
            metadata['steps_applied'].append('standard_contrast_enhancement')
        
        return enhanced
    
    def _ensemble_preprocessing(
        self, 
        image: np.ndarray, 
        region_type: str, 
        metadata: Dict[str, Any]
    ) -> List[np.ndarray]:
        """Generate multiple preprocessing variants for ensemble processing."""
        variants = []
        
        # Basic variant
        basic, _ = self.preprocess_image(image, PreprocessingMethod.BASIC, region_type)
        variants.append(basic)
        
        # Advanced variant
        advanced, _ = self.preprocess_image(image, PreprocessingMethod.ADVANCED, region_type)
        variants.append(advanced)
        
        # Game-specific variant
        game_specific, _ = self.preprocess_image(image, PreprocessingMethod.GAME_SPECIFIC, region_type)
        variants.append(game_specific)
        
        # Adaptive variant
        adaptive, _ = self.preprocess_image(image, PreprocessingMethod.ADAPTIVE, region_type)
        variants.append(adaptive)
        
        metadata['steps_applied'].append('ensemble_variants_generated')
        metadata['variant_count'] = len(variants)
        
        return variants


class MultiModelOCREngine:
    """Multi-model OCR engine with EasyOCR and Tesseract ensemble."""
    
    def __init__(self):
        self.easyocr_reader = None
        self.tesseract_config = '--oem 3 --psm 6'
        self.initialization_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def initialize_engines(self):
        """Initialize OCR engines with lazy loading."""
        if self.easyocr_reader is None:
            with self.initialization_lock:
                if self.easyocr_reader is None:
                    logger.info("🔄 Initializing EasyOCR engine...")
                    start_time = time.time()
                    self.easyocr_reader = easyocr.Reader(
                        ['en'], 
                        gpu=False, 
                        verbose=False,
                        model_storage_directory=None,
                        download_enabled=True
                    )
                    init_time = time.time() - start_time
                    logger.info(f"✅ EasyOCR initialized in {init_time:.3f}s")
    
    async def process_with_ensemble(
        self, 
        image: np.ndarray, 
        engine: OCREngine = OCREngine.ENSEMBLE,
        confidence_threshold: float = 0.5
    ) -> List[OCRResult]:
        """Process image with OCR ensemble."""
        
        self.initialize_engines()
        
        results = []
        start_time = time.time()
        
        if engine == OCREngine.EASYOCR or engine == OCREngine.ENSEMBLE:
            easyocr_results = await self._process_with_easyocr(image)
            results.extend(easyocr_results)
        
        if engine == OCREngine.TESSERACT or engine == OCREngine.ENSEMBLE:
            tesseract_results = await self._process_with_tesseract(image)
            results.extend(tesseract_results)
        
        # Filter by confidence threshold
        filtered_results = [r for r in results if r.confidence >= confidence_threshold]
        
        # If ensemble mode, perform result fusion
        if engine == OCREngine.ENSEMBLE and len(filtered_results) > 1:
            fused_results = self._fuse_ocr_results(filtered_results)
            return fused_results
        
        return filtered_results
    
    async def _process_with_easyocr(self, image: np.ndarray) -> List[OCRResult]:
        """Process image with EasyOCR."""
        start_time = time.time()
        
        try:
            # Run EasyOCR in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            raw_results = await loop.run_in_executor(
                self.executor,
                self.easyocr_reader.readtext,
                image,
                True  # detail=True
            )
            
            processing_time = time.time() - start_time
            
            results = []
            for bbox, text, confidence in raw_results:
                if text.strip():  # Only include non-empty text
                    result = OCRResult(
                        text=text.strip(),
                        confidence=float(confidence),
                        bbox=bbox,
                        engine="easyocr",
                        preprocessing_method="",
                        processing_time=processing_time,
                        metadata={
                            "raw_confidence": confidence,
                            "text_length": len(text.strip())
                        }
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"EasyOCR processing failed: {e}")
            return []
    
    async def _process_with_tesseract(self, image: np.ndarray) -> List[OCRResult]:
        """Process image with Tesseract."""
        start_time = time.time()
        
        try:
            # Convert numpy array to PIL Image for Tesseract
            if len(image.shape) == 3:
                pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                pil_image = Image.fromarray(image)
            
            # Run Tesseract in thread pool
            loop = asyncio.get_event_loop()
            
            # Get text with bounding boxes
            data = await loop.run_in_executor(
                self.executor,
                lambda: pytesseract.image_to_data(
                    pil_image, 
                    config=self.tesseract_config, 
                    output_type=pytesseract.Output.DICT
                )
            )
            
            processing_time = time.time() - start_time
            
            results = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                confidence = float(data['conf'][i]) / 100.0  # Convert to 0-1 range
                
                if text and confidence > 0:  # Only include valid text with confidence
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
                    
                    result = OCRResult(
                        text=text,
                        confidence=confidence,
                        bbox=bbox,
                        engine="tesseract",
                        preprocessing_method="",
                        processing_time=processing_time,
                        metadata={
                            "raw_confidence": data['conf'][i],
                            "word_num": data['word_num'][i],
                            "block_num": data['block_num'][i]
                        }
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Tesseract processing failed: {e}")
            return []
    
    def _fuse_ocr_results(self, results: List[OCRResult]) -> List[OCRResult]:
        """Fuse results from multiple OCR engines."""
        # Group results by spatial proximity and text similarity
        fused_results = []
        used_indices = set()
        
        for i, result1 in enumerate(results):
            if i in used_indices:
                continue
            
            # Find similar results from other engines
            similar_results = [result1]
            used_indices.add(i)
            
            for j, result2 in enumerate(results):
                if j <= i or j in used_indices:
                    continue
                
                # Check spatial proximity and text similarity
                if (self._are_spatially_close(result1.bbox, result2.bbox) and
                    self._are_texts_similar(result1.text, result2.text)):
                    similar_results.append(result2)
                    used_indices.add(j)
            
            # Fuse similar results
            if len(similar_results) > 1:
                fused_result = self._create_fused_result(similar_results)
                fused_results.append(fused_result)
            else:
                fused_results.append(result1)
        
        return fused_results
    
    def _are_spatially_close(self, bbox1: List[List[int]], bbox2: List[List[int]], threshold: float = 50) -> bool:
        """Check if two bounding boxes are spatially close."""
        # Calculate centers
        center1 = np.mean(bbox1, axis=0)
        center2 = np.mean(bbox2, axis=0)
        
        # Calculate distance
        distance = np.linalg.norm(center1 - center2)
        
        return distance < threshold
    
    def _are_texts_similar(self, text1: str, text2: str, threshold: float = 0.7) -> bool:
        """Check if two texts are similar."""
        from difflib import SequenceMatcher
        
        similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        return similarity >= threshold
    
    def _create_fused_result(self, results: List[OCRResult]) -> OCRResult:
        """Create a fused result from multiple similar results."""
        # Use the result with highest confidence as base
        best_result = max(results, key=lambda r: r.confidence)
        
        # Calculate ensemble confidence (weighted average)
        total_weight = sum(r.confidence for r in results)
        ensemble_confidence = total_weight / len(results)
        
        # Combine engines information
        engines = list(set(r.engine for r in results))
        
        return OCRResult(
            text=best_result.text,
            confidence=ensemble_confidence,
            bbox=best_result.bbox,
            engine=f"ensemble({','.join(engines)})",
            preprocessing_method=best_result.preprocessing_method,
            processing_time=sum(r.processing_time for r in results) / len(results),
            metadata={
                "fused_from": len(results),
                "individual_confidences": [r.confidence for r in results],
                "engines_used": engines
            }
        )


class QualityValidator:
    """Validates OCR quality and provides improvement suggestions."""
    
    def __init__(self):
        self.quality_thresholds = {
            'excellent': 0.9,
            'good': 0.7,
            'fair': 0.5,
            'poor': 0.3
        }
    
    def assess_quality(
        self, 
        image: np.ndarray, 
        ocr_results: List[OCRResult]
    ) -> Dict[str, Any]:
        """Assess the quality of OCR results and image."""
        
        image_quality = self._assess_image_quality(image)
        ocr_quality = self._assess_ocr_quality(ocr_results)
        
        overall_score = (image_quality['score'] + ocr_quality['score']) / 2
        
        quality_level = 'poor'
        for level, threshold in sorted(self.quality_thresholds.items(), 
                                     key=lambda x: x[1], reverse=True):
            if overall_score >= threshold:
                quality_level = level
                break
        
        return {
            'overall_score': overall_score,
            'quality_level': quality_level,
            'image_quality': image_quality,
            'ocr_quality': ocr_quality,
            'recommendations': self._generate_recommendations(image_quality, ocr_quality)
        }
    
    def _assess_image_quality(self, image: np.ndarray) -> Dict[str, Any]:
        """Assess image quality metrics."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Calculate various quality metrics
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()  # Sharpness
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)
        
        # Normalize metrics to 0-1 scale
        sharpness_score = min(laplacian_var / 1000, 1.0)  # Normalize sharpness
        brightness_score = 1.0 - abs(mean_brightness - 127.5) / 127.5  # Ideal brightness ~127.5
        contrast_score = min(std_brightness / 64, 1.0)  # Normalize contrast
        
        overall_score = (sharpness_score + brightness_score + contrast_score) / 3
        
        return {
            'score': overall_score,
            'sharpness': sharpness_score,
            'brightness': brightness_score,
            'contrast': contrast_score,
            'metrics': {
                'laplacian_variance': laplacian_var,
                'mean_brightness': mean_brightness,
                'std_brightness': std_brightness
            }
        }
    
    def _assess_ocr_quality(self, ocr_results: List[OCRResult]) -> Dict[str, Any]:
        """Assess OCR results quality."""
        if not ocr_results:
            return {
                'score': 0.0,
                'average_confidence': 0.0,
                'text_regions_found': 0,
                'high_confidence_ratio': 0.0
            }
        
        confidences = [r.confidence for r in ocr_results]
        average_confidence = np.mean(confidences)
        high_confidence_count = sum(1 for c in confidences if c >= 0.8)
        high_confidence_ratio = high_confidence_count / len(confidences)
        
        # Calculate text quality score
        text_lengths = [len(r.text) for r in ocr_results]
        avg_text_length = np.mean(text_lengths) if text_lengths else 0
        text_length_score = min(avg_text_length / 10, 1.0)  # Normalize
        
        overall_score = (average_confidence + high_confidence_ratio + text_length_score) / 3
        
        return {
            'score': overall_score,
            'average_confidence': average_confidence,
            'text_regions_found': len(ocr_results),
            'high_confidence_ratio': high_confidence_ratio,
            'average_text_length': avg_text_length
        }
    
    def _generate_recommendations(
        self, 
        image_quality: Dict[str, Any], 
        ocr_quality: Dict[str, Any]
    ) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        # Image quality recommendations
        if image_quality['sharpness'] < 0.5:
            recommendations.append("Image appears blurry - consider using sharpening preprocessing")
        
        if image_quality['brightness'] < 0.6:
            if image_quality['metrics']['mean_brightness'] < 100:
                recommendations.append("Image is too dark - consider brightness enhancement")
            else:
                recommendations.append("Image is too bright - consider brightness reduction")
        
        if image_quality['contrast'] < 0.5:
            recommendations.append("Low contrast detected - consider CLAHE enhancement")
        
        # OCR quality recommendations
        if ocr_quality['average_confidence'] < 0.6:
            recommendations.append("Low OCR confidence - try ensemble processing")
        
        if ocr_quality['text_regions_found'] < 5:
            recommendations.append("Few text regions detected - consider game-specific preprocessing")
        
        if ocr_quality['high_confidence_ratio'] < 0.5:
            recommendations.append("Many low-confidence detections - consider adaptive preprocessing")
        
        return recommendations


class EnhancedOCRProcessor:
    """
    Main enhanced OCR processor combining all components.
    
    Features:
    - Advanced image preprocessing pipeline
    - Multi-model OCR ensemble (EasyOCR + Tesseract)
    - Game-specific optimization for MLBB
    - Quality validation and scoring
    - Performance monitoring and caching
    """
    
    def __init__(self):
        self.preprocessor = AdvancedImagePreprocessor()
        self.ocr_engine = MultiModelOCREngine()
        self.quality_validator = QualityValidator()
        
        # Performance tracking
        self.processing_stats = {
            'total_processed': 0,
            'total_processing_time': 0,
            'cache_hits': 0,
            'quality_scores': []
        }
    
    async def process_image(
        self,
        image_path: str,
        preprocessing_method: PreprocessingMethod = PreprocessingMethod.ADVANCED,
        ocr_engine: OCREngine = OCREngine.ENSEMBLE,
        region_type: str = "general",
        confidence_threshold: float = 0.5
    ) -> EnhancedOCRResponse:
        """
        Process image with enhanced OCR pipeline.
        
        Args:
            image_path: Path to the image file
            preprocessing_method: Preprocessing method to use
            ocr_engine: OCR engine to use
            region_type: Type of region (for game-specific optimization)
            confidence_threshold: Minimum confidence threshold for results
            
        Returns:
            EnhancedOCRResponse with results and metadata
        """
        start_time = time.time()
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return EnhancedOCRResponse(
                    success=False,
                    results=[],
                    ensemble_confidence=0.0,
                    processing_time=0.0,
                    preprocessing_applied=[],
                    quality_score=0.0,
                    raw_engine_results={},
                    error=f"Failed to load image: {image_path}"
                )
            
            # Preprocess image
            if preprocessing_method == PreprocessingMethod.ENSEMBLE:
                # Process with multiple preprocessing variants
                processed_variants = self.preprocessor.preprocess_image(
                    image, preprocessing_method, region_type
                )[0]  # This returns a list for ensemble
                
                all_results = []
                preprocessing_applied = []
                
                # Process each variant
                for i, variant in enumerate(processed_variants):
                    variant_results = await self.ocr_engine.process_with_ensemble(
                        variant, ocr_engine, confidence_threshold
                    )
                    
                    # Tag results with preprocessing variant
                    for result in variant_results:
                        result.preprocessing_method = f"ensemble_variant_{i}"
                    
                    all_results.extend(variant_results)
                    preprocessing_applied.append(f"variant_{i}")
                
                # Fuse results from all variants
                if all_results:
                    final_results = self.ocr_engine._fuse_ocr_results(all_results)
                else:
                    final_results = []
                
                processed_image = processed_variants[0]  # Use first variant for quality assessment
                
            else:
                # Single preprocessing method
                processed_image, preprocessing_metadata = self.preprocessor.preprocess_image(
                    image, preprocessing_method, region_type
                )
                preprocessing_applied = preprocessing_metadata['steps_applied']
                
                # Perform OCR
                final_results = await self.ocr_engine.process_with_ensemble(
                    processed_image, ocr_engine, confidence_threshold
                )
                
                # Tag results with preprocessing method
                for result in final_results:
                    result.preprocessing_method = preprocessing_method.value
            
            # Assess quality
            quality_assessment = self.quality_validator.assess_quality(
                processed_image, final_results
            )
            
            # Calculate ensemble confidence
            if final_results:
                ensemble_confidence = np.mean([r.confidence for r in final_results])
            else:
                ensemble_confidence = 0.0
            
            processing_time = time.time() - start_time
            
            # Update statistics
            self._update_stats(processing_time, quality_assessment['overall_score'])
            
            return EnhancedOCRResponse(
                success=True,
                results=final_results,
                ensemble_confidence=ensemble_confidence,
                processing_time=processing_time,
                preprocessing_applied=preprocessing_applied,
                quality_score=quality_assessment['overall_score'],
                raw_engine_results={
                    'quality_assessment': quality_assessment,
                    'preprocessing_metadata': preprocessing_metadata if preprocessing_method != PreprocessingMethod.ENSEMBLE else {},
                    'total_text_regions': len(final_results)
                }
            )
            
        except Exception as e:
            logger.error(f"Enhanced OCR processing failed: {e}")
            return EnhancedOCRResponse(
                success=False,
                results=[],
                ensemble_confidence=0.0,
                processing_time=time.time() - start_time,
                preprocessing_applied=[],
                quality_score=0.0,
                raw_engine_results={},
                error=str(e)
            )
    
    def _update_stats(self, processing_time: float, quality_score: float):
        """Update processing statistics."""
        self.processing_stats['total_processed'] += 1
        self.processing_stats['total_processing_time'] += processing_time
        self.processing_stats['quality_scores'].append(quality_score)
        
        # Keep only last 100 quality scores
        if len(self.processing_stats['quality_scores']) > 100:
            self.processing_stats['quality_scores'] = self.processing_stats['quality_scores'][-100:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if self.processing_stats['total_processed'] == 0:
            return {'no_data': True}
        
        avg_processing_time = (
            self.processing_stats['total_processing_time'] / 
            self.processing_stats['total_processed']
        )
        
        avg_quality_score = np.mean(self.processing_stats['quality_scores'])
        
        return {
            'total_processed': self.processing_stats['total_processed'],
            'average_processing_time': avg_processing_time,
            'average_quality_score': avg_quality_score,
            'cache_hit_rate': (
                self.processing_stats['cache_hits'] / 
                self.processing_stats['total_processed']
            ) if self.processing_stats['total_processed'] > 0 else 0,
            'recent_quality_trend': np.mean(self.processing_stats['quality_scores'][-10:]) if len(self.processing_stats['quality_scores']) >= 10 else avg_quality_score
        }
    
    async def batch_process(
        self,
        image_paths: List[str],
        **kwargs
    ) -> List[EnhancedOCRResponse]:
        """Process multiple images in batch."""
        tasks = []
        for image_path in image_paths:
            task = self.process_image(image_path, **kwargs)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                error_response = EnhancedOCRResponse(
                    success=False,
                    results=[],
                    ensemble_confidence=0.0,
                    processing_time=0.0,
                    preprocessing_applied=[],
                    quality_score=0.0,
                    raw_engine_results={},
                    error=str(result)
                )
                processed_results.append(error_response)
            else:
                processed_results.append(result)
        
        return processed_results


# Convenience function for backward compatibility
async def process_image_enhanced(
    image_path: str,
    method: str = "advanced",
    engine: str = "ensemble",
    region_type: str = "general"
) -> Dict[str, Any]:
    """
    Convenience function for enhanced OCR processing.
    
    Returns results in format compatible with existing codebase.
    """
    processor = EnhancedOCRProcessor()
    
    # Convert string parameters to enums
    preprocessing_method = PreprocessingMethod(method.lower())
    ocr_engine = OCREngine(engine.lower())
    
    response = await processor.process_image(
        image_path=image_path,
        preprocessing_method=preprocessing_method,
        ocr_engine=ocr_engine,
        region_type=region_type
    )
    
    # Convert to legacy format
    legacy_results = []
    for result in response.results:
        # Convert bbox format
        bbox = result.bbox
        text = result.text
        confidence = result.confidence
        
        legacy_results.append((bbox, text, confidence))
    
    return {
        'success': response.success,
        'results': legacy_results,
        'metadata': {
            'ensemble_confidence': response.ensemble_confidence,
            'processing_time': response.processing_time,
            'quality_score': response.quality_score,
            'preprocessing_applied': response.preprocessing_applied,
            'error': response.error
        }
    }


if __name__ == "__main__":
    # Example usage and testing
    import asyncio
    
    async def test_enhanced_ocr():
        processor = EnhancedOCRProcessor()
        
        # Test with a sample image (replace with actual path)
        test_image = "test_screenshot.png"
        
        if os.path.exists(test_image):
            result = await processor.process_image(
                image_path=test_image,
                preprocessing_method=PreprocessingMethod.ENSEMBLE,
                ocr_engine=OCREngine.ENSEMBLE,
                region_type="general"
            )
            
            print(f"Processing successful: {result.success}")
            print(f"Found {len(result.results)} text regions")
            print(f"Ensemble confidence: {result.ensemble_confidence:.3f}")
            print(f"Quality score: {result.quality_score:.3f}")
            print(f"Processing time: {result.processing_time:.3f}s")
            
            for i, ocr_result in enumerate(result.results):
                print(f"Text {i+1}: '{ocr_result.text}' (confidence: {ocr_result.confidence:.3f})")
        
        else:
            print(f"Test image not found: {test_image}")
    
    # Run test
    # asyncio.run(test_enhanced_ocr())

