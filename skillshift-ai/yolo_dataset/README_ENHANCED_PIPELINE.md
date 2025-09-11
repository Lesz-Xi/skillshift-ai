# Enhanced Match-Type-Aware YOLO Dataset Pipeline

This enhanced pipeline implements **Match-Type-Aware Training** for YOLO object detection, specifically designed for MLBB (Mobile Legends) screenshot analysis. It addresses data bias between different match types (Ranked, Classic, Other) and ensures consistent model performance across all game modes.

## 🎯 Key Features

### ✅ **Requirements Fulfilled**

1. **✅ Match-Type Separation**: Images automatically categorized by match type from folder structure
2. **✅ Stratified Sampling**: Independent train/val/test splits per match type for balanced representation
3. **✅ Encoded Filenames**: Descriptive naming like `ranked_excellent_kda_001.jpg`, `classic_poor_dmg_042.jpg`
4. **✅ Synchronized Annotations**: Automatic .txt file renaming to match image files
5. **✅ Match Type Manifest**: CSV/JSON files linking images to metadata for downstream processing
6. **✅ Collision Prevention**: Unique filename generation with automatic collision resolution
7. **✅ Iterative Safety**: Safe re-runs without corrupting existing datasets

### 🚀 **Enhanced Capabilities**

- **Bias Detection**: Automated detection of performance gaps between match types
- **Weighted Training**: Class weighting based on match type distribution
- **Multi-Task Learning**: Optional match type prediction alongside object detection
- **Comprehensive Evaluation**: Per-match-type performance metrics and reporting
- **Automated Config Generation**: YOLO training configurations with match-type awareness

## 📁 Pipeline Components

### 1. **Enhanced Dataset Preparation** (`enhanced_prepare_for_annotation.py`)

**Main dataset preparation script with stratified sampling and filename encoding.**

```bash
# Clean start - removes existing output directories
python enhanced_prepare_for_annotation.py --clean_start

# Update existing dataset (safe for iterative runs)
python enhanced_prepare_for_annotation.py --update_existing

# Validate dataset integrity only
python enhanced_prepare_for_annotation.py --validate_only
```

**Key Features:**

- **Stratified splits**: 70/15/15 train/val/test ratio **per match type**
- **Filename encoding**: `{match_type}_{performance}_{view}_{index:03d}.jpg`
- **Collision handling**: Automatic filename uniqueness with `_01`, `_02` suffixes
- **Annotation sync**: Automatic .txt file renaming to match images
- **Manifest generation**: Both CSV and JSON formats for metadata tracking

**Example Output Structure:**

```
images/
├── train/
│   ├── ranked_excellent_kda_001.jpg
│   ├── ranked_good_dmg_002.jpg
│   ├── classic_average_kda_003.jpg
│   └── other_poor_dmg_004.jpg
├── val/
└── test/

labels/
├── train/
│   ├── ranked_excellent_kda_001.txt
│   ├── ranked_good_dmg_002.txt
│   └── ...
├── val/
└── test/

dataset_manifest.csv
dataset_manifest.json
```

### 2. **Match-Type-Aware Evaluator** (`match_type_evaluator.py`)

**Bias detection and performance evaluation across match types.**

```bash
# Evaluate trained model
python match_type_evaluator.py --model models/best.pt --test_dir images/test

# Use manifest for enhanced metadata
python match_type_evaluator.py --model models/best.pt --manifest dataset_manifest.json

# Custom bias threshold
python match_type_evaluator.py --model models/best.pt --bias_threshold 0.03
```

**Bias Detection Features:**

- **Performance Gap Analysis**: F1 score differences between match types
- **Confidence Gap Detection**: Confidence score variations across modes
- **Automated Recommendations**: Actionable suggestions for bias mitigation
- **Detailed Reporting**: JSON reports with per-image and aggregate metrics

**Example Bias Report:**

```json
{
  "bias_analysis": {
    "performance_gaps": [
      "F1 gap between ranked (0.924) and classic (0.867): 0.057"
    ],
    "confidence_gaps": [
      "Confidence gap between ranked (0.891) and classic (0.823): 0.068"
    ],
    "recommendations": [
      "Consider rebalancing training data or using weighted sampling",
      "Investigate confidence calibration across match types"
    ]
  }
}
```

### 3. **Training Configuration Generator** (`train_config_generator.py`)

**Generates YOLO configurations with match-type awareness.**

```bash
# Basic configuration
python train_config_generator.py --dataset_dir . --output dataset.yaml

# With match-type-aware weighting
python train_config_generator.py --match_type_weights --output weighted_config.yaml

# Multi-task learning (object detection + match type prediction)
python train_config_generator.py --multi_task --output multitask_config.yaml

# Generate training script
python train_config_generator.py --generate_script --output train_config.yaml
```

**Configuration Options:**

1. **Basic Config**: Standard YOLO dataset configuration
2. **Weighted Config**: Inverse frequency weighting based on match type distribution
3. **Multi-Task Config**: Joint training for object detection and match type classification

## 🔄 Complete Workflow

### Phase 1: Dataset Preparation

```bash
# 1. Organize your collection structure
collection/
├── 1_RANKED_MATCHES/
│   ├── excellent_performance/
│   │   ├── kda_view/
│   │   └── damage_view/
│   └── good_performance/
├── 2_CLASSIC_MATCHES/
└── 3_OTHER_MODES/

# 2. Run enhanced preparation
python enhanced_prepare_for_annotation.py --clean_start

# 3. Verify results
python enhanced_prepare_for_annotation.py --validate_only
```

### Phase 2: Annotation

```bash
# Start annotation workflow (existing)
./start_annotation.sh

# Annotate using Label Studio with generated images
# Files are already properly named and organized
```

### Phase 3: Training Configuration

```bash
# Generate training config with bias mitigation
python train_config_generator.py --match_type_weights --generate_script

# Review generated configuration
cat dataset.yaml
```

### Phase 4: Training

```bash
# Train with generated configuration
python train.py

# Or use traditional YOLO training
yolo train data=dataset.yaml model=yolov8n.pt epochs=100
```

### Phase 5: Evaluation & Bias Detection

```bash
# Evaluate trained model
python match_type_evaluator.py --model runs/detect/train/weights/best.pt

# Review bias analysis
cat match_type_evaluation_report.json
```

## 📊 Match Type Distribution Analysis

The pipeline automatically analyzes your dataset distribution:

```
🎯 Match Type Distribution:
  Ranked: 45 images (56.2%)
  Classic: 28 images (35.0%)
  Other: 7 images (8.8%)

📊 Split Distribution:
  Train: 56 images (70.0%)
  Val: 12 images (15.0%)
  Test: 12 images (15.0%)
```

## 🎭 Filename Convention

**Format**: `{match_type}_{performance}_{view}_{index:03d}[_collision].jpg`

**Components:**

- **match_type**: `ranked` | `classic` | `other`
- **performance**: `excellent` | `good` | `average` | `poor` | `mvploss`
- **view**: `kda` | `dmg`
- **index**: Zero-padded 3-digit number (`001`, `002`, etc.)
- **collision**: Optional collision resolver (`_01`, `_02`, etc.)

**Examples:**

- `ranked_excellent_kda_001.jpg` - Ranked match, excellent performance, KDA view, first image
- `classic_poor_dmg_023.jpg` - Classic match, poor performance, damage view, 23rd image
- `other_mvploss_kda_005_01.jpg` - Other mode, MVP loss, KDA view, collision resolved

## ⚠️ Bias Mitigation Strategies

### 1. **Stratified Sampling** (Implemented)

- Independent train/val/test splits per match type
- Ensures balanced representation in each subset
- Prevents training set bias from affecting validation

### 2. **Weighted Training** (Available)

- Inverse frequency weighting based on match type distribution
- Reduces impact of overrepresented match types
- Configurable through training configuration generator

### 3. **Multi-Task Learning** (Available)

- Joint training for object detection and match type prediction
- Helps model learn match-type-invariant features
- Optional auxiliary loss for match type classification

### 4. **Bias Monitoring** (Implemented)

- Automated detection of performance gaps
- Confidence score analysis across match types
- Regular evaluation and reporting

## 🔧 Configuration Options

### Dataset Preparation

```python
# Split ratios (customizable)
split_ratios = {
    "train": 0.70,
    "val": 0.15,
    "test": 0.15
}

# Filename collision handling
collision_resolution = True
preserve_original_names = False
```

### Training Configuration

```yaml
# Match-type-aware weighting
train_params:
  class_weights:
    ranked: 0.89
    classic: 1.43
    other: 3.57

# Multi-task learning
multi_task:
  primary_task: object_detection
  auxiliary_task: match_type_classification
  auxiliary_weight: 0.1
```

### Evaluation Settings

```yaml
evaluation:
  bias_threshold: 0.05
  confidence_threshold: 0.25
  match_type_aware: true
  per_class_metrics: true
```

## 📈 Performance Monitoring

The pipeline provides comprehensive performance tracking:

### Match-Type Metrics

- **Precision/Recall/F1** per match type
- **Confidence score** distributions
- **Class-specific performance** analysis
- **Bias detection** with thresholds

### Output Reports

- **CSV Manifest**: Tabular data for easy analysis
- **JSON Manifest**: Structured data for programmatic access
- **Evaluation Reports**: Detailed performance and bias analysis
- **Training Logs**: Match type distribution and weighting information

## 🚀 Next Steps & Advanced Features

### Recommended Workflow

1. **Start with Ranked-only training** (your current approach is good!)
2. **Collect Classic/Other data** gradually
3. **Run bias detection** before mixing datasets
4. **Use weighted training** if bias is detected
5. **Monitor performance** across all match types

### Advanced Features

- **Data augmentation** tailored per match type
- **Confidence calibration** across match types
- **Active learning** for targeted data collection
- **Domain adaptation** techniques for bias reduction

### Integration with Existing Pipeline

This enhanced pipeline is **fully compatible** with your existing annotation workflow:

- Works with existing `start_annotation.sh`
- Compatible with Label Studio setup
- Maintains existing class definitions
- Preserves annotation quality standards

## 📋 File Reference

| File                                 | Purpose                     | Key Features                                               |
| ------------------------------------ | --------------------------- | ---------------------------------------------------------- |
| `enhanced_prepare_for_annotation.py` | Main preparation script     | Stratified sampling, filename encoding, collision handling |
| `match_type_evaluator.py`            | Bias detection & evaluation | Performance gap analysis, confidence monitoring            |
| `train_config_generator.py`          | Training configuration      | Weighted sampling, multi-task learning options             |
| `dataset_manifest.csv`               | Tabular metadata            | Easy analysis in Excel/pandas                              |
| `dataset_manifest.json`              | Structured metadata         | Programmatic access, detailed information                  |

---

**🎉 Result**: A robust, bias-aware YOLO training pipeline that ensures consistent performance across all MLBB match types while maintaining full compatibility with your existing annotation workflow.

The pipeline automatically handles the complexities of match-type-aware training while providing comprehensive monitoring and bias detection capabilities to ensure your model performs reliably across Ranked, Classic, and Other game modes.
