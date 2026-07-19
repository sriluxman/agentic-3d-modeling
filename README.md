# Agentic 3D Modeling

Small, practical workspace for agent-generated parametric 3D models.

## Current Toolchain

- OpenSCAD: `C:\Program Files\OpenSCAD\openscad.exe`
- FreeCAD command mode: `C:\Users\srilu\AppData\Local\Programs\FreeCAD 1.1\bin\freecadcmd.exe`
- Git: available on PATH

See `docs/agentic_cad_stack.md` for the agentic CAD architecture.

## First Project: Snap-Fit Coupon

The first model is a two-part FDM snap-fit test:

- `plug`: a base with a flexible cantilever tab and small hook.
- `socket`: a receiver block with a channel and retention window.
- `both`: preview layout with both parts side by side.

Print the plug and socket separately, then test how the plug slides and snaps into the socket.

Recommended first material: PETG if available. PLA can work, but flexing tabs may fatigue or snap sooner.

## Export

From PowerShell:

```powershell
.\scripts\export-openscad.ps1
```

This exports STL files into `exports\`.

Then run a basic geometry check:

```powershell
python .\scripts\check-stl.py .\exports\snapfit_plug.stl .\exports\snapfit_socket.stl
```

## Basic Iteration Loop

1. Change parameters in `models\snapfit_pair.scad`.
2. Export STL.
3. Slice and print.
4. Measure fit with calipers.
5. Record what happened.
6. Adjust `clearance`, `hook_height`, or `beam_thickness`.
