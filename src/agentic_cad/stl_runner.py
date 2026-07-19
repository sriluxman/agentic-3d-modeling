from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import trimesh

from .profile import load_profile
from .slicer import slice_stl


def evaluate_stl(
    stl_path: Path,
    profile_path: Path,
    output_dir: Path,
    *,
    expected_bodies: int = 1,
    enable_slicer: bool = True,
) -> tuple[Path, dict[str, Any]]:
    profile = load_profile(profile_path)
    loaded = trimesh.load_mesh(stl_path, force="mesh", process=True, validate=True)
    if not isinstance(loaded, trimesh.Trimesh):
        raise TypeError(f"Expected one Trimesh from {stl_path}")

    extents = [float(value) for value in loaded.bounding_box.extents]
    nondegenerate = bool(np.all(loaded.nondegenerate_faces()))
    checks = [
        {"name": "mesh_watertight", "status": "pass" if loaded.is_watertight else "fail"},
        {"name": "winding_consistent", "status": "pass" if loaded.is_winding_consistent else "fail"},
        {"name": "mesh_is_volume", "status": "pass" if loaded.is_volume else "fail"},
        {
            "name": "mesh_body_count",
            "status": "pass" if loaded.body_count == expected_bodies else "fail",
            "measured": int(loaded.body_count),
            "expected": expected_bodies,
        },
        {"name": "nondegenerate_faces", "status": "pass" if nondegenerate else "fail"},
        {
            "name": "printer_envelope",
            "status": "pass" if all(value > 0 for value in extents) else "fail",
            "measured_bbox_mm": extents,
        },
    ]
    slicer = (
        slice_stl(stl_path, output_dir / "slicer", profile)
        if enable_slicer
        else {"status": "not_run", "reason": "Disabled by caller"}
    )
    statuses = [check["status"] for check in checks] + [slicer["status"]]
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_stl": str(stl_path),
        "printer_profile": str(profile_path),
        "checks": checks,
        "metrics": {
            "triangles": len(loaded.faces),
            "body_count": int(loaded.body_count),
            "bounding_box_mm": extents,
            "surface_area_mm2": float(loaded.area),
            "volume_mm3": float(loaded.volume),
        },
        "slicer": slicer,
        "status": "fail" if "fail" in statuses else "pass",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report_path, report
