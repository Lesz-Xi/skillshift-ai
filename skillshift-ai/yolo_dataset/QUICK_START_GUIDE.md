# 🚀 Quick Start: Enhanced Match-Type-Aware Pipeline

## ⚡ Immediate Implementation (5 minutes)

### Step 1: Run Enhanced Dataset Preparation

```bash
cd skillshift-ai/yolo_dataset

# First time setup (cleans existing directories)
python enhanced_prepare_for_annotation.py --clean_start

# Subsequent runs (safe, preserves existing data)
python enhanced_prepare_for_annotation.py --update_existing
```

### Step 2: Verify Results

```bash
# Check what was generated
ls -la images/train/ | head -10
ls -la labels/train/ | head -10

# Validate dataset integrity
python enhanced_prepare_for_annotation.py --validate_only
```

### Step 3: Review Dataset Manifest

```bash
# Quick overview in CSV format
head -20 dataset_manifest.csv

# Detailed JSON structure
cat dataset_manifest.json | jq '.metadata'
```

### Step 4: Generate Training Configuration

```bash
# Basic configuration
python train_config_generator.py --output dataset.yaml

# OR with bias mitigation (recommended)
python train_config_generator.py --match_type_weights --generate_script --output dataset.yaml
```

### Step 5: Start Training

```bash
# If you generated the training script
python train.py

# OR traditional YOLO training
yolo train data=dataset.yaml model=yolov8n.pt epochs=100 imgsz=640
```

---

## 📊 Expected Output

After running `enhanced_prepare_for_annotation.py --clean_start`, you'll see:

```
🚀 Starting Enhanced MLBB YOLO Dataset Preparation
============================================================
🔍 Scanning collection directory...
  📁 Processing ranked matches...
  📁 Processing classic matches...
  📁 Processing other matches...
  ✅ Found 87 images across all match types

🎯 Performing stratified splits per match type...
  📊 Splitting 45 ranked images...
    📈 ranked: train=31, val=7, test=7
  📊 Splitting 28 classic images...
    📈 classic: train=19, val=4, test=5
  📊 Splitting 14 other images...
    📈 other: train=9, val=2, test=3

📁 Preparing output directories...
📋 Copying images and synchronizing annotations...
📄 Generating dataset manifests...
  ✅ Generated CSV manifest: dataset_manifest.csv
  ✅ Generated JSON manifest: dataset_manifest.json

📊 Dataset Preparation Statistics
==================================================
📈 Total Images: 87

🎯 Match Type Distribution:
  Ranked: 45 images (51.7%)
  Classic: 28 images (32.2%)
  Other: 14 images (16.1%)

📊 Split Distribution:
  Train: 59 images (67.8%)
  Val: 13 images (14.9%)
  Test: 15 images (17.2%)

🎭 Performance Distribution:
  Excellent: 23 images (26.4%)
  Good: 31 images (35.6%)
  Average: 18 images (20.7%)
  Poor: 15 images (17.2%)

⚠️ Filename Collisions Resolved: 0
📝 Annotation Files Synchronized: 87
📋 Annotation Coverage: 100.0%

🔍 Validating dataset integrity...
✅ Dataset validation passed!

🎉 Dataset preparation completed successfully!
```

---

## 🎭 Filename Examples

Your images will be renamed like this:

```
Original: 1_ranked_matches_excellent_performance_match01_win_kda.PNG
New:      ranked_excellent_kda_001.jpg

Original: 2_classic_matches_poor_performance_match05_loss_damage.PNG
New:      classic_poor_dmg_002.jpg

Original: 3_other_modes_mvp_loss_performance_match03_mvploss_kda.PNG
New:      other_mvploss_kda_003.jpg
```

---

## 🔧 Troubleshooting

### Issue: "No images found in collection directory"

**Solution**: Ensure your collection structure follows this format:

```
collection/
├── 1_RANKED_MATCHES/
│   ├── excellent_performance/
│   │   ├── kda_view/
│   │   └── damage_view/
└── 2_CLASSIC_MATCHES/
    └── good_performance/
        ├── kda_view/
        └── damage_view/
```

### Issue: Missing annotations after preparation

**Check**: Annotation files (.txt) should be in the same directory as images with same base name:

```
kda_view/
├── image001.jpg
├── image001.txt  ← Annotation file
├── image002.png
└── image002.txt  ← Annotation file
```

### Issue: Filename collisions

**Normal**: The system automatically resolves collisions with `_01`, `_02` suffixes. Check `collision_resolved` field in manifest.

---

## 📈 Next Steps After Preparation

### 1. **Review Dataset Balance**

```bash
# Check match type distribution
python -c "
import pandas as pd
df = pd.read_csv('dataset_manifest.csv')
print(df.groupby('match_type').size())
print(df.groupby(['match_type', 'split']).size())
"
```

### 2. **Start Annotation** (if not done)

```bash
./start_annotation.sh
# Continue with your existing Label Studio workflow
```

### 3. **Train Your Model**

```bash
# With bias mitigation
python train_config_generator.py --match_type_weights --generate_script
python train.py

# Monitor training for match type balance
```

### 4. **Evaluate for Bias** (after training)

```bash
python match_type_evaluator.py --model runs/detect/train/weights/best.pt
```

---

## ⚠️ Important Notes

1. **Backup First**: The `--clean_start` flag removes existing `images/` and `labels/` directories
2. **Iterative Safe**: Use `--update_existing` for subsequent runs
3. **Annotation Sync**: .txt files are automatically renamed to match images
4. **Collision Handling**: Duplicate filenames get `_01`, `_02` suffixes automatically
5. **Manifest Files**: `dataset_manifest.csv` and `dataset_manifest.json` track all metadata

---

## 🎯 Key Benefits You'll Get

✅ **Stratified Sampling**: Balanced train/val/test per match type  
✅ **Encoded Filenames**: Easy identification of match type and performance  
✅ **Bias Detection**: Automatic monitoring of performance gaps  
✅ **Synchronized Annotations**: No mismatched image-annotation pairs  
✅ **Collision Prevention**: Unique filenames across all splits  
✅ **Iterative Safety**: Safe re-runs without data corruption  
✅ **Full Compatibility**: Works with existing annotation workflow

---

**Result**: Your dataset will be properly organized with match-type awareness, giving you the foundation for bias-free YOLO training across Ranked, Classic, and Other MLBB match types! 🎉
