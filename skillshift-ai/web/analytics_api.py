"""
Analytics API - REST endpoints for advanced analytics and ML pipeline
====================================================================

Provides comprehensive API endpoints for:
- Player behavior analysis
- Meta game tracking  
- ML model training and deployment
- A/B testing framework
- Data science platform integration
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Body
from pydantic import BaseModel, Field
import pandas as pd

from ..core.ml_pipeline import (
    get_training_pipeline, get_deployment_manager, get_ab_testing_framework,
    TrainingConfig, ModelType, DeploymentStrategy, ExperimentConfig, ExperimentType
)
from ..analytics import get_behavior_analyzer, get_meta_tracker
from ..core.services.base_service import ServiceResult

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PlayerBehaviorRequest(BaseModel):
    """Request model for player behavior analysis."""
    player_id: str = Field(..., description="Player ID to analyze")
    match_history: List[Dict[str, Any]] = Field(..., description="Player match history")
    force_refresh: bool = Field(False, description="Force refresh cached analysis")


class MetaAnalysisRequest(BaseModel):
    """Request model for meta game analysis."""
    match_data: List[Dict[str, Any]] = Field(..., description="Match data for analysis")
    analysis_period_days: int = Field(7, description="Analysis period in days")


class TrainingRequest(BaseModel):
    """Request model for ML model training."""
    model_type: str = Field(..., description="Type of model to train")
    model_name: str = Field(..., description="Name for the model")
    version: str = Field("1.0", description="Model version")
    data_source: str = Field("default", description="Data source for training")
    auto_deploy: bool = Field(False, description="Auto-deploy after training")
    max_epochs: int = Field(100, description="Maximum training epochs")
    min_accuracy: float = Field(0.85, description="Minimum accuracy threshold")


class DeploymentRequest(BaseModel):
    """Request model for model deployment."""
    model_name: str = Field(..., description="Model name to deploy")
    version: str = Field(..., description="Model version to deploy")
    strategy: str = Field("canary", description="Deployment strategy")
    traffic_percentage: float = Field(0.1, description="Initial traffic percentage")


class ABTestRequest(BaseModel):
    """Request model for A/B testing."""
    experiment_name: str = Field(..., description="Experiment name")
    experiment_type: str = Field("performance_comparison", description="Type of experiment")
    description: str = Field(..., description="Experiment description")
    control_model_name: str = Field(..., description="Control model name")
    control_model_version: str = Field(..., description="Control model version")
    treatment_model_name: str = Field(..., description="Treatment model name")
    treatment_model_version: str = Field(..., description="Treatment model version")
    traffic_split: float = Field(0.5, description="Traffic split for treatment")
    sample_size: int = Field(10000, description="Target sample size")
    max_duration_days: int = Field(30, description="Maximum experiment duration")


class AnalyticsResponse(BaseModel):
    """Standard analytics response model."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# PLAYER BEHAVIOR ANALYTICS ENDPOINTS
# ============================================================================

@router.post("/behavior/analyze", response_model=AnalyticsResponse)
async def analyze_player_behavior(request: PlayerBehaviorRequest):
    """
    Analyze player behavioral patterns and create behavioral profile.
    
    Returns comprehensive behavioral analysis including:
    - Playstyle classification
    - Risk profile assessment
    - Strengths and weaknesses
    - Performance patterns
    - Improvement recommendations
    """
    try:
        logger.info(f"Analyzing behavior for player: {request.player_id}")
        
        # Get behavior analyzer
        analyzer = get_behavior_analyzer()
        
        # Perform analysis
        profile = await analyzer.analyze_player_behavior(
            player_id=request.player_id,
            match_history=request.match_history,
            force_refresh=request.force_refresh
        )
        
        return AnalyticsResponse(
            success=True,
            data=profile.__dict__,
            metadata={
                "player_id": request.player_id,
                "analysis_type": "behavioral_profile",
                "sample_size": profile.sample_size,
                "confidence": profile.profile_confidence
            }
        )
        
    except Exception as e:
        logger.error(f"Behavior analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/behavior/profile/{player_id}", response_model=AnalyticsResponse)
async def get_player_profile(player_id: str):
    """Get cached behavioral profile for a player."""
    try:
        analyzer = get_behavior_analyzer()
        
        result = await analyzer.process({
            'action': 'get_cached_profile',
            'player_id': player_id
        })
        
        if result.success:
            return AnalyticsResponse(
                success=True,
                data=result.data,
                metadata=result.metadata
            )
        else:
            raise HTTPException(status_code=404, detail=result.error)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/behavior/compare", response_model=AnalyticsResponse)
async def compare_players(player_ids: List[str] = Body(..., embed=True)):
    """Compare behavioral profiles of multiple players."""
    try:
        analyzer = get_behavior_analyzer()
        
        result = await analyzer.process({
            'action': 'compare_players',
            'player_ids': player_ids
        })
        
        if result.success:
            return AnalyticsResponse(
                success=True,
                data=result.data,
                metadata=result.metadata
            )
        else:
            raise HTTPException(status_code=400, detail=result.error)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Player comparison failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# META GAME ANALYTICS ENDPOINTS
# ============================================================================

@router.post("/meta/analyze", response_model=AnalyticsResponse)
async def analyze_meta_trends(request: MetaAnalysisRequest):
    """
    Analyze meta game trends and generate comprehensive insights.
    
    Returns meta analysis including:
    - Hero tier rankings
    - Pick/ban rates
    - Win rate analysis
    - Trend identification
    - Strategic recommendations
    """
    try:
        logger.info(f"Analyzing meta trends from {len(request.match_data)} matches")
        
        # Get meta tracker
        tracker = get_meta_tracker()
        
        # Perform analysis
        insights = await tracker.analyze_meta_trends(
            match_data=request.match_data,
            analysis_period_days=request.analysis_period_days
        )
        
        return AnalyticsResponse(
            success=True,
            data=insights.__dict__,
            metadata={
                "analysis_type": "meta_trends",
                "sample_size": insights.sample_size,
                "confidence": insights.analysis_confidence,
                "data_quality": insights.data_quality
            }
        )
        
    except Exception as e:
        logger.error(f"Meta analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meta/hero/{hero_name}", response_model=AnalyticsResponse)
async def get_hero_meta_data(hero_name: str):
    """Get detailed meta data for a specific hero."""
    try:
        tracker = get_meta_tracker()
        
        result = await tracker.process({
            'action': 'get_hero_data',
            'hero_name': hero_name
        })
        
        if result.success:
            return AnalyticsResponse(
                success=True,
                data=result.data,
                metadata=result.metadata
            )
        else:
            raise HTTPException(status_code=404, detail=result.error)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hero data retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meta/tier-list", response_model=AnalyticsResponse)
async def get_current_tier_list():
    """Get current meta tier list."""
    try:
        tracker = get_meta_tracker()
        
        result = await tracker.process({
            'action': 'get_tier_list'
        })
        
        return AnalyticsResponse(
            success=True,
            data=result.data,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Tier list retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meta/compare-heroes", response_model=AnalyticsResponse)
async def compare_heroes(hero_names: List[str] = Body(..., embed=True)):
    """Compare multiple heroes in the current meta."""
    try:
        tracker = get_meta_tracker()
        
        result = await tracker.process({
            'action': 'compare_heroes',
            'hero_names': hero_names
        })
        
        return AnalyticsResponse(
            success=True,
            data=result.data,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Hero comparison failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ML TRAINING PIPELINE ENDPOINTS
# ============================================================================

@router.post("/ml/train", response_model=AnalyticsResponse)
async def start_model_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    """
    Start ML model training pipeline.
    
    Supports training various model types:
    - hero_detection: Hero detection models
    - performance_prediction: Performance prediction models
    - behavior_classification: Behavioral classification models
    - quality_assessment: Image quality assessment models
    - win_rate_prediction: Win rate prediction models
    """
    try:
        logger.info(f"Starting training for {request.model_type} model: {request.model_name}")
        
        # Get training pipeline
        pipeline = get_training_pipeline()
        
        # Create training config
        config = TrainingConfig(
            model_type=ModelType(request.model_type),
            model_name=request.model_name,
            version=request.version,
            data_source=request.data_source,
            auto_deploy=request.auto_deploy,
            max_epochs=request.max_epochs,
            min_accuracy=request.min_accuracy
        )
        
        # Start training
        training_id = await pipeline.start_training(config)
        
        return AnalyticsResponse(
            success=True,
            data={"training_id": training_id},
            metadata={
                "action": "start_training",
                "model_type": request.model_type,
                "model_name": request.model_name
            }
        )
        
    except Exception as e:
        logger.error(f"Training start failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/training/{training_id}/status", response_model=AnalyticsResponse)
async def get_training_status(training_id: str):
    """Get status of a training pipeline."""
    try:
        pipeline = get_training_pipeline()
        
        result = await pipeline.process({
            'action': 'get_status',
            'training_id': training_id
        })
        
        if result.success:
            return AnalyticsResponse(
                success=True,
                data=result.data,
                metadata=result.metadata
            )
        else:
            raise HTTPException(status_code=404, detail=result.error)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Training status retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/training/history", response_model=AnalyticsResponse)
async def get_training_history(limit: int = Query(50, description="Number of training records to return")):
    """Get training history."""
    try:
        pipeline = get_training_pipeline()
        
        result = await pipeline.process({
            'action': 'list_history',
            'limit': limit
        })
        
        return AnalyticsResponse(
            success=True,
            data=result.data,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Training history retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/ml/training/{training_id}", response_model=AnalyticsResponse)
async def cancel_training(training_id: str):
    """Cancel an active training pipeline."""
    try:
        pipeline = get_training_pipeline()
        
        result = await pipeline.process({
            'action': 'cancel_training',
            'training_id': training_id
        })
        
        return AnalyticsResponse(
            success=result.success,
            data=result.data,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Training cancellation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MODEL DEPLOYMENT ENDPOINTS
# ============================================================================

@router.post("/ml/deploy", response_model=AnalyticsResponse)
async def deploy_model(request: DeploymentRequest):
    """
    Deploy a trained model using specified strategy.
    
    Deployment strategies:
    - canary: Gradual traffic increase
    - blue_green: Environment switching
    - rolling: Instance-by-instance deployment
    - immediate: Direct production deployment
    """
    try:
        logger.info(f"Deploying model: {request.model_name} v{request.version}")
        
        # Get deployment manager
        manager = get_deployment_manager()
        
        # Create model version (simplified - in production would load from registry)
        from ..core.ml_versioning import ModelVersion, ModelMetrics
        
        model_version = ModelVersion(
            model_name=request.model_name,
            version=request.version,
            model_path=f"models/{request.model_name}_{request.version}.pkl",
            metrics=ModelMetrics(accuracy=0.85)  # Placeholder
        )
        
        # Start deployment
        result = await manager.process({
            'action': 'deploy',
            'model_version': model_version.__dict__,
            'strategy': request.strategy,
            'traffic_percentage': request.traffic_percentage
        })
        
        if result.success:
            return AnalyticsResponse(
                success=True,
                data=result.data,
                metadata=result.metadata
            )
        else:
            raise HTTPException(status_code=400, detail=result.error)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model deployment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/deployments/{deployment_id}/status", response_model=AnalyticsResponse)
async def get_deployment_status(deployment_id: str):
    """Get status of a model deployment."""
    try:
        manager = get_deployment_manager()
        
        result = await manager.process({
            'action': 'get_status',
            'deployment_id': deployment_id
        })
        
        if result.success:
            return AnalyticsResponse(
                success=True,
                data=result.data,
                metadata=result.metadata
            )
        else:
            raise HTTPException(status_code=404, detail=result.error)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deployment status retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/deployments", response_model=AnalyticsResponse)
async def list_deployments(limit: int = Query(50, description="Number of deployments to return")):
    """List deployment history."""
    try:
        manager = get_deployment_manager()
        
        result = await manager.process({
            'action': 'list_deployments',
            'limit': limit
        })
        
        return AnalyticsResponse(
            success=True,
            data=result.data,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Deployment listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/production-models", response_model=AnalyticsResponse)
async def get_production_models():
    """Get currently deployed production models."""
    try:
        manager = get_deployment_manager()
        
        result = await manager.process({
            'action': 'get_production_models'
        })
        
        return AnalyticsResponse(
            success=True,
            data=result.data,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Production models retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/rollback/{model_name}", response_model=AnalyticsResponse)
async def rollback_model(model_name: str, reason: str = Body(..., embed=True)):
    """Rollback a deployed model to previous version."""
    try:
        manager = get_deployment_manager()
        
        result = await manager.process({
            'action': 'rollback',
            'model_name': model_name,
            'reason': reason
        })
        
        return AnalyticsResponse(
            success=result.success,
            data=result.data,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Model rollback failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# A/B TESTING ENDPOINTS
# ============================================================================

@router.post("/ab-test/start", response_model=AnalyticsResponse)
async def start_ab_test(request: ABTestRequest):
    """
    Start a new A/B testing experiment.
    
    Experiment types:
    - performance_comparison: Compare model performance
    - latency_test: Test response time differences
    - accuracy_test: Test accuracy improvements
    - user_experience: Test user satisfaction
    - business_metric: Test business impact
    """
    try:
        logger.info(f"Starting A/B test: {request.experiment_name}")
        
        # Get A/B testing framework
        framework = get_ab_testing_framework()
        
        # Create experiment config (simplified)
        from ..core.ml_versioning import ModelVersion, ModelMetrics
        
        control_model = ModelVersion(
            model_name=request.control_model_name,
            version=request.control_model_version,
            model_path=f"models/{request.control_model_name}_{request.control_model_version}.pkl",
            metrics=ModelMetrics(accuracy=0.85)
        )
        
        treatment_model = ModelVersion(
            model_name=request.treatment_model_name,
            version=request.treatment_model_version,
            model_path=f"models/{request.treatment_model_name}_{request.treatment_model_version}.pkl",
            metrics=ModelMetrics(accuracy=0.87)
        )
        
        config = ExperimentConfig(
            experiment_name=request.experiment_name,
            experiment_type=ExperimentType(request.experiment_type),
            description=request.description,
            control_model=control_model,
            treatment_model=treatment_model,
            traffic_split=request.traffic_split,
            sample_size=request.sample_size,
            max_duration_days=request.max_duration_days
        )
        
        # Start experiment
        experiment_id = await framework.start_experiment(config)
        
        return AnalyticsResponse(
            success=True,
            data={"experiment_id": experiment_id},
            metadata={
                "action": "start_experiment",
                "experiment_name": request.experiment_name,
                "experiment_type": request.experiment_type
            }
        )
        
    except Exception as e:
        logger.error(f"A/B test start failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-test/{experiment_id}/status", response_model=AnalyticsResponse)
async def get_experiment_status(experiment_id: str):
    """Get status of an A/B testing experiment."""
    try:
        framework = get_ab_testing_framework()
        
        result = await framework.process({
            'action': 'get_status',
            'experiment_id': experiment_id
        })
        
        if result.success:
            return AnalyticsResponse(
                success=True,
                data=result.data,
                metadata=result.metadata
            )
        else:
            raise HTTPException(status_code=404, detail=result.error)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Experiment status retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-test/experiments", response_model=AnalyticsResponse)
async def list_experiments(limit: int = Query(50, description="Number of experiments to return")):
    """List A/B testing experiment history."""
    try:
        framework = get_ab_testing_framework()
        
        result = await framework.process({
            'action': 'list_experiments',
            'limit': limit
        })
        
        return AnalyticsResponse(
            success=True,
            data=result.data,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Experiment listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-test/{experiment_id}/stop", response_model=AnalyticsResponse)
async def stop_experiment(experiment_id: str, reason: str = Body(..., embed=True)):
    """Stop an active A/B testing experiment."""
    try:
        framework = get_ab_testing_framework()
        
        result = await framework.process({
            'action': 'stop_experiment',
            'experiment_id': experiment_id,
            'reason': reason
        })
        
        return AnalyticsResponse(
            success=result.success,
            data=result.data,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Experiment stop failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-test/{experiment_id}/pause", response_model=AnalyticsResponse)
async def pause_experiment(experiment_id: str):
    """Pause an active A/B testing experiment."""
    try:
        framework = get_ab_testing_framework()
        
        result = await framework.process({
            'action': 'pause_experiment',
            'experiment_id': experiment_id
        })
        
        return AnalyticsResponse(
            success=result.success,
            data=result.data,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Experiment pause failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-test/{experiment_id}/resume", response_model=AnalyticsResponse)
async def resume_experiment(experiment_id: str):
    """Resume a paused A/B testing experiment."""
    try:
        framework = get_ab_testing_framework()
        
        result = await framework.process({
            'action': 'resume_experiment',
            'experiment_id': experiment_id
        })
        
        return AnalyticsResponse(
            success=result.success,
            data=result.data,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Experiment resume failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SYSTEM STATUS AND HEALTH ENDPOINTS
# ============================================================================

@router.get("/status", response_model=AnalyticsResponse)
async def get_analytics_status():
    """Get overall analytics system status."""
    try:
        # Get component statuses
        behavior_analyzer = get_behavior_analyzer()
        meta_tracker = get_meta_tracker()
        training_pipeline = get_training_pipeline()
        deployment_manager = get_deployment_manager()
        ab_framework = get_ab_testing_framework()
        
        status_data = {
            "system_status": "healthy",
            "components": {
                "behavior_analyzer": "active",
                "meta_tracker": "active", 
                "training_pipeline": "active",
                "deployment_manager": "active",
                "ab_testing_framework": "active"
            },
            "active_processes": {
                "training_jobs": len(training_pipeline.active_trainings),
                "deployments": len(deployment_manager.active_deployments),
                "experiments": len(ab_framework.active_experiments)
            },
            "cache_status": {
                "behavior_profiles": len(behavior_analyzer.behavior_profiles),
                "meta_snapshots": len(meta_tracker.meta_snapshots)
            }
        }
        
        return AnalyticsResponse(
            success=True,
            data=status_data,
            metadata={
                "system": "analytics_platform",
                "version": "1.0",
                "uptime": "active"
            }
        )
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "analytics_api",
        "timestamp": datetime.now().isoformat()
    }
