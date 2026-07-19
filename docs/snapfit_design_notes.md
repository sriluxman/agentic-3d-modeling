# Snap-Fit Design Notes

These notes summarize the local references in `docs/snapfit-know-hows/`.

## Main Lessons

- A snap-fit is an assembly path plus a temporary deflection, not just a hook and hole.
- The hook/undercut must have a clear insertion path and a clear release path if the joint is meant to be removable.
- For cantilever snaps, the root is the vulnerable section.
- Avoid sharp transitions at the cantilever root. Add relief, radius, or a thicker root pad.
- Tapered cantilever arms are better than constant-thickness arms because they distribute strain more evenly.
- The guide recommends tapering thickness toward the hook; one example reduces end thickness to about half the root thickness.
- For repeated snap/release, use a lower allowable strain than for one-time assembly.
- For FDM prototypes, start with conservative undercuts and generous clearance.

## Formula Used In Experiment 003

For a tapered cantilever snap-fit arm:

`h = 1.09 * eps * l^2 / y`

where:

- `h` is root thickness.
- `eps` is allowable strain as a decimal.
- `l` is free arm length.
- `y` is required deflection, often related to the undercut.

Experiment 003 uses:

- `eps = 0.018`
- `l = 26 mm`
- `y = 3.4 mm`
- `safety_factor = 1.35`

## Material Starting Points

For hobby FDM, treat these as test starting points, not final engineering values:

- PLA: stiff and easy to print, but brittle. Use conservative deflection.
- PETG: better first choice for snap-fit experiments because it tolerates flex better.
- ABS/ASA: useful later, but printer/environment requirements are higher.

## FDM Print Guidance

- Print cantilever arms lying in the XY plane when possible.
- Avoid snap arms that depend on layer adhesion in tension.
- Use enough perimeters/walls so thin snap arms are not sparse infill.
- Keep first experiments small and parametric.
- Tune by changing one variable at a time: clearance, undercut/hook height, arm length, arm thickness.

## Licensing Note

The included third-party Simple Snap-Fit Joints Library is Creative Commons Attribution Non-Commercial. Treat it as reference material unless the project is intentionally non-commercial or the licensing is changed/cleared.

