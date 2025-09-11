# YOLO Dataset Classes Reference

## Overview

This document outlines all **51 object classes** (IDs: 0-50) for the MLBB YOLO dataset, applicable to both `damage_view` and `kda_view` screenshots.

## Total Classes: 51

### High Priority Classes (21 classes)

**Target**: 200-500 annotations per class

#### Hero Detection (Classes 0-9)

| Class ID | Class Name | Description |
|----------|------------|-------------|
| 0 | `hero_icon_ally_1` | Ally team hero position 1 (top-left) |
| 1 | `hero_icon_ally_2` | Ally team hero position 2 |
| 2 | `hero_icon_ally_3` | Ally team hero position 3 |
| 3 | `hero_icon_ally_4` | Ally team hero position 4 |
| 4 | `hero_icon_ally_5` | Ally team hero position 5 (bottom-right) |
| 5 | `hero_icon_enemy_1` | Enemy team hero position 1 (top-left) |
| 6 | `hero_icon_enemy_2` | Enemy team hero position 2 |
| 7 | `hero_icon_enemy_3` | Enemy team hero position 3 |
| 8 | `hero_icon_enemy_4` | Enemy team hero position 4 |
| 9 | `hero_icon_enemy_5` | Enemy team hero position 5 (bottom-right) |

#### Performance Badges (Classes 10-14)

| Class ID | Class Name | Description |
|----------|------------|-------------|
| 10 | `mvp_badge` | MVP crown/badge for winning team |
| 11 | `mvp_loss_badge` | MVP badge for losing team |
| 12 | `medal_gold` | Gold performance medal |
| 13 | `medal_silver` | Silver performance medal |
| 14 | `medal_bronze` | Bronze performance medal |

#### Match Information (Classes 15-21)

| Class ID | Class Name | Description |
|----------|------------|-------------|
| 15 | `match_type_classic` | Classic match mode indicator |
| 16 | `match_type_ranked` | Ranked match mode indicator |
| 17 | `match_type_brawl` | Brawl mode indicator |
| 18 | `match_type_custom` | Custom game mode indicator |
| 19 | `victory_text` | Victory result text |
| 20 | `defeat_text` | Defeat result text |

### Medium Priority Classes (13 classes)

**Target**: 100-300 annotations per class

#### Player Statistics (Classes 21-32)

| Class ID | Class Name | Description |
|----------|------------|-------------|
| 21 | `kda_display` | Kill/Death/Assist display (e.g., 5/2/8) |
| 22 | `player_name` | Player IGN display |
| 23 | `gold_amount` | Total gold earned |
| 24 | `gpm_display` | Gold per minute |
| 25 | `damage_dealt` | Damage dealt to heroes |
| 26 | `damage_taken` | Damage taken |
| 27 | `healing_done` | Healing provided |
| 28 | `participation_rate` | Team fight participation percentage |
| 29 | `turret_damage` | Damage to structures |
| 30 | `match_duration` | Game length display |
| 31 | `player_level` | Player level display |

#### UI Elements (Classes 32-34)

| Class ID | Class Name | Description |
|----------|------------|-------------|
| 32 | `team_indicator_ally` | Ally team section marker |
| 33 | `team_indicator_enemy` | Enemy team section marker |
| 34 | `scoreboard_container` | Main statistics display area |

### Low Priority Classes (17 classes)

**Target**: 50-150 annotations per class

#### Equipment (Classes 35-43)

| Class ID | Class Name | Description |
|----------|------------|-------------|
| 35 | `item_icon_1` | Equipment slot 1 (leftmost) |
| 36 | `item_icon_2` | Equipment slot 2 |
| 37 | `item_icon_3` | Equipment slot 3 |
| 38 | `item_icon_4` | Equipment slot 4 |
| 39 | `item_icon_5` | Equipment slot 5 |
| 40 | `item_icon_6` | Equipment slot 6 (rightmost) |
| 41 | `battle_spell_1` | First battle spell slot |
| 42 | `battle_spell_2` | Second battle spell slot |

#### Achievements & Roles (Classes 43-48)

| Class ID | Class Name | Description |
|----------|------------|-------------|
| 43 | `savage_indicator` | Savage kill achievement badge |
| 44 | `maniac_indicator` | Maniac kill achievement badge |
| 45 | `legendary_indicator` | Legendary kill streak badge |
| 46 | `role_indicator` | Player role badge/text |
| 47 | `position_rank` | Ranking within role |

#### Quality Control (Classes 48-50)

| Class ID | Class Name | Description |
|----------|------------|-------------|
| 48 | `ui_complete` | Interface fully loaded indicator |
| 49 | `text_readable` | Text clearly legible marker |
| 50 | `icons_clear` | Icons properly rendered marker |

## View-Specific Focus Areas

### Damage View Screenshots

**Primary Focus Classes:**

- Classes 25-29: `damage_dealt`, `damage_taken`, `healing_done`, `turret_damage`, `participation_rate`
- Classes 0-9: Hero icons for team composition
- Classes 19-20: Victory/defeat indicators

### KDA View Screenshots

**Primary Focus Classes:**

- Class 21: `kda_display` (Kill/Death/Assist numbers)
- Classes 35-42: Item slots and battle spells
- Classes 0-9: Hero icons for team composition
- Classes 19-20: Victory/defeat indicators

## Annotation Guidelines

### Validation Requirements

- **Minimum Resolution**: 1080p
- **Supported Formats**: JPG, JPEG, PNG
- **Accuracy Target**: 95%
- **Inter-annotator Agreement**: 90%

### Bounding Box Standards

- **Format**: Center_width_height (x_center, y_center, width, height)
- **Coordinates**: Normalized (0-1 range)
- **Aspect Ratios**: Maintained per class specifications
- **Size Constraints**: Min/max dimensions enforced per class

### Priority Distribution

- **High Priority (Classes 0-20)**: 21 classes - Essential elements
- **Medium Priority (Classes 21-33)**: 13 classes - Statistical information
- **Low Priority (Classes 34-50)**: 17 classes - Supporting elements

## Current Dataset Status

### Available Images

- **Training Set**: 44 images (damage + kda views)
- **Validation Set**: 8 images (mvp_loss + poor performance)
- **Test Set**: 10 images (poor performance)

### Collection Coverage

- **Ranked Matches**: ✅ Complete (5 performance categories)
- **Classic Matches**: ⚠️ Structure only (no images)
- **Other Modes**: ⚠️ Structure only (no images)

## Next Steps for Annotation

1. **Start with High Priority Classes** (0-20)
2. **Focus on clearly visible elements** first
3. **Use consistent naming conventions** from this reference
4. **Validate bounding boxes** against size constraints
5. **Maintain quality standards** throughout annotation process

---

*Generated from YOLO dataset configuration - Last updated: 2024*
