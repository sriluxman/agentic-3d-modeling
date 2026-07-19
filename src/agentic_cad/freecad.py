from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .contracts import PartSpec


def _find_freecad() -> Path | None:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        return None
    candidates = sorted((Path(local_appdata) / "Programs").glob("FreeCAD */bin/freecadcmd.exe"), reverse=True)
    return candidates[0] if candidates else None


def validate_step(step_path: Path, report_path: Path, part: PartSpec) -> dict[str, Any]:
    executable = _find_freecad()
    if executable is None:
        return {"status": "not_run", "reason": "FreeCADCmd not found"}

    script = Path(__file__).resolve().parents[2] / "scripts" / "freecad_validate_step.py"
    completed = subprocess.run(
        [str(executable), str(script), str(step_path), str(report_path)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0 or not report_path.exists():
        return {
            "status": "fail",
            "reason": "FreeCAD failed to validate exported STEP",
            "return_code": completed.returncode,
            "log_tail": (completed.stdout + completed.stderr)[-2000:],
        }

    metrics = json.loads(report_path.read_text(encoding="utf-8"))
    bbox_ok = all(
        abs(actual - expected) <= part.bbox_tolerance_mm
        for actual, expected in zip(metrics["bounding_box_mm"], part.expected_bbox_mm)
    )
    checks = {
        "valid_shape": bool(metrics["is_valid"]),
        "solid_count": metrics["solid_count"] == part.expected_bodies,
        "positive_volume": metrics["volume_mm3"] > 0,
        "bounding_box": bbox_ok,
    }
    return {"status": "pass" if all(checks.values()) else "fail", "checks": checks, "metrics": metrics}
