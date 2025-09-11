#!/usr/bin/env python3
"""
OCR Microservice for MLBB Coach AI
Dedicated service for OCR processing with health checks and monitoring
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
from typing import Dict, Any, Optional
import time
import tempfile
from PIL import Image
import numpy as np

from core.services.ocr_service import OCRService
from core.observability.metrics_collector import MetricsCollector
from core.observability.logger_config import setup_logging

# Setup logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MLBB Coach AI - OCR Service",
    description="Dedicated OCR processing service",
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
ocr_service = OCRService()
metrics_collector = MetricsCollector()

class OCRRequest(BaseModel):
    """OCR processing request model"""
    image_data: Optional[str] = None  # Base64 encoded image
    preprocessing_options: Dict[str, Any] = {}
    ocr_engine: str = "easyocr"  # easyocr, tesseract, or both

class OCRResponse(BaseModel):
    """OCR processing response model"""
    extracted_text: str
    confidence: float
    bounding_boxes: list
    processing_time: float
    engine_used: str
    success: bool
    error_message: Optional[str] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test OCR service
        test_result = await ocr_service.health_check()
        
        return {
            "status": "healthy",
            "service": "ocr-service",
            "version": "1.0.0",
            "timestamp": time.time(),
            "ocr_service_status": test_result.status.value,
            "uptime": time.time() - start_time
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/process", response_model=OCRResponse)
async def process_ocr(request: OCRRequest):
    """Process OCR request"""
    start_time = time.time()
    
    try:
        logger.info(f"Processing OCR request with engine: {request.ocr_engine}")
        
        # Process the OCR request
        result = await ocr_service.process_text_extraction(
            image_data=request.image_data,
            preprocessing_options=request.preprocessing_options,
            engine=request.ocr_engine
        )
        
        processing_time = time.time() - start_time
        
        # Update metrics
        metrics_collector.record_request_duration("ocr_process", processing_time)
        metrics_collector.increment_counter("ocr_requests_total")
        
        if result.success:
            metrics_collector.increment_counter("ocr_requests_success")
        else:
            metrics_collector.increment_counter("ocr_requests_failed")
        
        return OCRResponse(
            extracted_text=result.data.get("text", ""),
            confidence=result.data.get("confidence", 0.0),
            bounding_boxes=result.data.get("bounding_boxes", []),
            processing_time=processing_time,
            engine_used=request.ocr_engine,
            success=result.success,
            error_message=result.error if not result.success else None
        )
        
    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        metrics_collector.increment_counter("ocr_requests_failed")
        
        return OCRResponse(
            extracted_text="",
            confidence=0.0,
            bounding_boxes=[],
            processing_time=time.time() - start_time,
            engine_used=request.ocr_engine,
            success=False,
            error_message=str(e)
        )

@app.post("/upload-process")
async def upload_and_process(file: UploadFile = File(...)):
    """Upload image and process OCR"""
    start_time = time.time()
    
    try:
        # Read uploaded file
        contents = await file.read()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
        
        try:
            # Process with OCR service
            result = await ocr_service.process_image_file(temp_path)
            
            processing_time = time.time() - start_time
            
            # Update metrics
            metrics_collector.record_request_duration("ocr_upload_process", processing_time)
            metrics_collector.increment_counter("ocr_upload_requests_total")
            
            return OCRResponse(
                extracted_text=result.data.get("text", ""),
                confidence=result.data.get("confidence", 0.0),
                bounding_boxes=result.data.get("bounding_boxes", []),
                processing_time=processing_time,
                engine_used="easyocr",
                success=result.success,
                error_message=result.error if not result.success else None
            )
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Upload OCR processing failed: {e}")
        metrics_collector.increment_counter("ocr_upload_requests_failed")
        
        return OCRResponse(
            extracted_text="",
            confidence=0.0,
            bounding_boxes=[],
            processing_time=time.time() - start_time,
            engine_used="easyocr",
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
        "service": "ocr-service",
        "status": "running",
        "version": "1.0.0",
        "uptime": time.time() - start_time,
        "metrics": metrics_collector.get_metrics(),
        "ocr_engines": ["easyocr", "tesseract"],
        "capabilities": [
            "text_extraction",
            "confidence_scoring",
            "bounding_box_detection",
            "preprocessing_optimization"
        ]
    }

# Global start time for uptime calculation
start_time = time.time()

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8001))
    
    logger.info(f"Starting OCR Service on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="info"
    )
