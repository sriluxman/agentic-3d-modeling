# The Design Journey: idea -> design -> product

The platform's user is not a CAD expert. Their journey, and what the platform provides at each step:

## 1. Intake: text, reference files, images

The user brings a description, community STLs/STEPs to remix, or photos. First action is always to **measure the references with the platform's own tools** (trimesh bounds/sections, STEP import, `render_views_svg` + `rasterize_svg` to *look* at them). Reference dimensions become named constants with provenance comments - never guesses. Vendor files stay local-only with license noted.

## 2. Concept: cheap 2D before expensive 3D

Iterate direction with the user on **2D SVG sketches** (silhouettes, labeled dimensions, arrows) - written directly by the agent, no geometry kernel involved, near-zero token cost per revision, instantly viewable. Only when the user confirms direction does B-rep work start. The run renders (views/sections SVG-PNG) continue this: every iteration produces images the user can react to.

## 3. Reuse: proven concepts first

Search `components/catalog.json` (`agentic-cad-components`), the `agentic_cad.interfaces` library (Skadis today; each new project's interface work gets generalized back into it), and community parametric libraries. `agentic_cad.openscad.render_scad` turns any BOSL2/MCAD/SnapLib part into an STL that flows through the same checks, renders, and slicer (`agentic-cad-stl`).

## 4. Parametric 3D with evidence

Build the design as a model with `overrides`, contracts (`PartSpec`, `MotionSpec`, `ClearanceSpec`, `DesignCheckSpec`), and profile-driven clearances - **always** `measured_calibration.xy_clearance_sliding_mm`, never hardcoded fits (0.15/side cannot insert on this printer; 0.25 is the measured tight-sliding fit). Run `agentic-cad <model> --png`, read the report and the renders.

## 5. Annotation: the user points, the agent acts

Every rendered run emits **`annotate.html`**: the user clicks pins onto the orthographic views and writes notes; export produces `annotations.json` where each pin carries the part, the view, and the **mm offset from the view center**. The agent reads it with `agentic_cad.annotate.load_annotations` and maps every comment to an exact model region - no more "the thing on the left side". Iterate steps 4-5 until the user is satisfied.

## 6. Uncertain parameters: study, don't guess

`agentic-cad-study` sweeps the open parameters, rejects infeasible candidates with named failing checks, and recommends against an objective.

## 7. Release: full gates, print, calibrate back

FreeCAD round-trip + slicer on the final design, print the smallest coupon first, and write physical results back into the profile (`docs/sliding_fit_calibration.md` procedure) so the next design starts from measured truth.
