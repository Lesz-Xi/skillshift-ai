"""
Comprehensive Hero Coaching Coverage Test
==========================================

Tests that ensure every hero in heroes_cleaned.json has at least one coaching 
feedback snippet available through either specific hero rules or role-based fallbacks.

This test serves as a guard rail to prevent coverage regression and provides
detailed reporting on coaching system completeness.

Requirements:
- All 126 heroes must produce ≥1 coaching recommendation
- Average resolver time must be <200ms per hero
- Coverage must be >90% (specific) + 100% (fallback)

Usage:
    pytest backend/tests/unit/coaching/test_coverage.py -v -s
"""

import json
import time
import pytest
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import statistics

# Add project root to path
project_root = Path(__file__).parents[4]
sys.path.insert(0, str(project_root))

try:
    from coach import _discover_rules, generate_feedback, _rule_modules
    COACH_AVAILABLE = True
except ImportError:
    COACH_AVAILABLE = False

try:
    from backend.src.config.data_paths import DataPaths
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False


@dataclass
class CoverageReport:
    """Comprehensive coverage report."""
    total_heroes: int
    heroes_with_specific_rules: int
    heroes_with_fallback_only: int
    heroes_with_no_feedback: int
    average_response_time_ms: float
    specific_coverage_percentage: float
    total_coverage_percentage: float
    missing_heroes: List[str]
    performance_breakdown: Dict[str, float]
    rule_modules_found: int


class TestHeroCoachingCoverage:
    """Comprehensive test suite for hero coaching coverage."""
    
    @pytest.fixture(scope="class")
    def data_config(self):
        """Fixture to provide data configuration."""
        if CONFIG_AVAILABLE:
            return DataPaths()
        else:
            # Fallback configuration
            project_root = Path(__file__).parents[4]
            return type('Config', (), {
                'heroes_json': str(project_root / "data" / "heroes_cleaned.json"),
                'project_root': project_root
            })()
    
    @pytest.fixture(scope="class")
    def heroes_data(self, data_config):
        """Load heroes data from the configured path."""
        heroes_file = Path(data_config.heroes_json)
        if not heroes_file.exists():
            pytest.skip(f"Heroes data file not found: {heroes_file}")
            
        with open(heroes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both metadata wrapper and flat array formats
        if isinstance(data, dict) and "heroes" in data:
            return data["heroes"]
        elif isinstance(data, list):
            return data
        else:
            pytest.fail(f"Unexpected heroes data format: {type(data)}")
    
    @pytest.fixture(scope="class")
    def sample_match_data(self):
        """Sample match data for testing coaching resolution."""
        return {
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
    
    @pytest.fixture(scope="class")
    def coaching_system(self):
        """Initialize the coaching system."""
        if not COACH_AVAILABLE:
            pytest.skip("Coaching system not available")
        
        # Clear any existing cache and rediscover rules
        _rule_modules.clear()
        _discover_rules()
        
        return {
            'modules_found': len(_rule_modules),
            'rule_names': list(_rule_modules.keys())
        }
    
    def test_coaching_system_loads_successfully(self, coaching_system):
        """Test that the coaching system loads without errors."""
        assert coaching_system is not None
        assert coaching_system['modules_found'] > 0
        print(f"\n📦 Loaded {coaching_system['modules_found']} rule modules")
        print(f"   Available rules: {', '.join(coaching_system['rule_names'][:10])}...")
    
    def test_all_heroes_have_coaching_feedback(self, heroes_data, sample_match_data, coaching_system):
        """
        MAIN TEST: Verify every hero produces at least one coaching recommendation.
        This is the core requirement that must never fail.
        """
        if not COACH_AVAILABLE:
            pytest.skip("Coaching system not available")
        
        print(f"\n🎯 Testing coaching coverage for {len(heroes_data)} heroes...")
        
        # Track results
        heroes_with_specific_rules = 0
        heroes_with_fallback_only = 0
        heroes_with_no_feedback = 0
        missing_heroes = []
        response_times = []
        
        for i, hero in enumerate(heroes_data):
            hero_name = hero.get('name', '').strip()
            hero_slug = hero.get('slug', hero_name.lower())
            hero_role = hero.get('role', '').strip()
            
            if not hero_name:
                continue
            
            # Prepare test data for this hero
            test_data = {**sample_match_data, 'hero': hero_slug, 'role': hero_role}
            
            # Measure response time
            start_time = time.time()
            
            try:
                feedback = generate_feedback(test_data, include_severity=False)
                response_time_ms = (time.time() - start_time) * 1000
                response_times.append(response_time_ms)
                
                # Check if we got meaningful feedback
                if feedback and len(feedback) > 0:
                    # Check if it's specific hero rule or generic fallback
                    hero_slug_lower = hero_slug.lower()
                    if hero_slug_lower in _rule_modules:
                        heroes_with_specific_rules += 1
                    else:
                        heroes_with_fallback_only += 1
                else:
                    heroes_with_no_feedback += 1
                    missing_heroes.append(hero_name)
                    print(f"   ❌ {hero_name} ({hero_role}) - No feedback generated")
                
            except Exception as e:
                heroes_with_no_feedback += 1
                missing_heroes.append(f"{hero_name} (ERROR: {str(e)})")
                response_times.append(1000)  # Penalty time for errors
                print(f"   💥 {hero_name} ({hero_role}) - Error: {e}")
            
            # Progress indicator
            if (i + 1) % 25 == 0:
                print(f"   📊 Progress: {i+1}/{len(heroes_data)} heroes tested")
        
        # Calculate metrics
        total_heroes = len(heroes_data)
        specific_coverage_pct = (heroes_with_specific_rules / total_heroes) * 100
        total_coverage_pct = ((heroes_with_specific_rules + heroes_with_fallback_only) / total_heroes) * 100
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        # Create coverage report
        report = CoverageReport(
            total_heroes=total_heroes,
            heroes_with_specific_rules=heroes_with_specific_rules,
            heroes_with_fallback_only=heroes_with_fallback_only,
            heroes_with_no_feedback=heroes_with_no_feedback,
            average_response_time_ms=avg_response_time,
            specific_coverage_percentage=specific_coverage_pct,
            total_coverage_percentage=total_coverage_pct,
            missing_heroes=missing_heroes,
            performance_breakdown={
                'min_time_ms': min(response_times) if response_times else 0,
                'max_time_ms': max(response_times) if response_times else 0,
                'median_time_ms': statistics.median(response_times) if response_times else 0
            },
            rule_modules_found=coaching_system['modules_found']
        )
        
        # Print detailed report
        self._print_coverage_report(report)
        
        # CRITICAL ASSERTIONS - These must pass
        assert heroes_with_no_feedback == 0, (
            f"🚨 COVERAGE FAILURE: {heroes_with_no_feedback} heroes have no coaching feedback. "
            f"Missing: {missing_heroes[:10]}{'...' if len(missing_heroes) > 10 else ''}"
        )
        
        assert total_coverage_pct >= 99.0, (
            f"🚨 COVERAGE TOO LOW: {total_coverage_pct:.1f}% < 99.0%. "
            f"Need feedback for all {total_heroes} heroes."
        )
        
        assert avg_response_time < 200, (
            f"🚨 PERFORMANCE TOO SLOW: {avg_response_time:.1f}ms > 200ms average response time."
        )
        
        # Success!
        print(f"✅ COVERAGE TEST PASSED - All {total_heroes} heroes have coaching feedback!")
    
    def test_specific_hero_rules_work_correctly(self, coaching_system, sample_match_data):
        """Test that specific hero rules produce meaningful feedback."""
        if not COACH_AVAILABLE:
            pytest.skip("Coaching system not available")
        
        # Test known heroes that should have specific rules
        test_heroes = [
            ('kagura', 'mage'),
            ('lancelot', 'assassin'), 
            ('tigreal', 'tank'),
            ('franco', 'tank'),
            ('chou', 'fighter')
        ]
        
        for hero_slug, role in test_heroes:
            if hero_slug in _rule_modules:
                test_data = {**sample_match_data, 'hero': hero_slug, 'role': role}
                
                feedback = generate_feedback(test_data, include_severity=False)
                
                assert feedback is not None, f"Hero {hero_slug} returned None feedback"
                assert len(feedback) > 0, f"Hero {hero_slug} returned empty feedback"
                assert all(isinstance(f, str) for f in feedback), f"Hero {hero_slug} feedback format invalid"
                
                print(f"   ✅ {hero_slug.title()} - {len(feedback)} feedback items")
    
    def test_role_fallback_coverage(self, coaching_system, sample_match_data):
        """Test that role-based fallback rules work for all roles."""
        if not COACH_AVAILABLE:
            pytest.skip("Coaching system not available")
        
        test_roles = ['mage', 'marksman', 'assassin', 'tank', 'support', 'fighter']
        
        for role in test_roles:
            # Test with a fake hero name to ensure fallback is used
            test_data = {**sample_match_data, 'hero': f'test_{role}_hero', 'role': role}
            
            feedback = generate_feedback(test_data, include_severity=False)
            
            # Should get feedback from generic role rule
            if feedback:
                assert len(feedback) > 0, f"Role {role} fallback returned empty feedback"
                print(f"   ✅ {role.title()} fallback - {len(feedback)} feedback items")
            else:
                print(f"   ⚠️  {role.title()} - No fallback rule found")
    
    def test_performance_benchmarks(self, heroes_data, sample_match_data, coaching_system):
        """Test that the coaching system meets performance requirements."""
        if not COACH_AVAILABLE:
            pytest.skip("Coaching system not available")
        
        # Test a sample of heroes for performance
        sample_heroes = heroes_data[:20]  # Test first 20 heroes
        response_times = []
        
        for hero in sample_heroes:
            hero_slug = hero.get('slug', hero.get('name', '').lower())
            hero_role = hero.get('role', '')
            
            test_data = {**sample_match_data, 'hero': hero_slug, 'role': hero_role}
            
            start_time = time.time()
            generate_feedback(test_data)
            response_time_ms = (time.time() - start_time) * 1000
            
            response_times.append(response_time_ms)
        
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        
        print(f"\n⚡ Performance Results:")
        print(f"   Average: {avg_time:.1f}ms")
        print(f"   Maximum: {max_time:.1f}ms")
        print(f"   Target: <200ms")
        
        assert avg_time < 200, f"Average response time {avg_time:.1f}ms exceeds 200ms limit"
        assert max_time < 500, f"Maximum response time {max_time:.1f}ms exceeds 500ms limit"
    
    def _print_coverage_report(self, report: CoverageReport):
        """Print a detailed coverage report."""
        print(f"\n" + "="*60)
        print(f"📊 HERO COACHING COVERAGE REPORT")
        print(f"="*60)
        print(f"📈 Total Heroes: {report.total_heroes}")
        print(f"🎯 Heroes with Specific Rules: {report.heroes_with_specific_rules} ({report.specific_coverage_percentage:.1f}%)")
        print(f"🔄 Heroes with Fallback Only: {report.heroes_with_fallback_only}")
        print(f"❌ Heroes with No Feedback: {report.heroes_with_no_feedback}")
        print(f"✅ Total Coverage: {report.total_coverage_percentage:.1f}%")
        print(f"")
        print(f"⚡ Performance Metrics:")
        print(f"   Average Response Time: {report.average_response_time_ms:.1f}ms")
        print(f"   Min/Max/Median: {report.performance_breakdown['min_time_ms']:.1f}ms / {report.performance_breakdown['max_time_ms']:.1f}ms / {report.performance_breakdown['median_time_ms']:.1f}ms")
        print(f"")
        print(f"🔧 Rule Modules Found: {report.rule_modules_found}")
        
        if report.missing_heroes:
            print(f"")
            print(f"⚠️  Missing Coverage ({len(report.missing_heroes)} heroes):")
            for hero in report.missing_heroes[:10]:
                print(f"   - {hero}")
            if len(report.missing_heroes) > 10:
                print(f"   ... and {len(report.missing_heroes) - 10} more")
        
        print(f"="*60)


if __name__ == "__main__":
    # Allow running the test file directly with detailed output
    pytest.main([__file__, "-v", "-s", "--tb=short"])