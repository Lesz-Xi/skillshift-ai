# /backend/src/api/v2/ocr.py
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.src.services.ocr_debug_service import OCRDebugService
from backend.ocr.detectors import row_agnostic_detector

router = APIRouter()


# ---------- Schemas ----------

class OCRDebugRequest(BaseModel):
    image_path: str = Field(
        ..., description="Path to KDA or scoreboard screenshot"
    )
    target_ign: str = Field(..., description="Exact IGN to locate")
    debug_mode: bool = False
    extract_options: Optional[Dict[str, Any]] = None


class OCRDebugResponse(BaseModel):
    player_located: bool
    player_ign: Optional[str]
    kda: Dict[str, Any]
    overall_confidence: float
    rows_count: int
    table_bbox: Optional[Any] = None
    debug: Optional[Dict[str, Any]] = None


class OCRFusionRequest(BaseModel):
    kda_image_path: str = Field(..., description="Path to KDA screenshot")
    damage_image_path: str = Field(
        ..., description="Path to damage screenshot"
    )
    target_ign: str = Field(..., description="Exact IGN to locate")
    fusion_mode: Optional[str] = Field(default="auto")
    hero_crop_path: Optional[str] = Field(None, description="Path to hero portrait crop for advanced resolution")


class OCRFusionResponse(BaseModel):
    player_located: bool
    player_ign: Optional[str]
    kda: Dict[str, Any]
    damage: Dict[str, Any]
    mvp_score: int
    hero: str
    hero_confidence: float
    hero_resolution_method: str
    overall_confidence: float
    fusion_mode: str


# ---------- Endpoints ----------

@router.post("/ocr/debug", response_model=OCRDebugResponse)
def ocr_debug(req: OCRDebugRequest):
    # Pydantic handles 422 on malformed/missing JSON/fields
    from pathlib import Path
    
    # Validate file path before processing (raises ValueError -> 400)
    path = Path(req.image_path)
    if not path.exists() or not path.is_file():
        raise ValueError(f"Invalid image path: {req.image_path}")
    
    service = OCRDebugService()
    result = service.debug(
        image_path=req.image_path,
        target_ign=req.target_ign,
        debug_mode=req.debug_mode,
        extract_options=req.extract_options,
    )
    
    # Return properly serialized response
    response = OCRDebugResponse.model_validate(result)
    return response.model_dump(by_alias=True, exclude_none=True)


@router.post("/ocr/fusion", response_model=OCRFusionResponse)
def ocr_fusion(req: OCRFusionRequest):
    """OCR fusion endpoint with hero resolution support (OCR Mission 4)."""
    from pathlib import Path
    from backend.src.services.ocr_debug_service import _load_image
    import cv2
    import numpy as np

    # Validate file paths before processing (raises ValueError -> 400)
    kda_path = Path(req.kda_image_path)
    if not kda_path.exists() or not kda_path.is_file():
        raise ValueError(f"Invalid KDA image path: {req.kda_image_path}")
    
    dmg_path = Path(req.damage_image_path)
    if not dmg_path.exists() or not dmg_path.is_file():
        raise ValueError(f"Invalid damage image path: {req.damage_image_path}")

    kda_img = _load_image(req.kda_image_path)
    dmg_img = _load_image(req.damage_image_path)

    from backend.ocr.parsers_kda import kda_parser
    from backend.ocr.parsers_damage import damage_parser
    from backend.ocr.fuse import cross_view_fusion

    # Parse KDA and damage
    kda = kda_parser.parse_kda_from_screenshot(req.kda_image_path, req.target_ign)
    dmg = damage_parser.parse_damage_from_screenshot(req.damage_image_path, req.target_ign)
    
    # Load hero crop if provided
    hero_crop = None
    if req.hero_crop_path:
        try:
            hero_crop = cv2.imread(req.hero_crop_path)
            if hero_crop is not None:
                hero_crop = np.array(hero_crop)
        except Exception as e:
            print(f"Warning: Could not load hero crop from {req.hero_crop_path}: {e}")
    
    # Perform fusion with hero resolution
    fusion = cross_view_fusion(kda, dmg, hero_crop)
    
    if fusion is None:
        error_data = {
            "player_located": False,
            "player_ign": None,
            "kda": {"k": 0, "d": 0, "a": 0, "ratio": 0.0},
            "damage": {"hero_pct": 0.0, "turret_pct": 0.0, "taken_pct": 0.0},
            "mvp_score": 0,
            "hero": "unknown",
            "hero_confidence": 0.0,
            "hero_resolution_method": "none",
            "overall_confidence": 0.0,
            "fusion_mode": req.fusion_mode or "auto",
        }
        response = OCRFusionResponse.model_validate(error_data)
        return response.model_dump(by_alias=True, exclude_none=True)
    
    # Return enriched schema (OCR Mission 4 format)
    enriched_schema = fusion.to_enriched_schema()
    
    result_data = {
        "player_located": True,
        "player_ign": fusion.player_ign,
        "kda": enriched_schema["kda"],
        "damage": enriched_schema["damage"],
        "mvp_score": enriched_schema["mvp_score"],
        "hero": enriched_schema["hero"],
        "hero_confidence": enriched_schema["hero_confidence"],
        "hero_resolution_method": enriched_schema["hero_resolution_method"],
        "overall_confidence": enriched_schema["confidence"],
        "fusion_mode": req.fusion_mode or "auto",
    }
    
    # Return properly serialized response
    response = OCRFusionResponse.model_validate(result_data)
    return response.model_dump(by_alias=True, exclude_none=True)
