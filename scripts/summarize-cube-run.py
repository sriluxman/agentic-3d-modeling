import json
import re
import zipfile
from pathlib import Path

import trimesh


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "exports" / "india-austria-dovetail-cube"
PARTS = ["india-half", "austria-half"]
EXPECTED_3MF_JOBS = {
    "india-multicolor.3mf": {"india-green", "india-white", "india-saffron"},
    "austria-multicolor.3mf": {"austria-red-bottom", "austria-white", "austria-red-top"},
}


def seconds(value: str) -> int:
    units = {"h": 3600, "m": 60, "s": 1}
    return sum(int(number) * units[unit] for number, unit in re.findall(r"(\d+)([hms])", value))


reports = {
    part: json.loads((EXPORT_DIR / f"{part}-evaluation" / "report.json").read_text())
    for part in PARTS
}
production_seconds = sum(
    seconds(reports[part]["slicer"]["metrics"]["estimated_time"]) for part in PARTS
)

collision_path = EXPORT_DIR / "assembly-collision.stl"
collision = trimesh.load_mesh(collision_path, force="mesh", process=True)
collision_volume = 0.0 if min(collision.extents) <= 1e-9 else abs(float(collision.volume))

job_objects = {}
for file_name in EXPECTED_3MF_JOBS:
    with zipfile.ZipFile(EXPORT_DIR / file_name) as archive:
        model_path = next(name for name in archive.namelist() if name.lower().endswith(".model"))
        model_xml = archive.read(model_path).decode("utf-8")
    job_objects[file_name] = set(re.findall(r'<object[^>]+name="([^"]+)"', model_xml))

all_parts_passed = all(report["status"] == "pass" for report in reports.values())
summary = {
    "schema_version": 1,
    "status": "pass" if all_parts_passed and collision_volume <= 0.01 and job_objects == EXPECTED_3MF_JOBS else "fail",
    "connector": "vertical_jointscad_dovetail",
    "clearance_mm_per_side": 0.25,
    "production_estimated_time_seconds": production_seconds,
    "all_parts_passed": all_parts_passed,
    "assembly_collision_volume_mm3": collision_volume,
    "multicolor_jobs": {name: sorted(objects) for name, objects in job_objects.items()},
}
(EXPORT_DIR / "cube-report.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(f"{summary['status'].upper()}: production {production_seconds // 60}m {production_seconds % 60}s")
raise SystemExit(0 if summary["status"] == "pass" else 1)
