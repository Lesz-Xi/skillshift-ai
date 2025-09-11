"""
A/B Testing Framework - Model performance comparison and experimentation
======================================================================

Provides comprehensive A/B testing capabilities for ML models with
statistical significance testing, experiment management, and automated
decision making based on performance metrics.
"""

import asyncio
import logging
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats

from ..services.base_service import BaseService, ServiceResult
from ..ml_versioning.version_manager import ModelVersion

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """A/B experiment status enumeration."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"
    FAILED = "failed"


class ExperimentType(Enum):
    """A/B experiment type enumeration."""
    PERFORMANCE_COMPARISON = "performance_comparison"
    LATENCY_TEST = "latency_test"
    ACCURACY_TEST = "accuracy_test"
    USER_EXPERIENCE = "user_experience"
    BUSINESS_METRIC = "business_metric"


class DecisionCriteria(Enum):
    """Decision criteria for experiment conclusion."""
    STATISTICAL_SIGNIFICANCE = "statistical_significance"
    BUSINESS_THRESHOLD = "business_threshold"
    TIME_BASED = "time_based"
    MANUAL = "manual"


@dataclass
class ExperimentConfig:
    """Configuration for A/B testing experiment."""
    # Basic Configuration
    experiment_name: str
    experiment_type: ExperimentType
    description: str
    
    # Models
    control_model: ModelVersion
    treatment_model: ModelVersion
    
    # Traffic Configuration
    traffic_split: float = 0.5  # Percentage for treatment
    sample_size: int = 10000
    min_sample_size: int = 1000
    
    # Statistical Configuration
    significance_level: float = 0.05
    statistical_power: float = 0.8
    minimum_effect_size: float = 0.02
    
    # Performance Thresholds
    max_latency_degradation: float = 0.1  # 10% max degradation
    min_accuracy_improvement: float = 0.01  # 1% min improvement
    max_error_rate_increase: float = 0.005  # 0.5% max increase
    
    # Duration Configuration
    max_duration_days: int = 30
    min_duration_days: int = 7
    evaluation_interval_hours: int = 6
    
    # Decision Criteria
    primary_metric: str = "accuracy"
    secondary_metrics: List[str] = field(default_factory=lambda: ["latency", "error_rate"])
    decision_criteria: DecisionCriteria = DecisionCriteria.STATISTICAL_SIGNIFICANCE
    
    # Safety Configuration
    auto_stop_on_degradation: bool = True
    degradation_threshold: float = 0.05
    safety_check_interval_minutes: int = 30
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    owner: str = "system"


@dataclass
class ExperimentMetrics:
    """Metrics collected during A/B experiment."""
    # Sample Information
    control_samples: int = 0
    treatment_samples: int = 0
    total_samples: int = 0
    
    # Performance Metrics
    control_metrics: Dict[str, float] = field(default_factory=dict)
    treatment_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Statistical Analysis
    p_values: Dict[str, float] = field(default_factory=dict)
    effect_sizes: Dict[str, float] = field(default_factory=dict)
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    # Business Metrics
    conversion_rates: Dict[str, float] = field(default_factory=dict)
    revenue_impact: Optional[float] = None
    user_satisfaction: Dict[str, float] = field(default_factory=dict)
    
    # Temporal Data
    hourly_metrics: List[Dict[str, Any]] = field(default_factory=list)
    daily_metrics: List[Dict[str, Any]] = field(default_factory=list)
    
    # Last Updated
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ExperimentResult:
    """Result of A/B testing experiment."""
    # Experiment Information
    experiment_id: str
    experiment_name: str
    status: ExperimentStatus
    
    # Models
    control_model: ModelVersion
    treatment_model: ModelVersion
    winner: Optional[str] = None  # "control", "treatment", or "inconclusive"
    
    # Metrics
    metrics: ExperimentMetrics = field(default_factory=ExperimentMetrics)
    
    # Decision Information
    decision_reason: Optional[str] = None
    statistical_significance: bool = False
    business_significance: bool = False
    
    # Duration Information
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_hours: float = 0.0
    
    # Configuration
    config: Optional[ExperimentConfig] = None
    
    # Logs and Events
    events: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)


class ABTestingFramework(BaseService):
    """A/B testing framework for ML model comparison."""
    
    def __init__(self, 
                 experiments_dir: str = "experiments/ab_tests",
                 results_dir: str = "results/ab_tests"):
        super().__init__()
        
        # Directory setup
        self.experiments_dir = Path(experiments_dir)
        self.results_dir = Path(results_dir)
        
        # Create directories
        for dir_path in [self.experiments_dir, self.results_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Active experiments
        self.active_experiments: Dict[str, ExperimentResult] = {}
        self.experiment_history: List[ExperimentResult] = []
        
        # Data collection
        self.experiment_data: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("A/B Testing Framework initialized")
    
    async def start_experiment(self, config: ExperimentConfig) -> str:
        """Start a new A/B testing experiment."""
        
        # Generate experiment ID
        experiment_id = f"ab_test_{config.experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create experiment result
        experiment_result = ExperimentResult(
            experiment_id=experiment_id,
            experiment_name=config.experiment_name,
            status=ExperimentStatus.DRAFT,
            control_model=config.control_model,
            treatment_model=config.treatment_model,
            config=config,
            start_time=datetime.now()
        )
        
        # Validate experiment configuration
        validation_errors = await self._validate_experiment_config(config)
        if validation_errors:
            experiment_result.status = ExperimentStatus.FAILED
            experiment_result.warnings.extend(validation_errors)
            return experiment_id
        
        # Initialize data collection
        self.experiment_data[experiment_id] = []
        
        # Store experiment
        self.active_experiments[experiment_id] = experiment_result
        
        # Start experiment execution
        asyncio.create_task(self._run_experiment(experiment_id))
        
        logger.info(f"A/B experiment started: {experiment_id}")
        return experiment_id
    
    async def _validate_experiment_config(self, config: ExperimentConfig) -> List[str]:
        """Validate experiment configuration."""
        errors = []
        
        # Check models exist
        if not Path(config.control_model.model_path).exists():
            errors.append(f"Control model not found: {config.control_model.model_path}")
        
        if not Path(config.treatment_model.model_path).exists():
            errors.append(f"Treatment model not found: {config.treatment_model.model_path}")
        
        # Check statistical parameters
        if config.significance_level <= 0 or config.significance_level >= 1:
            errors.append("Significance level must be between 0 and 1")
        
        if config.statistical_power <= 0 or config.statistical_power >= 1:
            errors.append("Statistical power must be between 0 and 1")
        
        # Check traffic split
        if config.traffic_split <= 0 or config.traffic_split >= 1:
            errors.append("Traffic split must be between 0 and 1")
        
        # Check sample sizes
        if config.min_sample_size > config.sample_size:
            errors.append("Minimum sample size cannot be greater than target sample size")
        
        return errors
    
    async def _run_experiment(self, experiment_id: str):
        """Run the A/B testing experiment."""
        experiment = self.active_experiments[experiment_id]
        config = experiment.config
        
        try:
            # Start experiment
            experiment.status = ExperimentStatus.RUNNING
            experiment.events.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'experiment_started',
                'details': f'Running {config.experiment_type.value} experiment'
            })
            
            # Run experiment loop
            end_time = datetime.now() + timedelta(days=config.max_duration_days)
            last_evaluation = datetime.now()
            
            while datetime.now() < end_time and experiment.status == ExperimentStatus.RUNNING:
                # Collect data
                await self._collect_experiment_data(experiment_id)
                
                # Check if enough time passed for evaluation
                if datetime.now() - last_evaluation >= timedelta(hours=config.evaluation_interval_hours):
                    # Analyze results
                    await self._analyze_experiment(experiment_id)
                    
                    # Check for early stopping conditions
                    if await self._should_stop_experiment(experiment_id):
                        break
                    
                    last_evaluation = datetime.now()
                
                # Safety checks
                if await self._safety_check(experiment_id):
                    experiment.warnings.append("Safety check triggered experiment stop")
                    break
                
                # Wait before next iteration
                await asyncio.sleep(60)  # Check every minute
            
            # Complete experiment
            await self._complete_experiment(experiment_id)
            
        except Exception as e:
            experiment.status = ExperimentStatus.FAILED
            experiment.events.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'experiment_failed',
                'details': str(e)
            })
            
            logger.error(f"A/B experiment failed: {experiment_id} - {str(e)}")
        
        finally:
            # Save experiment result
            await self._save_experiment_result(experiment)
            
            # Move to history
            self.experiment_history.append(experiment)
            
            # Clean up active experiment
            if experiment_id in self.active_experiments:
                del self.active_experiments[experiment_id]
    
    async def _collect_experiment_data(self, experiment_id: str):
        """Collect data for A/B experiment."""
        experiment = self.active_experiments[experiment_id]
        config = experiment.config
        
        # Simulate data collection
        batch_size = min(100, config.sample_size // 100)
        
        for _ in range(batch_size):
            # Determine which model to use based on traffic split
            is_treatment = random.random() < config.traffic_split
            model_version = config.treatment_model if is_treatment else config.control_model
            
            # Simulate model prediction and metrics
            prediction_data = await self._simulate_prediction(model_version, is_treatment)
            
            # Store data point
            data_point = {
                'timestamp': datetime.now().isoformat(),
                'experiment_id': experiment_id,
                'is_treatment': is_treatment,
                'model_version': model_version.version_id,
                **prediction_data
            }
            
            self.experiment_data[experiment_id].append(data_point)
        
        # Update sample counts
        treatment_count = sum(1 for d in self.experiment_data[experiment_id] if d['is_treatment'])
        control_count = len(self.experiment_data[experiment_id]) - treatment_count
        
        experiment.metrics.treatment_samples = treatment_count
        experiment.metrics.control_samples = control_count
        experiment.metrics.total_samples = len(self.experiment_data[experiment_id])
        
        logger.debug(f"Collected data for experiment {experiment_id}: {len(self.experiment_data[experiment_id])} samples")
    
    async def _simulate_prediction(self, model_version: ModelVersion, is_treatment: bool) -> Dict[str, Any]:
        """Simulate model prediction and collect metrics."""
        
        # Base performance (control model)
        base_accuracy = 0.85
        base_latency = 150  # ms
        base_error_rate = 0.05
        
        # Treatment model modifications
        if is_treatment:
            # Simulate treatment model being slightly better
            accuracy_boost = random.uniform(0.01, 0.03)
            latency_change = random.uniform(-20, 10)  # Usually faster
            error_rate_change = random.uniform(-0.01, 0.005)
        else:
            accuracy_boost = 0
            latency_change = 0
            error_rate_change = 0
        
        # Generate metrics with noise
        accuracy = base_accuracy + accuracy_boost + random.normal(0, 0.02)
        latency = base_latency + latency_change + random.normal(0, 20)
        error_rate = base_error_rate + error_rate_change + random.normal(0, 0.01)
        
        # Ensure realistic bounds
        accuracy = max(0.0, min(1.0, accuracy))
        latency = max(50, latency)
        error_rate = max(0.0, min(0.2, error_rate))
        
        # Business metrics
        user_satisfaction = accuracy * 10  # Scale to 0-10
        conversion_rate = accuracy * 0.1  # Simulate conversion
        
        return {
            'accuracy': accuracy,
            'latency_ms': latency,
            'error_rate': error_rate,
            'user_satisfaction': user_satisfaction,
            'conversion_rate': conversion_rate,
            'prediction_time': random.uniform(0.1, 0.5)
        }
    
    async def _analyze_experiment(self, experiment_id: str):
        """Analyze experiment results and perform statistical tests."""
        experiment = self.active_experiments[experiment_id]
        data = self.experiment_data[experiment_id]
        
        if len(data) < experiment.config.min_sample_size:
            logger.debug(f"Insufficient data for analysis: {len(data)} samples")
            return
        
        # Separate control and treatment data
        control_data = [d for d in data if not d['is_treatment']]
        treatment_data = [d for d in data if d['is_treatment']]
        
        if len(control_data) < 50 or len(treatment_data) < 50:
            logger.debug("Insufficient samples in control or treatment group")
            return
        
        # Calculate metrics for each group
        metrics_to_analyze = ['accuracy', 'latency_ms', 'error_rate', 'user_satisfaction']
        
        for metric in metrics_to_analyze:
            control_values = [d[metric] for d in control_data]
            treatment_values = [d[metric] for d in treatment_data]
            
            # Calculate basic statistics
            control_mean = np.mean(control_values)
            treatment_mean = np.mean(treatment_values)
            
            # Store means
            experiment.metrics.control_metrics[metric] = control_mean
            experiment.metrics.treatment_metrics[metric] = treatment_mean
            
            # Perform statistical test
            if metric in ['accuracy', 'user_satisfaction']:
                # Higher is better - use one-tailed test
                statistic, p_value = stats.ttest_ind(treatment_values, control_values, alternative='greater')
            else:
                # Lower is better (latency, error_rate) - use one-tailed test
                statistic, p_value = stats.ttest_ind(control_values, treatment_values, alternative='greater')
            
            experiment.metrics.p_values[metric] = p_value
            
            # Calculate effect size (Cohen's d)
            pooled_std = np.sqrt((np.var(control_values) + np.var(treatment_values)) / 2)
            if pooled_std > 0:
                effect_size = abs(treatment_mean - control_mean) / pooled_std
            else:
                effect_size = 0.0
            
            experiment.metrics.effect_sizes[metric] = effect_size
            
            # Calculate confidence interval for the difference
            diff_mean = treatment_mean - control_mean
            diff_se = np.sqrt(np.var(control_values)/len(control_values) + np.var(treatment_values)/len(treatment_values))
            
            if diff_se > 0:
                ci_lower = diff_mean - 1.96 * diff_se
                ci_upper = diff_mean + 1.96 * diff_se
                experiment.metrics.confidence_intervals[metric] = (ci_lower, ci_upper)
        
        # Update timestamp
        experiment.metrics.last_updated = datetime.now()
        
        logger.info(f"Analysis completed for experiment {experiment_id}")
    
    async def _should_stop_experiment(self, experiment_id: str) -> bool:
        """Check if experiment should be stopped early."""
        experiment = self.active_experiments[experiment_id]
        config = experiment.config
        metrics = experiment.metrics
        
        # Check minimum duration
        if experiment.start_time and datetime.now() - experiment.start_time < timedelta(days=config.min_duration_days):
            return False
        
        # Check sample size
        if metrics.total_samples < config.min_sample_size:
            return False
        
        # Check decision criteria
        if config.decision_criteria == DecisionCriteria.STATISTICAL_SIGNIFICANCE:
            return await self._check_statistical_significance(experiment_id)
        elif config.decision_criteria == DecisionCriteria.BUSINESS_THRESHOLD:
            return await self._check_business_threshold(experiment_id)
        elif config.decision_criteria == DecisionCriteria.TIME_BASED:
            return datetime.now() - experiment.start_time >= timedelta(days=config.max_duration_days)
        
        return False
    
    async def _check_statistical_significance(self, experiment_id: str) -> bool:
        """Check if results are statistically significant."""
        experiment = self.active_experiments[experiment_id]
        config = experiment.config
        metrics = experiment.metrics
        
        primary_metric = config.primary_metric
        
        if primary_metric not in metrics.p_values:
            return False
        
        p_value = metrics.p_values[primary_metric]
        effect_size = metrics.effect_sizes.get(primary_metric, 0.0)
        
        # Check statistical significance
        is_significant = p_value < config.significance_level
        has_meaningful_effect = effect_size >= config.minimum_effect_size
        
        if is_significant and has_meaningful_effect:
            experiment.statistical_significance = True
            experiment.decision_reason = f"Statistically significant result (p={p_value:.4f}, effect_size={effect_size:.4f})"
            return True
        
        # Check if we have enough evidence of no effect
        if metrics.total_samples >= config.sample_size and p_value > 0.5:
            experiment.decision_reason = "No significant difference detected with sufficient sample size"
            return True
        
        return False
    
    async def _check_business_threshold(self, experiment_id: str) -> bool:
        """Check if business thresholds are met."""
        experiment = self.active_experiments[experiment_id]
        config = experiment.config
        metrics = experiment.metrics
        
        primary_metric = config.primary_metric
        
        if primary_metric not in metrics.treatment_metrics or primary_metric not in metrics.control_metrics:
            return False
        
        treatment_value = metrics.treatment_metrics[primary_metric]
        control_value = metrics.control_metrics[primary_metric]
        
        # Calculate improvement
        if primary_metric == 'accuracy':
            improvement = treatment_value - control_value
            threshold = config.min_accuracy_improvement
        elif primary_metric == 'latency_ms':
            improvement = control_value - treatment_value  # Lower is better
            threshold = config.max_latency_degradation * control_value
        elif primary_metric == 'error_rate':
            improvement = control_value - treatment_value  # Lower is better
            threshold = config.max_error_rate_increase
        else:
            improvement = treatment_value - control_value
            threshold = config.minimum_effect_size
        
        if improvement >= threshold:
            experiment.business_significance = True
            experiment.decision_reason = f"Business threshold met (improvement: {improvement:.4f} >= {threshold:.4f})"
            return True
        
        return False
    
    async def _safety_check(self, experiment_id: str) -> bool:
        """Perform safety checks to prevent degradation."""
        experiment = self.active_experiments[experiment_id]
        config = experiment.config
        metrics = experiment.metrics
        
        if not config.auto_stop_on_degradation:
            return False
        
        # Check for significant degradation
        for metric, treatment_value in metrics.treatment_metrics.items():
            control_value = metrics.control_metrics.get(metric, 0)
            
            if metric == 'accuracy' and control_value > 0:
                degradation = (control_value - treatment_value) / control_value
                if degradation > config.degradation_threshold:
                    experiment.decision_reason = f"Safety stop: {metric} degraded by {degradation:.2%}"
                    return True
            
            elif metric == 'error_rate' and control_value > 0:
                increase = (treatment_value - control_value) / control_value
                if increase > config.degradation_threshold:
                    experiment.decision_reason = f"Safety stop: {metric} increased by {increase:.2%}"
                    return True
        
        return False
    
    async def _complete_experiment(self, experiment_id: str):
        """Complete the A/B experiment and determine winner."""
        experiment = self.active_experiments[experiment_id]
        experiment.status = ExperimentStatus.COMPLETED
        experiment.end_time = datetime.now()
        
        if experiment.start_time:
            experiment.duration_hours = (experiment.end_time - experiment.start_time).total_seconds() / 3600
        
        # Determine winner
        await self._determine_winner(experiment_id)
        
        # Log completion
        experiment.events.append({
            'timestamp': datetime.now().isoformat(),
            'event': 'experiment_completed',
            'details': f'Winner: {experiment.winner}, Reason: {experiment.decision_reason}'
        })
        
        logger.info(f"A/B experiment completed: {experiment_id} - Winner: {experiment.winner}")
    
    async def _determine_winner(self, experiment_id: str):
        """Determine the winner of the A/B test."""
        experiment = self.active_experiments[experiment_id]
        config = experiment.config
        metrics = experiment.metrics
        
        primary_metric = config.primary_metric
        
        if primary_metric not in metrics.treatment_metrics or primary_metric not in metrics.control_metrics:
            experiment.winner = "inconclusive"
            experiment.decision_reason = "Insufficient data for decision"
            return
        
        treatment_value = metrics.treatment_metrics[primary_metric]
        control_value = metrics.control_metrics[primary_metric]
        
        # Determine winner based on primary metric
        if primary_metric in ['accuracy', 'user_satisfaction']:
            # Higher is better
            if treatment_value > control_value:
                experiment.winner = "treatment"
            elif control_value > treatment_value:
                experiment.winner = "control"
            else:
                experiment.winner = "tie"
        else:
            # Lower is better (latency, error_rate)
            if treatment_value < control_value:
                experiment.winner = "treatment"
            elif control_value < treatment_value:
                experiment.winner = "control"
            else:
                experiment.winner = "tie"
        
        # Check statistical significance
        p_value = metrics.p_values.get(primary_metric, 1.0)
        if p_value >= config.significance_level:
            experiment.winner = "inconclusive"
            if not experiment.decision_reason:
                experiment.decision_reason = f"No statistically significant difference (p={p_value:.4f})"
    
    async def _save_experiment_result(self, experiment: ExperimentResult):
        """Save experiment result to file."""
        result_path = self.results_dir / f"{experiment.experiment_id}.json"
        
        # Convert to dict
        result_dict = asdict(experiment)
        
        # Handle datetime serialization
        if experiment.start_time:
            result_dict['start_time'] = experiment.start_time.isoformat()
        if experiment.end_time:
            result_dict['end_time'] = experiment.end_time.isoformat()
        result_dict['created_at'] = experiment.created_at.isoformat()
        result_dict['metrics']['last_updated'] = experiment.metrics.last_updated.isoformat()
        
        # Save to file
        with open(result_path, 'w') as f:
            json.dump(result_dict, f, indent=2)
        
        logger.info(f"Experiment result saved: {result_path}")
    
    async def get_experiment_status(self, experiment_id: str) -> Optional[ExperimentResult]:
        """Get experiment status."""
        return self.active_experiments.get(experiment_id)
    
    async def list_experiments(self, limit: int = 50) -> List[ExperimentResult]:
        """List experiment history."""
        return self.experiment_history[-limit:]
    
    async def stop_experiment(self, experiment_id: str, reason: str = "Manual stop") -> bool:
        """Manually stop an experiment."""
        if experiment_id in self.active_experiments:
            experiment = self.active_experiments[experiment_id]
            experiment.status = ExperimentStatus.STOPPED
            experiment.decision_reason = reason
            
            experiment.events.append({
                'timestamp': datetime.now().isoformat(),
                'event': 'experiment_stopped',
                'details': reason
            })
            
            logger.info(f"Experiment stopped: {experiment_id} - {reason}")
            return True
        
        return False
    
    async def pause_experiment(self, experiment_id: str) -> bool:
        """Pause an active experiment."""
        if experiment_id in self.active_experiments:
            experiment = self.active_experiments[experiment_id]
            if experiment.status == ExperimentStatus.RUNNING:
                experiment.status = ExperimentStatus.PAUSED
                
                experiment.events.append({
                    'timestamp': datetime.now().isoformat(),
                    'event': 'experiment_paused',
                    'details': 'Experiment paused by user'
                })
                
                logger.info(f"Experiment paused: {experiment_id}")
                return True
        
        return False
    
    async def resume_experiment(self, experiment_id: str) -> bool:
        """Resume a paused experiment."""
        if experiment_id in self.active_experiments:
            experiment = self.active_experiments[experiment_id]
            if experiment.status == ExperimentStatus.PAUSED:
                experiment.status = ExperimentStatus.RUNNING
                
                experiment.events.append({
                    'timestamp': datetime.now().isoformat(),
                    'event': 'experiment_resumed',
                    'details': 'Experiment resumed by user'
                })
                
                logger.info(f"Experiment resumed: {experiment_id}")
                return True
        
        return False
    
    async def process(self, request: Dict[str, Any]) -> ServiceResult:
        """Process A/B testing requests."""
        try:
            action = request.get('action', 'start_experiment')
            
            if action == 'start_experiment':
                config_data = request.get('config', {})
                config = ExperimentConfig(**config_data)
                
                experiment_id = await self.start_experiment(config)
                
                return ServiceResult(
                    success=True,
                    data={'experiment_id': experiment_id},
                    metadata={'action': 'start_experiment'}
                )
                
            elif action == 'get_status':
                experiment_id = request.get('experiment_id')
                status = await self.get_experiment_status(experiment_id)
                
                if status:
                    return ServiceResult(
                        success=True,
                        data=asdict(status),
                        metadata={'action': 'get_status'}
                    )
                else:
                    return ServiceResult(
                        success=False,
                        error=f"Experiment not found: {experiment_id}"
                    )
                    
            elif action == 'list_experiments':
                limit = request.get('limit', 50)
                experiments = await self.list_experiments(limit)
                
                return ServiceResult(
                    success=True,
                    data=[asdict(exp) for exp in experiments],
                    metadata={'action': 'list_experiments', 'count': len(experiments)}
                )
                
            elif action == 'stop_experiment':
                experiment_id = request.get('experiment_id')
                reason = request.get('reason', 'Manual stop')
                
                success = await self.stop_experiment(experiment_id, reason)
                
                return ServiceResult(
                    success=success,
                    data={'stopped': success},
                    metadata={'action': 'stop_experiment'}
                )
                
            elif action == 'pause_experiment':
                experiment_id = request.get('experiment_id')
                success = await self.pause_experiment(experiment_id)
                
                return ServiceResult(
                    success=success,
                    data={'paused': success},
                    metadata={'action': 'pause_experiment'}
                )
                
            elif action == 'resume_experiment':
                experiment_id = request.get('experiment_id')
                success = await self.resume_experiment(experiment_id)
                
                return ServiceResult(
                    success=success,
                    data={'resumed': success},
                    metadata={'action': 'resume_experiment'}
                )
                
            else:
                return ServiceResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            logger.error(f"A/B testing framework error: {str(e)}")
            return ServiceResult(
                success=False,
                error=str(e)
            )


# Global A/B testing framework instance
_ab_testing_framework = None

def get_ab_testing_framework() -> ABTestingFramework:
    """Get global A/B testing framework instance."""
    global _ab_testing_framework
    if _ab_testing_framework is None:
        _ab_testing_framework = ABTestingFramework()
    return _ab_testing_framework
