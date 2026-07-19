---
name: engineer-functional-cad
description: Reuse, generate, and autonomously validate functional 3D-printable CAD. Use for mechanisms, snap-fits, joints, enclosures, brackets, calibration models, or assemblies built with build123d, OpenSCAD, FreeCAD, STEP, or STL, especially when selecting existing parametric components before creating geometry.
---

# Engineer Functional CAD

Build functional models through a reuse-first engineering loop. Treat a printable shape as unfinished until its interfaces, motion, geometry, and slicer behavior have evidence.

## Workflow

1. Read the printer profile, nearby model contracts, and validation report format.
2. Translate the request into interfaces and constraints: mating geometry, motion direction, retention, release method, loads, material, orientation, clearance, and print envelope.
3. Pass the reuse gate before writing geometry. Search `components/catalog.json` with `agentic-cad-components`, using mechanism names and `--engine`, `--category`, or `--interface` filters.
4. Prefer a physically validated local component. Next prefer an automatically validated component, then local parametric source, then an indexed remote library.
5. When no candidate fits, search upstream repositories and official documentation for a parametric mechanism. Add useful findings to the catalog before implementing them. Do not default to an uneditable mesh when parametric source or paired mating geometry exists.
6. Select the lightest suitable backend:
   - Use build123d for new precise B-rep models, assemblies, STEP output, and Python automation.
   - Use OpenSCAD when a proven library already implements the mechanism or the design is naturally constructive and parameter-driven.
   - Use FreeCAD for STEP interoperability, visual inspection, and FEM when structural evidence is justified.
7. Adapt the selected component minimally. Preserve its source URL, attribution, version, parameters, and license metadata. Experimental use does not remove provenance obligations; do not assume redistribution or commercial permission.
8. Define each printable body as a `PartSpec` (declare `min_wall_mm` only for intentional thin webs). Define every insertion, sliding, rotation, or assembly path as a `MotionSpec` - a static non-collision check cannot prove assembly - and set `min_clearance_mm` when the motion must keep running clearance. Declare every static mating fit as a `ClearanceSpec` band: interference fails, and so does a gap loose enough to rattle. Accept an `overrides` dict in `build_design` and reject unknown keys.
9. Run `agentic-cad <model> --profile profiles/elegoo_cc2_pla.json --output <directory> --png`. Treat `fail` as blocking and `not_run` as missing evidence, not success.
10. Look at the evidence, not just the numbers: open the generated `<part>.views.png` and `<part>.sections.png` (or the SVGs / `report.html`). A misplaced boolean or mirrored feature is visible in one glance and invisible in a bounding-box tuple. Then inspect STEP and STL checks, self-intersection and wall-thickness results, measured clearances, collision samples, orientation, and the slicer pass.
11. When a parameter is uncertain (wall, clearance, opening angle), do not guess-and-pray: run `agentic-cad-study <model> --profile <profile> --set "name=v1,v2,..." --minimize total_volume_mm3` and take the recommended feasible candidate. Read `study.md` for exactly which checks rejected each alternative.
12. When the user gives feedback, hand them the run's `annotate.html`: their exported `annotations.json` pins map each comment to a part, view, and mm offset - load it with `agentic_cad.annotate.load_annotations` and fix exactly what was pointed at. Revise geometry and rerun until the report passes; the run report (`report.json`, `report.html`) is the deliverable alongside the model source.
13. Print the smallest representative coupon first. Record measured clearance, failure mode, material, orientation, and profile. Promote a component to `physically_validated` only after a real print succeeds.

## Reuse Decisions

Read [references/component-sourcing.md](references/component-sourcing.md) when choosing, adding, or promoting a component. Keep remote packages indexed rather than vendoring whole libraries; import only the selected source and required dependencies when a model uses it.

Reject a candidate when its interface does not match, parameters cannot express the required envelope, mating geometry is absent, the print orientation conflicts with the load path, or its source cannot be traced. Explain the rejection in the design report, then evaluate the next candidate.
