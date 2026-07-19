import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
export_dir = ROOT / "exports" / "skadis-micro-cassette"
parts = ["cassette-body", "cassette-lid", "cassette-divider", "cassette-latch"]


def seconds(value: str) -> int:
    units = {"h": 3600, "m": 60, "s": 1}
    return sum(int(number) * units[unit] for number, unit in re.findall(r"(\d+)([hms])", value))


reports = {
    part: json.loads((export_dir / f"{part}-evaluation" / "report.json").read_text())
    for part in parts
}
total_seconds = sum(seconds(report["slicer"]["metrics"]["estimated_time"]) for report in reports.values())
summary = {
    "schema_version": 1,
    "status": "pass" if total_seconds <= 3600 else "fail",
    "production_parts": parts,
    "estimated_time_seconds": total_seconds,
    "target_time_seconds": 3600,
    "all_parts_passed": all(report["status"] == "pass" for report in reports.values()),
    "supports_enabled": any(report["slicer"]["metrics"]["supports_enabled"] for report in reports.values()),
}
summary["status"] = "pass" if summary["status"] == "pass" and summary["all_parts_passed"] else "fail"
output = export_dir / "cassette-report.json"
output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(f"{summary['status'].upper()}: {total_seconds // 60}m {total_seconds % 60}s production estimate")
raise SystemExit(0 if summary["status"] == "pass" else 1)
