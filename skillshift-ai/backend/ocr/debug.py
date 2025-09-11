import argparse, json, time, cv2
from backend.ocr.detectors import row_agnostic_detector
from backend.ocr.parsers_kda import kda_parser
from backend.ocr.parsers_damage import damage_parser
from backend.ocr.fuse import cross_view_fusion

def main():
    ap = argparse.ArgumentParser(description="OCR Debug Script")
    ap.add_argument("--kda", required=True, help="Path to KDA view image")
    ap.add_argument("--dmg", help="Path to Damage view image")
    ap.add_argument("--ign", required=True, help="Target IGN")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    img = cv2.imread(args.kda)
    table = row_agnostic_detector.detect_table_regions(img)
    rows = row_agnostic_detector.generate_row_crops(img, table)
    kda_res = kda_parser.parse_from_rows(rows, args.ign)
    dmg_res = None

    if args.dmg:
        img2 = cv2.imread(args.dmg)
        table2 = row_agnostic_detector.detect_table_regions(img2)
        rows2 = row_agnostic_detector.generate_row_crops(img2, table2)
        dmg_res = damage_parser.parse_from_rows(rows2, args.ign)

    fusion = cross_view_fusion(kda_res, dmg_res, ign=args.ign)
    out = {
        "elapsed_ms": round((time.time() - t0) * 1000, 1),
        "kda": getattr(kda_res, "kda", None) if kda_res else None,
        "damage": getattr(dmg_res, "damage", None) if dmg_res else None,
        "fusion": fusion.dict() if hasattr(fusion, "dict") else fusion,
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()