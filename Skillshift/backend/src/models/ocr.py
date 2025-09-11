"""
OCR Models - Pydantic models for OCR processing and results
Contains models for T015, T016, T017, T018, T019
"""

from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
from dataclasses import dataclass
from datetime import datetime


# T015: OCRExtractionResult model
class OCRExtractionResult(BaseModel):
    """Comprehensive OCR extraction result from screenshot analysis"""
    
    # Core identification
    player_located: bool = Field(description="Whether target player was found")
    player_ign: Optional[str] = Field(None, description="Player IGN if located")
    hero: Optional[str] = Field(None, description="Hero name if detected")
    
    # KDA data
    kda: Optional[Dict[str, int]] = Field(None, description="KDA values {k, d, a}")
    kda_ratio: Optional[float] = Field(None, description="Calculated KDA ratio")
    mvp_score: Optional[float] = Field(None, description="MVP score if available")
    
    # Economic data
    gold_earned: Optional[int] = Field(None, description="Total gold earned")
    gpm: Optional[float] = Field(None, description="Gold per minute")
    
    # Damage statistics
    hero_damage_pct: Optional[float] = Field(None, description="Hero damage percentage")
    teamfight_pct: Optional[float] = Field(None, description="Teamfight participation %")
    total_damage: Optional[int] = Field(None, description="Total damage dealt")
    
    # Match metadata
    match_duration: Optional[float] = Field(None, description="Match duration in minutes")
    match_result: Optional[str] = Field(None, description="Victory/Defeat")
    
    # Quality metrics
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Overall confidence score")
    data_completeness: float = Field(0.0, ge=0.0, le=1.0, description="Data completeness ratio")
    
    # Processing metadata
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    ocr_engine: str = Field("EasyOCR", description="OCR engine used")
    
    # Warnings and errors
    warnings: List[str] = Field(default_factory=list, description="Non-critical warnings")
    errors: List[str] = Field(default_factory=list, description="Critical errors")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


# T016: PlayerDetectionResult model (already exists, documenting for completeness)
class PlayerDetectionResult(BaseModel):
    """Result of player detection in OCR processing"""
    
    player_located: bool = Field(description="Whether player was successfully located")
    player_ign: Optional[str] = Field(None, description="Detected player IGN")
    row_index: Optional[int] = Field(None, description="Row index where player was found")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Detection confidence")
    detection_method: str = Field("fuzzy_match", description="Detection method used")
    similarity_score: float = Field(0.0, ge=0.0, le=1.0, description="IGN similarity score")
    
    # Bounding box information
    bbox: Optional[Dict[str, int]] = Field(None, description="Player row bounding box {x, y, w, h}")
    
    # Alternative candidates
    candidates: List[str] = Field(default_factory=list, description="Other IGN candidates found")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


# T017: RegionDetectionResult model
class RegionDetectionResult(BaseModel):
    """Result of table/region detection in screenshots"""
    
    # Region identification
    region_type: str = Field(description="Type of region (kda_table, damage_table, scoreboard)")
    detected: bool = Field(description="Whether region was successfully detected")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Detection confidence")
    
    # Geometric information
    bounding_box: Optional[Dict[str, int]] = Field(None, description="Region bbox {x, y, w, h}")
    normalized_coords: Optional[Dict[str, float]] = Field(None, description="Normalized coordinates")
    
    # Table structure (for scoreboard regions)
    rows_detected: Optional[int] = Field(None, description="Number of rows detected")
    columns_detected: Optional[int] = Field(None, description="Number of columns detected")
    row_height: Optional[int] = Field(None, description="Average row height in pixels")
    
    # Template matching results
    template_matches: List[Dict[str, Any]] = Field(default_factory=list, description="Template match results")
    anchor_points: List[Dict[str, Any]] = Field(default_factory=list, description="Detected anchor points")
    
    # Quality metrics
    structural_integrity: float = Field(0.0, ge=0.0, le=1.0, description="Table structure quality")
    ocr_readiness: float = Field(0.0, ge=0.0, le=1.0, description="Region readiness for OCR")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


# T018: CrossViewFusionResult model
class CrossViewFusionResult(BaseModel):
    """Result of fusing data from multiple views (KDA + Damage)"""
    
    # Player identification
    player_located: bool = Field(description="Whether player found in any view")
    player_ign: Optional[str] = Field(None, description="Unified player IGN")
    hero: Optional[str] = Field(None, description="Resolved hero name")
    
    # KDA data (from KDA view)
    kda: Optional[Dict[str, int]] = Field(None, description="KDA values {k, d, a}")
    kda_ratio: Optional[float] = Field(None, description="Calculated KDA ratio")
    mvp_score: Optional[float] = Field(None, description="MVP score")
    
    # Damage data (from Damage view)
    damage_stats: Optional[Dict[str, Any]] = Field(None, description="Damage statistics")
    
    # Economic data
    gold_earned: Optional[int] = Field(None, description="Total gold earned")
    gpm: Optional[float] = Field(None, description="Gold per minute")
    
    # Fusion quality metrics
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Fused confidence score")
    data_completeness: float = Field(0.0, ge=0.0, le=1.0, description="Data completeness ratio")
    
    # View-specific confidences
    kda_view_confidence: float = Field(0.0, ge=0.0, le=1.0, description="KDA view confidence")
    damage_view_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Damage view confidence")
    
    # Conflict resolution
    conflicts_detected: int = Field(0, description="Number of conflicts between views")
    conflicts_resolved: int = Field(0, description="Number of conflicts resolved")
    conflict_details: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed conflict info")
    
    # Processing metadata
    fusion_strategy: str = Field("confidence_weighted", description="Fusion strategy used")
    views_processed: List[str] = Field(default_factory=list, description="Views that were processed")
    
    # Warnings and validation
    warnings: List[str] = Field(default_factory=list, description="Fusion warnings")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


# T019: OCRConfiguration model
class OCRConfiguration(BaseModel):
    """Configuration for OCR processing pipeline"""
    
    # OCR Engine settings
    ocr_engine: str = Field("EasyOCR", description="OCR engine to use")
    languages: List[str] = Field(default_factory=lambda: ["en"], description="OCR languages")
    gpu_enabled: bool = Field(False, description="Whether to use GPU acceleration")
    
    # Image preprocessing
    preprocessing_enabled: bool = Field(True, description="Enable image preprocessing")
    resize_factor: float = Field(1.0, ge=0.1, le=5.0, description="Image resize factor")
    contrast_enhancement: bool = Field(True, description="Enable contrast enhancement")
    noise_reduction: bool = Field(True, description="Enable noise reduction")
    
    # Text detection thresholds
    text_confidence_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Min text confidence")
    fuzzy_match_threshold: float = Field(0.7, ge=0.0, le=1.0, description="IGN fuzzy match threshold")
    template_match_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Template match threshold")
    
    # Table detection settings
    table_detection_enabled: bool = Field(True, description="Enable automatic table detection")
    row_detection_method: str = Field("geometry", description="Row detection method")
    min_row_height: int = Field(20, description="Minimum row height in pixels")
    max_rows: int = Field(10, description="Maximum expected rows")
    
    # Region-specific settings
    kda_region: Dict[str, Any] = Field(default_factory=dict, description="KDA region parameters")
    damage_region: Dict[str, Any] = Field(default_factory=dict, description="Damage region parameters")
    
    # Performance settings
    timeout_seconds: int = Field(30, description="Processing timeout in seconds")
    parallel_processing: bool = Field(True, description="Enable parallel processing")
    max_concurrent_tasks: int = Field(4, description="Max concurrent OCR tasks")
    
    # Debug settings
    debug_mode: bool = Field(False, description="Enable debug output")
    save_debug_images: bool = Field(False, description="Save intermediate debug images")
    debug_output_path: Optional[str] = Field(None, description="Debug output directory")
    
    # Validation settings
    enable_validation: bool = Field(True, description="Enable result validation")
    min_confidence_threshold: float = Field(0.75, ge=0.0, le=1.0, description="Min overall confidence")
    min_completeness_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Min data completeness")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


# Additional helper models

class OCRProcessingStats(BaseModel):
    """Statistics about OCR processing performance"""
    
    total_processing_time_ms: int = Field(description="Total processing time")
    ocr_time_ms: int = Field(description="Pure OCR time")
    preprocessing_time_ms: int = Field(description="Image preprocessing time") 
    postprocessing_time_ms: int = Field(description="Result postprocessing time")
    
    images_processed: int = Field(description="Number of images processed")
    characters_detected: int = Field(description="Total characters detected")
    text_regions_found: int = Field(description="Number of text regions found")
    
    success_rate: float = Field(ge=0.0, le=1.0, description="Overall success rate")
    average_confidence: float = Field(ge=0.0, le=1.0, description="Average confidence score")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class OCRDebugInfo(BaseModel):
    """Debug information for OCR processing"""
    
    debug_enabled: bool = Field(description="Whether debug mode was enabled")
    debug_images_saved: int = Field(0, description="Number of debug images saved")
    debug_output_path: Optional[str] = Field(None, description="Debug output directory")
    
    preprocessing_steps: List[str] = Field(default_factory=list, description="Preprocessing steps applied")
    ocr_raw_results: List[Dict[str, Any]] = Field(default_factory=list, description="Raw OCR results")
    
    template_matches: List[Dict[str, Any]] = Field(default_factory=list, description="Template match details")
    region_detections: List[Dict[str, Any]] = Field(default_factory=list, description="Region detection details")
    
    performance_markers: Dict[str, float] = Field(default_factory=dict, description="Performance timestamps")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }