# Agentic CAD Architecture

The platform is the product. Individual models are disposable fixtures unless they contribute a reusable primitive, calibration result, or regression test.

## Backend Selection

- **build123d**: default for mechanical parts, STEP, B-rep checks, assemblies, and motion envelopes.
- **OpenSCAD**: compact parametric objects and licensed/proven libraries.
- **FreeCADCmd**: format interop, repair, and later CalculiX/FreeCAD FEM.
- **Trimesh**: mesh topology, metrics, and orientation evaluation.
- **ElegooSlicer CLI**: actual ECC2 slicing with installed presets and G-code metrics.

Every backend must end at the same report contract. A missing evaluator reports `not_run`; it never silently passes.

## Reusable Assets

- `src/agentic_cad/`: contracts, evaluators, runner, profile loader, slicer adapter.
- `profiles/`: machine/process/material facts and measured calibration.
- `models/python/`: small model sources implementing the common contract.
- `docs/snapfit-know-hows/`: licensed source knowledge and reusable OpenSCAD primitives.
- `tests/`: pipeline regressions.

## Near-Term Evaluators

1. Robust self-intersection detection.
2. Minimum wall/thickness sampling.
3. Bridge and support-volume estimation from slicer output.
4. Build-volume and toolpath sanity checks.
5. FEA only when a design declares loads, constraints, and material data.
