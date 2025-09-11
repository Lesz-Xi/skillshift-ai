# /backend/src/services/ocr_debug_service.py
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


def _load_image(path_str: str) -> np.ndarray:
    path = Path(path_str)
    if not path.exists() or not path.is_file():
        raise ValueError(f"Invalid image_path: {path_str}")
    img = cv2.imdecode(
        np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR
    )
    if img is None:
        raise ValueError(f"Unable to read image: {path_str}")
    return img


class OCRDebugService:
    """
    Thin façade over detectors/parsers to support the /ocr/debug contract.
    """

    def debug(
        self,
        image_path: str,
        target_ign: str,
        *,
        debug_mode: bool = False,
        extract_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # Load KDA (single view) for debug; damage is optional
        kda_img = _load_image(image_path)

        # Detect table + rows once (row-agnostic geometry)
        table_region = row_agnostic_detector.detect_table_regions(image_path)
        if not table_region:
            raise ValueError("Could not detect table regions")
        
        row_crops = row_agnostic_detector.generate_row_crops(table_region, image_path, target_ign)
        if not row_crops:
            raise ValueError("Could not generate row crops")

        # Parse from screenshot
        kda = kda_parser.parse_kda_from_screenshot(image_path, target_ign)
        # Optional damage pass when extract_options requests it
        dmg = None
        if extract_options and extract_options.get("with_damage", False):
            dmg = damage_parser.parse_damage_from_screenshot(image_path, target_ign)

        fusion_service = CrossViewFusion()
        fusion = fusion_service.fuse_kda_and_damage(kda, dmg)

        # Minimal, stable response shape for contract tests
        out: Dict[str, Any] = {
            "player_located": fusion is not None,
            "player_ign": fusion.player_ign if fusion else None,
            "kda": {
                "kills": fusion.kills if fusion else 0,
                "deaths": fusion.deaths if fusion else 0,
                "assists": fusion.assists if fusion else 0
            } if fusion else {"kills": 0, "deaths": 0, "assists": 0},
            "overall_confidence": fusion.overall_confidence if fusion else 0.0,
            "rows_count": len(row_crops),
            "table_bbox": getattr(table_region, "panel_bbox", None),
        }

        if debug_mode:
            # Add light debug metadata; keep it JSON-friendly.
            out["debug"] = {
                "ratios": {
                    "row_top": (
                        getattr(row_crops[0], "bbox_ratio", None)[0] if row_crops else None
                    ),
                    "row_height": (
                        getattr(row_crops[0], "bbox_ratio", None)[3] if row_crops else None
                    ),
                },
                "anchors_detected": getattr(table_region, "anchors_found", None),
            }

        return out
