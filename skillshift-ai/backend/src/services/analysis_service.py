# /backend/src/services/analysis_service.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import numpy as np
from fastapi import HTTPException

from backend.ocr.detectors import row_agnostic_detector
from backend.ocr.parsers_kda import kda_parser
from backend.ocr.parsers_damage import damage_parser
from backend.ocr.fuse import CrossViewFusion


def _load(path_str: str) -> np.ndarray:
    p = Path(path_str)
    if not p.exists() or not p.is_file():
        raise ValueError(f"Invalid image_path: {path_str}")
    img = cv2.imdecode(np.fromfile(str(p), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Unable to read image: {path_str}")
    return img


class ScreenshotAnalysisService:
    """
    Implements POST /analysis/screenshot with optional debug hooks.
    """

    def analyze(
        self,
        image_path: str,
        ign: str,
        *,
        debug_mode: bool = False,
        extract_options: Optional[Dict[str, Any]] = None,
        row_agnostic_mode: bool = True,
    ) -> Dict[str, Any]:
        img = _load(image_path)

        # Detect table + rows once (row-agnostic geometry)
        table_region = row_agnostic_detector.detect_table_regions(image_path)
        if not table_region:
            raise ValueError("Could not detect table regions")
        
        row_crops = row_agnostic_detector.generate_row_crops(table_region, image_path, ign)
        if not row_crops:
            raise ValueError("Could not generate row crops")

        kda = kda_parser.parse_kda_from_screenshot(image_path, ign)

        dmg = None
        if extract_options and extract_options.get("with_damage", False):
            dmg = damage_parser.parse_damage_from_screenshot(image_path, ign)

        fusion_service = CrossViewFusion()
        fusion = fusion_service.fuse_kda_and_damage(kda, dmg)

        resp: Dict[str, Any] = {
            "ign": ign,
            "player_located": fusion is not None,
            "player_ign": fusion.player_ign if fusion else None,
            "kda": {
                "kills": fusion.kills if fusion else 0,
                "deaths": fusion.deaths if fusion else 0,
                "assists": fusion.assists if fusion else 0
            } if fusion else {"kills": 0, "deaths": 0, "assists": 0},
            "overall_confidence": fusion.overall_confidence if fusion else 0.0,
            "row_agnostic_mode": row_agnostic_mode,
        }

        if debug_mode:
            resp["debug"] = {
                "table_bbox": getattr(table_region, "panel_bbox", None),
                "rows_count": len(row_crops),
            }

        return resp
