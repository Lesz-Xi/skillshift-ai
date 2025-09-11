#!/usr/bin/env python3
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

def train_model(config_path="ranked_complete_config.yaml"):
    """Train YOLO model with match-type-aware configuration."""
    
    # Load configuration
    config = load_config(config_path)
    
    # Initialize model
    model = YOLO('yolov8n.pt')  # Start with pre-trained model
    
    # Extract training parameters
    train_params = config.get('train_params', {})
    
    # Set default parameters
    default_params = {
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
    }
    
    # Merge with config parameters
    final_params = {**default_params, **train_params}
    
    # Remove non-ultralytics parameters
    ultralytics_params = {k: v for k, v in final_params.items() 
                          if k not in ['class_weights', 'match_type_distribution', 'multi_task_loss_weights']}
    
    print("🚀 Starting YOLO training with match-type-aware configuration...")
    print(f"📊 Dataset: {config['path']}")
    print(f"🎯 Classes: {config['nc']}")
    
    # Print match type distribution if available
    if 'match_type_distribution' in train_params:
        print("\n📈 Match Type Distribution:")
        for match_type, count in train_params['match_type_distribution'].items():
            print(f"  {match_type.capitalize()}: {count} images")
    
    # Train the model
    results = model.train(
        data=config_path,
        **ultralytics_params
    )
    
    print("\n🎉 Training completed!")
    print(f"📄 Results saved to: {results.save_dir}")
    
    return results

if __name__ == "__main__":
    train_model()
