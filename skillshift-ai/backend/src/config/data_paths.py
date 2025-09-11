"""
Data Path Configuration Module

Provides centralized configuration for all data file paths with environment variable overrides.
This allows switching between canonical data/* and imported data/_imports/* files.

Environment Variables:
    HEROES_JSON: Path to heroes data file (default: data/heroes_cleaned.json)
    HERO_ROLE_MAP_JSON: Path to hero role mapping (default: data/hero_role_mapping.json)  
    WINRATE_LEADERBOARD_JSON: Path to winrate leaderboard (default: data/mlbb-winrate-leaderboard-complete.json)
    PATCH_DIR: Directory containing patch files (default: data/patches)
    MLBB_HEROES_CORRECTED_JSON: Path to corrected heroes file (default: data/mlbb-heroes-corrected.json)
    
Usage:
    from backend.src.config.data_paths import DataPaths
    
    # Get configured paths
    config = DataPaths()
    heroes_file = config.heroes_json
    patches_dir = config.patch_dir
    
    # Override for testing
    config = DataPaths(use_imports=True)  # Uses data/_imports/*
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class DataPaths:
    """Centralized data path configuration with environment variable support."""
    
    def __init__(self, 
                 project_root: Optional[str] = None,
                 use_imports: bool = False):
        """
        Initialize data paths configuration.
        
        Args:
            project_root: Root directory of the project (auto-detected if None)
            use_imports: If True, use data/_imports/* instead of data/*
        """
        self.project_root = self._find_project_root(project_root)
        self.use_imports = use_imports
        
        # Set base directory
        if use_imports:
            self.data_dir = self.project_root / "data" / "_imports"
            self.patch_dir_default = self.data_dir  # Patches in _imports root
        else:
            self.data_dir = self.project_root / "data"
            self.patch_dir_default = self.data_dir / "patches"
    
    def _find_project_root(self, provided_root: Optional[str] = None) -> Path:
        """Find project root directory."""
        if provided_root:
            return Path(provided_root).resolve()
        
        # Try to find project root by looking for characteristic files
        current = Path(__file__).resolve()
        
        # Walk up directories looking for project markers
        for parent in current.parents:
            if any((parent / marker).exists() for marker in 
                   ["package.json", "pyproject.toml", "requirements.txt", ".git"]):
                return parent
        
        # Fallback: assume we're in skillshift-ai/backend/src/config/
        return current.parents[3]
    
    @property
    def heroes_json(self) -> str:
        """Path to heroes_cleaned.json with environment override."""
        env_path = os.getenv("HEROES_JSON")
        if env_path:
            return env_path
        
        return str(self.data_dir / "heroes_cleaned.json")
    
    @property
    def hero_role_mapping_json(self) -> str:
        """Path to hero_role_mapping.json with environment override."""
        env_path = os.getenv("HERO_ROLE_MAP_JSON")
        if env_path:
            return env_path
        
        return str(self.data_dir / "hero_role_mapping.json")
    
    @property
    def winrate_leaderboard_json(self) -> str:
        """Path to mlbb-winrate-leaderboard-complete.json with environment override."""
        env_path = os.getenv("WINRATE_LEADERBOARD_JSON")
        if env_path:
            return env_path
        
        return str(self.data_dir / "mlbb-winrate-leaderboard-complete.json")
    
    @property
    def mlbb_heroes_corrected_json(self) -> str:
        """Path to mlbb-heroes-corrected.json with environment override."""
        env_path = os.getenv("MLBB_HEROES_CORRECTED_JSON")
        if env_path:
            return env_path
        
        return str(self.data_dir / "mlbb-heroes-corrected.json")
    
    @property
    def patch_dir(self) -> str:
        """Path to patches directory with environment override."""
        env_path = os.getenv("PATCH_DIR")
        if env_path:
            return env_path
        
        return str(self.patch_dir_default)
    
    @property
    def player_history_json(self) -> str:
        """Path to player_history.json (usually in canonical data)."""
        env_path = os.getenv("PLAYER_HISTORY_JSON")
        if env_path:
            return env_path
        
        # Player history typically stays in canonical location
        canonical_data = self.project_root / "data"
        return str(canonical_data / "player_history.json")
    
    @property
    def sample_match_json(self) -> str:
        """Path to sample_match.json (usually in canonical data)."""
        env_path = os.getenv("SAMPLE_MATCH_JSON")
        if env_path:
            return env_path
        
        # Sample match typically stays in canonical location
        canonical_data = self.project_root / "data"
        return str(canonical_data / "sample_match.json")
    
    def exists(self, path_property: str) -> bool:
        """Check if a data file exists."""
        path = getattr(self, path_property)
        return Path(path).exists()
    
    def validate_paths(self) -> dict:
        """Validate all configured paths and return status."""
        results = {}
        
        paths_to_check = [
            "heroes_json",
            "hero_role_mapping_json", 
            "winrate_leaderboard_json",
            "mlbb_heroes_corrected_json",
            "patch_dir"
        ]
        
        for path_name in paths_to_check:
            path = getattr(self, path_name)
            exists = Path(path).exists()
            results[path_name] = {
                "path": path,
                "exists": exists,
                "size_kb": round(Path(path).stat().st_size / 1024, 1) if exists else 0
            }
        
        return results
    
    def get_environment_status(self) -> dict:
        """Get status of environment variable overrides."""
        env_vars = {
            "HEROES_JSON": self.heroes_json,
            "HERO_ROLE_MAP_JSON": self.hero_role_mapping_json,
            "WINRATE_LEADERBOARD_JSON": self.winrate_leaderboard_json,
            "MLBB_HEROES_CORRECTED_JSON": self.mlbb_heroes_corrected_json,
            "PATCH_DIR": self.patch_dir,
            "PLAYER_HISTORY_JSON": self.player_history_json,
            "SAMPLE_MATCH_JSON": self.sample_match_json
        }
        
        return {
            var: {
                "env_set": os.getenv(var) is not None,
                "current_value": path,
                "source": "environment" if os.getenv(var) else "default"
            }
            for var, path in env_vars.items()
        }
    
    def print_configuration(self):
        """Print current configuration for debugging."""
        print("=" * 60)
        print("📁 DATA PATHS CONFIGURATION")
        print("=" * 60)
        print(f"Project Root: {self.project_root}")
        print(f"Data Directory: {self.data_dir}")
        print(f"Using Imports: {self.use_imports}")
        print()
        
        print("📋 CONFIGURED PATHS:")
        print("-" * 60)
        paths = self.validate_paths()
        for name, info in paths.items():
            status = "✅" if info["exists"] else "❌"
            print(f"{status} {name}: {info['path']} ({info['size_kb']} KB)")
        
        print()
        print("🔧 ENVIRONMENT VARIABLES:")
        print("-" * 60)
        env_status = self.get_environment_status()
        for var, info in env_status.items():
            source_icon = "🌍" if info["env_set"] else "🏠"
            print(f"{source_icon} {var}: {info['current_value']} ({info['source']})")
        
        print("=" * 60)


# Singleton instance for easy import
default_config = DataPaths()

# Convenience functions for backward compatibility
def get_heroes_json_path() -> str:
    """Get heroes_cleaned.json path."""
    return default_config.heroes_json

def get_hero_role_mapping_path() -> str:
    """Get hero_role_mapping.json path."""
    return default_config.hero_role_mapping_json

def get_winrate_leaderboard_path() -> str:
    """Get winrate leaderboard path."""
    return default_config.winrate_leaderboard_json

def get_patch_dir_path() -> str:
    """Get patches directory path."""
    return default_config.patch_dir

def get_mlbb_heroes_corrected_path() -> str:
    """Get mlbb-heroes-corrected.json path."""
    return default_config.mlbb_heroes_corrected_json


if __name__ == "__main__":
    # CLI for debugging configuration
    import argparse
    
    parser = argparse.ArgumentParser(description="Data paths configuration utility")
    parser.add_argument("--use-imports", action="store_true",
                       help="Use data/_imports/* instead of data/*")
    parser.add_argument("--validate", action="store_true",
                       help="Validate all configured paths")
    
    args = parser.parse_args()
    
    config = DataPaths(use_imports=args.use_imports)
    config.print_configuration()
    
    if args.validate:
        print("\n🔍 VALIDATION RESULTS:")
        validation = config.validate_paths()
        all_exist = all(info["exists"] for info in validation.values())
        
        if all_exist:
            print("✅ All configured paths exist and are accessible")
        else:
            print("❌ Some configured paths are missing:")
            for name, info in validation.items():
                if not info["exists"]:
                    print(f"   • {name}: {info['path']}")