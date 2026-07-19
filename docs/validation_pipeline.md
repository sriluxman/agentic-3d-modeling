# Agentic CAD Validation Pipeline

Each design produces source geometry, exports, a validation report, and physical-test notes. A missing tool produces `not_run`, never a guessed pass.

## Gates

1. **CAD generation**: OpenSCAD now; build123d/CadQuery and FreeCAD B-rep models later.
2. **Exports**: STL now; STEP for B-rep designs; 3MF when the selected slicer workflow supports it.
3. **Design intent**: expected dimensions, mating clearance, collision-free assembled position, and insertion/removal path.
4. **Mesh integrity**: manifold edges and bounding box now; normals, duplicate faces, self-intersections, and thickness after adding Trimesh.
5. **Printability**: orientation, minimum wall, bridges, overhangs, supports, and estimated material.
6. **Slicer**: run a supported slicer CLI using an explicit printer/process/material profile.
7. **Engineering**: formula check for simple snap-fits; FEA only when loads, material data, and boundary conditions justify it.
8. **Agent report**: `pass`, `fail`, `warning`, or `not_run` for every gate, with actionable parameter changes.
9. **Physical calibration**: print, measure, photograph, and write results back to the profile and experiment log.

## Lightweight Rollout

- Stage A: OpenSCAD export, preview, STL manifold/bounds check, manual slicer review.
- Stage B: add Trimesh and automated assembly clearance/collision checks.
- Stage C: add build123d for STEP plus B-rep dimensions and interference checks.
- Stage D: connect whichever slicer is actually installed and export its profile.
- Stage E: add CalculiX/FreeCAD FEM only for a specific load case.

This order keeps the everyday loop fast on an 8 GB machine. Heavy tools are optional workers, not requirements for every model.

## Experiment 004

`models/library_cantilever_clip.scad` wraps the original library's `SnapY` module and follows its `ClipExample1` geometry. The source library, README, images, example STLs, license, and design-guide PDF live under `docs/snapfit-know-hows/`.

The clip and insert print separately and lie flat. The original visual test gauge is two loose crescents, so the wrapper joins them with a thin web inside the clip's empty circular cavity. The exterior mating contour and the library-generated cantilevers are unchanged. Insert the blue-preview key from the open jaw side; the two yellow cantilevers spread and then return around it. This is a calibration coupon, not yet the binder mechanism.
