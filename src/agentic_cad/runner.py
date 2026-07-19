from __future__ import annotations

import importlib.util
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any

from build123d import export_step, export_stl

from .contracts import DesignSpec
from .evaluate import brep_checks, clearance_check, mesh_checks, motion_check
from .freecad import validate_step
from .htmlreport import write_html_report
from .integrity import integrity_checks, load_mesh
from .profile import load_profile
from .raster import rasterize_svg
from .render import render_sections_svg, render_views_svg
from .slicer import slice_stl


def load_model(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("agentic_cad_user_model", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load CAD model from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_design(module: ModuleType, profile: dict[str, Any], overrides: dict[str, Any] | None = None) -> DesignSpec:
    """Call the model's build_design, passing overrides when it accepts them."""
    signature = inspect.signature(module.build_design)
    if "overrides" in signature.parameters:
        return module.build_design(profile, overrides=overrides or {})
    if overrides:
        raise TypeError("Model does not accept parameter overrides; add an 'overrides' argument to build_design")
    return module.build_design(profile)


def default_min_wall_mm(profile: dict[str, Any]) -> float:
    return 2.0 * float(profile["printer"]["nozzle_diameter_mm"])


def run(
    model_path: Path,
    profile_path: Path,
    output_root: Path,
    enable_slicer: bool = True,
    enable_render: bool = True,
    enable_freecad: bool = True,
    enable_raster: bool = False,
    overrides: dict[str, Any] | None = None,
) -> tuple[Path, dict[str, Any]]:
    profile = load_profile(profile_path)
    module = load_model(model_path)
    design: DesignSpec = build_design(module, profile, overrides)
    output_dir = output_root / design.name
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "schema_version": 2,
        "design": design.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_source": str(model_path),
        "printer_profile": str(profile_path),
        "parameters": design.parameters,
        "overrides": overrides or {},
        "parts": [],
        "motion_checks": [],
        "clearance_checks": [],
        "unavailable_checks": [
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
        mesh = load_mesh(stl_path)
        min_wall = part.min_wall_mm if part.min_wall_mm is not None else default_min_wall_mm(profile)
        i_checks, i_metrics = integrity_checks(mesh, min_wall)
        freecad_result = (
            validate_step(step_path, output_dir / f"{part.name}.freecad.json", part)
            if enable_freecad
            else {"status": "not_run", "reason": "Disabled by caller"}
        )
        slicer_result = (
            slice_stl(stl_path, output_dir / "slicer" / part.name, profile)
            if enable_slicer
            else {"status": "not_run", "reason": "Disabled by caller"}
        )
        renders: dict[str, Any] = {}
        if enable_render:
            renders["views"] = render_views_svg(mesh, output_dir / f"{part.name}.views.svg", part.name)
            sections = render_sections_svg(mesh, output_dir / f"{part.name}.sections.svg", part.name)
            if sections is not None:
                renders["sections"] = sections
            if enable_raster:
                for render in renders.values():
                    png = rasterize_svg(Path(render["path"]))
                    if png is not None:
                        render["png"] = str(png)

        checks = b_checks + m_checks + i_checks
        statuses.extend(item["status"] for item in checks)
        statuses.append(freecad_result["status"])
        statuses.append(slicer_result["status"])
        report["parts"].append(
            {
                "name": part.name,
                "artifacts": {"step": str(step_path), "stl": str(stl_path)},
                "renders": renders,
                "checks": checks,
                "brep_metrics": b_metrics,
                "mesh_metrics": m_metrics,
                "integrity_metrics": i_metrics,
                "freecad_step_roundtrip": freecad_result,
                "slicer": slicer_result,
            }
        )

    for motion in design.motions:
        result = motion_check(motion)
        statuses.append(result["status"])
        report["motion_checks"].append(result)

    for clearance in design.clearances:
        result = clearance_check(clearance)
        statuses.append(result["status"])
        report["clearance_checks"].append(result)

    report["status"] = "fail" if "fail" in statuses else "pass"
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if enable_render:
        report["html_report"] = str(write_html_report(report, output_dir))
    return report_path, report
