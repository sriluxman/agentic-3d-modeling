# Calculated Cantilever Latch Test Log

## Formula

The first design uses:

`h = 1.09 * eps * l^2 / y`

where `eps = 0.018`, `l = 26 mm`, and `y = 3.4 mm`.

## Print Setup

- Printer:
- Filament:
- Nozzle:
- Layer height:
- Wall count:
- Infill:
- Orientation:

## Result

- Arm flexes without whitening/cracking:
- Slides into striker:
- Hook catches:
- Releases by lifting/pressing:
- Too tight:
- Too loose:
- Broke at root:
- Broke at hook:

## Tuning

- If too stiff: reduce `target_deflection` or increase `arm_length`.
- If too loose: reduce `clearance` or increase `hook_height`.
- If root breaks: increase `arm_length`, reduce `target_deflection`, or use PETG.
- If hook catches too aggressively: reduce `hook_height`.

