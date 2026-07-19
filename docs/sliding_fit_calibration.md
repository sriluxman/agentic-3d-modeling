# Sliding-Fit Calibration

Use this calibration whenever a printer, material, nozzle, layer height, line width, temperature, flow, or XY compensation changes.

## Coupon

- Source: `models/jointscad_dovetail_coupon.scad`
- Export and validate: `scripts/export-jointscad-dovetail.ps1`
- One dimple: 0.15 mm per side
- Two dimples: 0.25 mm per side
- Three dimples: 0.35 mm per side

## Procedure

1. Export and slice the coupon with the exact target printer, process, and material profile. Do not scale it.
2. Print the receiver rack and key together in their generated orientation.
3. Let both parts cool fully, remove them from the build plate, and bring them to room temperature.
4. Remove only loose strings. Do not sand, scrape, heat, or force the mating surfaces.
5. Test the same key in all receivers. Fully insert and remove it five times where possible.
6. Classify each candidate as `cannot_insert`, `press_fit`, `tight_sliding`, `free_sliding`, or `loose`.
7. Select the smallest clearance that completes repeated insertion without damaging force for the intended mechanism.
8. Record every candidate, the selected value, and `fully_cooled_off_build_plate` in the matching profile under `measured_calibration`.

Hot-on-bed testing may be recorded as an observation, but it must not replace the cooled result used by generated CAD.

## Current Result

For Elegoo PLA+ with the ECC2 0.4 mm nozzle and 0.20 mm Standard profile, the selected sliding clearance is 0.25 mm per side: 0.15 mm cannot insert, 0.25 mm is a tight fit, and 0.35 mm is slightly loose after cooling.
