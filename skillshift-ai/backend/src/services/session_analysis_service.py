"""
Session-based analysis service for multi-screen data fusion.

Implements the session merge logic from Current_Problem_1.md to properly combine
KDA data from scoreboard screenshots with damage stats from damage view screenshots.
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
import uuid
import numpy as np
from pathlib import Path

from backend.ocr.parsers_kda import KDAResult, kda_parser
from backend.ocr.parsers_damage import DamageResult, damage_parser
from backend.ocr.fuse import CrossViewFusion, FusedResult
from backend.ocr.detectors import row_agnostic_detector
from backend.ocr.hero_resolver import hero_resolver, HeroMatchResult

logger = logging.getLogger(__name__)

@dataclass
class ScreenshotAnalysis:
    """Analysis result from a single screenshot."""
    screenshot_id: str
    image_path: str
    screen_type: str  # 'scoreboard' | 'damage_stats'
    timestamp: datetime
    kda_result: Optional[KDAResult] = None
    damage_result: Optional[DamageResult] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0

@dataclass 
class GameSession:
    """A game session that can contain multiple screenshots."""
    session_id: str
    user_id: str
    hero_id: str
    target_ign: str
    created_at: datetime
    screenshots: List[ScreenshotAnalysis] = field(default_factory=list)
    merged_analysis: Optional[Dict[str, Any]] = None
    is_complete: bool = False

class SessionAnalysisService:
    """
    Session-based analysis service that handles multi-screen data fusion.
    
    Implements the core requirement from Current_Problem_1.md:
    "When both images exist, build a MergedAnalysis per session"
    """
    
    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}
        self.fusion_engine = CrossViewFusion()
        
        # Screen type detection confidence thresholds
        self.screen_type_thresholds = {
            'scoreboard_confidence': 0.8,
            'damage_stats_confidence': 0.7
        }
    
    def create_session(self, user_id: str, hero_id: str, target_ign: str) -> str:
        """Create a new game session."""
        session_id = str(uuid.uuid4())
        session = GameSession(
            session_id=session_id,
            user_id=user_id,
            hero_id=hero_id,
            target_ign=target_ign,
            created_at=datetime.now()
        )
        self.sessions[session_id] = session
        logger.info(f"Created new session {session_id} for user {user_id}, hero {hero_id}, IGN {target_ign}")
        return session_id
    
    def add_screenshot(self, session_id: str, image_path: str) -> Dict[str, Any]:
        """
        Add a screenshot to a session and analyze it.
        
        This method implements the screen-type discrimination logic to determine
        whether this is a scoreboard/KDA screen or damage/stats screen.
        """
        try:
            # Validate session exists
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            
            # Detect screen type and parse accordingly
            screen_type, analysis_result = self._analyze_screenshot_type(image_path, session.target_ign)
            
            # Create screenshot analysis
            screenshot = ScreenshotAnalysis(
                screenshot_id=str(uuid.uuid4()),
                image_path=image_path,
                screen_type=screen_type,
                timestamp=datetime.now(),
                **analysis_result
            )
            
            session.screenshots.append(screenshot)
            
            # Try to merge data if we have both screen types
            if self._can_merge_session_data(session):
                self._merge_session_data(session)
            
            logger.info(f"Added {screen_type} screenshot to session {session_id}")
            
            return {
                'session_id': session_id,
                'screenshot_id': screenshot.screenshot_id,
                'screen_type': screen_type,
                'analysis_result': analysis_result,
                'session_complete': session.is_complete,
                'merged_analysis': session.merged_analysis
            }
            
        except Exception as e:
            logger.error(f"Error adding screenshot to session {session_id}: {e}")
            raise
    
    def _analyze_screenshot_type(self, image_path: str, target_ign: str) -> tuple[str, Dict[str, Any]]:
        """
        Determine screen type and parse accordingly.
        
        Returns: (screen_type, analysis_result_dict)
        """
        try:
            import cv2
            
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Use the enhanced damage parser's screen type detection
            # First extract text from the image
            import easyocr
            reader = easyocr.Reader(['en'])
            ocr_results = reader.readtext(img)
            screen_type = damage_parser._detect_screen_type(ocr_results)
            
            analysis_result = {
                'kda_result': None,
                'damage_result': None,
                'processing_time': 0.0,
                'raw_data': {}
            }
            
            start_time = datetime.now()
            
            if screen_type == 'scoreboard':
                # For scoreboard screens, only run KDA parser
                logger.info(f"Detected scoreboard screen, running KDA parser for {target_ign}")
                kda_result = kda_parser.parse_kda_from_screenshot(image_path, target_ign)
                analysis_result['kda_result'] = kda_result
                
            elif screen_type == 'damage' or screen_type == 'damage_stats':
                # For damage stats screens, only run damage parser
                logger.info(f"Detected damage stats screen, running damage parser for {target_ign}")
                damage_result = damage_parser.parse_damage_from_screenshot(image_path, target_ign)
                analysis_result['damage_result'] = damage_result
                
            else:
                # Unknown screen type, try both parsers as fallback
                logger.warning(f"Unknown screen type, running both parsers for {target_ign}")
                kda_result = kda_parser.parse_kda_from_screenshot(image_path, target_ign)
                damage_result = damage_parser.parse_damage_from_screenshot(image_path, target_ign)
                analysis_result['kda_result'] = kda_result
                analysis_result['damage_result'] = damage_result
                screen_type = 'unknown'
            
            processing_time = (datetime.now() - start_time).total_seconds()
            analysis_result['processing_time'] = processing_time
            
            return screen_type, analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing screenshot type for {image_path}: {e}")
            return 'error', {
                'kda_result': None,
                'damage_result': None,
                'processing_time': 0.0,
                'raw_data': {'error': str(e)}
            }
    
    def _can_merge_session_data(self, session: GameSession) -> bool:
        """Check if session has enough data for merging."""
        has_scoreboard = any(s.screen_type == 'scoreboard' for s in session.screenshots)
        has_damage_stats = any(s.screen_type == 'damage' or s.screen_type == 'damage_stats' for s in session.screenshots)
        
        return has_scoreboard and has_damage_stats
    
    def _merge_session_data(self, session: GameSession):
        """
        Merge data from multiple screenshots into a unified analysis.
        
        This implements the core requirement: "When both images exist, 
        build a MergedAnalysis per session"
        """
        try:
            logger.info(f"Merging session data for session {session.session_id}")
            
            # Find the best screenshots for each type
            best_scoreboard = self._find_best_screenshot(session, 'scoreboard')
            best_damage_stats = self._find_best_screenshot(session, 'damage') or self._find_best_screenshot(session, 'damage_stats')
            
            if not best_scoreboard or not best_damage_stats:
                logger.warning("Cannot merge session data - missing required screen types")
                return
            
            # Use the fusion engine to combine data from different screenshots
            fused_result = self.fusion_engine.parse_screenshot_pair(
                best_scoreboard.image_path,
                best_damage_stats.image_path,
                session.target_ign
            )
            
            if fused_result:
                # Create merged analysis with proper null handling
                merged_analysis = {
                    'session_id': session.session_id,
                    'ign': session.target_ign,
                    'hero': session.hero_id,
                    'player_located': fused_result.player_ign == session.target_ign,
                    'player_ign': fused_result.player_ign,
                    
                    # KDA data from scoreboard (never null when scoreboard exists)
                    'kda': {
                        'kills': fused_result.kills,
                        'deaths': fused_result.deaths,
                        'assists': fused_result.assists
                    },
                    
                    # Damage stats from damage view (never null when damage view exists)
                    'damage_stats': {
                        'hero_damage': fused_result.hero_damage if fused_result.hero_damage > 0 else None,
                        'damage_taken': fused_result.damage_taken if fused_result.damage_taken > 0 else None,
                        'turret_damage': fused_result.tower_damage if fused_result.tower_damage > 0 else None,
                        'teamfight_participation': fused_result.teamfight_participation if fused_result.teamfight_participation > 0 else None
                    },
                    
                    # Additional metrics from fusion
                    'gold_per_minute': fused_result.gold_per_minute if fused_result.gold_per_minute > 0 else None,
                    'kda_ratio': fused_result.kda_ratio,
                    'mvp_score': fused_result.mvp_score,
                    
                    # Quality metrics
                    'overall_confidence': fused_result.overall_confidence,
                    'data_completeness': fused_result.data_completeness,
                    'fusion_method': fused_result.fusion_method,
                    
                    # Source information
                    'sources': {
                        'scoreboard': {
                            'image_path': best_scoreboard.image_path,
                            'processing_time': best_scoreboard.processing_time,
                            'confidence': best_scoreboard.kda_result.confidence if best_scoreboard.kda_result else 0.0
                        },
                        'damage_stats': {
                            'image_path': best_damage_stats.image_path,
                            'processing_time': best_damage_stats.processing_time,
                            'confidence': best_damage_stats.damage_result.confidence if best_damage_stats.damage_result else 0.0
                        }
                    }
                }
                
                logger.info(f"Setting session.is_complete = True for {session.session_id}")
                session.merged_analysis = merged_analysis
                session.is_complete = True
                
                logger.info(f"Successfully merged session data for {session.session_id}")
                logger.info(f"Session completeness: {session.is_complete}")
                
            else:
                logger.warning(f"Failed to merge session data for {session.session_id}")
            
        except Exception as e:
            logger.error(f"Error merging session data for session {session.session_id}: {e}")
    
    def _find_best_screenshot(self, session: GameSession, screen_type: str) -> Optional[ScreenshotAnalysis]:
        """Find the best screenshot of a given type based on confidence."""
        candidates = [s for s in session.screenshots if s.screen_type == screen_type]
        
        if not candidates:
            return None
        
        # Select based on confidence score
        if screen_type == 'scoreboard':
            # Use KDA result confidence
            best = max(candidates, key=lambda s: s.kda_result.confidence if s.kda_result else 0.0)
        else:
            # Use damage result confidence
            best = max(candidates, key=lambda s: s.damage_result.confidence if s.damage_result else 0.0)
        
        return best
    
    def get_session_analysis(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the current analysis for a session."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # If session is complete, return merged analysis
        if session.is_complete and session.merged_analysis:
            return session.merged_analysis
        
        # Otherwise, return best available partial analysis
        return self._get_partial_analysis(session)
    
    def _get_partial_analysis(self, session: GameSession) -> Dict[str, Any]:
        """Get the best available partial analysis when session is incomplete."""
        best_scoreboard = self._find_best_screenshot(session, 'scoreboard')
        best_damage_stats = self._find_best_screenshot(session, 'damage') or self._find_best_screenshot(session, 'damage_stats')
        
        analysis = {
            'session_id': session.session_id,
            'ign': session.target_ign,
            'hero': session.hero_id,
            'player_located': False,
            'player_ign': None,
            'session_complete': False,
            'missing_screens': []
        }
        
        if best_scoreboard and best_scoreboard.kda_result:
            kda = best_scoreboard.kda_result
            analysis.update({
                'player_located': True,
                'player_ign': kda.player_ign,
                'kda': {
                    'kills': kda.kills,
                    'deaths': kda.deaths,
                    'assists': kda.assists
                }
            })
        else:
            analysis['missing_screens'].append('scoreboard')
        
        if best_damage_stats and best_damage_stats.damage_result:
            damage = best_damage_stats.damage_result
            analysis['damage_stats'] = {
                'hero_damage': damage.hero_damage if damage.hero_damage > 0 else None,
                'damage_taken': damage.damage_taken if damage.damage_taken > 0 else None,
                'turret_damage': damage.tower_damage if damage.tower_damage > 0 else None,
                'teamfight_participation': damage.teamfight_participation if damage.teamfight_participation > 0 else None
            }
            if 'gold_per_minute' in damage.raw_data:
                analysis['gold_per_minute'] = damage.raw_data['gold_per_minute']
        else:
            analysis['missing_screens'].append('damage_stats')
        
        return analysis
    
    def complete_session(self, session_id: str) -> Dict[str, Any]:
        """Mark a session as complete and return final analysis."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        final_analysis = self.get_session_analysis(session_id)
        
        logger.info(f"Completed session {session_id} with final analysis")
        
        return {
            'session_id': session_id,
            'final_analysis': final_analysis,
            'screenshots_processed': len(session.screenshots),
            'is_complete': session.is_complete
        }
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions to prevent memory leaks."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        sessions_to_remove = []
        for session_id, session in self.sessions.items():
            if session.created_at.timestamp() < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            logger.info(f"Cleaned up old session {session_id}")
        
        return len(sessions_to_remove)

# Global instance for easy access
session_analysis_service = SessionAnalysisService()