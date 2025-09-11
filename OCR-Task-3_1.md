# OCR Task 3.1: Performance Test Fix

## The Traceback Failing Performance Output

```
AttributeError: 'RowAgnosticScoreboardDetector' object has no attribute 'detect'
```

## Problem Analysis

So in your current implementation (detectors.py), the class `RowAgnosticScoreboardDetector` doesn't expose a `.detect()` method — but the performance test calls it directly:

```python
table = row_agnostic_detector.detect(kda_img)
```

## Why This Is Happening

- Your detector probably has methods like `detect_table_regions()` or `generate_row_crops()`, but not a unified `.detect()` entrypoint.
- The contract/perf test suite is written against the assumption that every detector implements a `.detect(img)` method returning a result object (table bbox + row info).

## How to Fix

We need to add a thin `.detect()` wrapper method to `RowAgnosticScoreboardDetector` that orchestrates table detection + row crop generation. For example:

```python
# in backend/ocr/detectors.py

class RowAgnosticScoreboardDetector:
    def __init__(self, config=None):
        self.config = config or {}

    def detect_table_regions(self, image):
        # your existing table region logic
        ...

    def generate_row_crops(self, image, table_bbox, rows_count=5):
        # your existing row crop logic
        ...

    def detect(self, image):
        """
        Unified detection entrypoint (for tests & services).
        Returns a dict with table bbox, row crops, and metadata.
        """
        table = self.detect_table_regions(image)
        if not table:
            return None

        row_crops = self.generate_row_crops(image, table["bbox"], table["rows_count"])
        return {
            "bbox": table["bbox"],
            "confidence": table.get("confidence", 0.0),
            "rows_count": table.get("rows_count", len(row_crops)),
            "row_crops": row_crops,
        }
```

## This Way

- Perf tests can call `.detect()` and get everything they expect.
- Services/parsers can still use the more granular methods directly.

## Next Step for You

1. Add that `.detect()` method into your `RowAgnosticScoreboardDetector`.
2. Re-run:

```bash
venv/bin/pytest backend/tests/performance/test_ocr_performance.py -q
```

→ The `test_cross_view_fusion_performance` should stop throwing `AttributeError`.
