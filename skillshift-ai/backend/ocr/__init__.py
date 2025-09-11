"""
Row-agnostic OCR system for MLBB screenshots.

This module provides row-agnostic scoreboard detection and parsing
capabilities that work for any player position in the scoreboard.
"""

from .detectors import row_agnostic_detector, RowAgnosticScoreboardDetector, TableRegion, RowCrop
from .parsers_kda import kda_parser, RowAgnosticKDAParser, KDAResult
from .parsers_damage import damage_parser, RowAgnosticDamageParser, DamageResult
from .fuse import cross_view_fusion, CrossViewFusion, FusedResult

__all__ = [
    'row_agnostic_detector',
    'RowAgnosticScoreboardDetector',
    'TableRegion',
    'RowCrop',
    'kda_parser',
    'RowAgnosticKDAParser',
    'KDAResult',
    'damage_parser',
    'RowAgnosticDamageParser',
    'DamageResult',
    'cross_view_fusion',
    'CrossViewFusion',
    'FusedResult'
]
