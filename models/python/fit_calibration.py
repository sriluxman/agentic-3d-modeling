from __future__ import annotations

from typing import Any

from build123d import Align, Axis, Box, Cylinder, Pos

from agentic_cad.contracts import DesignSpec, MotionSpec, PartSpec

DEFAULTS: dict[str, Any] = {
    "pin_diameter_mm": 5.0,
    "plate_thickness_mm": 4.0,
}


def build_design(profile: dict, overrides: dict[str, Any] | None = None) -> DesignSpec:
    parameters = dict(DEFAULTS)
    unknown = set(overrides or {}) - set(parameters)
    if unknown:
        raise KeyError(f"Unknown override(s) {sorted(unknown)}; supported: {sorted(parameters)}")
    parameters.update(overrides or {})
    pin_diameter = parameters["pin_diameter_mm"]
    thickness = parameters["plate_thickness_mm"]

    clearances = (0.10, 0.20, 0.30, 0.40, 0.50)
    x_positions = (-12.0, -6.0, 0.0, 6.0, 12.0)

    plate = Box(36, 14, thickness, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for x, clearance in zip(x_positions, clearances):
        hole = Pos(x, 0, 0) * Cylinder(
            (pin_diameter + clearance) / 2,
            thickness,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        plate -= hole

    head_radius = pin_diameter / 2 + 2.0
    pin = Cylinder(head_radius, 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    pin += Pos(0, 0, 2) * Cylinder(pin_diameter / 2, 5, align=(Align.CENTER, Align.CENTER, Align.MIN))

    insertion_pin = pin.rotate(Axis.X, 180)
    motions = []
    for x, clearance in zip(x_positions, clearances):
        samples = tuple((x, 0.0, z) for z in (12.0, 10.0, 8.0, 7.0, 6.0))
        motions.append(
            MotionSpec(
                name=f"pin_insertion_clearance_{clearance:.2f}_mm",
                fixed=plate,
                moving=insertion_pin,
                translations_mm=samples,
            )
        )

    return DesignSpec(
        name="fit_calibration",
        parts=(
            PartSpec(
                "clearance_plate",
                plate,
                expected_bbox_mm=(36, 14, thickness),
                # The web between the two largest holes is ~0.55 mm by design;
                # this coupon accepts single-wall webs.
                min_wall_mm=0.5,
            ),
            PartSpec(
                "test_pin",
                pin,
                expected_bbox_mm=(2 * head_radius, 2 * head_radius, 7),
            ),
        ),
        parameters={
            **parameters,
            "diametral_clearances_mm_left_to_right": list(clearances),
            "printer": profile["printer"]["name"],
            "material": profile["material"]["type"],
        },
        motions=tuple(motions),
    )
