#!/usr/bin/env python3
"""
Hero Coaching Coverage Verification Script
==========================================

Standalone script to verify that every hero in heroes_cleaned.json has coaching 
coverage and generate a detailed coverage report.

This script can be run independently of the test suite for quick coverage checks
and continuous integration validation.

Usage:
    python scripts/verify_coaching_coverage.py [--verbose] [--json-output]
    
Options:
    --verbose       Show detailed per-hero information  
    --json-output   Output report in JSON format
    --heroes-file   Path to heroes JSON file (default: data/heroes_cleaned.json)
    
Exit Codes:
    0: All heroes have coverage
    1: Some heroes missing coverage  
    2: Critical system error
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import statistics

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from coach import _discover_rules, generate_feedback, _rule_modules
    COACH_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error: Could not import coaching system: {e}")
    sys.exit(2)


def load_heroes_data(heroes_file: Path) -> List[Dict[str, Any]]:
    """Load and validate heroes data."""
    if not heroes_file.exists():
        print(f"❌ Error: Heroes file not found: {heroes_file}")
        sys.exit(2)
    
    try:
        with open(heroes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both metadata wrapper and flat array formats
        if isinstance(data, dict) and "heroes" in data:
            return data["heroes"]
        elif isinstance(data, list):
            return data
        else:
            print(f"❌ Error: Unexpected heroes data format: {type(data)}")
            sys.exit(2)
            
    except Exception as e:
        print(f"❌ Error loading heroes data: {e}")
        sys.exit(2)


def verify_coverage(heroes_data: List[Dict[str, Any]], verbose: bool = False) -> Dict[str, Any]:
    """Verify coaching coverage for all heroes."""
    
    # Initialize coaching system
    _rule_modules.clear()
    _discover_rules()
    
    print(f"🔍 Initializing coaching system...")
    print(f"   Loaded {len(_rule_modules)} rule modules")
    print(f"   Testing {len(heroes_data)} heroes...")
    print()
    
    # Sample match data for testing
    sample_match_data = {
        'kills': 5,
        'deaths': 2, 
        'assists': 8,
        'gold_per_min': 650,
        'hero_damage': 50000,
        'damage_taken': 15000,
        'teamfight_participation': 70,
        'match_duration': 18,
        'positioning_rating': 'good',
        'ult_usage': 'average'
    }
    
    # Track results
    results = {
        'total_heroes': len(heroes_data),
        'heroes_with_specific_rules': 0,
        'heroes_with_fallback_only': 0, 
        'heroes_with_no_feedback': 0,
        'missing_heroes': [],
        'specific_heroes': [],
        'response_times': [],
        'rule_modules_found': len(_rule_modules),
        'errors': []
    }
    
    # Test each hero
    for i, hero in enumerate(heroes_data):
        hero_name = hero.get('name', '').strip()
        hero_slug = hero.get('slug', hero_name.lower())
        hero_role = hero.get('role', '').strip()
        
        if not hero_name:
            continue
            
        # Prepare test data
        test_data = {**sample_match_data, 'hero': hero_slug, 'role': hero_role}
        
        # Measure response time
        start_time = time.time()
        
        try:
            feedback = generate_feedback(test_data, include_severity=False)
            response_time_ms = (time.time() - start_time) * 1000
            results['response_times'].append(response_time_ms)
            
            # Check coverage type
            if feedback and len(feedback) > 0:
                hero_slug_lower = hero_slug.lower()
                if hero_slug_lower in _rule_modules:
                    results['heroes_with_specific_rules'] += 1
                    results['specific_heroes'].append(hero_name)
                    if verbose:
                        print(f"   ✅ {hero_name:20} ({hero_role:10}) - Specific rule ({len(feedback)} items)")
                else:
                    results['heroes_with_fallback_only'] += 1
                    if verbose:
                        print(f"   🔄 {hero_name:20} ({hero_role:10}) - Fallback rule ({len(feedback)} items)")
            else:
                results['heroes_with_no_feedback'] += 1
                results['missing_heroes'].append(hero_name)
                if verbose:
                    print(f"   ❌ {hero_name:20} ({hero_role:10}) - No feedback")
                    
        except Exception as e:
            results['heroes_with_no_feedback'] += 1
            results['missing_heroes'].append(hero_name)
            results['errors'].append(f"{hero_name}: {str(e)}")
            results['response_times'].append(1000)  # Penalty time
            if verbose:
                print(f"   💥 {hero_name:20} ({hero_role:10}) - Error: {e}")
        
        # Progress indicator for large datasets
        if not verbose and (i + 1) % 25 == 0:
            print(f"   📊 Progress: {i+1}/{len(heroes_data)} heroes tested")
    
    # Calculate performance metrics
    if results['response_times']:
        results['avg_response_time_ms'] = statistics.mean(results['response_times'])
        results['min_response_time_ms'] = min(results['response_times'])
        results['max_response_time_ms'] = max(results['response_times'])
        results['median_response_time_ms'] = statistics.median(results['response_times'])
    else:
        results['avg_response_time_ms'] = 0
        results['min_response_time_ms'] = 0
        results['max_response_time_ms'] = 0
        results['median_response_time_ms'] = 0
    
    # Calculate coverage percentages
    results['specific_coverage_pct'] = (results['heroes_with_specific_rules'] / results['total_heroes']) * 100
    results['total_coverage_pct'] = ((results['heroes_with_specific_rules'] + results['heroes_with_fallback_only']) / results['total_heroes']) * 100
    
    return results


def print_coverage_report(results: Dict[str, Any]):
    """Print a detailed coverage report."""
    print("\n" + "="*60)
    print("📊 HERO COACHING COVERAGE REPORT")
    print("="*60)
    print(f"📈 Total Heroes: {results['total_heroes']}")
    print(f"🎯 Heroes with Specific Rules: {results['heroes_with_specific_rules']} ({results['specific_coverage_pct']:.1f}%)")
    print(f"🔄 Heroes with Fallback Only: {results['heroes_with_fallback_only']}")
    print(f"❌ Heroes with No Feedback: {results['heroes_with_no_feedback']}")
    print(f"✅ Total Coverage: {results['total_coverage_pct']:.1f}%")
    print()
    
    print("⚡ Performance Metrics:")
    print(f"   Average Response Time: {results['avg_response_time_ms']:.1f}ms")
    print(f"   Min/Max/Median: {results['min_response_time_ms']:.1f}ms / {results['max_response_time_ms']:.1f}ms / {results['median_response_time_ms']:.1f}ms")
    print()
    
    print(f"🔧 Rule Modules Found: {results['rule_modules_found']}")
    
    if results['specific_heroes']:
        print(f"\n🎯 Heroes with Specific Rules ({len(results['specific_heroes'])}):")
        for hero in sorted(results['specific_heroes'])[:20]:
            print(f"   • {hero}")
        if len(results['specific_heroes']) > 20:
            print(f"   ... and {len(results['specific_heroes']) - 20} more")
    
    if results['missing_heroes']:
        print(f"\n⚠️  Heroes Missing Coverage ({len(results['missing_heroes'])}):")
        for hero in results['missing_heroes'][:10]:
            print(f"   • {hero}")
        if len(results['missing_heroes']) > 10:
            print(f"   ... and {len(results['missing_heroes']) - 10} more")
    
    if results['errors']:
        print(f"\n💥 Errors Encountered ({len(results['errors'])}):")
        for error in results['errors'][:5]:
            print(f"   • {error}")
        if len(results['errors']) > 5:
            print(f"   ... and {len(results['errors']) - 5} more")
    
    print("="*60)
    
    # Final verdict
    if results['heroes_with_no_feedback'] == 0:
        print("✅ SUCCESS: All heroes have coaching coverage!")
        if results['total_coverage_pct'] >= 100.0:
            print("🎉 PERFECT: 100% coverage achieved!")
    else:
        print(f"❌ FAILURE: {results['heroes_with_no_feedback']} heroes lack coaching coverage")
        print("⚠️  Action required: Add missing hero rules or fix errors")


def main():
    """Main script entry point."""
    parser = argparse.ArgumentParser(description='Verify hero coaching coverage')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed per-hero information')
    parser.add_argument('--json-output', '-j', action='store_true', help='Output report in JSON format')
    parser.add_argument('--heroes-file', '-f', type=Path, default='data/heroes_cleaned.json', help='Path to heroes JSON file')
    
    args = parser.parse_args()
    
    # Resolve heroes file path
    heroes_file = project_root / args.heroes_file
    
    if not args.json_output:
        print("🔍 Hero Coaching Coverage Verification")
        print(f"📁 Heroes file: {heroes_file}")
        print()
    
    # Load heroes data
    heroes_data = load_heroes_data(heroes_file)
    
    # Verify coverage
    results = verify_coverage(heroes_data, verbose=args.verbose)
    
    # Output results
    if args.json_output:
        # JSON output for CI/CD integration
        json_results = {k: v for k, v in results.items() if k != 'response_times'}  # Exclude large arrays
        print(json.dumps(json_results, indent=2))
    else:
        # Human-readable report
        print_coverage_report(results)
    
    # Exit with appropriate code
    if results['heroes_with_no_feedback'] == 0:
        print("\n🎉 All checks passed!") if not args.json_output else None
        sys.exit(0)
    else:
        print("\n💥 Coverage check failed!") if not args.json_output else None
        sys.exit(1)


if __name__ == "__main__":
    main()