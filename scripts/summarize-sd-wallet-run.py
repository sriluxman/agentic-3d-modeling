import json
import re
from pathlib import Path

import trimesh


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "exports" / "sd-travel-wallet"
CARD_COUNTS = [5, 8]
PARTS = [
    f"sd-wallet-{count}-card-{part}"
    for count in CARD_COUNTS
    for part in ["tray", "sleeve"]
]


def seconds(value: str) -> int:
    units = {"h": 3600, "m": 60, "s": 1}
    return sum(int(number) * units[unit] for number, unit in re.findall(r"(\d+)([hms])", value))


reports = {
    part: json.loads((EXPORT_DIR / f"{part}-evaluation" / "report.json").read_text())
    for part in [*PARTS, "latch-preflight-coupon"]
}
production_seconds = {
    str(count): sum(
        seconds(reports[f"sd-wallet-{count}-card-{part}"]["slicer"]["metrics"]["estimated_time"])
        for part in ["tray", "sleeve"]
    )
    for count in CARD_COUNTS
}
coupon_seconds = seconds(
    reports["latch-preflight-coupon"]["slicer"]["metrics"]["estimated_time"]
)

collision_volumes = {}
for count in CARD_COUNTS:
    collision = trimesh.load_mesh(
        EXPORT_DIR / f"sd-wallet-{count}-card-assembly-collision.stl",
        force="mesh",
        process=True,
    )
    collision_volumes[str(count)] = (
        0.0 if min(collision.extents) <= 1e-9 else abs(float(collision.volume))
    )
all_parts_passed = all(report["status"] == "pass" for report in reports.values())
collisions_passed = all(volume <= 0.01 for volume in collision_volumes.values())

summary = {
    "schema_version": 1,
    "status": "pass" if all_parts_passed and collisions_passed else "fail",
    "card_type": "full_size_sd",
    "card_counts": CARD_COUNTS,
    "card_dimensions_mm": [24, 32, 2.1],
    "slot_clearance_mm_per_side": 0.25,
    "sleeve_clearance_mm_per_side": 0.35,
    "latch_bump_embed_mm": 0.8,
    "divider_embed_mm": 0.3,
    "card_exposure_mm": 6.0,
    "front_access_drop_mm": 3.0,
    "production_estimated_time_seconds": production_seconds,
    "coupon_estimated_time_seconds": coupon_seconds,
    "all_parts_passed": all_parts_passed,
    "assembly_collision_volume_mm3": collision_volumes,
}
(EXPORT_DIR / "wallet-report.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(
    f"{summary['status'].upper()}: "
    + "; ".join(
        f"{count}-card {duration // 60}m {duration % 60}s"
        for count, duration in production_seconds.items()
    )
    + f"; coupon {coupon_seconds // 60}m {coupon_seconds % 60}s"
)
raise SystemExit(0 if summary["status"] == "pass" else 1)
