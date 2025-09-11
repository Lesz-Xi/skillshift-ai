"""Configuration module for MLBB Coach AI backend."""

from .data_paths import DataPaths, default_config
from .data_paths import (
    get_heroes_json_path,
    get_hero_role_mapping_path, 
    get_winrate_leaderboard_path,
    get_patch_dir_path,
    get_mlbb_heroes_corrected_path
)

__all__ = [
    "DataPaths",
    "default_config",
    "get_heroes_json_path",
    "get_hero_role_mapping_path",
    "get_winrate_leaderboard_path", 
    "get_patch_dir_path",
    "get_mlbb_heroes_corrected_path"
]