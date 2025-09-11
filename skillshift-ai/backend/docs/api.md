# OCR API Documentation

This document provides comprehensive documentation for the OCR API endpoints in the MLBB Coach AI system.

## Overview

The OCR API provides endpoints for analyzing Mobile Legends: Bang Bang screenshots to extract player statistics, KDA data, and performance metrics. The API uses advanced OCR technology with row-agnostic detection and cross-view data fusion.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. All endpoints are publicly accessible.

## Endpoints

### 1. OCR Debug Endpoint

**POST** `/ocr/debug`

Debug OCR processing for a single screenshot with detailed diagnostic information.

#### Request Body

```json
{
  "image_path": "string",
  "target_ign": "string",
  "debug_mode": false,
  "extract_options": {
    "with_damage": false
  }
}
```

#### Parameters

| Field                         | Type    | Required | Description                                            |
| ----------------------------- | ------- | -------- | ------------------------------------------------------ |
| `image_path`                  | string  | Yes      | Path to the screenshot image file                      |
| `target_ign`                  | string  | Yes      | Exact In-Game Name (IGN) to locate                     |
| `debug_mode`                  | boolean | No       | Enable debug mode for detailed output (default: false) |
| `extract_options`             | object  | No       | Additional extraction options                          |
| `extract_options.with_damage` | boolean | No       | Include damage parsing (slower but more complete)      |

#### Response

```json
{
  "player_located": true,
  "player_ign": "Diary of dolls",
  "kda": {
    "kills": 9,
    "deaths": 2,
    "assists": 12
  },
  "overall_confidence": 0.85,
  "rows_count": 5,
  "table_bbox": [0.1, 0.2, 0.8, 0.6],
  "debug": {
    "ratios": {
      "row_top": 0.2,
      "row_height": 0.12
    },
    "anchors_detected": ["Hero Damage", "Victory"]
  }
}
```

#### Response Fields

| Field                | Type    | Description                                        |
| -------------------- | ------- | -------------------------------------------------- |
| `player_located`     | boolean | Whether the target player was found                |
| `player_ign`         | string  | The detected player IGN (null if not found)        |
| `kda`                | object  | KDA statistics (kills/deaths/assists)              |
| `overall_confidence` | float   | Overall confidence score (0.0-1.0)                 |
| `rows_count`         | integer | Number of player rows detected                     |
| `table_bbox`         | array   | Table bounding box as [x, y, width, height] ratios |
| `debug`              | object  | Debug information (only when debug_mode=true)      |

#### Example Usage

```bash
curl -X POST "http://localhost:8000/ocr/debug" \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "/path/to/screenshot.png",
    "target_ign": "Diary of dolls",
    "debug_mode": true,
    "extract_options": {
      "with_damage": true
    }
  }'
```

### 2. OCR Fusion Endpoint

**POST** `/ocr/fusion`

Process both KDA and Damage screenshots and fuse the data for comprehensive analysis.

#### Request Body

```json
{
  "kda_image_path": "string",
  "damage_image_path": "string",
  "target_ign": "string",
  "fusion_mode": "auto"
}
```

#### Parameters

| Field               | Type   | Required | Description                                                            |
| ------------------- | ------ | -------- | ---------------------------------------------------------------------- |
| `kda_image_path`    | string | Yes      | Path to the KDA/scoreboard screenshot                                  |
| `damage_image_path` | string | Yes      | Path to the damage statistics screenshot                               |
| `target_ign`        | string | Yes      | Exact In-Game Name (IGN) to locate                                     |
| `fusion_mode`       | string | No       | Fusion mode: "auto", "kda_primary", "damage_primary" (default: "auto") |

#### Response

```json
{
  "player_located": true,
  "player_ign": "Diary of dolls",
  "kda": {
    "kills": 9,
    "deaths": 2,
    "assists": 12
  },
  "overall_confidence": 0.92,
  "fusion_mode": "auto"
}
```

#### Example Usage

```bash
curl -X POST "http://localhost:8000/ocr/fusion" \
  -H "Content-Type: application/json" \
  -d '{
    "kda_image_path": "/path/to/kda_screenshot.png",
    "damage_image_path": "/path/to/damage_screenshot.png",
    "target_ign": "Diary of dolls",
    "fusion_mode": "auto"
  }'
```

### 3. Analysis Screenshot Endpoint

**POST** `/analysis/screenshot`

Analyze a screenshot with optional debug information and row-agnostic processing.

#### Request Body

```json
{
  "image_path": "string",
  "ign": "string",
  "debug_mode": false,
  "row_agnostic_mode": true,
  "extract_options": {
    "with_damage": false
  }
}
```

#### Parameters

| Field                         | Type    | Required | Description                                 |
| ----------------------------- | ------- | -------- | ------------------------------------------- |
| `image_path`                  | string  | Yes      | Path to the screenshot image file           |
| `ign`                         | string  | Yes      | Player IGN to target                        |
| `debug_mode`                  | boolean | No       | Enable debug mode (default: false)          |
| `row_agnostic_mode`           | boolean | No       | Use row-agnostic processing (default: true) |
| `extract_options`             | object  | No       | Additional extraction options               |
| `extract_options.with_damage` | boolean | No       | Include damage parsing                      |

#### Response

```json
{
  "ign": "Diary of dolls",
  "player_located": true,
  "player_ign": "Diary of dolls",
  "kda": {
    "kills": 9,
    "deaths": 2,
    "assists": 12
  },
  "overall_confidence": 0.85,
  "row_agnostic_mode": true,
  "debug": {
    "table_bbox": [0.1, 0.2, 0.8, 0.6],
    "rows_count": 5
  }
}
```

#### Example Usage

```bash
curl -X POST "http://localhost:8000/analysis/screenshot" \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "/path/to/screenshot.png",
    "ign": "Diary of dolls",
    "debug_mode": true,
    "row_agnostic_mode": true,
    "extract_options": {
      "with_damage": true
    }
  }'
```

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid image_path"
}
```

### 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": ["body", "image_path"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error

```json
{
  "detail": "OCR processing failed: [error details]"
}
```

## Performance Considerations

- **Processing Time**: Typical processing time is 1-3 seconds per screenshot
- **Image Requirements**: PNG or JPG format recommended
- **Resolution**: Higher resolution images generally provide better accuracy
- **Memory Usage**: Each request uses approximately 50-100MB of memory

## Best Practices

1. **Image Quality**: Use high-resolution screenshots for better OCR accuracy
2. **IGN Matching**: Ensure the target IGN matches exactly (case-sensitive)
3. **Debug Mode**: Enable debug mode for troubleshooting and development
4. **Error Handling**: Always check the `player_located` field before using results
5. **Confidence Scores**: Use confidence scores to determine result reliability

## CLI Tool

For development and testing, use the OCR Debug CLI:

```bash
# Test OCR debug service
python -m backend.src.cli.ocr_debug --image path/to/screenshot.png --ign "Player Name"

# Test with debug mode and damage parsing
python -m backend.src.cli.ocr_debug --image path/to/screenshot.png --ign "Player Name" --debug --damage

# Test all components
python -m backend.src.cli.ocr_debug --image path/to/screenshot.png --ign "Player Name" --all
```

## Technical Details

### OCR Pipeline

1. **Image Preprocessing**: Load and validate the image
2. **Table Detection**: Detect scoreboard table using anchor-based detection
3. **Row Generation**: Generate normalized row crops for each player
4. **Text Extraction**: Extract text from each row using OCR
5. **Data Parsing**: Parse KDA, damage, and other statistics
6. **Cross-View Fusion**: Combine data from multiple views if available
7. **Result Validation**: Validate and return structured results

### Row-Agnostic Detection

The system uses a row-agnostic approach that:

- Detects the scoreboard table once
- Normalizes all geometry to ratios
- Generates row crops dynamically
- Works with any player position in the scoreboard

### Confidence Scoring

Confidence scores are calculated based on:

- OCR text extraction quality
- IGN matching accuracy
- Data completeness
- Cross-validation between views

## Changelog

### v1.0.0 (2025-01-15)

- Initial release of OCR API
- Support for KDA and damage view analysis
- Row-agnostic detection system
- Cross-view data fusion
- Debug CLI tool
- Performance testing framework
