import re
from core.data_collector import DataCollector


def make_bbox(x_center: int, y_center: int, w: int = 60, h: int = 24):
    """Create a simple quadrilateral bbox around a center point.

    EasyOCR returns 4 points [ [x1,y1], [x2,y2], [x3,y3], [x4,y4] ].
    """
    x1 = x_center - w // 2
    x2 = x_center + w // 2
    y1 = y_center - h // 2
    y2 = y_center + h // 2
    return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]


def test_kda_and_gold_extraction_from_row():
    """Synthetic OCR row should yield correct K/D/A and reasonable gold."""
    ign = "HVD Diary of dolls"
    y = 500

    # Left-to-right simulated row: IGN, K, D, A, gold, damage
    ocr_results = [
        (make_bbox(200, y), ign, 0.95),
        (make_bbox(420, y), "9", 0.98),
        (make_bbox(470, y), "2", 0.98),
        (make_bbox(520, y), "12", 0.98),
        (make_bbox(680, y), "12374", 0.96),
        (make_bbox(760, y), "15435", 0.96),
    ]

    dc = DataCollector()
    parsed = dc._parse_player_row(ign, ocr_results)

    assert parsed, "Expected parsing to return a dict with fields"
    assert parsed.get("kills") == 9
    assert parsed.get("deaths") == 2
    assert parsed.get("assists") == 12
    assert parsed.get("gold") and parsed["gold"] >= 1000

