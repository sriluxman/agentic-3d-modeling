from __future__ import annotations

import importlib.util
import json
import sys
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
    resolved = path.resolve()
    module_name = f"agentic_cad_user_model_{path.stem}_{abs(hash(resolved))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load CAD model from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
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
        "design_checks": [],
        "unavailable_checks": [
            {"name": "mesh_self_intersection", "status": "not_run", "reason": "No robust local engine configured"},
            {"name": "minimum_wall_thickness", "status": "not_run", "reason": "No ray/voxel thickness engine configured"},
            {"name": "fea", "status": "not_run", "reason": "No load case or validated material model declared"},
        ],
    }

    statuses: list[str] = []
    for design_check in design.checks:
        result: dict[str, Any] = {
            "name": design_check.name,
            "status": "pass" if design_check.passed else "fail",
        }
        if design_check.measured is not None:
            result["measured"] = design_check.measured
        if design_check.expected is not None:
            result["expected"] = design_check.expected
        statuses.append(result["status"])
        report["design_checks"].append(result)

    for part in design.parts:
        step_path = output_dir / f"{part.name}.step"
        stl_path = output_dir / f"{part.name}.stl"
        assembly_stl_path = output_dir / f"{part.name}_assembly.stl"
        export_step(part.shape, step_path)
        print_shape = part.print_shape if part.print_shape is not None else part.shape
        export_stl(print_shape, stl_path, tolerance=0.02, angular_tolerance=0.1)
        if part.print_shape is not None:
            export_stl(part.shape, assembly_stl_path, tolerance=0.02, angular_tolerance=0.1)

        b_checks, b_metrics = brep_checks(part)
        m_checks, m_metrics = mesh_checks(stl_path, part)
        freecad_result = validate_step(step_path, output_dir / f"{part.name}.freecad.json", part)
        slicer_result = (
            slice_stl(
                stl_path,
                output_dir / "slicer" / part.name,
                profile,
                process_preset_project_relative=part.slicer_process_preset_project_relative,
            )
            if enable_slicer
            else {"status": "not_run", "reason": "Disabled by caller"}
        )
        checks = b_checks + m_checks
        statuses.extend(item["status"] for item in checks)
        statuses.append(freecad_result["status"])
        statuses.append(slicer_result["status"])
        artifacts = {"step": str(step_path), "stl": str(stl_path)}
        if part.print_shape is not None:
            artifacts["assembly_stl"] = str(assembly_stl_path)
        report["parts"].append(
            {
                "name": part.name,
                "artifacts": artifacts,
                "print_orientation": "custom" if part.print_shape is not None else "cad_default",
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
