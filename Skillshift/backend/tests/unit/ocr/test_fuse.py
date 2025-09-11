#!/usr/bin/env python3
"""
T011: Cross-View Fusion Test Suite - OCR Data Fusion Tests
Tests fusion of KDA view (IMG_1767) + Damage view (IMG_1768) for "Diary of dolls" → Kagura

Target Requirements:
- Merge KDA extraction + Damage extraction into unified result
- Handle conflicts between views with confidence-based resolution
- Achieve ≥0.85 overall_confidence and ≥0.85 data_completeness
- Comprehensive player data: hero=Kagura, KDA=9/2/12, MVP=10.5, damage_pct
- Explicit conflict resolution and data validation

TDD Status: MUST FAIL before implementation exists
"""

import pytest
from unittest.mock import Mock, patch
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

# Import functions that don't exist yet (TDD - must fail)
from backend.ocr.fuse import (
    fuse_cross_view_data,
    resolve_data_conflicts,
    validate_fused_result,
    CrossViewFusionResult,
    FusionConflict
)

# Import result types from other parsers (also don't exist yet)
from backend.ocr.parsers_kda import KDAViewResult
from backend.ocr.parsers_damage import DamageViewResult


class TestCrossViewFusion:
    """Core cross-view data fusion functionality"""
    
    def test_fuse_cross_view_complete_success(self, mock_kda_result, mock_damage_result):
        """T011-1: Complete fusion of KDA + Damage views for Diary of dolls → Kagura"""
        target_ign = "Diary of dolls"
        
        result = fuse_cross_view_data(
            kda_result=mock_kda_result,
            damage_result=mock_damage_result,
            target_ign=target_ign
        )
        
        # Core fusion requirements
        assert isinstance(result, CrossViewFusionResult), "Invalid fusion result type"
        assert result.player_ign == target_ign, f"Player IGN mismatch: {result.player_ign}"
        assert result.hero == "kagura", f"Hero mismatch: {result.hero}"
        
        # Target data completeness and confidence
        assert result.overall_confidence >= 0.85, f"Overall confidence {result.overall_confidence} below 0.85"
        assert result.data_completeness >= 0.85, f"Data completeness {result.data_completeness} below 0.85"
        
        # Complete data validation
        assert result.kda is not None, "KDA data missing from fusion"
        assert result.kda["k"] == 9 and result.kda["d"] == 2 and result.kda["a"] == 12, "Incorrect KDA values"
        assert result.mvp_score == 10.5, f"MVP score mismatch: {result.mvp_score}"
        assert result.player_located is True, "Player not located after fusion"
    
    def test_fuse_cross_view_with_conflicts(self, conflicting_kda_result, conflicting_damage_result):
        """T011-2: Handle conflicts between KDA and Damage view data"""
        result = fuse_cross_view_data(
            kda_result=conflicting_kda_result,
            damage_result=conflicting_damage_result,
            target_ign="Diary of dolls"
        )
        
        # Should have conflict resolution
        assert hasattr(result, 'conflicts'), "Fusion result should track conflicts"
        assert len(result.conflicts) > 0, "No conflicts detected in conflicting data"
        
        # Should still produce valid result with conflict resolution
        assert result.overall_confidence > 0.5, "Confidence too low after conflict resolution"
        assert result.hero is not None, "Hero should be resolved despite conflicts"
        
    def test_fuse_cross_view_confidence_weighting(self, high_conf_kda, low_conf_damage):
        """T011-3: Confidence-based data weighting in fusion"""
        result = fuse_cross_view_data(
            kda_result=high_conf_kda,
            damage_result=low_conf_damage,
            target_ign="Diary of dolls"
        )
        
        # High confidence KDA should dominate low confidence damage
        assert result.kda == high_conf_kda.kda, "High confidence KDA not preserved"
        assert result.hero == high_conf_kda.hero, "High confidence hero not preserved"
        
        # Overall confidence should reflect weighting
        expected_conf = (high_conf_kda.confidence * 0.7 + low_conf_damage.confidence * 0.3)
        assert abs(result.overall_confidence - expected_conf) < 0.1, "Confidence weighting incorrect"


class TestConflictResolution:
    """Data conflict detection and resolution"""
    
    def test_resolve_hero_conflicts(self):
        """T011-4: Resolve hero name conflicts between views"""
        kda_hero = "kagura"
        damage_hero = "kadita"  # OCR error
        
        conflicts = resolve_data_conflicts(
            kda_data={"hero": kda_hero, "confidence": 0.9},
            damage_data={"hero": damage_hero, "confidence": 0.6}
        )
        
        # Should detect hero conflict
        hero_conflict = next((c for c in conflicts if c.field == "hero"), None)
        assert hero_conflict is not None, "Hero conflict not detected"
        
        # Should resolve to higher confidence value
        assert hero_conflict.resolved_value == kda_hero, "Hero conflict not resolved to higher confidence"
        assert hero_conflict.confidence_diff > 0.2, "Confidence difference not tracked"
    
    def test_resolve_kda_conflicts(self):
        """T011-5: Resolve KDA value conflicts with validation"""
        kda_data = {"kda": {"k": 9, "d": 2, "a": 12}, "confidence": 0.85}
        damage_data = {"kda": {"k": 8, "d": 2, "a": 11}, "confidence": 0.70}  # Slight OCR differences
        
        conflicts = resolve_data_conflicts(kda_data=kda_data, damage_data=damage_data)
        
        kda_conflict = next((c for c in conflicts if c.field == "kda"), None)
        if kda_conflict:
            # Should prefer higher confidence KDA data
            assert kda_conflict.resolved_value == kda_data["kda"], "KDA conflict not resolved correctly"


class TestFusionValidation:
    """Validation of fused results"""
    
    def test_validate_fused_result_complete(self, complete_fusion_result):
        """T011-6: Validate complete fusion result meets requirements"""
        is_valid, validation_errors = validate_fused_result(complete_fusion_result)
        
        assert is_valid is True, f"Complete fusion result validation failed: {validation_errors}"
        assert len(validation_errors) == 0, f"Unexpected validation errors: {validation_errors}"
        
        # Specific validation checks
        assert complete_fusion_result.overall_confidence >= 0.85, "Confidence requirement not met"
        assert complete_fusion_result.data_completeness >= 0.85, "Data completeness requirement not met"
        assert complete_fusion_result.player_located is True, "Player location requirement not met"
    
    def test_validate_fused_result_incomplete(self, incomplete_fusion_result):
        """T011-7: Detect validation issues in incomplete fusion"""
        is_valid, validation_errors = validate_fused_result(incomplete_fusion_result)
        
        assert is_valid is False, "Incomplete fusion result should fail validation"
        assert len(validation_errors) > 0, "Validation errors not detected"
        
        # Should identify specific missing data
        error_messages = [str(error) for error in validation_errors]
        has_data_completeness_error = any("completeness" in msg.lower() for msg in error_messages)
        assert has_data_completeness_error, "Data completeness error not detected"


class TestFusionEdgeCases:
    """Edge cases and error handling for fusion"""
    
    def test_fuse_single_view_only(self, mock_kda_result):
        """T011-8: Handle fusion when only one view is available"""
        result = fuse_cross_view_data(
            kda_result=mock_kda_result,
            damage_result=None,  # Missing damage view
            target_ign="Diary of dolls"
        )
        
        # Should still produce valid result from single view
        assert isinstance(result, CrossViewFusionResult), "Single view fusion failed"
        assert result.hero == mock_kda_result.hero, "Single view data not preserved"
        assert result.overall_confidence < 0.85, "Confidence should be lower with single view"
        assert result.data_completeness < 0.85, "Data completeness should be lower with single view"
    
    def test_fuse_no_player_match(self, no_match_kda, no_match_damage):
        """T011-9: Handle fusion when player not found in either view"""
        result = fuse_cross_view_data(
            kda_result=no_match_kda,
            damage_result=no_match_damage,
            target_ign="Diary of dolls"
        )
        
        # Should indicate failed player location
        assert result.player_located is False, "Player located incorrectly reported as found"
        assert result.overall_confidence < 0.5, "Confidence too high for no player match"
        assert result.data_completeness < 0.3, "Data completeness too high for no matches"


# Test Fixtures
@pytest.fixture
def mock_kda_result():
    """Mock KDA view result for Diary of dolls → Kagura"""
    return Mock(spec=KDAViewResult,
                player_ign="Diary of dolls",
                hero="kagura", 
                kda={"k": 9, "d": 2, "a": 12},
                mvp_score=10.5,
                confidence=0.88,
                player_located=True)

@pytest.fixture  
def mock_damage_result():
    """Mock Damage view result for Diary of dolls → Kagura"""
    return Mock(spec=DamageViewResult,
                player_ign="Diary of dolls",
                hero="kagura",
                hero_damage_pct=18.2,
                teamfight_participation=85.0,
                confidence=0.82)

@pytest.fixture
def conflicting_kda_result(mock_kda_result):
    """KDA result with conflicting data for testing"""
    mock_kda_result.hero = "kagura"
    mock_kda_result.confidence = 0.9
    return mock_kda_result

@pytest.fixture  
def conflicting_damage_result(mock_damage_result):
    """Damage result with conflicting data for testing"""
    mock_damage_result.hero = "kadita"  # OCR error
    mock_damage_result.confidence = 0.6
    return mock_damage_result

@pytest.fixture
def high_conf_kda(mock_kda_result):
    """High confidence KDA result"""
    mock_kda_result.confidence = 0.95
    return mock_kda_result

@pytest.fixture
def low_conf_damage(mock_damage_result):
    """Low confidence damage result"""  
    mock_damage_result.confidence = 0.45
    return mock_damage_result

@pytest.fixture
def complete_fusion_result():
    """Complete fusion result meeting all requirements"""
    return Mock(spec=CrossViewFusionResult,
                player_ign="Diary of dolls",
                hero="kagura",
                kda={"k": 9, "d": 2, "a": 12},
                mvp_score=10.5,
                hero_damage_pct=18.2,
                overall_confidence=0.87,
                data_completeness=0.89,
                player_located=True,
                conflicts=[])

@pytest.fixture
def incomplete_fusion_result():
    """Incomplete fusion result for validation testing"""
    return Mock(spec=CrossViewFusionResult,
                player_ign="Diary of dolls",
                hero=None,  # Missing critical data
                kda=None,
                overall_confidence=0.45,
                data_completeness=0.32,
                player_located=False,
                conflicts=[])

@pytest.fixture
def no_match_kda():
    """KDA result with no player match"""
    return Mock(spec=KDAViewResult,
                player_ign=None,
                hero=None,
                player_located=False,
                confidence=0.15)

@pytest.fixture
def no_match_damage():
    """Damage result with no player match"""
    return Mock(spec=DamageViewResult,
                player_ign=None,
                hero=None,
                confidence=0.20)