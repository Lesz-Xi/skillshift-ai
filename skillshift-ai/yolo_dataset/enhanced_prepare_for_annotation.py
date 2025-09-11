#!/usr/bin/env python3
"""
Enhanced MLBB YOLO Dataset Preparation with Match-Type-Aware Training

This script implements a robust pipeline for preparing YOLO datasets with:
1. Match-type-aware stratified sampling
2. Consistent filename encoding (e.g., ranked_mvp_kda_001.jpg)
3. Synchronized annotation files
4. Manifest generation for downstream processing
5. Collision prevention and iterative safety

Usage:
    python enhanced_prepare_for_annotation.py --clean_start
    python enhanced_prepare_for_annotation.py --update_existing
    python enhanced_prepare_for_annotation.py --validate_only
"""

import shutil
import json
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ImageMetadata:
    """Metadata for each image in the dataset."""
    original_path: str
    match_type: str  # ranked, classic, other
    performance_level: str  # excellent, good, average, poor, mvp_loss
    view_type: str  # kda, damage
    new_filename: str
    split: str  # train, val, test
    annotation_exists: bool = False
    collision_resolved: bool = False


@dataclass
class DatasetStatistics:
    """Statistics for the prepared dataset."""
    total_images: int
    images_per_match_type: Dict[str, int]
    images_per_split: Dict[str, int]
    images_per_performance: Dict[str, int]
    collision_count: int
    annotation_sync_success: int


class MatchTypeAwareDatasetPreparer:
    """Enhanced dataset preparer with match-type awareness."""
    
    def __init__(self, base_dir: Path = None):
        """Initialize the dataset preparer."""
        self.base_dir = base_dir or Path(__file__).parent
        self.collection_dir = self.base_dir / "collection"
        self.images_dir = self.base_dir / "images"
        self.labels_dir = self.base_dir / "labels"
        
        # Match type mappings
        self.match_type_map = {
            "1_RANKED_MATCHES": "ranked",
            "2_CLASSIC_MATCHES": "classic", 
            "3_OTHER_MODES": "other"
        }
        
        # Performance level mappings (shortened for filenames)
        self.performance_map = {
            "excellent_performance": "excellent",
            "good_performance": "good",
            "average_performance": "average", 
            "poor_performance": "poor",
            "mvp_loss_performance": "mvploss"
        }
        
        # View type mappings
        self.view_map = {
            "kda_view": "kda",
            "damage_view": "dmg"
        }
        
        # Split ratios (stratified per match type)
        self.split_ratios = {
            "train": 0.70,
            "val": 0.15,
            "test": 0.15
        }
        
        # Filename collision tracking
        self.used_filenames: Set[str] = set()
        self.filename_counters = defaultdict(int)
        
    def scan_collection(self) -> List[ImageMetadata]:
        """Scan collection directory and build image metadata."""
        logger.info("🔍 Scanning collection directory...")
        
        image_metadata = []
        extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
        
        for match_type_dir in self.collection_dir.iterdir():
            if (not match_type_dir.is_dir() or 
                    match_type_dir.name not in self.match_type_map):
                continue
                
            match_type = self.match_type_map[match_type_dir.name]
            logger.info(f"  📁 Processing {match_type} matches...")
            
            for performance_dir in match_type_dir.iterdir():
                if (not performance_dir.is_dir() or 
                        performance_dir.name not in self.performance_map):
                    continue
                    
                performance = self.performance_map[performance_dir.name]
                
                for view_dir in performance_dir.iterdir():
                    if (not view_dir.is_dir() or 
                            view_dir.name not in self.view_map):
                        continue
                        
                    view_type = self.view_map[view_dir.name]
                    
                    # Find all images in this directory
                    for image_path in view_dir.iterdir():
                        if image_path.suffix in extensions:
                            metadata = ImageMetadata(
                                original_path=str(image_path),
                                match_type=match_type,
                                performance_level=performance,
                                view_type=view_type,
                                new_filename="",  # Will be generated
                                split="",  # Will be assigned
                            )
                            image_metadata.append(metadata)
        
        logger.info(f"  ✅ Found {len(image_metadata)} images across all match types")
        return image_metadata
    
    def generate_filename(self, metadata: ImageMetadata, index: int) -> str:
        """Generate a unique, descriptive filename."""
        # Base pattern: {match_type}_{performance}_{view}_{index:03d}.jpg
        base_name = (f"{metadata.match_type}_{metadata.performance_level}_"
                    f"{metadata.view_type}_{index:03d}")
        
        # Handle collisions by incrementing counter
        while base_name in self.used_filenames:
            self.filename_counters[base_name] += 1
            base_name = (f"{metadata.match_type}_{metadata.performance_level}_"
                        f"{metadata.view_type}_{index:03d}_"
                        f"{self.filename_counters[base_name]:02d}")
            metadata.collision_resolved = True
        
        self.used_filenames.add(base_name)
        return f"{base_name}.jpg"
    
    def stratified_split(self, 
                        metadata_list: List[ImageMetadata]) -> List[ImageMetadata]:
        """Perform stratified train/val/test split per match type."""
        logger.info("🎯 Performing stratified splits per match type...")
        
        # Group by match type
        match_type_groups = defaultdict(list)
        for metadata in metadata_list:
            match_type_groups[metadata.match_type].append(metadata)
        
        split_metadata = []
        
        for match_type, items in match_type_groups.items():
            logger.info(f"  📊 Splitting {len(items)} {match_type} images...")
            
            # Sort for consistent splits
            items.sort(key=lambda x: (x.performance_level, x.view_type, 
                                     x.original_path))
            
            # Calculate split indices
            total = len(items)
            train_end = int(total * self.split_ratios["train"])
            val_end = train_end + int(total * self.split_ratios["val"])
            
            # Assign splits
            for i, metadata in enumerate(items):
                if i < train_end:
                    metadata.split = "train"
                elif i < val_end:
                    metadata.split = "val"
                else:
                    metadata.split = "test"
                
                # Generate unique filename
                metadata.new_filename = self.generate_filename(metadata, i + 1)
            
            split_metadata.extend(items)
            
            # Log split statistics
            splits = defaultdict(int)
            for item in items:
                splits[item.split] += 1
            logger.info(f"    📈 {match_type}: train={splits['train']}, "
                       f"val={splits['val']}, test={splits['test']}")
        
        return split_metadata
    
    def prepare_directories(self, clean_start: bool = False):
        """Prepare output directories."""
        logger.info("📁 Preparing output directories...")
        
        if clean_start:
            logger.info("  🧹 Cleaning existing directories...")
            for dir_path in [self.images_dir, self.labels_dir]:
                if dir_path.exists():
                    shutil.rmtree(dir_path)
        
        # Create directory structure
        for base_dir in [self.images_dir, self.labels_dir]:
            for split in ["train", "val", "test"]:
                split_dir = base_dir / split
                split_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"    ✅ Created {split_dir}")
    
    def copy_images_and_annotations(self, 
                                   metadata_list: List[ImageMetadata]) -> int:
        """Copy images and synchronize annotation files."""
        logger.info("📋 Copying images and synchronizing annotations...")
        
        annotation_success_count = 0
        
        for metadata in metadata_list:
            # Copy image
            source_path = Path(metadata.original_path)
            target_image_path = (self.images_dir / metadata.split / 
                               metadata.new_filename)
            
            try:
                shutil.copy2(source_path, target_image_path)
                logger.debug(f"  ✅ Copied {source_path.name} → "
                           f"{metadata.new_filename}")
                
                # Handle annotation file if it exists
                annotation_success = self._handle_annotation_file(metadata, 
                                                                 source_path)
                if annotation_success:
                    annotation_success_count += 1
                    metadata.annotation_exists = True
                    
            except Exception as e:
                logger.error(f"  ❌ Failed to copy {source_path}: {e}")
        
        return annotation_success_count
    
    def _handle_annotation_file(self, metadata: ImageMetadata, 
                               source_image_path: Path) -> bool:
        """Handle annotation file copying and renaming."""
        # Look for corresponding annotation file
        annotation_extensions = ['.txt']
        
        for ext in annotation_extensions:
            source_annotation = source_image_path.with_suffix(ext)
            if source_annotation.exists():
                # Create target annotation path
                target_annotation_name = (Path(metadata.new_filename)
                                        .with_suffix(ext).name)
                target_annotation_path = (self.labels_dir / metadata.split / 
                                        target_annotation_name)
                
                try:
                    shutil.copy2(source_annotation, target_annotation_path)
                    logger.debug(f"    📝 Annotation: {source_annotation.name} "
                               f"→ {target_annotation_name}")
                    return True
                except Exception as e:
                    logger.error(f"    ❌ Failed to copy annotation "
                               f"{source_annotation}: {e}")
        
        return False
    
    def generate_manifest(self, 
                         metadata_list: List[ImageMetadata]) -> Tuple[str, str]:
        """Generate CSV and JSON manifests linking images to metadata."""
        logger.info("📄 Generating dataset manifests...")
        
        # Generate CSV manifest
        csv_path = self.base_dir / "dataset_manifest.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['filename', 'match_type', 'performance_level', 
                         'view_type', 'split', 'original_path', 
                         'annotation_exists', 'collision_resolved']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for metadata in metadata_list:
                writer.writerow({
                    'filename': metadata.new_filename,
                    'match_type': metadata.match_type,
                    'performance_level': metadata.performance_level,
                    'view_type': metadata.view_type,
                    'split': metadata.split,
                    'original_path': metadata.original_path,
                    'annotation_exists': metadata.annotation_exists,
                    'collision_resolved': metadata.collision_resolved
                })
        
        # Generate JSON manifest
        json_path = self.base_dir / "dataset_manifest.json"
        manifest_data = {
            'metadata': {
                'version': '1.0',
                'generated_by': 'enhanced_prepare_for_annotation.py',
                'total_images': len(metadata_list),
                'split_ratios': self.split_ratios,
                'naming_convention': ('{match_type}_{performance}_{view}_'
                                     '{index:03d}.jpg')
            },
            'images': [asdict(metadata) for metadata in metadata_list]
        }
        
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(manifest_data, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"  ✅ Generated CSV manifest: {csv_path}")
        logger.info(f"  ✅ Generated JSON manifest: {json_path}")
        
        return str(csv_path), str(json_path)
    
    def generate_statistics(self, 
                           metadata_list: List[ImageMetadata]) -> DatasetStatistics:
        """Generate comprehensive dataset statistics."""
        stats = DatasetStatistics(
            total_images=len(metadata_list),
            images_per_match_type=defaultdict(int),
            images_per_split=defaultdict(int),
            images_per_performance=defaultdict(int),
            collision_count=0,
            annotation_sync_success=0
        )
        
        for metadata in metadata_list:
            stats.images_per_match_type[metadata.match_type] += 1
            stats.images_per_split[metadata.split] += 1
            stats.images_per_performance[metadata.performance_level] += 1
            
            if metadata.collision_resolved:
                stats.collision_count += 1
            if metadata.annotation_exists:
                stats.annotation_sync_success += 1
        
        return stats
    
    def print_statistics(self, stats: DatasetStatistics):
        """Print comprehensive dataset statistics."""
        logger.info("\n📊 Dataset Preparation Statistics")
        logger.info("=" * 50)
        logger.info(f"📈 Total Images: {stats.total_images}")
        
        logger.info("\n🎯 Match Type Distribution:")
        for match_type, count in stats.images_per_match_type.items():
            percentage = (count / stats.total_images) * 100
            logger.info(f"  {match_type.capitalize()}: {count} images "
                       f"({percentage:.1f}%)")
        
        logger.info("\n📊 Split Distribution:")
        for split, count in stats.images_per_split.items():
            percentage = (count / stats.total_images) * 100
            logger.info(f"  {split.capitalize()}: {count} images "
                       f"({percentage:.1f}%)")
        
        logger.info("\n🎭 Performance Distribution:")
        for performance, count in stats.images_per_performance.items():
            percentage = (count / stats.total_images) * 100
            logger.info(f"  {performance.capitalize()}: {count} images "
                       f"({percentage:.1f}%)")
        
        logger.info(f"\n⚠️ Filename Collisions Resolved: {stats.collision_count}")
        logger.info(f"📝 Annotation Files Synchronized: "
                   f"{stats.annotation_sync_success}")
        
        annotation_rate = (stats.annotation_sync_success / stats.total_images) * 100
        logger.info(f"📋 Annotation Coverage: {annotation_rate:.1f}%")
    
    def validate_dataset(self) -> bool:
        """Validate the prepared dataset integrity."""
        logger.info("🔍 Validating dataset integrity...")
        
        validation_passed = True
        
        # Check directory structure
        for base_dir in [self.images_dir, self.labels_dir]:
            for split in ["train", "val", "test"]:
                split_dir = base_dir / split
                if not split_dir.exists():
                    logger.error(f"❌ Missing directory: {split_dir}")
                    validation_passed = False
        
        # Check image-annotation synchronization
        for split in ["train", "val", "test"]:
            images_dir = self.images_dir / split
            labels_dir = self.labels_dir / split
            
            if not images_dir.exists() or not labels_dir.exists():
                continue
                
            image_files = {f.stem for f in images_dir.glob("*.jpg")}
            label_files = {f.stem for f in labels_dir.glob("*.txt")}
            
            missing_labels = image_files - label_files
            orphaned_labels = label_files - image_files
            
            if missing_labels:
                logger.warning(f"⚠️ {split}: {len(missing_labels)} images "
                             f"missing annotations")
            if orphaned_labels:
                logger.warning(f"⚠️ {split}: {len(orphaned_labels)} orphaned "
                             f"annotation files")
        
        # Check manifest existence
        manifest_files = ["dataset_manifest.csv", "dataset_manifest.json"]
        for manifest_file in manifest_files:
            manifest_path = self.base_dir / manifest_file
            if not manifest_path.exists():
                logger.error(f"❌ Missing manifest: {manifest_file}")
                validation_passed = False
        
        if validation_passed:
            logger.info("✅ Dataset validation passed!")
        else:
            logger.error("❌ Dataset validation failed!")
        
        return validation_passed
    
    def prepare_dataset(self, clean_start: bool = False, 
                       validate_only: bool = False) -> bool:
        """Main dataset preparation pipeline."""
        logger.info("🚀 Starting Enhanced MLBB YOLO Dataset Preparation")
        logger.info("=" * 60)
        
        if validate_only:
            return self.validate_dataset()
        
        try:
            # Step 1: Scan collection
            metadata_list = self.scan_collection()
            if not metadata_list:
                logger.error("❌ No images found in collection directory!")
                return False
            
            # Step 2: Perform stratified split
            metadata_list = self.stratified_split(metadata_list)
            
            # Step 3: Prepare directories
            self.prepare_directories(clean_start=clean_start)
            
            # Step 4: Copy images and annotations
            annotation_success_count = self.copy_images_and_annotations(
                metadata_list)
            
            # Step 5: Generate manifests
            csv_path, json_path = self.generate_manifest(metadata_list)
            
            # Step 6: Generate and print statistics
            stats = self.generate_statistics(metadata_list)
            self.print_statistics(stats)
            
            # Step 7: Validate dataset
            validation_passed = self.validate_dataset()
            
            if validation_passed:
                logger.info("\n🎉 Dataset preparation completed successfully!")
                logger.info("\n🚀 Next Steps:")
                logger.info("1. Review manifest files for dataset overview")
                logger.info("2. Start annotation with: ./start_annotation.sh")
                logger.info("3. Configure YOLO training with match-type awareness")
                logger.info("4. Implement per-match-type evaluation metrics")
                return True
            else:
                logger.error("\n❌ Dataset preparation completed with "
                           "validation errors!")
                return False
                
        except Exception as e:
            logger.error(f"❌ Dataset preparation failed: {e}")
            return False


def main():
    """Main entry point with command line interface."""
    parser = argparse.ArgumentParser(
        description=("Enhanced MLBB YOLO Dataset Preparation with "
                    "Match-Type Awareness")
    )
    parser.add_argument(
        "--clean_start", 
        action="store_true",
        help="Remove existing output directories before preparation"
    )
    parser.add_argument(
        "--update_existing",
        action="store_true", 
        help="Update existing dataset without cleaning (default)"
    )
    parser.add_argument(
        "--validate_only",
        action="store_true",
        help="Only validate existing dataset without preparation"
    )
    parser.add_argument(
        "--base_dir",
        type=str,
        help="Base directory for dataset preparation (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Determine base directory
    base_dir = Path(args.base_dir) if args.base_dir else Path(__file__).parent
    
    # Initialize preparer
    preparer = MatchTypeAwareDatasetPreparer(base_dir=base_dir)
    
    # Run preparation
    clean_start = args.clean_start
    validate_only = args.validate_only
    
    success = preparer.prepare_dataset(
        clean_start=clean_start,
        validate_only=validate_only
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main()) 