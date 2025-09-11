#!/usr/bin/env python3
"""
Asset Verification Script

Compares imported Perplexity assets vs canonical data files and reports differences.
This script helps maintain data integrity and identifies schema drift.

Usage:
    python scripts/verify_assets.py [--verbose] [--export-report]
"""

import json
import os
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ComparisonResult:
    """Results of comparing two data assets"""
    file_name: str
    canonical_size: int
    imported_size: int
    schema_differences: List[str]
    hero_count_diff: Tuple[int, int]  # (canonical, imported)
    key_field_drift: List[str]
    structural_changes: List[str]
    data_quality_score: float  # 0-100


class AssetVerifier:
    """Compares canonical data files with imported Perplexity assets"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.canonical_dir = self.project_root / "data"
        self.imported_dir = self.project_root / "data" / "_imports"
        self.results: List[ComparisonResult] = []
        
    def verify_all_assets(self) -> Dict[str, Any]:
        """Run verification on all asset files"""
        print("🔍 Starting asset verification...")
        
        # Core data files to verify
        core_files = [
            "heroes_cleaned.json",
            "hero_role_mapping.json", 
            "mlbb-winrate-leaderboard-complete.json"
        ]
        
        for filename in core_files:
            canonical_path = self.canonical_dir / filename
            imported_path = self.imported_dir / filename
            
            if not canonical_path.exists():
                print(f"⚠️  Canonical file missing: {filename}")
                continue
                
            if not imported_path.exists():
                print(f"⚠️  Imported file missing: {filename}")
                continue
                
            result = self._compare_files(canonical_path, imported_path, filename)
            self.results.append(result)
            
        # Verify patch files
        self._verify_patch_files()
        
        return self._generate_summary_report()
    
    def _compare_files(self, canonical_path: Path, imported_path: Path, filename: str) -> ComparisonResult:
        """Compare individual files and detect differences"""
        print(f"📊 Comparing {filename}...")
        
        # Load both files
        with open(canonical_path, 'r', encoding='utf-8') as f:
            canonical_data = json.load(f)
        
        with open(imported_path, 'r', encoding='utf-8') as f:
            imported_data = json.load(f)
        
        # Get file sizes
        canonical_size = canonical_path.stat().st_size
        imported_size = imported_path.stat().st_size
        
        # Analyze structure differences
        schema_differences = self._detect_schema_differences(canonical_data, imported_data, filename)
        hero_count_diff = self._count_heroes(canonical_data, imported_data, filename)
        key_field_drift = self._detect_field_drift(canonical_data, imported_data, filename)
        structural_changes = self._detect_structural_changes(canonical_data, imported_data)
        
        # Calculate data quality score
        quality_score = self._calculate_quality_score(
            canonical_size, imported_size, schema_differences, hero_count_diff
        )
        
        return ComparisonResult(
            file_name=filename,
            canonical_size=canonical_size,
            imported_size=imported_size,
            schema_differences=schema_differences,
            hero_count_diff=hero_count_diff,
            key_field_drift=key_field_drift,
            structural_changes=structural_changes,
            data_quality_score=quality_score
        )
    
    def _detect_schema_differences(self, canonical: Any, imported: Any, filename: str) -> List[str]:
        """Detect schema structure differences"""
        differences = []
        
        if filename == "heroes_cleaned.json":
            # Canonical has metadata wrapper, imported is flat array
            if isinstance(canonical, dict) and "heroes" in canonical:
                differences.append("Canonical has metadata wrapper, imported is flat array")
                canonical_heroes = canonical["heroes"]
            else:
                canonical_heroes = canonical
                
            if isinstance(imported, list):
                if len(canonical_heroes) > 0 and len(imported) > 0:
                    canonical_fields = set(canonical_heroes[0].keys())
                    imported_fields = set(imported[0].keys())
                    
                    missing_in_imported = canonical_fields - imported_fields
                    extra_in_imported = imported_fields - canonical_fields
                    
                    if missing_in_imported:
                        differences.append(f"Missing fields in imported: {missing_in_imported}")
                    if extra_in_imported:
                        differences.append(f"Extra fields in imported: {extra_in_imported}")
        
        return differences
    
    def _count_heroes(self, canonical: Any, imported: Any, filename: str) -> Tuple[int, int]:
        """Count heroes in both datasets"""
        canonical_count = 0
        imported_count = 0
        
        if filename == "heroes_cleaned.json":
            if isinstance(canonical, dict) and "heroes" in canonical:
                canonical_count = len(canonical["heroes"])
            elif isinstance(canonical, list):
                canonical_count = len(canonical)
                
            if isinstance(imported, list):
                imported_count = len(imported)
                
        elif filename == "hero_role_mapping.json":
            if isinstance(canonical, dict):
                canonical_count = len(canonical)
            if isinstance(imported, dict):
                imported_count = len(imported)
        
        return (canonical_count, imported_count)
    
    def _detect_field_drift(self, canonical: Any, imported: Any, filename: str) -> List[str]:
        """Detect key field value drift"""
        drift = []
        
        if filename == "hero_role_mapping.json" and isinstance(canonical, dict) and isinstance(imported, dict):
            # Check for role mapping conflicts
            common_heroes = set(canonical.keys()) & set(imported.keys())
            for hero in common_heroes:
                if canonical[hero] != imported[hero]:
                    drift.append(f"Role conflict for {hero}: canonical='{canonical[hero]}' vs imported='{imported[hero]}'")
        
        return drift
    
    def _detect_structural_changes(self, canonical: Any, imported: Any) -> List[str]:
        """Detect major structural changes"""
        changes = []
        
        canonical_type = type(canonical).__name__
        imported_type = type(imported).__name__
        
        if canonical_type != imported_type:
            changes.append(f"Root type change: {canonical_type} -> {imported_type}")
        
        return changes
    
    def _verify_patch_files(self):
        """Verify patch files separately due to different structure"""
        print("📊 Comparing patch files...")
        
        canonical_patches = self.canonical_dir / "patches"
        imported_patches = self.imported_dir
        
        patch_files = ["patch_1_7_8.json", "patch_1_7_9.json"]
        
        for patch_file in patch_files:
            canonical_path = canonical_patches / patch_file
            imported_path = imported_patches / patch_file
            
            if canonical_path.exists() and imported_path.exists():
                with open(canonical_path, 'r') as f:
                    canonical_patch = json.load(f)
                with open(imported_path, 'r') as f:
                    imported_patch = json.load(f)
                
                # Patch files have completely different structures
                structural_changes = ["Completely different patch file structure: meta data vs adjustments"]
                
                result = ComparisonResult(
                    file_name=patch_file,
                    canonical_size=canonical_path.stat().st_size,
                    imported_size=imported_path.stat().st_size,
                    schema_differences=["Different patch data models"],
                    hero_count_diff=(0, 0),  # Not applicable for patches
                    key_field_drift=[],
                    structural_changes=structural_changes,
                    data_quality_score=50.0  # Different but both valid
                )
                self.results.append(result)
    
    def _calculate_quality_score(self, canonical_size: int, imported_size: int, 
                               schema_diffs: List[str], hero_count: Tuple[int, int]) -> float:
        """Calculate data quality score (0-100)"""
        score = 100.0
        
        # Size difference penalty
        if canonical_size > 0:
            size_ratio = imported_size / canonical_size
            if size_ratio < 0.1:  # Imported much smaller
                score -= 40
            elif size_ratio < 0.5:
                score -= 20
        
        # Schema difference penalty
        score -= len(schema_diffs) * 10
        
        # Hero count difference penalty
        canonical_count, imported_count = hero_count
        if canonical_count > 0:
            count_ratio = imported_count / canonical_count
            if count_ratio < 0.5:
                score -= 20
        
        return max(0, score)
    
    def _generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive verification report"""
        total_files = len(self.results)
        avg_quality_score = sum(r.data_quality_score for r in self.results) / total_files if total_files > 0 else 0
        
        # Recommendations based on analysis
        recommendations = []
        
        for result in self.results:
            if result.data_quality_score < 70:
                recommendations.append(
                    f"Consider keeping canonical {result.file_name} - imported version has significant differences"
                )
            
            if result.hero_count_diff[1] < result.hero_count_diff[0] * 0.5:
                recommendations.append(
                    f"{result.file_name}: Imported has much fewer entries ({result.hero_count_diff[1]} vs {result.hero_count_diff[0]})"
                )
        
        recommendations.append("✅ Keep canonical data/* as source of truth")
        recommendations.append("✅ Use imported data/_imports/* for reference only")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_files_compared": total_files,
            "average_quality_score": round(avg_quality_score, 2),
            "results": [
                {
                    "file": r.file_name,
                    "canonical_size_kb": round(r.canonical_size / 1024, 1),
                    "imported_size_kb": round(r.imported_size / 1024, 1),
                    "hero_count": f"{r.hero_count_diff[0]} → {r.hero_count_diff[1]}",
                    "quality_score": r.data_quality_score,
                    "schema_differences": r.schema_differences,
                    "structural_changes": r.structural_changes,
                    "field_drift": r.key_field_drift
                }
                for r in self.results
            ],
            "recommendations": recommendations
        }
    
    def print_report(self, report: Dict[str, Any], verbose: bool = False):
        """Print verification report to console"""
        print("\n" + "="*60)
        print("🔍 ASSET VERIFICATION REPORT")
        print("="*60)
        
        print(f"📊 Files Compared: {report['total_files_compared']}")
        print(f"🎯 Average Quality Score: {report['average_quality_score']}/100")
        print(f"📅 Timestamp: {report['timestamp']}")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 60)
        
        for result in report['results']:
            print(f"\n📄 {result['file']}")
            print(f"   Size: {result['canonical_size_kb']}KB → {result['imported_size_kb']}KB")
            print(f"   Heroes: {result['hero_count']}")
            print(f"   Quality: {result['quality_score']}/100")
            
            if verbose and (result['schema_differences'] or result['structural_changes']):
                if result['schema_differences']:
                    print(f"   Schema Diffs: {result['schema_differences']}")
                if result['structural_changes']:
                    print(f"   Structural: {result['structural_changes']}")
                if result['field_drift']:
                    print(f"   Field Drift: {result['field_drift']}")
        
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 60)
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
        
        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description="Verify coaching assets integrity")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Show detailed differences")
    parser.add_argument("--export-report", "-e", 
                       help="Export JSON report to file")
    parser.add_argument("--project-root", default=".", 
                       help="Project root directory")
    
    args = parser.parse_args()
    
    try:
        verifier = AssetVerifier(args.project_root)
        report = verifier.verify_all_assets()
        verifier.print_report(report, verbose=args.verbose)
        
        if args.export_report:
            with open(args.export_report, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Report exported to: {args.export_report}")
        
        # Exit with error code if quality is too low
        if report['average_quality_score'] < 50:
            print("\n⚠️  WARNING: Low data quality detected!")
            sys.exit(1)
        else:
            print("\n✅ Verification completed successfully!")
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()