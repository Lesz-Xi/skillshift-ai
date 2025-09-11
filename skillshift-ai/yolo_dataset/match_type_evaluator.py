#!/usr/bin/env python3
"""
Match-Type-Aware YOLO Model Evaluator

This script evaluates YOLO model performance across different match types
to detect bias and ensure consistent accuracy across Ranked, Classic, and Other modes.

Usage:
    python match_type_evaluator.py --model models/best.pt --test_dir images/test
    python match_type_evaluator.py --model models/best.pt --manifest dataset_manifest.json
"""

import json
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Results for a single image evaluation."""
    filename: str
    match_type: str
    performance_level: str
    view_type: str
    confidence_scores: List[float]
    detected_classes: List[int]
    ground_truth_classes: List[int]
    precision: float
    recall: float
    f1_score: float


@dataclass
class MatchTypeMetrics:
    """Aggregated metrics for a specific match type."""
    match_type: str
    total_images: int
    avg_precision: float
    avg_recall: float
    avg_f1: float
    avg_confidence: float
    class_performance: Dict[int, float]


class MatchTypeAwareEvaluator:
    """Evaluates YOLO model performance across different match types."""
    
    def __init__(self, model_path: str, manifest_path: str = None):
        """Initialize evaluator with model and optional manifest."""
        self.model_path = Path(model_path)
        self.manifest_path = Path(manifest_path) if manifest_path else None
        self.results: List[EvaluationResult] = []
        
        # Load model (placeholder - replace with actual YOLO loading)
        logger.info(f"Loading YOLO model from {self.model_path}")
        # self.model = YOLO(self.model_path)
        
    def load_manifest(self) -> Optional[pd.DataFrame]:
        """Load dataset manifest for match type metadata."""
        if not self.manifest_path or not self.manifest_path.exists():
            logger.warning("No manifest file provided or found")
            return None
            
        if self.manifest_path.suffix == '.json':
            with open(self.manifest_path) as f:
                data = json.load(f)
                return pd.DataFrame(data['images'])
        elif self.manifest_path.suffix == '.csv':
            return pd.read_csv(self.manifest_path)
        else:
            logger.error(f"Unsupported manifest format: {self.manifest_path.suffix}")
            return None
    
    def extract_match_type_from_filename(self, filename: str) -> Tuple[str, str, str]:
        """Extract match type info from enhanced filename format."""
        # Expected format: {match_type}_{performance}_{view}_{index:03d}.jpg
        parts = Path(filename).stem.split('_')
        
        if len(parts) >= 3:
            match_type = parts[0]  # ranked, classic, other
            performance = parts[1]  # excellent, good, average, poor, mvploss
            view_type = parts[2]    # kda, dmg
            return match_type, performance, view_type
        else:
            # Fallback for non-enhanced filenames
            return "unknown", "unknown", "unknown"
    
    def evaluate_image(self, image_path: Path, 
                      annotation_path: Path) -> EvaluationResult:
        """Evaluate a single image and return results."""
        # Extract match type information
        match_type, performance, view_type = self.extract_match_type_from_filename(
            image_path.name)
        
        # Load ground truth annotations
        ground_truth_classes = self.load_ground_truth(annotation_path)
        
        # Run YOLO inference (placeholder)
        # results = self.model(image_path)
        # detected_classes = results.boxes.cls.tolist()
        # confidence_scores = results.boxes.conf.tolist()
        
        # Placeholder values for demonstration
        detected_classes = [0, 1, 2]  # Replace with actual inference
        confidence_scores = [0.85, 0.72, 0.91]  # Replace with actual scores
        
        # Calculate metrics
        precision, recall, f1 = self.calculate_metrics(
            detected_classes, ground_truth_classes)
        
        return EvaluationResult(
            filename=image_path.name,
            match_type=match_type,
            performance_level=performance,
            view_type=view_type,
            confidence_scores=confidence_scores,
            detected_classes=detected_classes,
            ground_truth_classes=ground_truth_classes,
            precision=precision,
            recall=recall,
            f1_score=f1
        )
    
    def load_ground_truth(self, annotation_path: Path) -> List[int]:
        """Load ground truth class labels from YOLO annotation file."""
        if not annotation_path.exists():
            return []
        
        classes = []
        with open(annotation_path) as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    classes.append(int(parts[0]))  # First value is class ID
        
        return classes
    
    def calculate_metrics(self, detected: List[int], 
                         ground_truth: List[int]) -> Tuple[float, float, float]:
        """Calculate precision, recall, and F1 score."""
        if not ground_truth:
            return 0.0, 0.0, 0.0
        
        detected_set = set(detected)
        gt_set = set(ground_truth)
        
        if not detected_set:
            return 0.0, 0.0, 0.0
        
        true_positives = len(detected_set & gt_set)
        precision = true_positives / len(detected_set) if detected_set else 0.0
        recall = true_positives / len(gt_set) if gt_set else 0.0
        
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)
        
        return precision, recall, f1
    
    def evaluate_test_set(self, test_images_dir: Path, 
                         test_labels_dir: Path) -> List[EvaluationResult]:
        """Evaluate entire test set and return results."""
        logger.info("🧪 Evaluating test set...")
        
        results = []
        image_files = list(test_images_dir.glob("*.jpg"))
        
        for image_path in image_files:
            annotation_path = test_labels_dir / f"{image_path.stem}.txt"
            
            try:
                result = self.evaluate_image(image_path, annotation_path)
                results.append(result)
                
                logger.debug(f"Evaluated {image_path.name}: "
                           f"P={result.precision:.3f}, R={result.recall:.3f}, "
                           f"F1={result.f1_score:.3f}")
                
            except Exception as e:
                logger.error(f"Failed to evaluate {image_path.name}: {e}")
        
        self.results = results
        logger.info(f"✅ Evaluated {len(results)} images")
        return results
    
    def analyze_by_match_type(self) -> Dict[str, MatchTypeMetrics]:
        """Analyze results grouped by match type."""
        logger.info("📊 Analyzing results by match type...")
        
        match_type_groups = {}
        for result in self.results:
            match_type = result.match_type
            if match_type not in match_type_groups:
                match_type_groups[match_type] = []
            match_type_groups[match_type].append(result)
        
        metrics = {}
        for match_type, results in match_type_groups.items():
            if not results:
                continue
                
            # Calculate aggregate metrics
            avg_precision = sum(r.precision for r in results) / len(results)
            avg_recall = sum(r.recall for r in results) / len(results)
            avg_f1 = sum(r.f1_score for r in results) / len(results)
            
            # Calculate average confidence
            all_confidences = []
            for r in results:
                all_confidences.extend(r.confidence_scores)
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            
            # Calculate per-class performance (placeholder)
            class_performance = {}
            
            metrics[match_type] = MatchTypeMetrics(
                match_type=match_type,
                total_images=len(results),
                avg_precision=avg_precision,
                avg_recall=avg_recall,
                avg_f1=avg_f1,
                avg_confidence=avg_confidence,
                class_performance=class_performance
            )
        
        return metrics
    
    def detect_bias(self, metrics: Dict[str, MatchTypeMetrics], 
                   threshold: float = 0.05) -> Dict[str, List[str]]:
        """Detect bias between match types."""
        logger.info("🔍 Detecting bias between match types...")
        
        bias_report = {
            "performance_gaps": [],
            "confidence_gaps": [],
            "recommendations": []
        }
        
        # Compare performance between match types
        match_types = list(metrics.keys())
        for i, match_type1 in enumerate(match_types):
            for match_type2 in match_types[i+1:]:
                metrics1 = metrics[match_type1]
                metrics2 = metrics[match_type2]
                
                # Check F1 score gap
                f1_gap = abs(metrics1.avg_f1 - metrics2.avg_f1)
                if f1_gap > threshold:
                    bias_report["performance_gaps"].append(
                        f"F1 gap between {match_type1} ({metrics1.avg_f1:.3f}) "
                        f"and {match_type2} ({metrics2.avg_f1:.3f}): {f1_gap:.3f}"
                    )
                
                # Check confidence gap
                conf_gap = abs(metrics1.avg_confidence - metrics2.avg_confidence)
                if conf_gap > threshold:
                    bias_report["confidence_gaps"].append(
                        f"Confidence gap between {match_type1} "
                        f"({metrics1.avg_confidence:.3f}) and {match_type2} "
                        f"({metrics2.avg_confidence:.3f}): {conf_gap:.3f}"
                    )
        
        # Generate recommendations
        if bias_report["performance_gaps"]:
            bias_report["recommendations"].append(
                "Consider rebalancing training data or using weighted sampling"
            )
        if bias_report["confidence_gaps"]:
            bias_report["recommendations"].append(
                "Investigate confidence calibration across match types"
            )
        
        return bias_report
    
    def generate_report(self, output_path: str = "match_type_evaluation_report.json"):
        """Generate comprehensive evaluation report."""
        logger.info("📄 Generating evaluation report...")
        
        metrics = self.analyze_by_match_type()
        bias_report = self.detect_bias(metrics)
        
        report = {
            "model_path": str(self.model_path),
            "evaluation_timestamp": pd.Timestamp.now().isoformat(),
            "total_images_evaluated": len(self.results),
            "match_type_metrics": {
                mt: {
                    "total_images": m.total_images,
                    "avg_precision": m.avg_precision,
                    "avg_recall": m.avg_recall,
                    "avg_f1": m.avg_f1,
                    "avg_confidence": m.avg_confidence
                }
                for mt, m in metrics.items()
            },
            "bias_analysis": bias_report,
            "detailed_results": [
                {
                    "filename": r.filename,
                    "match_type": r.match_type,
                    "performance_level": r.performance_level,
                    "view_type": r.view_type,
                    "precision": r.precision,
                    "recall": r.recall,
                    "f1_score": r.f1_score,
                    "avg_confidence": sum(r.confidence_scores) / len(r.confidence_scores) if r.confidence_scores else 0.0
                }
                for r in self.results
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Report saved to {output_path}")
        return report
    
    def print_summary(self, metrics: Dict[str, MatchTypeMetrics]):
        """Print evaluation summary to console."""
        logger.info("\n📊 Match-Type-Aware Evaluation Summary")
        logger.info("=" * 50)
        
        for match_type, metric in metrics.items():
            logger.info(f"\n🎯 {match_type.upper()} MATCHES ({metric.total_images} images):")
            logger.info(f"  Precision: {metric.avg_precision:.3f}")
            logger.info(f"  Recall:    {metric.avg_recall:.3f}")
            logger.info(f"  F1 Score:  {metric.avg_f1:.3f}")
            logger.info(f"  Avg Conf:  {metric.avg_confidence:.3f}")
        
        # Overall performance
        all_f1_scores = [m.avg_f1 for m in metrics.values()]
        if all_f1_scores:
            overall_f1 = sum(all_f1_scores) / len(all_f1_scores)
            f1_std = pd.Series(all_f1_scores).std()
            
            logger.info(f"\n📈 OVERALL PERFORMANCE:")
            logger.info(f"  Average F1: {overall_f1:.3f}")
            logger.info(f"  F1 Std Dev: {f1_std:.3f}")
            
            if f1_std > 0.05:
                logger.warning("⚠️  High variance between match types detected!")
            else:
                logger.info("✅ Consistent performance across match types")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Match-Type-Aware YOLO Model Evaluator"
    )
    parser.add_argument(
        "--model", 
        required=True,
        help="Path to trained YOLO model (.pt file)"
    )
    parser.add_argument(
        "--test_dir",
        help="Path to test images directory"
    )
    parser.add_argument(
        "--labels_dir", 
        help="Path to test labels directory"
    )
    parser.add_argument(
        "--manifest",
        help="Path to dataset manifest (JSON or CSV)"
    )
    parser.add_argument(
        "--output",
        default="match_type_evaluation_report.json",
        help="Output report file path"
    )
    parser.add_argument(
        "--bias_threshold",
        type=float,
        default=0.05,
        help="Threshold for bias detection (default: 0.05)"
    )
    
    args = parser.parse_args()
    
    # Initialize evaluator
    evaluator = MatchTypeAwareEvaluator(args.model, args.manifest)
    
    # Determine test directories
    if args.test_dir:
        test_images_dir = Path(args.test_dir)
        test_labels_dir = Path(args.labels_dir) if args.labels_dir else test_images_dir.parent.parent / "labels" / "test"
    else:
        # Default to standard YOLO structure
        base_dir = Path(__file__).parent
        test_images_dir = base_dir / "images" / "test"
        test_labels_dir = base_dir / "labels" / "test"
    
    # Run evaluation
    logger.info("🚀 Starting match-type-aware evaluation...")
    results = evaluator.evaluate_test_set(test_images_dir, test_labels_dir)
    
    if not results:
        logger.error("❌ No evaluation results generated!")
        return 1
    
    # Analyze and report
    metrics = evaluator.analyze_by_match_type()
    evaluator.print_summary(metrics)
    
    # Generate detailed report
    report = evaluator.generate_report(args.output)
    
    # Check for bias
    bias_report = evaluator.detect_bias(metrics, args.bias_threshold)
    
    if bias_report["performance_gaps"] or bias_report["confidence_gaps"]:
        logger.warning("\n⚠️  BIAS DETECTED:")
        for gap in bias_report["performance_gaps"]:
            logger.warning(f"  📉 {gap}")
        for gap in bias_report["confidence_gaps"]:
            logger.warning(f"  📊 {gap}")
        
        logger.info("\n💡 Recommendations:")
        for rec in bias_report["recommendations"]:
            logger.info(f"  • {rec}")
    else:
        logger.info("\n✅ No significant bias detected between match types!")
    
    logger.info(f"\n🎉 Evaluation complete! Report saved to {args.output}")
    return 0


if __name__ == "__main__":
    exit(main()) 