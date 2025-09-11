"""
Contract tests for POST /ocr/fusion endpoint.

Tests the OCR fusion API endpoint to ensure it follows the expected contract
and can handle KDA and Damage view fusion scenarios.
"""

import pytest
import json
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the FastAPI app (assuming it exists)
try:
    from web.app import app
except ImportError:
    # Create a mock app for testing
    from fastapi import FastAPI
    app = FastAPI()


class TestOCRFusionAPI:
    """Contract tests for OCR fusion API."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def valid_fusion_request(self):
        """Valid OCR fusion request payload."""
        return {
            "kda_image_path": str(project_root.parent / "Trial-Image" / "IMG_1767.PNG"),
            "damage_image_path": str(project_root.parent / "Trial-Image" / "IMG_1768.PNG"),
            "target_ign": "Diary of dolls",
            "fusion_mode": "intelligent"
        }
    
    def test_ocr_fusion_endpoint_exists(self, client):
        """Test that the OCR fusion endpoint exists."""
        # This test will fail until the endpoint is implemented
        # but it documents the expected contract
        response = client.post("/ocr/fusion", json={})
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404, "OCR fusion endpoint should exist"
    
    def test_ocr_fusion_valid_request(self, client, valid_fusion_request):
        """Test OCR fusion with valid request."""
        response = client.post("/ocr/fusion", json=valid_fusion_request)
        
        # Should return 200 for valid request
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            assert "success" in data, "Response should have success field"
            assert "fused_result" in data, "Response should have fused_result field"
            assert "fusion_method" in data, "Response should have fusion_method field"
            assert "overall_confidence" in data, "Response should have overall_confidence field"
            
            if data["success"]:
                # Validate fused result structure
                fused_result = data["fused_result"]
                assert "player_ign" in fused_result, "Fused result should have player_ign"
                assert "hero" in fused_result, "Fused result should have hero"
                assert "kills" in fused_result, "Fused result should have kills"
                assert "deaths" in fused_result, "Fused result should have deaths"
                assert "assists" in fused_result, "Fused result should have assists"
                assert "hero_damage" in fused_result, "Fused result should have hero_damage"
                assert "overall_confidence" in fused_result, "Fused result should have overall_confidence"
                assert "data_completeness" in fused_result, "Fused result should have data_completeness"
    
    def test_ocr_fusion_missing_kda_image(self, client):
        """Test OCR fusion with missing KDA image."""
        request = {
            "damage_image_path": str(project_root.parent / "Trial-Image" / "IMG_1768.PNG"),
            "target_ign": "Diary of dolls"
        }
        
        response = client.post("/ocr/fusion", json=request)
        
        # Should return 400 for missing required field
        assert response.status_code in [400, 422], "Should return error for missing KDA image"
    
    def test_ocr_fusion_missing_damage_image(self, client):
        """Test OCR fusion with missing damage image."""
        request = {
            "kda_image_path": str(project_root.parent / "Trial-Image" / "IMG_1767.PNG"),
            "target_ign": "Diary of dolls"
        }
        
        response = client.post("/ocr/fusion", json=request)
        
        # Should return 400 for missing required field
        assert response.status_code in [400, 422], "Should return error for missing damage image"
    
    def test_ocr_fusion_missing_target_ign(self, client):
        """Test OCR fusion with missing target IGN."""
        request = {
            "kda_image_path": str(project_root.parent / "Trial-Image" / "IMG_1767.PNG"),
            "damage_image_path": str(project_root.parent / "Trial-Image" / "IMG_1768.PNG")
        }
        
        response = client.post("/ocr/fusion", json=request)
        
        # Should return 400 for missing required field
        assert response.status_code in [400, 422], "Should return error for missing target_ign"
    
    def test_ocr_fusion_invalid_image_paths(self, client):
        """Test OCR fusion with invalid image paths."""
        request = {
            "kda_image_path": "/nonexistent/kda.png",
            "damage_image_path": "/nonexistent/damage.png",
            "target_ign": "Diary of dolls"
        }
        
        response = client.post("/ocr/fusion", json=request)
        
        # Should return 400 or 422 for invalid images
        assert response.status_code in [400, 422], "Should return error for invalid images"
    
    def test_ocr_fusion_different_fusion_modes(self, client, valid_fusion_request):
        """Test OCR fusion with different fusion modes."""
        fusion_modes = ["intelligent", "kda_priority", "damage_priority", "confidence_weighted"]
        
        for mode in fusion_modes:
            request = valid_fusion_request.copy()
            request["fusion_mode"] = mode
            
            response = client.post("/ocr/fusion", json=request)
            
            if response.status_code == 200:
                data = response.json()
                assert "success" in data, f"Response should have success field for mode {mode}"
    
    def test_ocr_fusion_single_view_fallback(self, client):
        """Test OCR fusion with only one view (fallback behavior)."""
        # Test with only KDA view
        request = {
            "kda_image_path": str(project_root.parent / "Trial-Image" / "IMG_1767.PNG"),
            "damage_image_path": None,
            "target_ign": "Diary of dolls"
        }
        
        response = client.post("/ocr/fusion", json=request)
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data, "Should handle single view fallback"
            if data["success"]:
                assert data["fusion_method"] in ["kda_only", "damage_only"], "Should indicate single view method"
    
    def test_ocr_fusion_response_time(self, client, valid_fusion_request):
        """Test that OCR fusion responds within reasonable time."""
        import time
        
        start_time = time.time()
        response = client.post("/ocr/fusion", json=valid_fusion_request)
        response_time = time.time() - start_time
        
        # Should respond within 60 seconds (fusion takes longer)
        assert response_time < 60, f"OCR fusion should respond within 60s, took {response_time:.2f}s"
    
    def test_ocr_fusion_conflict_resolution(self, client, valid_fusion_request):
        """Test OCR fusion conflict resolution."""
        response = client.post("/ocr/fusion", json=valid_fusion_request)
        
        if response.status_code == 200:
            data = response.json()
            
            if data["success"] and "conflicts_resolved" in data["fused_result"]:
                conflicts = data["fused_result"]["conflicts_resolved"]
                assert isinstance(conflicts, list), "Conflicts resolved should be a list"
    
    def test_ocr_fusion_error_handling(self, client):
        """Test OCR fusion error handling."""
        # Test with malformed JSON
        response = client.post("/ocr/fusion", data="invalid json")
        assert response.status_code == 422, "Should return 422 for malformed JSON"
        
        # Test with empty request
        response = client.post("/ocr/fusion", json={})
        assert response.status_code in [400, 422], "Should return error for empty request"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
