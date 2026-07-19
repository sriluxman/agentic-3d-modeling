"""OpenSCAD as a first-class backend: parametric .scad -> STL -> STL pipeline.

Generalizes the per-model PowerShell scripts into one function so proven
community libraries (BOSL2, MCAD, SnapLib, JointSCAD, ...) plug straight into
the evidence loop: render with parameter overrides, then run the exported STL
through ``agentic-cad-stl`` checks, renders, and the slicer.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


def find_openscad() -> Path | None:
    found = shutil.which("openscad")
    if found:
        return Path(found)
    for base in (os.environ.get("ProgramFiles", "C:/Program Files"),
                 os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")):
        candidate = Path(base) / "OpenSCAD" / "openscad.exe"
        if candidate.exists():
            return candidate
    return None


def _define_args(defines: dict[str, Any] | None) -> list[str]:
    args: list[str] = []
    for name, value in (defines or {}).items():
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, (int, float)):
            rendered = repr(value)
        else:
            rendered = f'"{value}"'
        args += ["-D", f"{name}={rendered}"]
    return args


def render_scad(
    scad_path: Path,
    stl_path: Path,
    defines: dict[str, Any] | None = None,
    timeout_s: int = 300,
) -> dict[str, Any]:
    """Render a .scad file to STL with -D parameter overrides.

    Returns a status dict in the pipeline's pass/fail/not_run convention.
    """
    executable = find_openscad()
    if executable is None:
        return {"status": "not_run", "reason": "OpenSCAD executable not found"}
    stl_path.parent.mkdir(parents=True, exist_ok=True)
    command = [str(executable), "-o", str(stl_path), *_define_args(defines), str(scad_path)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_s, check=False)
    if completed.returncode != 0 or not stl_path.exists() or stl_path.stat().st_size == 0:
        return {
            "status": "fail",
            "return_code": completed.returncode,
            "reason": "OpenSCAD did not produce a non-empty STL",
            "log_tail": (completed.stdout + completed.stderr)[-2000:],
        }
    return {
        "status": "pass",
        "stl": str(stl_path),
        "defines": defines or {},
        "size_bytes": stl_path.stat().st_size,
    }
