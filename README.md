# Agentic Functional CAD

Reusable, agent-first tooling for generating functional CAD and rejecting bad geometry before printing.

## Current Loop

- build123d B-rep models in Python
- STEP and STL export
- B-rep validity, volume, solid-count, and dimension assertions
- FreeCAD headless STEP re-import and geometry verification
- Trimesh watertightness, winding, volume, body-count, and degeneracy checks
- six-axis print-orientation scoring
- sampled B-rep collision checks for declared assembly motion
- ElegooSlicer CLI pass using the installed ECC2 machine/process/material presets
- machine-readable JSON report with explicit `pass`, `fail`, and `not_run` states

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\scripts\run-python-cad.ps1
.\.venv\Scripts\python.exe -m pytest -q
```

Artifacts and `report.json` are written under `exports/python/<design>/`.

## Model Contract

A Python model exposes `build_design(profile) -> DesignSpec` and returns:

- named `PartSpec` objects with expected dimensions and body counts;
- declared parameters for traceability;
- optional `MotionSpec` paths for sampled interference checks.

Use `models/python/fit_calibration.py` as the compact reference implementation.

## Backends

Python/build123d is the primary mechanical CAD backend. OpenSCAD remains available for proven parametric libraries such as `models/library_cantilever_clip.scad`. FreeCAD command mode remains an interop and future FEM backend.

The third-party snap-fit library and design guide are retained under `docs/snapfit-know-hows/` with their CC Attribution-NonCommercial license.
