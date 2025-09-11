#!/usr/bin/env python3
"""
Detection Microservice for MLBB Coach AI
Dedicated service for YOLO detection and computer vision processing
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add core modules to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import time
import tempfile
import json

from core.services.detection_service import DetectionService
from core.services.yolo_detection_service import get_yolo_detection_service
from core.observability.metrics_collector import MetricsCollector
from core.observability.logger_config import setup_logging

# Setup logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MLBB Coach AI - Detection Service",
    description="Dedicated YOLO detection and computer vision service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
detection_service = DetectionService()
yolo_service = get_yolo_detection_service()
metrics_collector = MetricsCollector()

class DetectionRequest(BaseModel):
    """Detection processing request model"""
    image_data: Optional[str] = None  # Base64 encoded image
    detection_types: List[str] = ["heroes", "medals", "ui_elements"]
    confidence_threshold: float = 0.5
    use_yolo: bool = True
    use_traditional_cv: bool = True

class DetectionResult(BaseModel):
    """Individual detection result"""
    class_name: str
    confidence: float
    bounding_box: List[float]  # [x1, y1, x2, y2]
    center_point: List[float]  # [x, y]
    detection_method: str

class DetectionResponse(BaseModel):
    """Detection processing response model"""
    detections: List[DetectionResult]
    total_detections: int
    processing_time: float
    methods_used: List[str]
    success: bool
    error_message: Optional[str] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test detection services
        detection_health = await detection_service.health_check()
        yolo_health = await yolo_service.health_check()
        
        return {
            "status": "healthy",
            "service": "detection-service",
            "version": "1.0.0",
            "timestamp": time.time(),
            "detection_service_status": detection_health.status.value,
            "yolo_service_status": yolo_health.status.value,
            "uptime": time.time() - start_time
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/detect", response_model=DetectionResponse)
async def detect_objects(request: DetectionRequest):
    """Process detection request"""
    start_time_req = time.time()
    
    try:
        logger.info(f"Processing detection request for types: {request.detection_types}")
        
        detections = []
        methods_used = []
        
        # YOLO Detection
        if request.use_yolo:
            try:
                yolo_result = await yolo_service.detect_objects(
                    image_data=request.image_data,
                    confidence_threshold=request.confidence_threshold,
                    detection_classes=request.detection_types
                )
                
                if yolo_result.success:
                    methods_used.append("yolo")
                    for detection in yolo_result.data.get("detections", []):
                        detections.append(DetectionResult(
                            class_name=detection["class"],
                            confidence=detection["confidence"],
                            bounding_box=detection["bbox"],
                            center_point=detection["center"],
                            detection_method="yolo"
                        ))
                        
            except Exception as e:
                logger.warning(f"YOLO detection failed: {e}")
        
        # Traditional CV Detection
        if request.use_traditional_cv:
            try:
                cv_result = await detection_service.detect_traditional(
                    image_data=request.image_data,
                    detection_types=request.detection_types,
                    confidence_threshold=request.confidence_threshold
                )
                
                if cv_result.success:
                    methods_used.append("traditional_cv")
                    for detection in cv_result.data.get("detections", []):
                        detections.append(DetectionResult(
                            class_name=detection["class"],
                            confidence=detection["confidence"],
                            bounding_box=detection["bbox"],
                            center_point=detection["center"],
                            detection_method="traditional_cv"
                        ))
                        
            except Exception as e:
                logger.warning(f"Traditional CV detection failed: {e}")
        
        processing_time = time.time() - start_time_req
        
        # Update metrics
        metrics_collector.record_request_duration("detection_process", processing_time)
        metrics_collector.increment_counter("detection_requests_total")
        metrics_collector.increment_counter("detection_requests_success")
        
        return DetectionResponse(
            detections=detections,
            total_detections=len(detections),
            processing_time=processing_time,
            methods_used=methods_used,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Detection processing failed: {e}")
        metrics_collector.increment_counter("detection_requests_failed")
        
        return DetectionResponse(
            detections=[],
            total_detections=0,
            processing_time=time.time() - start_time_req,
            methods_used=[],
            success=False,
            error_message=str(e)
        )

@app.post("/detect-heroes")
async def detect_heroes(file: UploadFile = File(...)):
    """Specialized hero detection endpoint"""
    start_time_req = time.time()
    
    try:
        # Read uploaded file
        contents = await file.read()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
        
        try:
            # Process with detection service
            result = await detection_service.detect_heroes_from_file(temp_path)
            
            processing_time = time.time() - start_time_req
            
            # Update metrics
            metrics_collector.record_request_duration("hero_detection", processing_time)
            metrics_collector.increment_counter("hero_detection_requests_total")
            
            hero_detections = []
            if result.success:
                for hero in result.data.get("heroes", []):
                    hero_detections.append(DetectionResult(
                        class_name=hero["name"],
                        confidence=hero["confidence"],
                        bounding_box=hero["bbox"],
                        center_point=hero["center"],
                        detection_method="premium_detector"
                    ))
            
            return DetectionResponse(
                detections=hero_detections,
                total_detections=len(hero_detections),
                processing_time=processing_time,
                methods_used=["premium_detector"],
                success=result.success,
                error_message=result.error if not result.success else None
            )
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Hero detection failed: {e}")
        metrics_collector.increment_counter("hero_detection_requests_failed")
        
        return DetectionResponse(
            detections=[],
            total_detections=0,
            processing_time=time.time() - start_time_req,
            methods_used=[],
            success=False,
            error_message=str(e)
        )

@app.post("/detect-medals")
async def detect_medals(file: UploadFile = File(...)):
    """Specialized medal detection endpoint"""
    start_time_req = time.time()
    
    try:
        # Read uploaded file
        contents = await file.read()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
        
        try:
            # Process with detection service
            result = await detection_service.detect_medals_from_file(temp_path)
            
            processing_time = time.time() - start_time_req
            
            # Update metrics
            metrics_collector.record_request_duration("medal_detection", processing_time)
            metrics_collector.increment_counter("medal_detection_requests_total")
            
            medal_detections = []
            if result.success:
                for medal in result.data.get("medals", []):
                    medal_detections.append(DetectionResult(
                        class_name=medal["type"],
                        confidence=medal["confidence"],
                        bounding_box=medal["bbox"],
                        center_point=medal["center"],
                        detection_method="trophy_detector_v3"
                    ))
            
            return DetectionResponse(
                detections=medal_detections,
                total_detections=len(medal_detections),
                processing_time=processing_time,
                methods_used=["trophy_detector_v3"],
                success=result.success,
                error_message=result.error if not result.success else None
            )
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Medal detection failed: {e}")
        metrics_collector.increment_counter("medal_detection_requests_failed")
        
        return DetectionResponse(
            detections=[],
            total_detections=0,
            processing_time=time.time() - start_time_req,
            methods_used=[],
            success=False,
            error_message=str(e)
        )

@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    return metrics_collector.get_metrics()

@app.get("/status")
async def get_status():
    """Get detailed service status"""
    return {
        "service": "detection-service",
        "status": "running",
        "version": "1.0.0",
        "uptime": time.time() - start_time,
        "metrics": metrics_collector.get_metrics(),
        "detection_methods": ["yolo", "traditional_cv", "premium_detector", "trophy_detector_v3"],
        "supported_classes": ["heroes", "medals", "ui_elements", "mvp_badges"],
        "capabilities": [
            "hero_detection",
            "medal_detection", 
            "ui_element_detection",
            "multi_method_ensemble",
            "confidence_scoring"
        ]
    }

# Global start time for uptime calculation
start_time = time.time()

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8002))
    
    logger.info(f"Starting Detection Service on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="info"
    )
