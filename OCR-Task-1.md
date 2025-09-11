# How to Make Row-Agnostic (Generalized for Any Player Row)

<think>

## 1. Detect the scoreboard table once

Extend `detect_table_regions` to return:

- **panel_bbox** → (top, left, width, height) of the scoreboard panel
- **rows_count** → usually 5 (but compute dynamically if possible)
- **row_top, row_height** → either measured from anchors or computed from panel height ÷ row count

## 2. Normalize all geometry to ratios

Express all bounding boxes relative to the panel:

- **Example:** `row_top_ratio = (row_top - panel_top) / panel_height`
- **Example:** `row_height_ratio = row_height / panel_height`
- Store all coordinates as fractions of panel width/height instead of raw pixels.

## 3. Generate row crops dynamically

For `i` in `range(rows_count)` → compute:

- `row_y = panel_top + i * row_height`
- `row_bbox = (row_y, panel_left, panel_width, row_height)`
- Crop each row using these normalized boxes.

## 4. Anchor parsing per row

- Run IGN OCR for each row crop.
- When `target_ign` is found → assign that row index.
- Pass that row crop into KDA/Damage parsers.

## 5. Fallback & Validation

- If IGN OCR is noisy → confirm with fuzzy match (≥0.7 similarity).
- If still unresolved → fallback to MVP crown detection as tie-breaker. 

</think>
