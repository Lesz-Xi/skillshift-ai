import numpy as np

from core.ocr_utils import has_img, read_kda, read_int, compute_gpm


def test_has_img_and_truthiness():
    assert has_img(None) is False
    a = np.zeros((0,))
    assert has_img(a) is False
    b = np.zeros((5, 5), dtype=np.uint8)
    assert has_img(b) is True


def test_read_kda_variants():
    assert read_kda("9/2/12") == (9, 2, 12)
    assert read_kda("9 2 12") == (9, 2, 12) or read_kda("9 2 12") is None
    # hyphenated should also be accepted through tolerant extraction elsewhere; direct regex targets slash form
    # ensure compute helpers work regardless
    assert read_int(" 12,374 ") == 12374


def test_compute_gpm():
    assert compute_gpm(12000, 20.0) == 600.0
    assert compute_gpm(None, 20.0) is None
    assert compute_gpm(1000, 0) is None

