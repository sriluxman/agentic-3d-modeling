import json
import re
from pathlib import Path

import trimesh


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "exports" / "sd-travel-wallet"
PARTS = ["sd-wallet-tray", "sd-wallet-sleeve"]


def seconds(value: str) -> int:
    units = {"h": 3600, "m": 60, "s": 1}
    return sum(int(number) * units[unit] for number, unit in re.findall(r"(\d+)([hms])", value))


reports = {
    part: json.loads((EXPORT_DIR / f"{part}-evaluation" / "report.json").read_text())
    for part in [*PARTS, "latch-preflight-coupon"]
}
production_seconds = sum(
    seconds(reports[part]["slicer"]["metrics"]["estimated_time"]) for part in PARTS
)
coupon_seconds = seconds(
    reports["latch-preflight-coupon"]["slicer"]["metrics"]["estimated_time"]
)

collision = trimesh.load_mesh(EXPORT_DIR / "assembly-collision.stl", force="mesh", process=True)
collision_volume = 0.0 if min(collision.extents) <= 1e-9 else abs(float(collision.volume))
all_parts_passed = all(report["status"] == "pass" for report in reports.values())

summary = {
    "schema_version": 1,
    "status": "pass" if all_parts_passed and collision_volume <= 0.01 else "fail",
    "card_type": "full_size_sd",
    "card_count": 5,
    "card_dimensions_mm": [24, 32, 2.1],
    "slot_clearance_mm_per_side": 0.25,
    "sleeve_clearance_mm_per_side": 0.35,
    "latch_bump_embed_mm": 0.8,
    "divider_embed_mm": 0.3,
    "production_estimated_time_seconds": production_seconds,
    "coupon_estimated_time_seconds": coupon_seconds,
    "all_parts_passed": all_parts_passed,
    "assembly_collision_volume_mm3": collision_volume,
}
(EXPORT_DIR / "wallet-report.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(
    f"{summary['status'].upper()}: production {production_seconds // 60}m {production_seconds % 60}s; "
    f"coupon {coupon_seconds // 60}m {coupon_seconds % 60}s"
)
raise SystemExit(0 if summary["status"] == "pass" else 1)
