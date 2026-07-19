from __future__ import annotations

from build123d import Align, Axis, Box, Cylinder, Pos

from agentic_cad.contracts import DesignSpec, MotionSpec, PartSpec


def build_design(profile: dict) -> DesignSpec:
    pin_diameter = 5.0
    clearances = (0.10, 0.20, 0.30, 0.40, 0.50)
    x_positions = (-12.0, -6.0, 0.0, 6.0, 12.0)

    plate = Box(36, 14, 4, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for x, clearance in zip(x_positions, clearances):
        hole = Pos(x, 0, 0) * Cylinder(
            (pin_diameter + clearance) / 2,
            4,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        plate -= hole

    pin = Cylinder(4.5, 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    pin += Pos(0, 0, 2) * Cylinder(2.5, 5, align=(Align.CENTER, Align.CENTER, Align.MIN))

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
            PartSpec("clearance_plate", plate, expected_bbox_mm=(36, 14, 4)),
            PartSpec("test_pin", pin, expected_bbox_mm=(9, 9, 7)),
        ),
        parameters={
            "pin_diameter_mm": pin_diameter,
            "diametral_clearances_mm_left_to_right": list(clearances),
            "printer": profile["printer"]["name"],
            "material": profile["material"]["type"],
        },
        motions=tuple(motions),
    )
