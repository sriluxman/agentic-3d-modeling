import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "exports" / "ikea-canvas-frame-clips"
PARTS = [
    "single-canvas-clip",
    "four-canvas-clips-print-plate",
    "board-gap-fit-coupon",
]


def seconds(value: str) -> int:
    units = {"h": 3600, "m": 60, "s": 1}
    return sum(int(number) * units[unit] for number, unit in re.findall(r"(\d+)([hms])", value))


reports = {
    part: json.loads((EXPORT_DIR / f"{part}-evaluation" / "report.json").read_text())
    for part in PARTS
}
all_parts_passed = all(report["status"] == "pass" for report in reports.values())
four_clip_seconds = seconds(
    reports["four-canvas-clips-print-plate"]["slicer"]["metrics"]["estimated_time"]
)
coupon_seconds = seconds(
    reports["board-gap-fit-coupon"]["slicer"]["metrics"]["estimated_time"]
)

summary = {
    "schema_version": 1,
    "status": "pass" if all_parts_passed else "fail",
    "frame_depth_nominal_mm": 15.5,
    "frame_gap_default_mm": 16.2,
    "frame_face_width_mm": 40,
    "taper_length_mm": 6,
    "canvas_reach_mm": 30,
    "board_gap_default_mm": 3.0,
    "board_gap_coupon_mm": [3.0, 3.5, 4.0],
    "clip_width_mm": 20,
    "clip_thickness_mm": 2.8,
    "four_clip_estimated_time_seconds": four_clip_seconds,
    "coupon_estimated_time_seconds": coupon_seconds,
    "all_parts_passed": all_parts_passed,
    "physical": "pending; select the cooled board-gap coupon with the best secure removable fit",
}
(EXPORT_DIR / "clip-report.json").write_text(
    json.dumps(summary, indent=2) + "\n",
    encoding="utf-8",
)
print(
    f"{summary['status'].upper()}: four clips {four_clip_seconds // 60}m "
    f"{four_clip_seconds % 60}s; coupon {coupon_seconds // 60}m {coupon_seconds % 60}s"
)
raise SystemExit(0 if summary["status"] == "pass" else 1)
