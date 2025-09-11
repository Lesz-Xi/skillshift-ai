"""
Geometry utilities for MLBB OCR system
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class BBox:
    """Bounding box with x, y, width, height"""
    x: int
    y: int
    w: int
    h: int

    def pad(self, px: int, W: int, H: int) -> "BBox":
        """Add padding around the bbox, constrained to image bounds"""
        x = max(0, self.x - px)
        y = max(0, self.y - px)
        w = min(W - x, self.w + 2*px)
        h = min(H - y, self.h + 2*px)
        return BBox(x, y, w, h)

    def crop(self, image):
        """Extract crop from image using this bbox"""
        return image[self.y:self.y+self.h, self.x:self.x+self.w]

    def to_tuple(self) -> Tuple[int, int, int, int]:
        """Convert to (x, y, w, h) tuple"""
        return (self.x, self.y, self.w, self.h)

    def to_xyxy(self) -> Tuple[int, int, int, int]:
        """Convert to (x1, y1, x2, y2) format"""
        return (self.x, self.y, self.x + self.w, self.y + self.h)


def pct_to_abs(parent: BBox, rel: Tuple[float, float, float, float]) -> BBox:
    """Convert relative coordinates to absolute bbox within parent"""
    rx, ry, rw, rh = rel
    return BBox(
        x = int(parent.x + rx * parent.w),
        y = int(parent.y + ry * parent.h),
        w = int(rw * parent.w),
        h = int(rh * parent.h),
    )


def row_bbox(panel: BBox, row_index: int, rows: int,
             top_off: float, bot_off: float) -> BBox:
    """Calculate bbox for a specific row within a panel"""
    usable_h = panel.h * (1.0 - top_off - bot_off)
    row_h = usable_h / rows
    y0 = int(panel.y + panel.h * top_off + row_index * row_h)
    return BBox(panel.x, y0, panel.w, int(row_h))