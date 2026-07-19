# Agentic Functional CAD

Reusable, agent-first tooling for generating functional CAD and rejecting bad geometry before printing. The platform gives an agent three abilities a text-only loop lacks: **measurement** (evidence gates), **perception** (renders it can look at), and **iteration** (design-space search).

## Evidence gates

- build123d B-rep models in Python; STEP and STL export
- B-rep validity, volume, solid-count, and dimension assertions
- FreeCAD headless STEP re-import and geometry verification
- Trimesh watertightness, winding, volume, body-count, and degeneracy checks
- exact triangle/triangle **self-intersection** detection (KD-tree broadphase + Moller interval test)
- sampled ray-cast **minimum wall thickness** against the part's or profile's printable limit
- six-axis print-orientation scoring
- sampled B-rep collision checks for declared assembly motion, now with **measured clearance (mm)** at every sample and an optional demanded minimum
- **rotation sampling** in motion checks (`MotionSpec.rotations_deg` + `rotation_axis`) for twist-locks, bayonets, and keyed inserts
- static **clearance bands** (`ClearanceSpec`): a mating fit fails when it interferes, when the gap is below minimum, and when it is loose enough to rattle
- ElegooSlicer CLI pass using the installed ECC2 machine/process/material presets
- machine-readable JSON report with explicit `pass`, `fail`, and `not_run` states

## Perception

- four-view flat-shaded SVG render per part (isometric / front / top / right, shared mm scale bar)
- mid-plane cross-section SVGs exposing internal walls and fits
- optional PNG rasterization via a local headless Edge/Chrome (`--png`) so multimodal agents can look at parts directly
- self-contained `report.html` design review: renders inline, every check color-coded, motion clearance tables
- `annotate.html` per run: the user pins comments onto the views; exported `annotations.json` carries part, view, and mm offsets so the agent maps every remark to an exact model region (`agentic_cad.annotate.load_annotations`)

## Iteration

`agentic-cad-study` sweeps declared parameters over a grid, runs the fast gates (B-rep, mesh, integrity, motion, clearance) per candidate, and ranks the feasible ones against an objective:

```powershell
agentic-cad-study models/python/cable_clip.py --profile profiles/elegoo_cc2_pla.json `
  --set "wall_mm=1.2,1.6,2.0" --set "grip_clearance_mm=0.1,0.2,0.4" --minimize total_volume_mm3
```

The study writes `study.json` and a `study.md` table with per-case failed checks, and recommends the best feasible candidate. FreeCAD round-trip and slicing stay out of the inner loop; run them once on the chosen design.

## Design journey

The full idea-to-product workflow for non-CAD users (intake, 2D concepting, reuse, evidence, annotation, studies, release) is described in `docs/design_journey.md`. Clearances always come from the profile's physically measured calibration (`docs/sliding_fit_calibration.md`): 0.25 mm per side tight-sliding on this printer, cooled - 0.15 cannot insert. OpenSCAD libraries (BOSL2, SnapLib, ...) plug in via `agentic_cad.openscad.render_scad`.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\scripts\run-python-cad.ps1
.\.venv\Scripts\python.exe -m pytest -q
```

Single design: `agentic-cad models/python/cable_clip.py --profile profiles/elegoo_cc2_pla.json --png`. Artifacts, `report.json`, and `report.html` are written under `exports/python/<design>/`.

## Model Contract

A Python model exposes `build_design(profile, overrides=None) -> DesignSpec` and returns:

- named `PartSpec` objects with expected dimensions, body counts, and an optional `min_wall_mm` (coupons with intentional thin webs declare their own limit instead of silencing the gate);
- declared parameters for traceability; models validate override names and raise on unknown keys;
- optional `MotionSpec` paths for sampled interference checks, with `min_clearance_mm` when the motion must keep running clearance;
- optional `ClearanceSpec` bands for static mating fits (`min_mm`..`max_mm`).

Reference implementations: `models/python/fit_calibration.py` (clearance coupon), `models/python/cable_clip.py` (clearance band + demanded motion clearance + study-ready parameters; its rounded lips exist because the wall-thickness gate rejected the raw feather-edged cut - the loop working as intended), and `models/python/skadis_container.py` (multi-part assembly: sliding-lid container with IKEA Skadis T-clip mounting, twist-lock insertion verified with rotation sampling).

## Interface library

`agentic_cad.interfaces` holds parametric encodings of real-world mounting interfaces, starting with IKEA Skadis (`interfaces/skadis.py`): slot cutters, board coupons for verification, seat bosses to union into designs, and a T-clip replica dimensioned from the vendor reference (its stadium foot exists because the motion check caught the square-cornered foot colliding with the slot's rounded ends). Vendor files under `models/ikea/` stay local-only reference evidence and are not redistributed.

## Backends

Python/build123d is the primary mechanical CAD backend. OpenSCAD remains available for proven parametric libraries such as `models/library_cantilever_clip.scad`. FreeCAD command mode remains an interop and future FEM backend.

The third-party snap-fit library and design guide are retained under `docs/snapfit-know-hows/` with their CC Attribution-NonCommercial license.
