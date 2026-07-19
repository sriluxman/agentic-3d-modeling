# Agentic CAD Validation Pipeline

Each design produces source geometry, exports, a validation report, and physical-test notes. A missing tool produces `not_run`, never a guessed pass.

## Gates

1. **CAD generation**: build123d B-rep by default; OpenSCAD and FreeCAD adapters where appropriate.
2. **Exports**: STEP and STL for Python CAD, followed by a FreeCAD headless STEP round-trip; 3MF when a backend provides a reliable writer.
3. **Design intent**: expected dimensions, body counts, mating clearance, collision-free assembled position, and insertion/removal path.
4. **Mesh integrity**: watertightness, winding, volume, body count, and degeneracy through Trimesh.
5. **Printability**: six-axis orientation scoring and overhang area now; thickness and bridge analysis next.
6. **Slicer**: ElegooSlicer CLI with the installed ECC2 machine, process, and filament presets; parse G-code metrics.
7. **Engineering**: formula check for simple snap-fits; FEA only when loads, material data, and boundary conditions justify it.
8. **Agent report**: `pass`, `fail`, `warning`, or `not_run` for every gate, with actionable parameter changes.
9. **Physical calibration**: print, cool, measure, and write results back to the profile using the reusable [sliding-fit calibration](sliding_fit_calibration.md) where applicable.

Assembly orientation and print orientation are separate concerns. Thin covers should place their largest uninterrupted face on the bed; generated G-code must confirm the declared temperatures, supports, and any required brim instead of trusting preset names.

The current implementation lives in `src/agentic_cad/`. Heavy evaluators remain optional workers so the normal loop stays practical on an 8 GB machine.
