#!/usr/bin/env python3
"""
Analysis Microservice for MLBB Coach AI
Dedicated service for AI coaching and performance analysis
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add core modules to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import time
import json

from core.services.analysis_service import AnalysisService
from core.services.behavioral_modeling_service import BehavioralModelingService
from core.services.tactical_coaching_service import TacticalCoachingService
from core.observability.metrics_collector import MetricsCollector
from core.observability.logger_config import setup_logging

# Setup logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MLBB Coach AI - Analysis Service",
    description="Dedicated AI coaching and performance analysis service",
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
analysis_service = AnalysisService()
behavioral_service = BehavioralModelingService()
tactical_service = TacticalCoachingService()
metrics_collector = MetricsCollector()

class AnalysisRequest(BaseModel):
    """Analysis processing request model"""
    match_data: Dict[str, Any]
    analysis_types: List[str] = ["performance", "coaching", "behavioral"]
    player_ign: Optional[str] = None
    hero_name: Optional[str] = None
    include_coaching: bool = True
    include_mental_boost: bool = True

class CoachingInsight(BaseModel):
    """Individual coaching insight"""
    category: str
    severity: str
    message: str
    recommendation: str
    confidence: float

class AnalysisResponse(BaseModel):
    """Analysis processing response model"""
    overall_score: float
    performance_metrics: Dict[str, Any]
    coaching_insights: List[CoachingInsight]
    behavioral_profile: Dict[str, Any]
    tactical_analysis: Dict[str, Any]
    mental_boost_message: str
    processing_time: float
    success: bool
    error_message: Optional[str] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test analysis services
        analysis_health = await analysis_service.health_check()
        behavioral_health = await behavioral_service.health_check()
        tactical_health = await tactical_service.health_check()
        
        return {
            "status": "healthy",
            "service": "analysis-service",
            "version": "1.0.0",
            "timestamp": time.time(),
            "analysis_service_status": analysis_health.status.value,
            "behavioral_service_status": behavioral_health.status.value,
            "tactical_service_status": tactical_health.status.value,
            "uptime": time.time() - start_time
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_match(request: AnalysisRequest):
    """Process comprehensive match analysis"""
    start_time_req = time.time()
    
    try:
        logger.info(f"Processing analysis request for types: {request.analysis_types}")
        
        results = {}
        
        # Performance Analysis
        if "performance" in request.analysis_types:
            perf_result = await analysis_service.analyze_performance(
                match_data=request.match_data,
                player_ign=request.player_ign,
                hero_name=request.hero_name
            )
            results["performance"] = perf_result.data if perf_result.success else {}
        
        # Behavioral Analysis
        if "behavioral" in request.analysis_types:
            behavioral_result = await behavioral_service.analyze_behavior(
                match_data=request.match_data,
                player_ign=request.player_ign
            )
            results["behavioral"] = behavioral_result.data if behavioral_result.success else {}
        
        # Tactical Analysis
        if "coaching" in request.analysis_types:
            tactical_result = await tactical_service.generate_coaching(
                match_data=request.match_data,
                player_ign=request.player_ign,
                hero_name=request.hero_name
            )
            results["tactical"] = tactical_result.data if tactical_result.success else {}
        
        # Compile coaching insights
        coaching_insights = []
        if results.get("tactical", {}).get("insights"):
            for insight in results["tactical"]["insights"]:
                coaching_insights.append(CoachingInsight(
                    category=insight.get("category", "general"),
                    severity=insight.get("severity", "info"),
                    message=insight.get("message", ""),
                    recommendation=insight.get("recommendation", ""),
                    confidence=insight.get("confidence", 0.8)
                ))
        
        processing_time = time.time() - start_time_req
        
        # Update metrics
        metrics_collector.record_request_duration("analysis_process", processing_time)
        metrics_collector.increment_counter("analysis_requests_total")
        metrics_collector.increment_counter("analysis_requests_success")
        
        return AnalysisResponse(
            overall_score=results.get("performance", {}).get("overall_score", 0.0),
            performance_metrics=results.get("performance", {}).get("metrics", {}),
            coaching_insights=coaching_insights,
            behavioral_profile=results.get("behavioral", {}).get("profile", {}),
            tactical_analysis=results.get("tactical", {}).get("analysis", {}),
            mental_boost_message=results.get("tactical", {}).get("mental_boost", "Keep improving!"),
            processing_time=processing_time,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Analysis processing failed: {e}")
        metrics_collector.increment_counter("analysis_requests_failed")
        
        return AnalysisResponse(
            overall_score=0.0,
            performance_metrics={},
            coaching_insights=[],
            behavioral_profile={},
            tactical_analysis={},
            mental_boost_message="Analysis temporarily unavailable",
            processing_time=time.time() - start_time_req,
            success=False,
            error_message=str(e)
        )

@app.post("/coaching-only")
async def generate_coaching(request: AnalysisRequest):
    """Generate coaching insights only"""
    start_time_req = time.time()
    
    try:
        # Generate tactical coaching
        result = await tactical_service.generate_coaching(
            match_data=request.match_data,
            player_ign=request.player_ign,
            hero_name=request.hero_name
        )
        
        processing_time = time.time() - start_time_req
        
        # Update metrics
        metrics_collector.record_request_duration("coaching_only", processing_time)
        metrics_collector.increment_counter("coaching_requests_total")
        
        if result.success:
            coaching_insights = []
            for insight in result.data.get("insights", []):
                coaching_insights.append(CoachingInsight(
                    category=insight.get("category", "general"),
                    severity=insight.get("severity", "info"),
                    message=insight.get("message", ""),
                    recommendation=insight.get("recommendation", ""),
                    confidence=insight.get("confidence", 0.8)
                ))
            
            return {
                "coaching_insights": coaching_insights,
                "mental_boost_message": result.data.get("mental_boost", "Keep improving!"),
                "processing_time": processing_time,
                "success": True
            }
        else:
            return {
                "coaching_insights": [],
                "mental_boost_message": "Coaching temporarily unavailable",
                "processing_time": processing_time,
                "success": False,
                "error_message": result.error
            }
            
    except Exception as e:
        logger.error(f"Coaching generation failed: {e}")
        metrics_collector.increment_counter("coaching_requests_failed")
        
        return {
            "coaching_insights": [],
            "mental_boost_message": "Coaching temporarily unavailable",
            "processing_time": time.time() - start_time_req,
            "success": False,
            "error_message": str(e)
        }

@app.post("/behavioral-analysis")
async def analyze_behavior(request: AnalysisRequest):
    """Generate behavioral analysis only"""
    start_time_req = time.time()
    
    try:
        # Generate behavioral analysis
        result = await behavioral_service.analyze_behavior(
            match_data=request.match_data,
            player_ign=request.player_ign
        )
        
        processing_time = time.time() - start_time_req
        
        # Update metrics
        metrics_collector.record_request_duration("behavioral_analysis", processing_time)
        metrics_collector.increment_counter("behavioral_requests_total")
        
        return {
            "behavioral_profile": result.data if result.success else {},
            "processing_time": processing_time,
            "success": result.success,
            "error_message": result.error if not result.success else None
        }
        
    except Exception as e:
        logger.error(f"Behavioral analysis failed: {e}")
        metrics_collector.increment_counter("behavioral_requests_failed")
        
        return {
            "behavioral_profile": {},
            "processing_time": time.time() - start_time_req,
            "success": False,
            "error_message": str(e)
        }

@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    return metrics_collector.get_metrics()

@app.get("/status")
async def get_status():
    """Get detailed service status"""
    return {
        "service": "analysis-service",
        "status": "running",
        "version": "1.0.0",
        "uptime": time.time() - start_time,
        "metrics": metrics_collector.get_metrics(),
        "analysis_types": ["performance", "coaching", "behavioral", "tactical"],
        "capabilities": [
            "performance_analysis",
            "ai_coaching",
            "behavioral_modeling",
            "tactical_insights",
            "mental_boost_generation"
        ]
    }

# Global start time for uptime calculation
start_time = time.time()

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8003))
    
    logger.info(f"Starting Analysis Service on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="info"
    )
