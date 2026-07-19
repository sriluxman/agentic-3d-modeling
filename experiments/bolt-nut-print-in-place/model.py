"""Print-in-place bolt and nut, support-free.

Bolt 100 mm tall, 30 mm thread diameter (as requested). Both parts print as
ONE plate: the bolt stands on its hex head and the nut is printed in place
around the shaft, floating 0.3 mm above the head (a trivially bridgeable
ring gap). The 45-degree trapezoidal thread needs no support.

Threads come from agentic_cad.threads with deterministic phase math, so the
in-place nut ridge is centered between the bolt ridges by construction and
the unscrew motion check runs the REAL threaded pair (helical samples).
"""

from __future__ import annotations

import math
from typing import Any

from build123d import Align, Cylinder, Pos, RegularPolygon, Rot, extrude

from agentic_cad import threads
from agentic_cad.contracts import ClearanceSpec, DesignCheckSpec, DesignSpec, MotionSpec, PartSpec

DEFAULTS: dict[str, Any] = {
    "thread_diameter_mm": 30.0,
    "total_height_mm": 100.0,
    "pitch_mm": 6.0,
    "head_across_flats_mm": 45.0,
    "head_height_mm": 12.0,
    "nut_across_flats_mm": 45.0,
    "nut_height_mm": 15.0,
    "fit_mm": None,  # diametral; None -> max(1.0, 4 x measured print clearance)
}

THREAD_ANGLE = 45.0
NUT_FLOAT = 0.3  # print-in-place vertical gap above the head


def _hex_prism(across_flats: float, height: float):
    radius = across_flats / 2 / math.cos(math.radians(30))
    return extrude(RegularPolygon(radius, 6), amount=height), radius


def build_design(profile: dict, overrides: dict[str, Any] | None = None) -> DesignSpec:
    parameters = dict(DEFAULTS)
    unknown = set(overrides or {}) - set(parameters)
    if unknown:
        raise KeyError(f"Unknown override(s) {sorted(unknown)}; supported: {sorted(parameters)}")
    parameters.update(overrides or {})

    major = parameters["thread_diameter_mm"]
    total_h = parameters["total_height_mm"]
    pitch = parameters["pitch_mm"]
    head_af = parameters["head_across_flats_mm"]
    head_h = parameters["head_height_mm"]
    nut_af = parameters["nut_across_flats_mm"]
    nut_h = parameters["nut_height_mm"]
    measured = profile["measured_calibration"]["xy_clearance_sliding_mm"]
    if parameters["fit_mm"] is None:
        parameters["fit_mm"] = max(1.0, 4 * measured)
    fit = parameters["fit_mm"]

    depth = threads.thread_depth(pitch)
    rod_r = major / 2 - depth
    bore_r = major / 2 + fit / 2
    shaft_len = total_h - head_h
    nut_z = head_h + NUT_FLOAT

    head, head_r = _hex_prism(head_af, head_h)
    # fuse ridge to the bare rod first - a single clean seam imprint - then
    # add the head (the reversed order left OCC with unsplit faces the
    # self-intersection gate rejected)
    shaft = Cylinder(rod_r, shaft_len, align=(Align.CENTER, Align.CENTER, Align.MIN))
    shaft += threads.external_ridge(rod_r, pitch, shaft_len)
    bolt = head + Pos(0, 0, head_h) * shaft

    nut_body, nut_r = _hex_prism(nut_af, nut_h)
    nut = nut_body - Cylinder(bore_r, 3 * nut_h, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    phase = threads.mating_rotation_deg(pitch, nut_z - head_h)
    nut += Rot(0, 0, phase) * threads.internal_ridge(bore_r, pitch, nut_h)
    nut = Pos(0, 0, nut_z) * nut

    plate = bolt + nut  # one printable plate, two bodies

    unscrew = MotionSpec(
        name="nut_unscrews_real_threads",
        fixed=bolt,
        moving=nut,
        translations_mm=((0, 0, 0), (0, 0, pitch), (0, 0, 2 * pitch), (0, 0, shaft_len + 5)),
        rotations_deg=(0.0, 360.0, 720.0, 0.0),
        rotation_axis=((0, 0, 0), (0, 0, 1)),
        min_clearance_mm=0.05,
    )

    return DesignSpec(
        name="bolt_nut_print_in_place",
        parts=(
            PartSpec(
                "bolt_nut_plate",
                plate,
                expected_bbox_mm=(2 * max(head_r, nut_r), max(head_af, nut_af), total_h),
                expected_bodies=2,
            ),
        ),
        parameters={
            **parameters,
            "thread_angle_deg": THREAD_ANGLE,
            "nut_float_mm": NUT_FLOAT,
            "predicted_flank_backlash_mm": round(threads.backlash(pitch, fit), 3),
            "print_orientation": "as modeled: head on bed, nut in place, no supports",
            "printer": profile["printer"]["name"],
            "material": profile["material"]["type"],
        },
        motions=(unscrew,),
        clearances=(
            ClearanceSpec("nut_thread_engagement", nut, bolt, min_mm=0.05, max_mm=0.6),
        ),
        checks=(
            DesignCheckSpec(
                name="total_height_mm",
                passed=abs(float(plate.bounding_box().size.Z) - total_h) < 0.05,
                measured=float(plate.bounding_box().size.Z),
                expected=total_h,
            ),
            DesignCheckSpec(
                name="positive_flank_backlash",
                passed=threads.backlash(pitch, fit) > 0.05,
                measured=round(threads.backlash(pitch, fit), 3),
                expected="> 0.05 mm",
            ),
        ),
    )
