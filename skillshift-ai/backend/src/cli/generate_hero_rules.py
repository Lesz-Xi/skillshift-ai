#!/usr/bin/env python3
"""
Hero Rules Generator for MLBB Coach AI

Generates missing hero rule stubs from heroes_cleaned.json to ensure
all heroes have basic coaching coverage.

Usage:
    python -m backend.src.cli.generate_hero_rules --heroes-file data/heroes_cleaned.json --output-dir backend/coaching/rules/heroes --dry-run
    
    # With environment variables:
    HEROES_JSON=data/_imports/heroes_cleaned.json python -m backend.src.cli.generate_hero_rules --output-dir backend/coaching/rules/heroes
"""

import json
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from datetime import datetime

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parents[2]
sys.path.insert(0, str(project_root))

try:
    from src.config.data_paths import get_heroes_json_path
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)


class HeroRulesGenerator:
    """Generates hero rule stubs for missing heroes."""
    
    def __init__(self, heroes_file: str, output_dir: str):
        """Initialize the hero rules generator."""
        self.heroes_file = Path(heroes_file)
        self.output_dir = Path(output_dir)
        self.heroes_data = []
        self.existing_rules = set()
        
    def load_heroes_data(self) -> None:
        """Load heroes data from JSON file."""
        try:
            with open(self.heroes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both metadata wrapper and flat array formats
            if isinstance(data, dict) and "heroes" in data:
                self.heroes_data = data["heroes"]
                logger.info(f"Loaded {len(self.heroes_data)} heroes from wrapped format")
            elif isinstance(data, list):
                self.heroes_data = data
                logger.info(f"Loaded {len(self.heroes_data)} heroes from array format")
            else:
                raise ValueError(f"Unexpected data format: {type(data)}")
                
        except Exception as e:
            logger.error(f"Failed to load heroes data from {self.heroes_file}: {e}")
            raise
    
    def scan_existing_rules(self) -> None:
        """Scan existing hero rule files."""
        if not self.output_dir.exists():
            logger.info(f"Output directory doesn't exist: {self.output_dir}")
            self.existing_rules = set()
            return
        
        for rule_file in self.output_dir.glob("*.py"):
            if rule_file.name != "__init__.py":
                hero_name = rule_file.stem.lower()
                self.existing_rules.add(hero_name)
        
        logger.info(f"Found {len(self.existing_rules)} existing hero rule files")
    
    def generate_rule_stub(self, hero: Dict) -> str:
        """Generate a hero rule stub template."""
        hero_name = hero.get("name", "Unknown")
        hero_slug = hero.get("slug", hero_name.lower().replace(" ", "_"))
        hero_role = hero.get("role", "unknown")
        
        template = f'''"""
Coaching rules for {hero_name}

Auto-generated stub - please customize with specific coaching logic.
Generated on: {datetime.now().isoformat()}
"""

from typing import Dict, List, Any
from ..base_hero_rules import BaseHeroRules


class {hero_name.replace(" ", "").replace("-", "")}Rules(BaseHeroRules):
    """Coaching rules for {hero_name} ({hero_role})."""
    
    def __init__(self):
        super().__init__(
            hero_name="{hero_name}",
            hero_slug="{hero_slug}",
            role="{hero_role}"
        )
    
    def analyze_performance(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze {hero_name} performance and provide coaching feedback."""
        feedback = super().analyze_performance(match_data)
        
        # TODO: Add {hero_name}-specific analysis
        # Example areas to implement:
        # - Role-specific KDA thresholds
        # - Skill usage patterns
        # - Item build recommendations
        # - Positioning advice
        # - Team fight participation
        
        return feedback
    
    def get_skill_tips(self) -> List[str]:
        """Get {hero_name}-specific skill tips."""
        base_tips = super().get_skill_tips()
        
        # TODO: Add {hero_name}-specific skill tips
        hero_specific_tips = [
            "Customize this with {hero_name} skill mechanics",
            "Add combo recommendations",
            "Include skill order suggestions"
        ]
        
        return base_tips + hero_specific_tips
    
    def get_item_recommendations(self, match_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get {hero_name} item build recommendations."""
        # TODO: Implement {hero_name}-specific item builds
        return [
            {{
                "type": "core_items",
                "items": ["Item recommendations for {hero_name}"],
                "reason": "Core build for {hero_role} role"
            }},
            {{
                "type": "situational",
                "items": ["Situational items based on enemy team"],
                "reason": "Adapt to enemy composition"
            }}
        ]
    
    def get_positioning_advice(self, game_phase: str) -> List[str]:
        """Get {hero_name} positioning advice for different game phases."""
        # TODO: Implement {hero_name}-specific positioning
        return [
            f"{{game_phase}} phase positioning for {hero_name}",
            f"Role-specific advice for {hero_role}"
        ]
'''
        return template
    
    def create_base_rules_if_needed(self) -> None:
        """Create base hero rules class if it doesn't exist."""
        base_rules_path = self.output_dir.parent / "base_hero_rules.py"
        
        if base_rules_path.exists():
            return
        
        base_template = '''"""
Base hero rules class for MLBB Coach AI

Provides common functionality that all hero-specific rules inherit from.
"""

from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod


class BaseHeroRules(ABC):
    """Base class for all hero-specific coaching rules."""
    
    def __init__(self, hero_name: str, hero_slug: str, role: str):
        self.hero_name = hero_name
        self.hero_slug = hero_slug
        self.role = role
    
    def analyze_performance(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Base performance analysis that all heroes share."""
        return {
            "hero": self.hero_name,
            "role": self.role,
            "timestamp": match_data.get("timestamp"),
            "basic_analysis": self._basic_analysis(match_data)
        }
    
    def _basic_analysis(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Basic analysis common to all heroes."""
        return {
            "kda_analysis": "Basic KDA evaluation",
            "farm_efficiency": "Basic farming analysis",
            "team_participation": "Basic team fight analysis"
        }
    
    def get_skill_tips(self) -> List[str]:
        """Get general skill tips applicable to all heroes."""
        return [
            "Practice last-hitting for better gold income",
            "Ward key areas for map control",
            "Communicate with your team"
        ]
    
    @abstractmethod
    def get_item_recommendations(self, match_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get hero-specific item recommendations."""
        pass
    
    @abstractmethod
    def get_positioning_advice(self, game_phase: str) -> List[str]:
        """Get hero-specific positioning advice."""
        pass
'''
        
        # Create parent directory if needed
        base_rules_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(base_rules_path, 'w', encoding='utf-8') as f:
            f.write(base_template)
            
        logger.info(f"Created base rules class: {base_rules_path}")
    
    def generate_missing_rules(self, dry_run: bool = False) -> Dict[str, Any]:
        """Generate rule stubs for heroes without existing rules."""
        self.load_heroes_data()
        self.scan_existing_rules()
        
        missing_heroes = []
        generated_files = []
        
        for hero in self.heroes_data:
            hero_name = hero.get("name", "").lower()
            if not hero_name:
                continue
                
            # Normalize hero name for file naming
            file_name = hero_name.replace(" ", "_").replace("-", "_")
            
            if file_name not in self.existing_rules:
                missing_heroes.append(hero)
                
                if not dry_run:
                    # Create output directory if needed
                    self.output_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Create base rules if needed
                    self.create_base_rules_if_needed()
                    
                    # Generate rule file
                    rule_content = self.generate_rule_stub(hero)
                    rule_file_path = self.output_dir / f"{file_name}.py"
                    
                    with open(rule_file_path, 'w', encoding='utf-8') as f:
                        f.write(rule_content)
                    
                    generated_files.append(str(rule_file_path))
                    logger.info(f"Generated rule stub: {rule_file_path}")
        
        # Update __init__.py if we generated any files
        if generated_files and not dry_run:
            self._update_init_file()
        
        coverage_stats = self._calculate_coverage_stats(len(missing_heroes))
        
        return {
            "total_heroes": len(self.heroes_data),
            "existing_rules": len(self.existing_rules),
            "missing_heroes": len(missing_heroes),
            "generated_files": len(generated_files) if not dry_run else 0,
            "coverage_percentage": coverage_stats["coverage_percentage"],
            "new_coverage_percentage": coverage_stats["new_coverage_percentage"],
            "missing_hero_list": [h.get("name", "Unknown") for h in missing_heroes],
            "generated_file_list": generated_files if not dry_run else [],
            "dry_run": dry_run
        }
    
    def _update_init_file(self) -> None:
        """Update __init__.py to include all rule classes."""
        init_file = self.output_dir / "__init__.py"
        
        # Collect all rule files
        rule_files = []
        for rule_file in self.output_dir.glob("*.py"):
            if rule_file.name not in ["__init__.py", "base_hero_rules.py"]:
                rule_files.append(rule_file.stem)
        
        if not rule_files:
            return
        
        init_content = '"""Hero-specific coaching rules."""\n\n'
        
        # Add imports
        for rule_file in sorted(rule_files):
            class_name = rule_file.replace("_", "").title() + "Rules"
            init_content += f"from .{rule_file} import {class_name}\n"
        
        init_content += "\n__all__ = [\n"
        for rule_file in sorted(rule_files):
            class_name = rule_file.replace("_", "").title() + "Rules"
            init_content += f'    "{class_name}",\n'
        init_content += "]\n"
        
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(init_content)
        
        logger.info(f"Updated {init_file} with {len(rule_files)} rule classes")
    
    def _calculate_coverage_stats(self, missing_count: int) -> Dict[str, float]:
        """Calculate coverage statistics."""
        total_heroes = len(self.heroes_data)
        existing_count = len(self.existing_rules)
        
        if total_heroes == 0:
            return {"coverage_percentage": 0.0, "new_coverage_percentage": 0.0}
        
        current_coverage = (existing_count / total_heroes) * 100
        new_coverage = ((existing_count + missing_count) / total_heroes) * 100
        
        return {
            "coverage_percentage": round(current_coverage, 1),
            "new_coverage_percentage": round(new_coverage, 1)
        }


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Generate hero rule stubs for missing heroes")
    
    # Get default heroes file from configuration if available
    default_heroes_file = "data/heroes_cleaned.json"
    if CONFIG_AVAILABLE:
        try:
            default_heroes_file = get_heroes_json_path()
        except Exception:
            pass
    
    parser.add_argument(
        "--heroes-file",
        default=default_heroes_file,
        help="Path to heroes_cleaned.json file"
    )
    parser.add_argument(
        "--output-dir", 
        default="backend/coaching/rules/heroes",
        help="Output directory for hero rule files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without creating files"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(message)s'
    )
    
    try:
        generator = HeroRulesGenerator(args.heroes_file, args.output_dir)
        results = generator.generate_missing_rules(dry_run=args.dry_run)
        
        # Print results
        print(f"📊 Hero Rules Generation {'(DRY RUN)' if results['dry_run'] else ''}")
        print("=" * 60)
        print(f"Total Heroes: {results['total_heroes']}")
        print(f"Existing Rules: {results['existing_rules']}")
        print(f"Missing Heroes: {results['missing_heroes']}")
        
        if results['dry_run']:
            print(f"Would Generate: {results['missing_heroes']} rule files")
        else:
            print(f"Generated: {results['generated_files']} rule files")
        
        print(f"Current Coverage: {results['coverage_percentage']}%")
        if not results['dry_run'] and results['generated_files'] > 0:
            print(f"New Coverage: {results['new_coverage_percentage']}%")
        
        if results['missing_hero_list']:
            print(f"\nMissing Heroes ({len(results['missing_hero_list'])}):")
            for hero in sorted(results['missing_hero_list'][:10]):  # Show first 10
                print(f"  • {hero}")
            if len(results['missing_hero_list']) > 10:
                print(f"  ... and {len(results['missing_hero_list']) - 10} more")
        
        if results.get('generated_file_list'):
            print(f"\nGenerated Files:")
            for file_path in results['generated_file_list'][:5]:  # Show first 5
                print(f"  • {file_path}")
            if len(results['generated_file_list']) > 5:
                print(f"  ... and {len(results['generated_file_list']) - 5} more")
        
        print("\n✅ Hero rules generation completed successfully!")
        
        if results['coverage_percentage'] < 95:
            print(f"\n💡 Tip: Run without --dry-run to generate {results['missing_heroes']} missing rule stubs")
            
    except Exception as e:
        logger.error(f"❌ Hero rules generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()