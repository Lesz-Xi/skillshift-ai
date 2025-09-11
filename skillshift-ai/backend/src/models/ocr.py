from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

class OCRExtractionResult(BaseModel):
    image_path: str
    player_ign: Optional[str] = None
    kda: Optional[Dict[str, int]] = None   # {'k':9,'d':2,'a':12}
    mvp_score: Optional[float] = None
    hero: Optional[str] = None
    raw_ocr: List[Tuple[Optional[List[int]], str, float]] = Field(default_factory=list)  # (bbox, text, conf)
    debug: Dict[str, object] = Field(default_factory=dict)
    confidence: float = 0.0

class PlayerDetectionResult(BaseModel):
    player_located: bool
    player_ign: Optional[str] = None
    row_index: Optional[int] = None
    table_bbox_ratio: Optional[Tuple[float, float, float, float]] = None
    rows_detected: int = 0
    anchors: List[str] = Field(default_factory=list)

class RegionDetectionResult(BaseModel):
    table_bbox_ratio: Tuple[float, float, float, float]
    rows: int
    anchors: List[str] = Field(default_factory=list)
    confidence: float = 0.0

class FusionConflict(BaseModel):
    field: str
    kda_view_value: Optional[object] = None
    dmg_view_value: Optional[object] = None
    resolved_value: Optional[object] = None
    rule: Optional[str] = None

class CrossViewFusionResult(BaseModel):
    player_located: bool
    player_ign: Optional[str]
    kda: Optional[Dict[str, object]] = None  # {'k':9,'d':2,'a':12,'ratio':10.5}
    damage: Optional[Dict[str, object]] = None
    hero: Optional[str] = None
    overall_confidence: float = 0.0
    completeness: float = 0.0
    conflicts: List[FusionConflict] = Field(default_factory=list)
    raw: Dict[str, object] = Field(default_factory=dict)

class OCRConfiguration(BaseModel):
    """OCR configuration model for system settings."""
    confidence_threshold: float = 0.8
    max_detection_results: int = 100
    enable_preprocessing: bool = True
    preprocessing_params: Dict[str, object] = Field(default_factory=dict)
    ocr_engine: str = "easyocr"
    supported_languages: List[str] = Field(default_factory=lambda: ["en"])
    debug_mode: bool = False