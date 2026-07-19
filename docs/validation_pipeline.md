# Agentic CAD Validation Pipeline

Each design produces source geometry, exports, a validation report, and physical-test notes. A missing tool produces `not_run`, never a guessed pass.

## Gates

1. **CAD generation**: build123d B-rep by default; OpenSCAD and FreeCAD adapters where appropriate.
2. **Exports**: STEP and STL for Python CAD, followed by a FreeCAD headless STEP round-trip; 3MF when a backend provides a reliable writer.
3. **Design intent**: expected dimensions, body counts, mating clearance bands (`ClearanceSpec`, min and max gap), collision-free assembled position, and insertion/removal path with measured per-sample clearance (`MotionSpec.min_clearance_mm`).
4. **Mesh integrity**: watertightness, winding, volume, body count, and degeneracy through Trimesh; exact transversal self-intersection detection (KD-tree broadphase + Moller interval test).
5. **Printability**: six-axis orientation scoring and overhang area; seeded ray-cast minimum wall thickness against `PartSpec.min_wall_mm` or the profile's 2x-nozzle default; bridge analysis next.
6. **Visual evidence**: four-view SVG render and mid-plane cross-sections per part; optional headless-browser PNG rasterization; self-contained `report.html` design review.
7. **Slicer**: ElegooSlicer CLI with the installed ECC2 machine, process, and filament presets; parse G-code metrics.
8. **Engineering**: formula check for simple snap-fits; FEA only when loads, material data, and boundary conditions justify it.
9. **Iteration**: `agentic-cad-study` grid sweeps over model overrides with fast gates, aggregate metrics, per-case failure lists, and objective-ranked recommendation (see `docs/agentic_loop.md`).
10. **Agent report**: `pass`, `fail`, `warning`, or `not_run` for every gate, with actionable parameter changes.
11. **Physical calibration**: print, measure, photograph, and write results back to the profile and experiment log.

The current implementation lives in `src/agentic_cad/`. Heavy evaluators remain optional workers so the normal loop stays practical on an 8 GB machine.
