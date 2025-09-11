"""
Model Deployment Manager - Automated model deployment with A/B testing
=====================================================================

Handles automated deployment strategies including canary, blue-green, 
and rolling deployments with traffic management and rollback capabilities.
"""

import asyncio
import logging
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import yaml

from ..services.base_service import BaseService, ServiceResult
from ..ml_versioning.version_manager import ModelVersion

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """Deployment status enumeration."""
    PENDING = "pending"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeploymentStrategy(Enum):
    """Deployment strategy enumeration."""
    CANARY = "canary"
    BLUE_GREEN = "blue_green"
    ROLLING = "rolling"
    IMMEDIATE = "immediate"


@dataclass
class DeploymentConfig:
    """Configuration for model deployment."""
    # Deployment Strategy
    strategy: DeploymentStrategy = DeploymentStrategy.CANARY
    traffic_percentage: float = 0.1
    
    # Health Checks
    health_check_interval: int = 30  # seconds
    health_check_timeout: int = 10
    success_threshold: int = 3
    failure_threshold: int = 2
    
    # Performance Thresholds
    max_latency_ms: float = 500.0
    min_accuracy: float = 0.85
    max_error_rate: float = 0.05
    
    # Rollback Configuration
    auto_rollback: bool = True
    rollback_timeout_minutes: int = 30
    
    # Monitoring
    monitoring_duration_minutes: int = 60
    metrics_collection_interval: int = 60
    
    # Notifications
    notify_on_deployment: bool = True
    notify_on_failure: bool = True
    notification_channels: List[str] = field(default_factory=list)


@dataclass
class DeploymentResult:
    """Result of model deployment."""
    # Status Information
    deployment_id: str
    status: DeploymentStatus
    model_version: ModelVersion
    
    # Deployment Information
    strategy: DeploymentStrategy
    traffic_percentage: float
    deployed_at: Optional[datetime] = None
    
    # Health Information
    health_status: str = "unknown"
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    error_count: int = 0
    success_count: int = 0
    
    # Rollback Information
    rollback_triggered: bool = False
    rollback_reason: Optional[str] = None
    rollback_at: Optional[datetime] = None
    
    # Configuration
    config: Optional[DeploymentConfig] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    logs: List[str] = field(default_factory=list)


class ModelDeploymentManager(BaseService):
    """Automated model deployment with multiple strategies."""
    
    def __init__(self, 
                 deployments_dir: str = "deployments",
                 models_dir: str = "models"):
        super().__init__()
        
        # Directory setup
        self.deployments_dir = Path(deployments_dir)
        self.models_dir = Path(models_dir)
        
        # Create directories
        for dir_path in [self.deployments_dir, self.models_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Active deployments
        self.active_deployments: Dict[str, DeploymentResult] = {}
        self.deployment_history: List[DeploymentResult] = []
        
        # Current production models
        self.production_models: Dict[str, ModelVersion] = {}
        
        logger.info("Model Deployment Manager initialized")
    
    async def deploy_model(self, 
                          model_version: ModelVersion,
                          strategy: DeploymentStrategy = DeploymentStrategy.CANARY,
                          traffic_percentage: float = 0.1,
                          config: Optional[DeploymentConfig] = None) -> str:
        """Deploy a model using specified strategy."""
        
        # Generate deployment ID
        deployment_id = f"deploy_{model_version.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Use default config if not provided
        if config is None:
            config = DeploymentConfig(
                strategy=strategy,
                traffic_percentage=traffic_percentage
            )
        
        # Create deployment result
        deployment_result = DeploymentResult(
            deployment_id=deployment_id,
            status=DeploymentStatus.PENDING,
            model_version=model_version,
            strategy=strategy,
            traffic_percentage=traffic_percentage,
            config=config
        )
        
        # Store deployment
        self.active_deployments[deployment_id] = deployment_result
        
        # Start deployment asynchronously
        asyncio.create_task(self._execute_deployment(deployment_id))
        
        logger.info(f"Started deployment: {deployment_id}")
        return deployment_id
    
    async def _execute_deployment(self, deployment_id: str):
        """Execute the deployment process."""
        deployment = self.active_deployments[deployment_id]
        
        try:
            deployment.status = DeploymentStatus.DEPLOYING
            deployment.logs.append(f"Starting deployment: {deployment.strategy.value}")
            
            # Execute strategy-specific deployment
            if deployment.strategy == DeploymentStrategy.CANARY:
                await self._deploy_canary(deployment)
            elif deployment.strategy == DeploymentStrategy.BLUE_GREEN:
                await self._deploy_blue_green(deployment)
            elif deployment.strategy == DeploymentStrategy.ROLLING:
                await self._deploy_rolling(deployment)
            elif deployment.strategy == DeploymentStrategy.IMMEDIATE:
                await self._deploy_immediate(deployment)
            
            # Monitor deployment
            await self._monitor_deployment(deployment)
            
            # Complete deployment
            deployment.status = DeploymentStatus.DEPLOYED
            deployment.deployed_at = datetime.now()
            deployment.logs.append("Deployment completed successfully")
            
            # Update production model
            self.production_models[deployment.model_version.model_name] = deployment.model_version
            
            logger.info(f"Deployment completed: {deployment_id}")
            
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.logs.append(f"Deployment failed: {str(e)}")
            
            logger.error(f"Deployment failed: {deployment_id} - {str(e)}")
            
            # Trigger rollback if configured
            if deployment.config.auto_rollback:
                await self._rollback_deployment(deployment, f"Deployment failure: {str(e)}")
        
        finally:
            # Save deployment result
            await self._save_deployment_result(deployment)
            
            # Move to history
            self.deployment_history.append(deployment)
            
            # Clean up active deployment
            if deployment_id in self.active_deployments:
                del self.active_deployments[deployment_id]
    
    async def _deploy_canary(self, deployment: DeploymentResult):
        """Execute canary deployment."""
        deployment.logs.append("Executing canary deployment")
        
        # Step 1: Deploy canary version
        await self._deploy_model_instance(
            deployment.model_version, 
            f"canary_{deployment.deployment_id}",
            deployment.traffic_percentage
        )
        
        deployment.logs.append(f"Canary deployed with {deployment.traffic_percentage*100}% traffic")
        
        # Step 2: Monitor canary performance
        await asyncio.sleep(5)  # Simulate monitoring
        
        # Step 3: Gradually increase traffic if healthy
        traffic_steps = [0.1, 0.25, 0.5, 1.0]
        for traffic in traffic_steps:
            if traffic <= deployment.traffic_percentage:
                continue
                
            # Check health before increasing traffic
            if not await self._check_deployment_health(deployment):
                raise Exception("Canary health check failed")
            
            await self._update_traffic_split(deployment.deployment_id, traffic)
            deployment.traffic_percentage = traffic
            deployment.logs.append(f"Increased traffic to {traffic*100}%")
            
            # Wait and monitor
            await asyncio.sleep(2)
        
        deployment.logs.append("Canary deployment completed")
    
    async def _deploy_blue_green(self, deployment: DeploymentResult):
        """Execute blue-green deployment."""
        deployment.logs.append("Executing blue-green deployment")
        
        # Step 1: Deploy green environment
        await self._deploy_model_instance(
            deployment.model_version,
            f"green_{deployment.deployment_id}",
            0.0  # No traffic initially
        )
        
        deployment.logs.append("Green environment deployed")
        
        # Step 2: Health check green environment
        if not await self._check_deployment_health(deployment):
            raise Exception("Green environment health check failed")
        
        # Step 3: Switch traffic to green
        await self._switch_traffic(deployment.deployment_id, "green")
        deployment.traffic_percentage = 1.0
        deployment.logs.append("Traffic switched to green environment")
        
        # Step 4: Keep blue environment for rollback
        deployment.logs.append("Blue environment kept for potential rollback")
        
        deployment.logs.append("Blue-green deployment completed")
    
    async def _deploy_rolling(self, deployment: DeploymentResult):
        """Execute rolling deployment."""
        deployment.logs.append("Executing rolling deployment")
        
        # Step 1: Deploy to first instance
        instances = ["instance_1", "instance_2", "instance_3"]
        
        for i, instance in enumerate(instances):
            # Deploy to instance
            await self._deploy_model_instance(
                deployment.model_version,
                f"{instance}_{deployment.deployment_id}",
                (i + 1) / len(instances)
            )
            
            deployment.logs.append(f"Deployed to {instance}")
            
            # Health check
            if not await self._check_deployment_health(deployment):
                raise Exception(f"Rolling deployment health check failed at {instance}")
            
            # Wait before next instance
            await asyncio.sleep(1)
        
        deployment.traffic_percentage = 1.0
        deployment.logs.append("Rolling deployment completed")
    
    async def _deploy_immediate(self, deployment: DeploymentResult):
        """Execute immediate deployment."""
        deployment.logs.append("Executing immediate deployment")
        
        # Deploy directly to production
        await self._deploy_model_instance(
            deployment.model_version,
            f"production_{deployment.deployment_id}",
            1.0
        )
        
        deployment.traffic_percentage = 1.0
        deployment.logs.append("Immediate deployment completed")
    
    async def _deploy_model_instance(self, model_version: ModelVersion, 
                                   instance_name: str, traffic_percentage: float):
        """Deploy model instance."""
        logger.info(f"Deploying model instance: {instance_name}")
        
        # Simulate model deployment
        instance_dir = self.deployments_dir / instance_name
        instance_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy model file
        model_path = Path(model_version.model_path)
        if model_path.exists():
            shutil.copy2(model_path, instance_dir / "model.pkl")
        
        # Create deployment metadata
        metadata = {
            'model_version': asdict(model_version),
            'instance_name': instance_name,
            'traffic_percentage': traffic_percentage,
            'deployed_at': datetime.now().isoformat()
        }
        
        with open(instance_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Model instance deployed: {instance_name}")
    
    async def _monitor_deployment(self, deployment: DeploymentResult):
        """Monitor deployment health and performance."""
        logger.info(f"Monitoring deployment: {deployment.deployment_id}")
        
        config = deployment.config
        monitoring_end = datetime.now() + timedelta(minutes=config.monitoring_duration_minutes)
        
        consecutive_successes = 0
        consecutive_failures = 0
        
        while datetime.now() < monitoring_end:
            # Check deployment health
            is_healthy = await self._check_deployment_health(deployment)
            
            if is_healthy:
                consecutive_successes += 1
                consecutive_failures = 0
                deployment.success_count += 1
            else:
                consecutive_failures += 1
                consecutive_successes = 0
                deployment.error_count += 1
            
            # Check if rollback needed
            if consecutive_failures >= config.failure_threshold:
                if config.auto_rollback:
                    await self._rollback_deployment(
                        deployment, 
                        f"Health check failures: {consecutive_failures}"
                    )
                    return
                else:
                    raise Exception(f"Deployment health check failed {consecutive_failures} times")
            
            # Check if deployment is stable
            if consecutive_successes >= config.success_threshold:
                deployment.logs.append("Deployment is stable")
                break
            
            # Wait before next check
            await asyncio.sleep(config.health_check_interval)
        
        logger.info(f"Deployment monitoring completed: {deployment.deployment_id}")
    
    async def _check_deployment_health(self, deployment: DeploymentResult) -> bool:
        """Check deployment health."""
        logger.debug(f"Checking health for deployment: {deployment.deployment_id}")
        
        # Simulate health checks
        await asyncio.sleep(0.5)
        
        # Generate synthetic health metrics
        import random
        
        latency = random.uniform(100, 600)  # ms
        accuracy = random.uniform(0.8, 0.95)
        error_rate = random.uniform(0.0, 0.1)
        
        # Update performance metrics
        deployment.performance_metrics.update({
            'latency_ms': latency,
            'accuracy': accuracy,
            'error_rate': error_rate,
            'timestamp': datetime.now().isoformat()
        })
        
        # Check against thresholds
        config = deployment.config
        
        is_healthy = (
            latency <= config.max_latency_ms and
            accuracy >= config.min_accuracy and
            error_rate <= config.max_error_rate
        )
        
        deployment.health_status = "healthy" if is_healthy else "unhealthy"
        
        logger.debug(f"Health check result: {deployment.health_status}")
        return is_healthy
    
    async def _update_traffic_split(self, deployment_id: str, traffic_percentage: float):
        """Update traffic split for canary deployment."""
        logger.info(f"Updating traffic split to {traffic_percentage*100}%")
        
        # Simulate traffic management
        await asyncio.sleep(0.2)
        
        # In real implementation, this would update load balancer configuration
        logger.info(f"Traffic split updated: {traffic_percentage*100}%")
    
    async def _switch_traffic(self, deployment_id: str, environment: str):
        """Switch traffic for blue-green deployment."""
        logger.info(f"Switching traffic to {environment} environment")
        
        # Simulate traffic switch
        await asyncio.sleep(0.5)
        
        # In real implementation, this would update routing configuration
        logger.info(f"Traffic switched to {environment}")
    
    async def _rollback_deployment(self, deployment: DeploymentResult, reason: str):
        """Rollback deployment to previous version."""
        logger.warning(f"Rolling back deployment: {deployment.deployment_id} - {reason}")
        
        deployment.status = DeploymentStatus.ROLLING_BACK
        deployment.rollback_triggered = True
        deployment.rollback_reason = reason
        deployment.rollback_at = datetime.now()
        deployment.logs.append(f"Rollback triggered: {reason}")
        
        try:
            # Get previous production model
            model_name = deployment.model_version.model_name
            previous_model = self.production_models.get(model_name)
            
            if previous_model:
                # Deploy previous version
                await self._deploy_model_instance(
                    previous_model,
                    f"rollback_{deployment.deployment_id}",
                    1.0
                )
                
                deployment.logs.append(f"Rolled back to version: {previous_model.version}")
            else:
                deployment.logs.append("No previous version to rollback to")
            
            deployment.status = DeploymentStatus.ROLLED_BACK
            logger.info(f"Rollback completed: {deployment.deployment_id}")
            
        except Exception as e:
            deployment.logs.append(f"Rollback failed: {str(e)}")
            logger.error(f"Rollback failed: {deployment.deployment_id} - {str(e)}")
    
    async def _save_deployment_result(self, deployment: DeploymentResult):
        """Save deployment result."""
        result_path = self.deployments_dir / f"{deployment.deployment_id}_result.json"
        
        # Convert to dict
        result_dict = asdict(deployment)
        
        # Handle datetime serialization
        if deployment.deployed_at:
            result_dict['deployed_at'] = deployment.deployed_at.isoformat()
        if deployment.rollback_at:
            result_dict['rollback_at'] = deployment.rollback_at.isoformat()
        result_dict['created_at'] = deployment.created_at.isoformat()
        
        # Save to file
        with open(result_path, 'w') as f:
            json.dump(result_dict, f, indent=2)
        
        logger.info(f"Deployment result saved: {result_path}")
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentResult]:
        """Get deployment status."""
        return self.active_deployments.get(deployment_id)
    
    async def list_deployments(self, limit: int = 50) -> List[DeploymentResult]:
        """List deployment history."""
        return self.deployment_history[-limit:]
    
    async def get_production_models(self) -> Dict[str, ModelVersion]:
        """Get currently deployed production models."""
        return self.production_models.copy()
    
    async def rollback_model(self, model_name: str, reason: str = "Manual rollback") -> bool:
        """Manually rollback a model."""
        # Find active deployment for model
        for deployment in self.active_deployments.values():
            if deployment.model_version.model_name == model_name:
                await self._rollback_deployment(deployment, reason)
                return True
        
        return False
    
    async def process(self, request: Dict[str, Any]) -> ServiceResult:
        """Process deployment requests."""
        try:
            action = request.get('action', 'deploy')
            
            if action == 'deploy':
                model_version_data = request.get('model_version', {})
                model_version = ModelVersion(**model_version_data)
                
                strategy = DeploymentStrategy(request.get('strategy', 'canary'))
                traffic_percentage = request.get('traffic_percentage', 0.1)
                
                deployment_id = await self.deploy_model(
                    model_version, strategy, traffic_percentage
                )
                
                return ServiceResult(
                    success=True,
                    data={'deployment_id': deployment_id},
                    metadata={'action': 'deploy'}
                )
                
            elif action == 'get_status':
                deployment_id = request.get('deployment_id')
                status = await self.get_deployment_status(deployment_id)
                
                if status:
                    return ServiceResult(
                        success=True,
                        data=asdict(status),
                        metadata={'action': 'get_status'}
                    )
                else:
                    return ServiceResult(
                        success=False,
                        error=f"Deployment not found: {deployment_id}"
                    )
                    
            elif action == 'list_deployments':
                limit = request.get('limit', 50)
                deployments = await self.list_deployments(limit)
                
                return ServiceResult(
                    success=True,
                    data=[asdict(d) for d in deployments],
                    metadata={'action': 'list_deployments', 'count': len(deployments)}
                )
                
            elif action == 'get_production_models':
                models = await self.get_production_models()
                
                return ServiceResult(
                    success=True,
                    data={k: asdict(v) for k, v in models.items()},
                    metadata={'action': 'get_production_models'}
                )
                
            elif action == 'rollback':
                model_name = request.get('model_name')
                reason = request.get('reason', 'Manual rollback')
                
                success = await self.rollback_model(model_name, reason)
                
                return ServiceResult(
                    success=success,
                    data={'rolled_back': success},
                    metadata={'action': 'rollback'}
                )
                
            else:
                return ServiceResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            logger.error(f"Deployment manager error: {str(e)}")
            return ServiceResult(
                success=False,
                error=str(e)
            )


# Global deployment manager instance
_deployment_manager = None

def get_deployment_manager() -> ModelDeploymentManager:
    """Get global deployment manager instance."""
    global _deployment_manager
    if _deployment_manager is None:
        _deployment_manager = ModelDeploymentManager()
    return _deployment_manager
