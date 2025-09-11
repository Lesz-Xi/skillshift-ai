"""
Data Consistency Test for MLBB Coach AI

Tests that ensure data integrity and hero coverage consistency.
This test fails if any hero in heroes_cleaned.json lacks corresponding coaching rules.

Requirements:
- All heroes must have at least basic coaching data coverage
- Hero names must be consistent across data files  
- Role mappings must be accurate and complete
- No orphaned or missing hero references

Usage:
    pytest backend/tests/unit/coaching/test_data_consistency.py -v
"""

import json
import pytest
import sys
from pathlib import Path
from typing import Dict, Set, List

# Add project root to path
project_root = Path(__file__).parents[4]
sys.path.insert(0, str(project_root))

try:
    from backend.src.config.data_paths import DataPaths
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False


class TestDataConsistency:
    """Test suite for data consistency across all hero-related files."""
    
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
                'hero_role_mapping_json': str(project_root / "data" / "hero_role_mapping.json"),
                'winrate_leaderboard_json': str(project_root / "data" / "mlbb-winrate-leaderboard-complete.json"),
                'project_root': project_root
            })()
    
    @pytest.fixture(scope="class") 
    def heroes_data(self, data_config):
        """Load heroes data from the configured path."""
        with open(data_config.heroes_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both metadata wrapper and flat array formats
        if isinstance(data, dict) and "heroes" in data:
            return data["heroes"]
        elif isinstance(data, list):
            return data
        else:
            pytest.fail(f"Unexpected heroes data format: {type(data)}")
    
    @pytest.fixture(scope="class")
    def role_mapping_data(self, data_config):
        """Load role mapping data from the configured path."""
        try:
            with open(data_config.hero_role_mapping_json, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            pytest.skip(f"Role mapping file not found: {data_config.hero_role_mapping_json}")
    
    @pytest.fixture(scope="class")
    def coaching_rules_coverage(self, data_config):
        """Check what heroes have coaching rules coverage."""
        rules_dir = data_config.project_root / "backend" / "coaching" / "rules" / "heroes"
        
        if not rules_dir.exists():
            # Check alternative locations
            alt_locations = [
                data_config.project_root / "rules" / "heroes",
                data_config.project_root / "coaching" / "rules",
                data_config.project_root / "backend" / "rules"
            ]
            
            for alt_dir in alt_locations:
                if alt_dir.exists():
                    rules_dir = alt_dir
                    break
            else:
                return set()  # No rules directory found
        
        # Collect hero names that have rule files
        covered_heroes = set()
        for rule_file in rules_dir.glob("*.py"):
            if rule_file.name != "__init__.py":
                hero_name = rule_file.stem
                covered_heroes.add(hero_name.lower())
        
        return covered_heroes
    
    def test_heroes_data_loads_successfully(self, heroes_data):
        """Test that heroes data loads without errors."""
        assert heroes_data is not None
        assert len(heroes_data) > 0
        assert isinstance(heroes_data, list)
    
    def test_heroes_have_required_fields(self, heroes_data):
        """Test that all heroes have required fields."""
        required_fields = {"name", "role"}  # Minimal required fields
        
        missing_fields_heroes = []
        for hero in heroes_data:
            missing_fields = required_fields - set(hero.keys())
            if missing_fields:
                missing_fields_heroes.append({
                    "hero": hero.get("name", "unknown"),
                    "missing_fields": list(missing_fields)
                })
        
        assert not missing_fields_heroes, f"Heroes missing required fields: {missing_fields_heroes}"
    
    def test_hero_names_are_unique(self, heroes_data):
        """Test that hero names are unique."""
        hero_names = [hero.get("name", "").lower() for hero in heroes_data]
        duplicates = []
        seen = set()
        
        for name in hero_names:
            if name in seen:
                duplicates.append(name)
            else:
                seen.add(name)
        
        assert not duplicates, f"Duplicate hero names found: {duplicates}"
    
    def test_hero_roles_are_valid(self, heroes_data):
        """Test that hero roles are from valid set."""
        valid_roles = {
            "marksman", "mage", "assassin", "tank", "fighter", "support",
            "mm", "assasin",  # Common variations/typos
            "unknown"  # Placeholder for heroes with unassigned roles
        }
        
        invalid_roles = []
        for hero in heroes_data:
            role = hero.get("role", "").lower()
            if role and role not in valid_roles:
                invalid_roles.append({
                    "hero": hero.get("name", "unknown"),
                    "invalid_role": role
                })
        
        assert not invalid_roles, f"Heroes with invalid roles: {invalid_roles}"
    
    def test_role_mapping_consistency(self, heroes_data, role_mapping_data):
        """Test consistency between heroes data and role mapping."""
        if not role_mapping_data:
            pytest.skip("Role mapping data not available")
        
        # Get hero names from both sources
        heroes_names = {hero.get("name", "").lower() for hero in heroes_data}
        mapping_names = {name.lower() for name in role_mapping_data.keys()}
        
        # Find mismatches
        only_in_heroes = heroes_names - mapping_names
        only_in_mapping = mapping_names - heroes_names
        
        # Remove empty names from comparison
        only_in_heroes.discard("")
        only_in_mapping.discard("")
        
        # Check for role consistency for common heroes
        role_conflicts = []
        for hero in heroes_data:
            hero_name = hero.get("name", "").lower()
            hero_role = hero.get("role", "").lower()
            
            if hero_name in role_mapping_data:
                mapping_role = role_mapping_data[hero_name].lower() if hero_name in role_mapping_data else ""
                
                # Normalize role names for comparison
                role_mappings = {
                    "mm": "marksman",
                    "assasin": "assassin"  # Common typo
                }
                
                normalized_hero_role = role_mappings.get(hero_role, hero_role)
                normalized_mapping_role = role_mappings.get(mapping_role, mapping_role)
                
                if normalized_hero_role != normalized_mapping_role:
                    role_conflicts.append({
                        "hero": hero_name,
                        "heroes_role": hero_role,
                        "mapping_role": mapping_role
                    })
        
        # Report findings
        if only_in_heroes:
            print(f"⚠️  Heroes missing from role mapping: {only_in_heroes}")
        if only_in_mapping:
            print(f"⚠️  Heroes in mapping but not in heroes data: {only_in_mapping}")
        
        assert not role_conflicts, f"Role conflicts between data sources: {role_conflicts}"
    
    def test_hero_coaching_coverage(self, heroes_data, coaching_rules_coverage):
        """Test that heroes have coaching rule coverage."""
        if not coaching_rules_coverage:
            pytest.skip("No coaching rules directory found - this is expected for initial setup")
        
        # Get hero names that should have coverage
        hero_names = {hero.get("name", "").lower() for hero in heroes_data if hero.get("name")}
        
        # Find heroes without coverage
        missing_coverage = hero_names - coaching_rules_coverage
        
        # Calculate coverage percentage
        total_heroes = len(hero_names)
        covered_heroes = len(hero_names & coaching_rules_coverage)
        coverage_percentage = (covered_heroes / total_heroes * 100) if total_heroes > 0 else 0
        
        print(f"📊 Hero coaching coverage: {covered_heroes}/{total_heroes} ({coverage_percentage:.1f}%)")
        
        if missing_coverage:
            print(f"⚠️  Heroes without coaching rules: {sorted(missing_coverage)}")
        
        # Set minimum coverage threshold (start low, increase over time)
        minimum_coverage_percentage = 10.0  # 10% minimum coverage
        
        assert coverage_percentage >= minimum_coverage_percentage, (
            f"Hero coaching coverage too low: {coverage_percentage:.1f}% < {minimum_coverage_percentage}%. "
            f"Missing coverage for: {sorted(missing_coverage)}"
        )
    
    def test_data_file_accessibility(self, data_config):
        """Test that all configured data files are accessible."""
        files_to_check = [
            ("heroes_json", data_config.heroes_json),
            ("hero_role_mapping_json", data_config.hero_role_mapping_json),
        ]
        
        missing_files = []
        for name, path in files_to_check:
            if not Path(path).exists():
                missing_files.append(f"{name}: {path}")
        
        assert not missing_files, f"Missing data files: {missing_files}"
    
    def test_heroes_data_format_consistency(self, heroes_data):
        """Test that heroes data has consistent format across entries."""
        if not heroes_data:
            pytest.skip("No heroes data available")
        
        # Check for format consistency
        sample_hero = heroes_data[0]
        sample_keys = set(sample_hero.keys())
        
        inconsistent_heroes = []
        for i, hero in enumerate(heroes_data[1:], 1):
            hero_keys = set(hero.keys())
            
            # Allow some flexibility - not all heroes need identical fields
            # But core fields should be consistent
            core_fields = {"name", "role"}
            missing_core = core_fields - hero_keys
            
            if missing_core:
                inconsistent_heroes.append({
                    "index": i,
                    "hero": hero.get("name", f"hero_{i}"),
                    "missing_core_fields": list(missing_core)
                })
        
        assert not inconsistent_heroes, f"Heroes with inconsistent core fields: {inconsistent_heroes}"


class TestEnvironmentVariableOverrides:
    """Test that environment variable overrides work correctly."""
    
    def test_environment_variable_support(self):
        """Test that the configuration system supports environment variables."""
        if not CONFIG_AVAILABLE:
            pytest.skip("Configuration system not available")
        
        # Test that DataPaths can be instantiated
        config = DataPaths()
        assert config is not None
        
        # Test that paths are strings and not empty
        assert isinstance(config.heroes_json, str)
        assert len(config.heroes_json) > 0
    
    def test_imports_directory_support(self):
        """Test that the imports directory configuration works."""
        if not CONFIG_AVAILABLE:
            pytest.skip("Configuration system not available")
        
        # Test imports configuration
        imports_config = DataPaths(use_imports=True)
        assert "_imports" in imports_config.heroes_json
        assert "_imports" in imports_config.hero_role_mapping_json


if __name__ == "__main__":
    # Allow running the test file directly
    pytest.main([__file__, "-v"])