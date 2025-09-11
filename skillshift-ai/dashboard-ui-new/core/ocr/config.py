"""
OCR Configuration System for Mission 3
Implements configuration hardening and hardware path selection.
"""
import os
import yaml
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
import platform

logger = logging.getLogger(__name__)


class OCRConfiguration:
    """
    OCR configuration system with environment and YAML support.
    
    Features:
    - Environment variable override
    - YAML configuration files
    - Hardware path selection
    - Performance optimization settings
    - Validation and error handling
    """
    
    def __init__(self):
        self.config = self._get_default_config()
        self.config_file = None
        self.environment_overrides = {}
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'performance': {
                'budget_ms': 500,
                'max_side': 512,
                'min_side': 64,
                'downscale_size': 1280,
                'enable_caching': True,
                'cache_size': 4096,
                'enable_early_exit': True,
                'confidence_threshold': 0.9,
                'max_iterations': 5
            },
            'hardware': {
                'prefer_gpu': False,
                'gpu_backend': 'auto',  # auto, cuda, mps, cpu
                'enable_mps': True,
                'enable_cuda': True,
                'fallback_to_cpu': True
            },
            'ocr': {
                'languages': ['en'],
                'allowlist': '0123456789/%,.',
                'detail': 0,
                'paragraph': False,
                'width_ths': 0.7,
                'height_ths': 0.7,
                'enable_verbose': False
            },
            'roi': {
                'max_side': 512,
                'min_side': 64,
                'gaussian_blur': (3, 3),
                'morphology_kernel': (2, 2),
                'otsu_threshold': True
            },
            'table_detection': {
                'downscale_size': 1280,
                'y_tolerance': 20,
                'min_gap': 10,
                'min_row_height': 10,
                'confidence_threshold': 0.3
            },
            'fusion': {
                'early_exit_threshold': 0.9,
                'max_iterations': 5,
                'enable_performance_monitoring': True,
                'mvp_calculation': True
            },
            'logging': {
                'level': 'INFO',
                'enable_json_logs': False,
                'enable_performance_logs': True,
                'log_file': None
            }
        }
    
    def load_from_env_or_yaml(self, config_file: Optional[Union[str, Path]] = None) -> 'OCRConfiguration':
        """
        Load configuration from environment variables or YAML file.
        
        Args:
            config_file: Path to YAML configuration file
            
        Returns:
            Self for method chaining
        """
        try:
            # Load from YAML file if provided
            if config_file:
                self.config_file = Path(config_file)
                if self.config_file.exists():
                    self._load_from_yaml(self.config_file)
                    logger.info(f"Loaded configuration from {self.config_file}")
            
            # Apply environment variable overrides
            self._apply_environment_overrides()
            
            # Validate configuration
            self.validate()
            
            logger.info("Configuration loaded and validated successfully")
            return self
            
        except Exception as e:
            logger.error(f"Configuration loading failed: {e}")
            raise
    
    def _load_from_yaml(self, config_file: Path):
        """Load configuration from YAML file."""
        try:
            with open(config_file, 'r') as f:
                yaml_config = yaml.safe_load(f)
            
            if yaml_config:
                self._merge_config(self.config, yaml_config)
                logger.debug(f"Loaded YAML configuration from {config_file}")
                
        except Exception as e:
            logger.warning(f"Failed to load YAML config from {config_file}: {e}")
    
    def _merge_config(self, base_config: Dict[str, Any], override_config: Dict[str, Any]):
        """Recursively merge configuration dictionaries."""
        for key, value in override_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value
    
    def _apply_environment_overrides(self):
        """Apply environment variable overrides."""
        env_mappings = {
            'OCR_BUDGET_MS': ('performance', 'budget_ms', int),
            'OCR_MAX_SIDE': ('performance', 'max_side', int),
            'OCR_MIN_SIDE': ('performance', 'min_side', int),
            'OCR_DOWNSCALE_SIZE': ('performance', 'downscale_size', int),
            'OCR_ENABLE_CACHING': ('performance', 'enable_caching', lambda x: x.lower() in ('1', 'true', 'yes')),
            'OCR_CACHE_SIZE': ('performance', 'cache_size', int),
            'OCR_ENABLE_EARLY_EXIT': ('performance', 'enable_early_exit', lambda x: x.lower() in ('1', 'true', 'yes')),
            'OCR_CONFIDENCE_THRESHOLD': ('performance', 'confidence_threshold', float),
            'OCR_MAX_ITERATIONS': ('performance', 'max_iterations', int),
            'OCR_GPU': ('hardware', 'prefer_gpu', lambda x: x.lower() in ('1', 'true', 'yes')),
            'OCR_GPU_BACKEND': ('hardware', 'gpu_backend', str),
            'OCR_ENABLE_MPS': ('hardware', 'enable_mps', lambda x: x.lower() in ('1', 'true', 'yes')),
            'OCR_ENABLE_CUDA': ('hardware', 'enable_cuda', lambda x: x.lower() in ('1', 'true', 'yes')),
            'OCR_FALLBACK_CPU': ('hardware', 'fallback_to_cpu', lambda x: x.lower() in ('1', 'true', 'yes')),
            'OCR_ALLOWLIST': ('ocr', 'allowlist', str),
            'OCR_DETAIL': ('ocr', 'detail', int),
            'OCR_PARAGRAPH': ('ocr', 'paragraph', lambda x: x.lower() in ('1', 'true', 'yes')),
            'OCR_WIDTH_THS': ('ocr', 'width_ths', float),
            'OCR_HEIGHT_THS': ('ocr', 'height_ths', float),
            'OCR_VERBOSE': ('ocr', 'enable_verbose', lambda x: x.lower() in ('1', 'true', 'yes')),
            'OCR_JSON_LOGS': ('logging', 'enable_json_logs', lambda x: x.lower() in ('1', 'true', 'yes')),
            'OCR_PERF_LOGS': ('logging', 'enable_performance_logs', lambda x: x.lower() in ('1', 'true', 'yes')),
            'OCR_LOG_LEVEL': ('logging', 'level', str),
            'OCR_LOG_FILE': ('logging', 'log_file', str)
        }
        
        for env_var, (section, key, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    converted_value = converter(value)
                    self.config[section][key] = converted_value
                    self.environment_overrides[f"{section}.{key}"] = converted_value
                    logger.debug(f"Applied environment override: {env_var} -> {section}.{key} = {converted_value}")
                except Exception as e:
                    logger.warning(f"Failed to apply environment override {env_var}: {e}")
    
    def validate(self):
        """Validate configuration values."""
        try:
            # Validate performance settings
            perf = self.config['performance']
            assert 100 <= perf['budget_ms'] <= 10000, "budget_ms must be between 100 and 10000"
            assert 32 <= perf['max_side'] <= 2048, "max_side must be between 32 and 2048"
            assert 16 <= perf['min_side'] <= 512, "min_side must be between 16 and 512"
            assert 0.0 <= perf['confidence_threshold'] <= 1.0, "confidence_threshold must be between 0.0 and 1.0"
            assert 1 <= perf['max_iterations'] <= 20, "max_iterations must be between 1 and 20"
            
            # Validate hardware settings
            hw = self.config['hardware']
            assert hw['gpu_backend'] in ['auto', 'cuda', 'mps', 'cpu'], "gpu_backend must be auto, cuda, mps, or cpu"
            
            # Validate OCR settings
            ocr = self.config['ocr']
            assert isinstance(ocr['languages'], list), "languages must be a list"
            assert len(ocr['languages']) > 0, "languages must not be empty"
            assert 0.0 <= ocr['width_ths'] <= 1.0, "width_ths must be between 0.0 and 1.0"
            assert 0.0 <= ocr['height_ths'] <= 1.0, "height_ths must be between 0.0 and 1.0"
            
            # Validate ROI settings
            roi = self.config['roi']
            assert 16 <= roi['max_side'] <= 1024, "roi.max_side must be between 16 and 1024"
            assert 8 <= roi['min_side'] <= 256, "roi.min_side must be between 8 and 256"
            
            # Validate table detection settings
            td = self.config['table_detection']
            assert 256 <= td['downscale_size'] <= 2048, "downscale_size must be between 256 and 2048"
            assert 5 <= td['y_tolerance'] <= 100, "y_tolerance must be between 5 and 100"
            assert 0.0 <= td['confidence_threshold'] <= 1.0, "confidence_threshold must be between 0.0 and 1.0"
            
            # Validate fusion settings
            fusion = self.config['fusion']
            assert 0.0 <= fusion['early_exit_threshold'] <= 1.0, "early_exit_threshold must be between 0.0 and 1.0"
            assert 1 <= fusion['max_iterations'] <= 20, "max_iterations must be between 1 and 20"
            
            logger.info("Configuration validation passed")
            
        except AssertionError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            raise
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated key path (e.g., 'performance.budget_ms')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        try:
            keys = key_path.split('.')
            value = self.config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.warning(f"Failed to get config value for {key_path}: {e}")
            return default
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation.
        
        Args:
            key_path: Dot-separated key path
            value: Value to set
        """
        try:
            keys = key_path.split('.')
            config = self.config
            
            # Navigate to parent dictionary
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Set value
            config[keys[-1]] = value
            logger.debug(f"Set config value: {key_path} = {value}")
            
        except Exception as e:
            logger.error(f"Failed to set config value for {key_path}: {e}")
            raise
    
    def get_hardware_config(self) -> Dict[str, Any]:
        """Get hardware-specific configuration."""
        hw_config = self.config['hardware'].copy()
        
        # Auto-detect best hardware configuration
        if hw_config['gpu_backend'] == 'auto':
            hw_config['gpu_backend'] = self._detect_best_gpu_backend()
        
        # Apply hardware-specific optimizations
        hw_config.update(self._get_hardware_optimizations())
        
        return hw_config
    
    def _detect_best_gpu_backend(self) -> str:
        """Detect the best GPU backend for the current system."""
        try:
            system = platform.system().lower()
            
            # Check for Apple Silicon (MPS)
            if system == 'darwin' and self.config['hardware']['enable_mps']:
                try:
                    import torch
                    if torch.backends.mps.is_available():
                        logger.info("Detected Apple Silicon with MPS support")
                        return 'mps'
                except ImportError:
                    pass
            
            # Check for CUDA
            if self.config['hardware']['enable_cuda']:
                try:
                    import torch
                    if torch.cuda.is_available():
                        logger.info("Detected CUDA support")
                        return 'cuda'
                except ImportError:
                    pass
            
            # Fallback to CPU
            logger.info("No GPU support detected, using CPU")
            return 'cpu'
            
        except Exception as e:
            logger.warning(f"Hardware detection failed: {e}")
            return 'cpu'
    
    def _get_hardware_optimizations(self) -> Dict[str, Any]:
        """Get hardware-specific optimizations."""
        backend = self.config['hardware']['gpu_backend']
        
        optimizations = {
            'cpu': {
                'batch_size': 1,
                'num_workers': 1,
                'prefetch_factor': 2
            },
            'cuda': {
                'batch_size': 4,
                'num_workers': 2,
                'prefetch_factor': 4
            },
            'mps': {
                'batch_size': 2,
                'num_workers': 1,
                'prefetch_factor': 2
            }
        }
        
        return optimizations.get(backend, optimizations['cpu'])
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance-optimized configuration."""
        perf_config = self.config['performance'].copy()
        
        # Apply hardware-specific performance tweaks
        hw_config = self.get_hardware_config()
        if hw_config['gpu_backend'] != 'cpu':
            # GPU optimizations
            perf_config['max_side'] = min(perf_config['max_side'], 1024)
            perf_config['cache_size'] = min(perf_config['cache_size'], 8192)
        else:
            # CPU optimizations
            perf_config['max_side'] = min(perf_config['max_side'], 512)
            perf_config['cache_size'] = min(perf_config['cache_size'], 4096)
        
        return perf_config
    
    def save_to_yaml(self, file_path: Union[str, Path]):
        """Save configuration to YAML file."""
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {file_path}: {e}")
            raise
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """Get summary of environment overrides."""
        return {
            'overrides_applied': len(self.environment_overrides),
            'override_keys': list(self.environment_overrides.keys()),
            'config_file': str(self.config_file) if self.config_file else None,
            'hardware_backend': self.get_hardware_config()['gpu_backend'],
            'performance_budget_ms': self.get('performance.budget_ms'),
            'caching_enabled': self.get('performance.enable_caching'),
            'early_exit_enabled': self.get('performance.enable_early_exit')
        }


# Global configuration instance
_global_config = None


def get_global_config() -> OCRConfiguration:
    """Get global configuration instance."""
    global _global_config
    
    if _global_config is None:
        _global_config = OCRConfiguration()
        _global_config.load_from_env_or_yaml()
    
    return _global_config


def reset_global_config():
    """Reset global configuration."""
    global _global_config
    _global_config = None


def load_config_from_file(config_file: Union[str, Path]) -> OCRConfiguration:
    """Load configuration from specific file."""
    config = OCRConfiguration()
    config.load_from_env_or_yaml(config_file)
    return config
