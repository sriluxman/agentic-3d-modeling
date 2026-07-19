from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any

from build123d import export_step, export_stl

from .contracts import DesignSpec
from .evaluate import brep_checks, mesh_checks, motion_check
from .freecad import validate_step
from .profile import load_profile
from .slicer import slice_stl


def load_model(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("agentic_cad_user_model", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load CAD model from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(
    model_path: Path,
    profile_path: Path,
    output_root: Path,
    enable_slicer: bool = True,
) -> tuple[Path, dict[str, Any]]:
    profile = load_profile(profile_path)
    module = load_model(model_path)
    design: DesignSpec = module.build_design(profile)
    output_dir = output_root / design.name
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "schema_version": 1,
        "design": design.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_source": str(model_path),
        "printer_profile": str(profile_path),
        "parameters": design.parameters,
        "parts": [],
        "motion_checks": [],
        "unavailable_checks": [
            {"name": "mesh_self_intersection", "status": "not_run", "reason": "No robust local engine configured"},
            {"name": "minimum_wall_thickness", "status": "not_run", "reason": "No ray/voxel thickness engine configured"},
            {"name": "fea", "status": "not_run", "reason": "No load case or validated material model declared"},
        ],
    }

    statuses: list[str] = []
    for part in design.parts:
        step_path = output_dir / f"{part.name}.step"
        stl_path = output_dir / f"{part.name}.stl"
        export_step(part.shape, step_path)
        export_stl(part.shape, stl_path, tolerance=0.02, angular_tolerance=0.1)

        b_checks, b_metrics = brep_checks(part)
        m_checks, m_metrics = mesh_checks(stl_path, part)
        freecad_result = validate_step(step_path, output_dir / f"{part.name}.freecad.json", part)
        slicer_result = (
            slice_stl(stl_path, output_dir / "slicer" / part.name, profile)
            if enable_slicer
            else {"status": "not_run", "reason": "Disabled by caller"}
        )
        checks = b_checks + m_checks
        statuses.extend(item["status"] for item in checks)
        statuses.append(freecad_result["status"])
        statuses.append(slicer_result["status"])
        report["parts"].append(
            {
                "name": part.name,
                "artifacts": {"step": str(step_path), "stl": str(stl_path)},
                "checks": checks,
                "brep_metrics": b_metrics,
                "mesh_metrics": m_metrics,
                "freecad_step_roundtrip": freecad_result,
                "slicer": slicer_result,
            }
        )

    for motion in design.motions:
        result = motion_check(motion)
        statuses.append(result["status"])
        report["motion_checks"].append(result)

    report["status"] = "fail" if "fail" in statuses else "pass"
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report_path, report
