#!/usr/bin/env python3
"""
Match-Type-Aware YOLO Training Configuration Generator

This script generates YOLO training configurations that can optionally
incorporate match type awareness for improved model performance.

Usage:
    python train_config_generator.py --dataset_dir . --output train_config.yaml
    python train_config_generator.py --match_type_weights --multi_task
"""

import yaml
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YOLOConfigGenerator:
    """Generates YOLO training configurations with match-type awareness."""
    
    def __init__(self, dataset_dir: Path):
        """Initialize with dataset directory."""
        self.dataset_dir = Path(dataset_dir)
        self.manifest_path = self.dataset_dir / "dataset_manifest.json"
        self.classes_config = self.dataset_dir / "configs" / "classes.yaml"
        
    def load_manifest(self) -> Dict[str, Any]:
        """Load dataset manifest for match type distribution."""
        if self.manifest_path.exists():
            with open(self.manifest_path) as f:
                return json.load(f)
        return {}
    
    def load_classes(self) -> Dict[str, Any]:
        """Load class configuration."""
        if self.classes_config.exists():
            with open(self.classes_config) as f:
                return yaml.safe_load(f)
        return {}
    
    def analyze_dataset_distribution(self) -> Dict[str, int]:
        """Analyze match type distribution in the dataset."""
        manifest = self.load_manifest()
        
        distribution = {}
        if 'images' in manifest:
            for image_data in manifest['images']:
                match_type = image_data.get('match_type', 'unknown')
                distribution[match_type] = distribution.get(match_type, 0) + 1
        
        return distribution
    
    def calculate_class_weights(self, distribution: Dict[str, int]) -> Dict[str, float]:
        """Calculate class weights for balanced training."""
        total_images = sum(distribution.values())
        weights = {}
        
        for match_type, count in distribution.items():
            # Inverse frequency weighting
            weights[match_type] = total_images / (len(distribution) * count)
        
        return weights
    
    def generate_basic_config(self) -> Dict[str, Any]:
        """Generate basic YOLO training configuration."""
        config = {
            'path': str(self.dataset_dir),
            'train': 'images/train',
            'val': 'images/val',
            'test': 'images/test',
            'nc': 50,  # Number of classes
            'names': []
        }
        
        # Load class names from classes.yaml
        classes_config = self.load_classes()
        if 'classes' in classes_config:
            class_names = self._extract_class_names(classes_config['classes'])
            config['names'] = class_names
            config['nc'] = len(class_names)
        
        return config
    
    def _extract_class_names(self, classes_config: Dict) -> List[str]:
        """Extract ordered class names from classes configuration."""
        class_names = [''] * 50  # Initialize with empty strings
        
        # Process different sections of classes
        for section_name, section in classes_config.items():
            if isinstance(section, dict) and 'priority' in section:
                self._process_class_section(section, class_names)
        
        # Filter out empty names and return
        return [name for name in class_names if name]
    
    def _process_class_section(self, section: Dict, class_names: List[str]):
        """Process a class section and add names to the list."""
        for category_name, category in section.items():
            if category_name in ['priority', 'description']:
                continue
                
            if isinstance(category, list):
                for class_def in category:
                    if isinstance(class_def, dict) and 'id' in class_def and 'name' in class_def:
                        class_id = class_def['id']
                        class_name = class_def['name']
                        if 0 <= class_id < len(class_names):
                            class_names[class_id] = class_name
            elif isinstance(category, dict):
                for subcategory in category.values():
                    if isinstance(subcategory, list):
                        for class_def in subcategory:
                            if isinstance(class_def, dict) and 'id' in class_def and 'name' in class_def:
                                class_id = class_def['id']
                                class_name = class_def['name']
                                if 0 <= class_id < len(class_names):
                                    class_names[class_id] = class_name
    
    def generate_weighted_config(self) -> Dict[str, Any]:
        """Generate configuration with match-type-aware class weights."""
        config = self.generate_basic_config()
        
        # Analyze dataset distribution
        distribution = self.analyze_dataset_distribution()
        weights = self.calculate_class_weights(distribution)
        
        # Add training parameters with weights
        config['train_params'] = {
            'epochs': 100,
            'batch_size': 16,
            'imgsz': 640,
            'optimizer': 'AdamW',
            'lr0': 0.001,
            'weight_decay': 0.0005,
            'class_weights': weights,
            'match_type_distribution': distribution
        }
        
        return config
    
    def generate_multi_task_config(self) -> Dict[str, Any]:
        """Generate configuration for multi-task learning with match type prediction."""
        config = self.generate_basic_config()
        
        # Add match type as auxiliary task
        config['match_types'] = ['ranked', 'classic', 'other']
        config['multi_task'] = {
            'primary_task': 'object_detection',
            'auxiliary_task': 'match_type_classification',
            'auxiliary_weight': 0.1  # Weight for auxiliary loss
        }
        
        # Enhanced training parameters
        config['train_params'] = {
            'epochs': 150,
            'batch_size': 12,  # Smaller batch for multi-task
            'imgsz': 640,
            'optimizer': 'AdamW',
            'lr0': 0.0008,  # Slightly lower learning rate
            'weight_decay': 0.0005,
            'multi_task_loss_weights': {
                'detection': 1.0,
                'match_type': 0.1
            }
        }
        
        return config
    
    def generate_evaluation_config(self) -> Dict[str, Any]:
        """Generate configuration for match-type-aware evaluation."""
        return {
            'evaluation': {
                'metrics': ['precision', 'recall', 'f1', 'map50', 'map95'],
                'match_type_aware': True,
                'bias_threshold': 0.05,
                'confidence_threshold': 0.25,
                'iou_threshold': 0.5,
                'per_class_metrics': True,
                'confusion_matrix': True
            },
            'validation': {
                'frequency': 5,  # Validate every 5 epochs
                'save_best': True,
                'early_stopping': {
                    'patience': 20,
                    'min_delta': 0.001
                }
            }
        }
    
    def save_config(self, config: Dict[str, Any], output_path: str):
        """Save configuration to YAML file."""
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        logger.info(f"✅ Configuration saved to {output_path}")
    
    def generate_training_script(self, config_path: str) -> str:
        """Generate a training script that uses the configuration."""
        script_content = f'''#!/usr/bin/env python3
"""
Auto-generated YOLO training script with match-type awareness.
"""

from ultralytics import YOLO
import yaml
import json
from pathlib import Path

def load_config(config_path):
    """Load training configuration."""
    with open(config_path) as f:
        return yaml.safe_load(f)

def train_model(config_path="{config_path}"):
    """Train YOLO model with match-type-aware configuration."""
    
    # Load configuration
    config = load_config(config_path)
    
    # Initialize model
    model = YOLO('yolov8n.pt')  # Start with pre-trained model
    
    # Extract training parameters
    train_params = config.get('train_params', {{}})
    
    # Set default parameters
    default_params = {{
        'epochs': 100,
        'imgsz': 640,
        'batch': 16,
        'optimizer': 'AdamW',
        'lr0': 0.001,
        'weight_decay': 0.0005,
        'device': 0,  # GPU 0
        'workers': 8,
        'patience': 20,
        'save': True,
        'plots': True,
        'val': True
    }}
    
    # Merge with config parameters
    final_params = {{**default_params, **train_params}}
    
    # Remove non-ultralytics parameters
    ultralytics_params = {{k: v for k, v in final_params.items() 
                          if k not in ['class_weights', 'match_type_distribution', 'multi_task_loss_weights']}}
    
    print("🚀 Starting YOLO training with match-type-aware configuration...")
    print(f"📊 Dataset: {{config['path']}}")
    print(f"🎯 Classes: {{config['nc']}}")
    
    # Print match type distribution if available
    if 'match_type_distribution' in train_params:
        print("\\n📈 Match Type Distribution:")
        for match_type, count in train_params['match_type_distribution'].items():
            print(f"  {{match_type.capitalize()}}: {{count}} images")
    
    # Train the model
    results = model.train(
        data=config_path,
        **ultralytics_params
    )
    
    print("\\n🎉 Training completed!")
    print(f"📄 Results saved to: {{results.save_dir}}")
    
    return results

if __name__ == "__main__":
    train_model()
'''
        
        script_path = Path(config_path).parent / "train.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        script_path.chmod(0o755)
        
        logger.info(f"✅ Training script saved to {script_path}")
        return str(script_path)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="YOLO Training Configuration Generator with Match-Type Awareness"
    )
    parser.add_argument(
        "--dataset_dir",
        default=".",
        help="Dataset directory path (default: current directory)"
    )
    parser.add_argument(
        "--output",
        default="dataset.yaml",
        help="Output configuration file (default: dataset.yaml)"
    )
    parser.add_argument(
        "--match_type_weights",
        action="store_true",
        help="Enable match-type-aware class weighting"
    )
    parser.add_argument(
        "--multi_task",
        action="store_true", 
        help="Enable multi-task learning with match type prediction"
    )
    parser.add_argument(
        "--generate_script",
        action="store_true",
        help="Generate training script alongside configuration"
    )
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = YOLOConfigGenerator(args.dataset_dir)
    
    logger.info("🔧 Generating YOLO training configuration...")
    
    # Generate appropriate configuration
    if args.multi_task:
        logger.info("🎯 Multi-task learning configuration enabled")
        config = generator.generate_multi_task_config()
    elif args.match_type_weights:
        logger.info("⚖️ Match-type-aware weighting enabled")
        config = generator.generate_weighted_config()
    else:
        logger.info("📋 Basic configuration")
        config = generator.generate_basic_config()
    
    # Add evaluation configuration
    eval_config = generator.generate_evaluation_config()
    config.update(eval_config)
    
    # Save configuration
    generator.save_config(config, args.output)
    
    # Generate training script if requested
    if args.generate_script:
        script_path = generator.generate_training_script(args.output)
        logger.info(f"🎬 Training script generated: {script_path}")
    
    # Print summary
    logger.info("\n📊 Configuration Summary:")
    logger.info(f"  Dataset Path: {config['path']}")
    logger.info(f"  Number of Classes: {config['nc']}")
    
    if 'train_params' in config:
        params = config['train_params']
        logger.info(f"  Epochs: {params.get('epochs', 'default')}")
        logger.info(f"  Batch Size: {params.get('batch_size', 'default')}")
        
        if 'match_type_distribution' in params:
            logger.info("\n🎯 Match Type Distribution:")
            for match_type, count in params['match_type_distribution'].items():
                logger.info(f"    {match_type.capitalize()}: {count} images")
    
    logger.info(f"\n🚀 Ready to train! Use: python train.py")
    logger.info(f"📋 Configuration file: {args.output}")


if __name__ == "__main__":
    main() 