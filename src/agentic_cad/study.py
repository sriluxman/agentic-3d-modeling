"""Design-space studies: sweep model parameters, gate, and rank candidates.

This closes the agentic loop. A model that accepts ``overrides`` becomes a
searchable design space: the study runs the fast evidence gates (B-rep, mesh,
integrity, motion, clearance) for every parameter combination, keeps the
feasible candidates, and ranks them against a declared objective. FreeCAD
round-trip and slicing stay out of the inner loop - they are release
verification, run once on the chosen design.
"""

from __future__ import annotations

import argparse
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .runner import run


def parse_value(text: str) -> Any:
    lowered = text.strip().lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    for kind in (int, float):
        try:
            return kind(text)
        except ValueError:
            continue
    return text.strip()


def parse_grid(assignments: list[str]) -> dict[str, list[Any]]:
    grid: dict[str, list[Any]] = {}
    for assignment in assignments:
        name, _, values = assignment.partition("=")
        if not name or not values:
            raise ValueError(f"Expected name=v1,v2,... got: {assignment}")
        grid[name.strip()] = [parse_value(item) for item in values.split(",")]
    return grid


def _failed_checks(report: dict[str, Any]) -> list[str]:
    failed: list[str] = []
    for part in report.get("parts", []):
        failed.extend(
            f"{part['name']}:{item['name']}" for item in part["checks"] if item["status"] == "fail"
        )
        for gate in ("freecad_step_roundtrip", "slicer"):
            if part.get(gate, {}).get("status") == "fail":
                failed.append(f"{part['name']}:{gate}")
    for section in ("motion_checks", "clearance_checks"):
        failed.extend(item["name"] for item in report.get(section, []) if item["status"] == "fail")
    return failed


def _aggregate(report: dict[str, Any]) -> dict[str, Any]:
    volumes = [part["brep_metrics"]["volume_mm3"] for part in report.get("parts", [])]
    walls = [
        part["integrity_metrics"]["wall_thickness"].get("minimum_measured_mm")
        for part in report.get("parts", [])
    ]
    walls = [value for value in walls if value is not None]
    clearances = [
        motion.get("minimum_clearance_mm") for motion in report.get("motion_checks", [])
    ] + [item.get("measured_gap_mm") for item in report.get("clearance_checks", [])]
    clearances = [value for value in clearances if value is not None]
    return {
        "total_volume_mm3": sum(volumes) if volumes else None,
        "min_wall_mm": min(walls) if walls else None,
        "min_clearance_mm": min(clearances) if clearances else None,
    }


def run_study(
    model_path: Path,
    profile_path: Path,
    output_root: Path,
    grid: dict[str, list[Any]],
    minimize: str | None = None,
    maximize: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    if minimize and maximize:
        raise ValueError("Declare one objective: minimize or maximize")
    objective_key = minimize or maximize
    names = list(grid)
    combos = [dict(zip(names, values)) for values in itertools.product(*grid.values())]

    output_root.mkdir(parents=True, exist_ok=True)
    cases: list[dict[str, Any]] = []
    for index, overrides in enumerate(combos):
        case_id = f"case_{index:03d}"
        _, report = run(
            model_path,
            profile_path,
            output_root / case_id,
            enable_slicer=False,
            enable_render=False,
            enable_freecad=False,
            overrides=overrides,
        )
        aggregate = _aggregate(report)
        cases.append(
            {
                "case": case_id,
                "overrides": overrides,
                "status": report["status"],
                "failed_checks": _failed_checks(report),
                **aggregate,
                "report": str(output_root / case_id / report["design"] / "report.json"),
            }
        )

    feasible = [case for case in cases if case["status"] == "pass"]
    best = None
    if objective_key and feasible:
        scored = [case for case in feasible if case.get(objective_key) is not None]
        if scored:
            best = (min if minimize else max)(scored, key=lambda case: case[objective_key])
    elif feasible:
        best = feasible[0]

    study = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_source": str(model_path),
        "printer_profile": str(profile_path),
        "grid": grid,
        "objective": {"minimize": minimize, "maximize": maximize},
        "cases": cases,
        "feasible_count": len(feasible),
        "recommended": best,
    }
    study_path = output_root / "study.json"
    study_path.write_text(json.dumps(study, indent=2) + "\n", encoding="utf-8")
    _write_markdown(study, output_root / "study.md", names)
    return study_path, study


def _write_markdown(study: dict[str, Any], path: Path, parameter_names: list[str]) -> None:
    metric_names = ["status", "total_volume_mm3", "min_wall_mm", "min_clearance_mm"]
    header = ["case", *parameter_names, *metric_names, "failed checks"]
    lines = [
        f"# Design study: {Path(study['model_source']).stem}",
        "",
        f"- generated: {study['generated_at']}",
        f"- objective: {study['objective']}",
        f"- feasible: {study['feasible_count']} / {len(study['cases'])}",
        "",
        "| " + " | ".join(header) + " |",
        "|" + "---|" * len(header),
    ]
    for case in study["cases"]:
        row = [case["case"]]
        row += [str(case["overrides"].get(name, "")) for name in parameter_names]
        for metric in metric_names:
            value = case.get(metric)
            row.append(f"{value:.4g}" if isinstance(value, float) else str(value))
        row.append(", ".join(case["failed_checks"]) or "-")
        lines.append("| " + " | ".join(row) + " |")
    recommended = study.get("recommended")
    lines += [
        "",
        (
            f"**Recommended:** `{recommended['case']}` with `{recommended['overrides']}`"
            if recommended
            else "**Recommended:** none - no feasible candidate"
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sweep a model's design space and rank candidates")
    parser.add_argument("model", type=Path)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("exports/studies"))
    parser.add_argument(
        "--set",
        dest="assignments",
        action="append",
        default=[],
        metavar="NAME=V1,V2,...",
        help="Parameter values to sweep; repeat for a grid",
    )
    parser.add_argument("--minimize", choices=["total_volume_mm3", "min_wall_mm", "min_clearance_mm"])
    parser.add_argument("--maximize", choices=["total_volume_mm3", "min_wall_mm", "min_clearance_mm"])
    args = parser.parse_args()
    if not args.assignments:
        parser.error("Declare at least one --set NAME=V1,V2,...")

    study_path, study = run_study(
        args.model,
        args.profile,
        args.output / args.model.stem,
        parse_grid(args.assignments),
        minimize=args.minimize,
        maximize=args.maximize,
    )
    recommended = study["recommended"]
    print(f"feasible {study['feasible_count']}/{len(study['cases'])}: {study_path}")
    if recommended:
        print(f"recommended: {recommended['case']} {recommended['overrides']}")
        return 0
    print("recommended: none")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
