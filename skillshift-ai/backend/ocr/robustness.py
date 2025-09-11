"""
OCR Mission 5: Robustness & Drift Hardening

This module implements drift guards, adaptive processing, and telemetry
for bulletproofing the pipeline against layout drift, resolution variance,
device filters, and hero skin changes.

Target: <500ms fast-path latency with no accuracy regressions.
"""

import cv2
import numpy as np
import logging
import json
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DriftTelemetry:
    """Drift telemetry data for monitoring and debugging."""
    row_variance: float
    anchors_used: List[str]
    ign_score: float
    hero_conf: float
    phash_dist: Optional[int]
    cache_hits: int
    stage_ms: Dict[str, float]
    drift_warnings: List[str]
    corrective_actions: List[str]


@dataclass
class RobustnessConfig:
    """Configuration for robustness features."""
    robust_mode: bool = True
    grid_variance_warn: float = 0.015
    grid_variance_correct: float = 0.03
    bbox_expand_pct: float = 0.03
    phash_threshold: int = 12
    use_sauvola_fallback: bool = True
    enable_drift_telemetry: bool = True
    min_anchor_consensus: int = 2


class DetectorDriftGuards:
    """
    Detector drift guards for layout robustness.
    
    Implements:
    - Row-grid projection validator with variance threshold & auto-correct
    - Multi-anchor consensus (Victory/Defeat, slash-band, column separators)
    - Letterboxing/crop tolerance via dynamic bbox expansion
    """
    
    def __init__(self, config: Optional[RobustnessConfig] = None):
        self.config = config or RobustnessConfig()
        self.telemetry = DriftTelemetry(
            row_variance=0.0,
            anchors_used=[],
            ign_score=0.0,
            hero_conf=0.0,
            phash_dist=None,
            cache_hits=0,
            stage_ms={},
            drift_warnings=[],
            corrective_actions=[]
        )
    
    def validate_row_grid(self, bands: List[float], image_height: int) -> Tuple[List[float], List[str]]:
        """
        Validate and correct row grid projection.
        
        Args:
            bands: Detected band positions
            image_height: Image height for normalization
            
        Returns:
            Tuple of (corrected_bands, warnings)
        """
        start_time = time.time()
        warnings = []
        corrective_actions = []
        
        try:
            if len(bands) < 3:
                warnings.append("Insufficient bands detected for grid validation")
                return bands, warnings
            
            # Calculate row heights and variance
            row_heights = np.diff(bands)
            normalized_heights = row_heights / np.mean(row_heights)
            variance = np.var(normalized_heights)
            
            self.telemetry.row_variance = variance
            
            # Check variance threshold
            if variance > self.config.grid_variance_correct:
                warnings.append(f"High row variance detected: {variance:.4f} > {self.config.grid_variance_correct}")
                corrective_actions.append("Applying grid regularization")
                corrected_bands = self._regularize_bands(bands)
            elif variance > self.config.grid_variance_warn:
                warnings.append(f"Row variance warning: {variance:.4f} > {self.config.grid_variance_warn}")
                # Don't correct, just warn
                corrected_bands = bands
            else:
                corrected_bands = bands
            
            # Log drift warning if needed
            if variance > self.config.grid_variance_warn:
                logger.warning(f"DRIFT_WARN row variance={variance:.4f}")
                if variance > self.config.grid_variance_correct:
                    logger.info("DRIFT_CORRECT applying grid regularization")
            
            self.telemetry.drift_warnings.extend(warnings)
            self.telemetry.corrective_actions.extend(corrective_actions)
            
            processing_time = (time.time() - start_time) * 1000
            self.telemetry.stage_ms["grid_validation"] = processing_time
            
            return corrected_bands, warnings
            
        except Exception as e:
            logger.error(f"Error in row grid validation: {e}")
            return bands, [f"Grid validation error: {str(e)}"]
    
    def _regularize_bands(self, bands: List[float]) -> List[float]:
        """Regularize bands to equal spacing."""
        try:
            if len(bands) < 2:
                return bands
            
            # Calculate average spacing
            total_height = bands[-1] - bands[0]
            avg_spacing = total_height / (len(bands) - 1)
            
            # Create regularized bands
            regularized = [bands[0]]
            for i in range(1, len(bands)):
                regularized.append(regularized[0] + i * avg_spacing)
            
            return regularized
            
        except Exception as e:
            logger.error(f"Error regularizing bands: {e}")
            return bands
    
    def multi_anchor_consensus(self, gray_image: np.ndarray, width: int, height: int) -> Tuple[List[str], float]:
        """
        Multi-anchor consensus detection for table band validation.
        
        Args:
            gray_image: Grayscale image
            width: Image width
            height: Image height
            
        Returns:
            Tuple of (found_anchors, consensus_confidence)
        """
        start_time = time.time()
        
        try:
            # Define anchor patterns for MLBB scoreboard
            anchor_patterns = {
                "victory": ["victory", "win", "defeat", "lose"],
                "kda": ["kda", "k/d/a", "kills", "deaths", "assists"],
                "damage": ["damage", "hero damage", "tower damage"],
                "gold": ["gold", "gpm", "gold per minute"],
                "mvp": ["mvp", "bronze", "silver", "gold"],
                "slash_band": ["/", "|", "\\"]  # Column separators
            }
            
            found_anchors = []
            anchor_confidence = 0.0
            
            # Use optimized text extraction
            from backend.ocr.ocr_reader import extract_text_optimized
            texts = extract_text_optimized(gray_image)
            
            # Check for anchor patterns
            for category, patterns in anchor_patterns.items():
                for text in texts:
                    text_lower = text.lower().strip()
                    for pattern in patterns:
                        if pattern in text_lower and len(text_lower) > 2:
                            found_anchors.append(f"{category}:{pattern}")
                            anchor_confidence += 0.1
                            break
            
            # Check consensus requirement
            consensus_met = len(found_anchors) >= self.config.min_anchor_consensus
            
            if not consensus_met:
                logger.warning(f"Anchor consensus not met: {len(found_anchors)} < {self.config.min_anchor_consensus}")
            
            self.telemetry.anchors_used = found_anchors
            
            processing_time = (time.time() - start_time) * 1000
            self.telemetry.stage_ms["anchor_consensus"] = processing_time
            
            return found_anchors, min(1.0, anchor_confidence)
            
        except Exception as e:
            logger.error(f"Error in multi-anchor consensus: {e}")
            return [], 0.0
    
    def expand_bbox_dynamic(self, bbox: Tuple[float, float, float, float], 
                          width: int, height: int, 
                          expand_pct: Optional[float] = None) -> Tuple[float, float, float, float]:
        """
        Dynamically expand bbox to tolerate minor crops/letterboxing.
        
        Args:
            bbox: (top, left, width, height) as ratios
            width: Image width
            height: Image height
            expand_pct: Expansion percentage (uses config default if None)
            
        Returns:
            Expanded bbox as ratios
        """
        start_time = time.time()
        
        try:
            if expand_pct is None:
                expand_pct = self.config.bbox_expand_pct
            
            top, left, bbox_width, bbox_height = bbox
            
            # Calculate expansion in pixels
            expand_x = bbox_width * width * expand_pct
            expand_y = bbox_height * height * expand_pct
            
            # Expand bbox
            new_left = max(0.0, left - expand_x / width)
            new_top = max(0.0, top - expand_y / height)
            new_width = min(1.0 - new_left, bbox_width + 2 * expand_x / width)
            new_height = min(1.0 - new_top, bbox_height + 2 * expand_y / height)
            
            processing_time = (time.time() - start_time) * 1000
            self.telemetry.stage_ms["bbox_expansion"] = processing_time
            
            return (new_top, new_left, new_width, new_height)
            
        except Exception as e:
            logger.error(f"Error expanding bbox: {e}")
            return bbox


class AdaptiveNormalizer:
    """
    Adaptive normalizer with hardened preprocessing.
    
    Implements:
    - Adaptive binarization (locally tuned Otsu; fallback Sauvola)
    - % extraction tolerant to OCR oddities (45°, 45·, 45o/o → 45%)
    """
    
    def __init__(self, config: Optional[RobustnessConfig] = None):
        self.config = config or RobustnessConfig()
    
    def adaptive_binarization(self, gray_image: np.ndarray) -> np.ndarray:
        """
        Adaptive binarization with Otsu primary and Sauvola fallback.
        
        Args:
            gray_image: Input grayscale image
            
        Returns:
            Binarized image
        """
        start_time = time.time()
        
        try:
            # Try Otsu thresholding first
            _, binary_otsu = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Check if Otsu produced too many midtones (heuristic)
            if self._too_many_midtones(binary_otsu):
                logger.debug("Otsu produced too many midtones, falling back to Sauvola")
                if self.config.use_sauvola_fallback:
                    binary_sauvola = self._sauvola_binarization(gray_image)
                    processing_time = (time.time() - start_time) * 1000
                    logger.debug(f"Sauvola binarization completed in {processing_time:.1f}ms")
                    return binary_sauvola
                else:
                    logger.warning("Sauvola fallback disabled, using Otsu despite midtones")
            
            processing_time = (time.time() - start_time) * 1000
            logger.debug(f"Otsu binarization completed in {processing_time:.1f}ms")
            return binary_otsu
            
        except Exception as e:
            logger.error(f"Error in adaptive binarization: {e}")
            # Fallback to simple threshold
            _, binary = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
            return binary
    
    def _too_many_midtones(self, binary_image: np.ndarray) -> bool:
        """Heuristic to detect if binarization produced too many midtones."""
        try:
            # Count pixels that are neither pure black nor pure white
            total_pixels = binary_image.size
            midtone_pixels = np.sum((binary_image > 50) & (binary_image < 205))
            midtone_ratio = midtone_pixels / total_pixels
            
            # If more than 20% are midtones, consider it problematic
            return midtone_ratio > 0.2
            
        except Exception as e:
            logger.debug(f"Error checking midtones: {e}")
            return False
    
    def _sauvola_binarization(self, gray_image: np.ndarray, window_size: int = 25, k: float = 0.2) -> np.ndarray:
        """
        Sauvola binarization implementation.
        
        Args:
            gray_image: Input grayscale image
            window_size: Window size for local thresholding
            k: Sauvola parameter
            
        Returns:
            Binarized image
        """
        try:
            # Convert to float for calculations
            img_float = gray_image.astype(np.float64)
            
            # Calculate local mean and standard deviation
            kernel = np.ones((window_size, window_size), np.float64) / (window_size * window_size)
            local_mean = cv2.filter2D(img_float, -1, kernel)
            local_sq_mean = cv2.filter2D(img_float * img_float, -1, kernel)
            local_std = np.sqrt(local_sq_mean - local_mean * local_mean)
            
            # Calculate Sauvola threshold
            threshold = local_mean * (1 + k * (local_std / 128 - 1))
            
            # Apply threshold
            binary = (img_float > threshold).astype(np.uint8) * 255
            
            return binary
            
        except Exception as e:
            logger.error(f"Error in Sauvola binarization: {e}")
            # Fallback to Otsu
            _, binary = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return binary
    
    def normalize_percentage_tokens(self, text: str) -> str:
        """
        Normalize funky percent tokens before regex.
        
        Args:
            text: Input text with potential OCR artifacts
            
        Returns:
            Normalized text with standard % symbols
        """
        try:
            # Normalize funky percent tokens
            normalized = text.replace("°", "%")
            normalized = normalized.replace("·", "%")
            normalized = normalized.replace("o/o", "%")
            normalized = normalized.replace("O/O", "%")
            normalized = normalized.replace("0/0", "%")
            normalized = normalized.replace("o/0", "%")
            normalized = normalized.replace("0/o", "%")
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing percentage tokens: {e}")
            return text


class DriftTelemetryLogger:
    """
    Drift telemetry logger for monitoring and debugging.
    
    Emits JSON logs with drift metrics and suggested corrective actions.
    """
    
    def __init__(self, config: Optional[RobustnessConfig] = None):
        self.config = config or RobustnessConfig()
    
    def log_analysis_telemetry(self, telemetry: DriftTelemetry, event_type: str = "OCR_ANALYSIS"):
        """
        Log analysis telemetry in JSON format.
        
        Args:
            telemetry: DriftTelemetry object
            event_type: Type of analysis event
        """
        try:
            if not self.config.enable_drift_telemetry:
                return
            
            log_data = {
                "event": event_type,
                "timestamp": time.time(),
                "row_variance": float(telemetry.row_variance),
                "anchors_used": telemetry.anchors_used,
                "ign_score": float(telemetry.ign_score),
                "hero_conf": float(telemetry.hero_conf),
                "phash_dist": telemetry.phash_dist,
                "cache_hits": telemetry.cache_hits,
                "stage_ms": telemetry.stage_ms,
                "drift_warnings": telemetry.drift_warnings,
                "corrective_actions": telemetry.corrective_actions
            }
            
            # Emit DRIFT_WARN when thresholds crossed
            if telemetry.drift_warnings:
                logger.warning(f"DRIFT_WARN: {json.dumps(log_data, indent=2)}")
            else:
                logger.info(f"DRIFT_TELEMETRY: {json.dumps(log_data, indent=2)}")
            
            # Include suggested corrective actions
            if telemetry.corrective_actions:
                logger.info(f"DRIFT_ACTIONS: {', '.join(telemetry.corrective_actions)}")
                
        except Exception as e:
            logger.error(f"Error logging drift telemetry: {e}")
    
    def emit_drift_warning(self, message: str, suggested_action: str = ""):
        """Emit a drift warning with suggested corrective action."""
        try:
            warning_data = {
                "event": "DRIFT_WARN",
                "timestamp": time.time(),
                "message": message,
                "suggested_action": suggested_action
            }
            
            logger.warning(f"DRIFT_WARN: {json.dumps(warning_data)}")
            
            if suggested_action:
                logger.info(f"DRIFT_SUGGESTION: {suggested_action}")
                
        except Exception as e:
            logger.error(f"Error emitting drift warning: {e}")


# Global instances with config integration
from backend.ocr.config import get_config

def get_robustness_config() -> RobustnessConfig:
    """Get robustness config from OCR Mission 5 config."""
    ocr_config = get_config()
    return RobustnessConfig(
        robust_mode=ocr_config.robust_mode,
        grid_variance_warn=ocr_config.grid_variance_warn,
        grid_variance_correct=ocr_config.grid_variance_correct,
        bbox_expand_pct=ocr_config.bbox_expand_pct,
        phash_threshold=ocr_config.phash_threshold,
        use_sauvola_fallback=ocr_config.use_sauvola_fallback,
        enable_drift_telemetry=ocr_config.enable_drift_telemetry,
        min_anchor_consensus=ocr_config.min_anchor_consensus
    )

robustness_config = get_robustness_config()
detector_drift_guards = DetectorDriftGuards(robustness_config)
adaptive_normalizer = AdaptiveNormalizer(robustness_config)
drift_telemetry_logger = DriftTelemetryLogger(robustness_config)
