# /backend/src/api/v2/analysis.py
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.src.services.analysis_service import ScreenshotAnalysisService

router = APIRouter()


class ScreenshotAnalysisRequest(BaseModel):
    image_path: str = Field(..., description="Path to input screenshot")
    ign: str = Field(..., description="Player IGN to target")
    debug_mode: bool = False
    row_agnostic_mode: bool = True
    extract_options: Optional[Dict[str, Any]] = None


class ScreenshotAnalysisResponse(BaseModel):
    ign: str
    player_located: bool
    player_ign: Optional[str]
    overall_confidence: float
    row_agnostic_mode: bool
    analysis: Optional[Dict[str, Any]] = None
    damage_stats: Optional[Dict[str, Any]] = None
    debug: Optional[Dict[str, Any]] = None


@router.post("/analysis/screenshot", response_model=ScreenshotAnalysisResponse)
def analyze_screenshot(req: ScreenshotAnalysisRequest):
    from pathlib import Path
    
    # Validate file path before processing (raises ValueError -> 400)
    path = Path(req.image_path)
    if not path.exists() or not path.is_file():
        raise ValueError(f"Invalid image path: {req.image_path}")
    
    service = ScreenshotAnalysisService()
    result = service.analyze(
        image_path=req.image_path,
        ign=req.ign,
        debug_mode=req.debug_mode,
        extract_options=req.extract_options,
        row_agnostic_mode=req.row_agnostic_mode,
    )
    
    # Return properly serialized response
    response = ScreenshotAnalysisResponse.model_validate(result)
    return response.model_dump(by_alias=True, exclude_none=True)
