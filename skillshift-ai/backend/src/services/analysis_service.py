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
from backend.src.services.session_analysis_service import session_analysis_service


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
        session_id: Optional[str] = None,
        hero_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Enhanced analysis method supporting both legacy and session-based approaches.
        
        If session_id is provided, uses session-based multi-screen fusion.
        Otherwise, falls back to legacy single-screenshot analysis.
        """
        # Use session-based approach if session parameters are provided
        if session_id:
            return self._analyze_with_session(
                image_path, ign, session_id, hero_id, user_id,
                debug_mode, extract_options, row_agnostic_mode
            )
        else:
            # Legacy single-screenshot analysis (fallback)
            return self._analyze_legacy(
                image_path, ign, debug_mode, extract_options, row_agnostic_mode
            )
    
    def _analyze_with_session(
        self,
        image_path: str,
        ign: str,
        session_id: str,
        hero_id: Optional[str],
        user_id: Optional[str],
        debug_mode: bool = False,
        extract_options: Optional[Dict[str, Any]] = None,
        row_agnostic_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Session-based analysis that can handle multiple screenshots per game.
        
        This implements the fix for the core issue: running both parsers on same screenshot
        vs. proper screen-type discrimination and session-based fusion.
        """
        try:
            # Add screenshot to session
            result = session_analysis_service.add_screenshot(session_id, image_path)
            
            # Get current session analysis
            session_analysis = session_analysis_service.get_session_analysis(session_id)
            
            if not session_analysis:
                raise ValueError(f"Failed to get analysis for session {session_id}")
            
            # Format response compatible with legacy API
            resp: Dict[str, Any] = {
                "ign": ign,
                "player_located": session_analysis.get("player_located", False),
                "player_ign": session_analysis.get("player_ign"),
                "session_id": session_id,
                "session_complete": session_analysis.get("session_complete", False),
                "overall_confidence": session_analysis.get("overall_confidence", 0.0),
                "row_agnostic_mode": row_agnostic_mode,
            }
            
            # Add KDA data (always present from scoreboard)
            if "kda" in session_analysis:
                resp["kda"] = session_analysis["kda"]
            else:
                resp["kda"] = {"kills": 0, "deaths": 0, "assists": 0}
            
            # Add damage stats if available (null when not available)
            if "damage_stats" in session_analysis and session_analysis["damage_stats"]:
                resp["damage_stats"] = session_analysis["damage_stats"]
            
            # Add additional metrics if available
            if "gold_per_minute" in session_analysis and session_analysis["gold_per_minute"]:
                resp["gold_per_minute"] = session_analysis["gold_per_minute"]
            
            if "kda_ratio" in session_analysis:
                resp["kda_ratio"] = session_analysis["kda_ratio"]
            
            if "mvp_score" in session_analysis:
                resp["mvp_score"] = session_analysis["mvp_score"]
            
            # Add debug info
            if debug_mode:
                resp["debug"] = {
                    "session_info": {
                        "screenshots_processed": result.get("screenshots_processed", 0),
                        "screen_type": result.get("screen_type"),
                        "fusion_method": session_analysis.get("fusion_method"),
                        "data_completeness": session_analysis.get("data_completeness", 0.0),
                    },
                    "missing_screens": session_analysis.get("missing_screens", []),
                    "sources": session_analysis.get("sources", {}),
                }
            
            return resp
            
        except Exception as e:
            logger.error(f"Error in session-based analysis: {e}")
            # Fall back to legacy analysis on session errors
            logger.info("Falling back to legacy analysis due to session error")
            return self._analyze_legacy(image_path, ign, debug_mode, extract_options, row_agnostic_mode)
    
    def _analyze_legacy(
        self,
        image_path: str,
        ign: str,
        debug_mode: bool = False,
        extract_options: Optional[Dict[str, Any]] = None,
        row_agnostic_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Legacy single-screenshot analysis (original implementation).
        
        This is kept for backward compatibility but will show the original issues
        since it runs both parsers on the same screenshot.
        """
        img = _load(image_path)

        # Detect table + rows once (row-agnostic geometry)
        table_region = row_agnostic_detector.detect_table_regions(image_path)
        if not table_region:
            raise ValueError("Could not detect table regions")
        
        row_crops = row_agnostic_detector.generate_row_crops(table_region, image_path, ign)
        if not row_crops:
            raise ValueError("Could not generate row crops")

        # FIXED: Use screen-type aware parsing
        kda = kda_parser.parse_kda_from_screenshot(image_path, ign)

        dmg = None
        if extract_options and extract_options.get("with_damage", False):
            # Use fixed damage parser that respects screen types
            dmg = damage_parser.parse_damage_from_screenshot(image_path, ign)

        fusion_service = CrossViewFusion()
        fusion = fusion_service.fuse_kda_and_damage(kda, dmg)

        resp: Dict[str, Any] = {
            "ign": ign,
            "player_located": fusion is not None,
            "player_ign": fusion.player_ign if fusion else None,
            "overall_confidence": fusion.overall_confidence if fusion else 0.0,
            "row_agnostic_mode": row_agnostic_mode,
            "analysis_method": "legacy",  # Indicate this is legacy mode
        }

        # Add structured analysis wrapper as per OCR-Task-4.md
        resp["analysis"] = {
            "performance": {
                "kda": {
                    "kills": fusion.kills if fusion else 0,
                    "deaths": fusion.deaths if fusion else 0,
                    "assists": fusion.assists if fusion else 0
                } if fusion else {"kills": 0, "deaths": 0, "assists": 0},
                "gpm": fusion.gold_per_minute if fusion else None,
                "role": fusion.role if fusion else None,
                "hero": fusion.hero if fusion else None,
            }
        }

        # Add damage statistics if available (never null from scoreboard due to fixes)
        if dmg and dmg.hero_damage is not None and dmg.hero_damage > 0:
            resp["analysis"]["damage_statistics"] = {
                "hero_damage": dmg.hero_damage,
                "tower_damage": dmg.tower_damage if dmg.tower_damage > 0 else None,
                "damage_taken": dmg.damage_taken if dmg.damage_taken > 0 else None,
                "teamfight_participation": dmg.teamfight_participation if dmg.teamfight_participation > 0 else None,
            }
            
            # Keep legacy damage_stats for backward compatibility
            resp["damage_stats"] = {
                "hero_damage": dmg.hero_damage,
                "damage_taken": dmg.damage_taken if dmg.damage_taken > 0 else None,
                "tower_damage": dmg.tower_damage if dmg.tower_damage > 0 else None,
                "teamfight_participation": dmg.teamfight_participation if dmg.teamfight_participation > 0 else None,
            }

        if debug_mode:
            resp["debug"] = {
                "table_bbox": getattr(table_region, "panel_bbox", None),
                "rows_count": len(row_crops),
                "analysis_method": "legacy_single_screenshot",
                "fusion_method": fusion.fusion_method if fusion else "none",
            }

        return resp
    
    def create_session(self, user_id: str, hero_id: str, target_ign: str) -> str:
        """Create a new analysis session."""
        return session_analysis_service.create_session(user_id, hero_id, target_ign)
    
    def get_session_analysis(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis results for a session."""
        return session_analysis_service.get_session_analysis(session_id)
    
    def complete_session(self, session_id: str) -> Dict[str, Any]:
        """Complete a session and get final results."""
        return session_analysis_service.complete_session(session_id)
