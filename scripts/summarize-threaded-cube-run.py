import json
import re
import zipfile
from pathlib import Path

import trimesh


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "exports" / "india-austria-threaded-cube"
PARTS = ["india-half", "austria-half"]
EXPECTED_3MF_OBJECTS = {
    "india-white-core",
    "india-saffron",
    "india-green",
    "india-chakra-navy",
    "austria-white-core",
    "austria-red",
}


def seconds(value: str) -> int:
    units = {"h": 3600, "m": 60, "s": 1}
    return sum(int(number) * units[unit] for number, unit in re.findall(r"(\d+)([hms])", value))


reports = {
    part: json.loads((EXPORT_DIR / f"{part}-evaluation" / "report.json").read_text())
    for part in [*PARTS, "thread-preflight-coupon"]
}
production_seconds = sum(
    seconds(reports[part]["slicer"]["metrics"]["estimated_time"]) for part in PARTS
)
coupon_seconds = seconds(reports["thread-preflight-coupon"]["slicer"]["metrics"]["estimated_time"])

collision_path = EXPORT_DIR / "assembly-collision.stl"
collision = trimesh.load_mesh(collision_path, force="mesh", process=True)
collision_volume = 0.0 if min(collision.extents) <= 1e-9 else abs(float(collision.volume))

with zipfile.ZipFile(EXPORT_DIR / "multicolor-print-plate.3mf") as archive:
    model_path = next(name for name in archive.namelist() if name.lower().endswith(".model"))
    model_xml = archive.read(model_path).decode("utf-8")
names = set(re.findall(r'<object[^>]+name="([^"]+)"', model_xml))

all_parts_passed = all(report["status"] == "pass" for report in reports.values())
summary = {
    "schema_version": 1,
    "status": "pass" if all_parts_passed and collision_volume <= 0.01 and names == EXPECTED_3MF_OBJECTS else "fail",
    "production_estimated_time_seconds": production_seconds,
    "coupon_estimated_time_seconds": coupon_seconds,
    "all_parts_passed": all_parts_passed,
    "assembly_collision_volume_mm3": collision_volume,
    "multicolor_3mf_objects": sorted(names),
}
(EXPORT_DIR / "cube-report.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(
    f"{summary['status'].upper()}: production {production_seconds // 60}m {production_seconds % 60}s; "
    f"coupon {coupon_seconds // 60}m {coupon_seconds % 60}s"
)
raise SystemExit(0 if summary["status"] == "pass" else 1)
