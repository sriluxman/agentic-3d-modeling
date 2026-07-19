# The Agentic Engineering Loop

Text-only CAD generation fails in predictable ways: geometry that is valid B-rep but unprintable, fits that are checked for collision but never for looseness, and "fixed" parameters that were never compared against alternatives. The platform closes those gaps with three capabilities.

## 1. Measure - evidence instead of assumption

Every claim about a design maps to a gate that produces `pass`, `fail`, or `not_run`:

| Claim | Gate | Module |
|---|---|---|
| "the solid is valid" | B-rep validity, volume, solid count, bbox | `evaluate.brep_checks` |
| "the mesh will slice" | watertight, winding, volume, degeneracy | `evaluate.mesh_checks` |
| "no hidden geometry corruption" | exact tri/tri self-intersection (transversal) | `integrity.self_intersections` |
| "walls are printable" | seeded ray-cast thickness vs `min_wall_mm` | `integrity.wall_thickness` |
| "the parts assemble" | sampled B-rep collision along declared path (translations, and rotations for twist-locks/bayonets) | `evaluate.motion_check` |
| "the fit is right" | measured mm gap in `[min, max]` band | `evaluate.clearance_check` |
| "the STEP survives interop" | FreeCAD headless round-trip | `freecad.validate_step` |
| "the slicer accepts it" | ElegooSlicer CLI + G-code metrics | `slicer.slice_stl` |

Design intent lives in the model as contracts (`PartSpec`, `MotionSpec`, `ClearanceSpec`), so a report is falsifiable: a check fails loudly rather than a shape merely looking plausible.

Notes on the integrity gates:

- Self-intersection flags *transversal* crossings (the kind that corrupt slicing). Shared-vertex adjacency, touching within tolerance, and coplanar overlaps are deliberately not flagged.
- Wall thickness is sampled (seeded, deterministic) and ray-based: it measures material depth along the inward normal. Parts with intentional thin webs declare `min_wall_mm` on the `PartSpec` instead of silencing the gate.

## 2. Perceive - the agent looks at its work

Numbers miss category errors (a wedge cut in the wrong place still has plausible volume). Each run emits:

- `<part>.views.svg` - four orthographic flat-shaded views, shared mm scale bar;
- `<part>.sections.svg` - mid-plane cross-sections that expose internal walls and fits;
- optional `<part>.views.png` / `.sections.png` via a local headless Edge/Chrome (`--png` or `enable_raster=True`) for direct multimodal inspection;
- `report.html` - a self-contained design review with renders inline and every check color-coded.

Workflow for an agent: after a run, read the PNGs. A misplaced boolean, a mirrored feature, or a missing cut is visible in one glance and invisible in a bbox tuple. (Real example: the cable clip's opening wedge was silently bbox-centered off-axis; the bounding-box gate flagged a 0.7 mm discrepancy and the top view showed the cut sitting inside the bore.)

## 3. Iterate - search the design space instead of guessing

Models accept `overrides` and validate the keys. `agentic-cad-study` turns that into a searchable space:

```
agentic-cad-study <model> --profile <profile> --set "wall_mm=1.2,1.6,2.0" \
    --set "grip_clearance_mm=0.1,0.2,0.4" --minimize total_volume_mm3
```

Per candidate it runs the fast gates (B-rep, mesh, integrity, motion, clearance - FreeCAD and slicer stay out of the inner loop), aggregates `total_volume_mm3`, `min_wall_mm`, `min_clearance_mm`, and lists exactly which checks failed. Feasible candidates are ranked against the declared objective; `study.md` is the human-readable table, `study.json` the machine-readable one.

This is the difference between "0.2 mm clearance worked once" and "0.1 mm fails the running-clearance demand, 0.4 mm rattles out of the band, 0.2 mm is the feasible optimum at every wall thickness."

## Evidence hierarchy

1. `fail` blocks. `not_run` is missing evidence, never success.
2. Automated pass -> print the smallest representative coupon -> physical measurement promotes the design (`physically_validated` in the component catalog).
3. The slicer and FreeCAD round-trip are release gates for the chosen design, not inner-loop costs.

## Interface library

Recurring real-world interfaces live in `agentic_cad.interfaces` as parametric generators rather than vendored meshes: reference geometry for verification (e.g. a Skadis board coupon), features to union into designs (seat bosses, slot cutters), and mating-part replicas for motion checks (the T-clip). A new project against a known interface starts from these instead of re-deriving dimensions; new interfaces (DIN rail, GoPro mounts, ...) follow the same pattern. Vendor reference files stay local-only evidence with provenance recorded in the module docstring.

## Module map

```
contracts.py    PartSpec / MotionSpec / ClearanceSpec / DesignSpec
runner.py       orchestrates one design run -> report.json + report.html
evaluate.py     B-rep, mesh, orientation, motion, clearance gates
integrity.py    self-intersection + wall thickness engines
render.py       SVG views + cross-sections
interfaces/     parametric real-world interfaces (skadis.py: slots, coupons, T-clip)
raster.py       headless-browser SVG -> PNG
htmlreport.py   self-contained design review
study.py        parameter sweeps, gating, ranking
freecad.py      STEP round-trip verification
slicer.py       ElegooSlicer CLI + G-code metrics
```
