"""IKEA-style box with sliding TOP lid, mountable on Skadis - true to the
models/ikea reference (Box with Slide Lid, ~100 x 60 x 30).

Kept as the original: shallow tray, full-footprint lid on TOP with a raised
center and recessed border, tongue edges sliding in grooves cut into the long
walls, entering from the right end. The only addition is Skadis mounting:
two seat bosses on the back long wall (40 mm pitch, horizontal) and short-bar
T-clips - the vendor's 28.3 mm bar cannot rotate inside a 30 mm-tall box, so
the parametric clip uses a 20 mm bar that still locks across the 15 mm slot.

All sliding clearances come from the profile's physically measured value
(0.25 mm per side, cooled; see docs/sliding_fit_calibration.md).
"""

from __future__ import annotations

import math
from typing import Any

from build123d import Align, Axis, Box, Pos

from agentic_cad.contracts import ClearanceSpec, DesignCheckSpec, DesignSpec, MotionSpec, PartSpec
from agentic_cad.interfaces import skadis

DEFAULTS: dict[str, Any] = {
    "width_mm": 100.0,
    "depth_mm": 60.0,
    "height_mm": 30.0,
    "wall_mm": 2.4,
    "lid_clearance_mm": None,  # None -> profile measured sliding clearance
    "seat_standoff_mm": 3.0,
    "bar_length_mm": 20.0,
}

FLOOR = 2.4
GROOVE_DEPTH = 1.4
TONGUE = 1.8
RAIL_TOP = 1.5
LID_RECESS = 0.4
SEAT_PITCH = 40.0


def build_design(profile: dict, overrides: dict[str, Any] | None = None) -> DesignSpec:
    parameters = dict(DEFAULTS)
    unknown = set(overrides or {}) - set(parameters)
    if unknown:
        raise KeyError(f"Unknown override(s) {sorted(unknown)}; supported: {sorted(parameters)}")
    parameters.update(overrides or {})

    width = parameters["width_mm"]
    depth = parameters["depth_mm"]
    height = parameters["height_mm"]
    wall = parameters["wall_mm"]
    standoff = parameters["seat_standoff_mm"]
    bar_length = parameters["bar_length_mm"]
    measured = profile["measured_calibration"]["xy_clearance_sliding_mm"]
    if parameters["lid_clearance_mm"] is None:
        parameters["lid_clearance_mm"] = measured
    clearance = parameters["lid_clearance_mm"]

    groove_height = TONGUE + 2 * clearance
    groove_top = height - RAIL_TOP
    groove_bottom = groove_top - groove_height
    seat_diameter = bar_length + 4.0
    bar_sweep = math.hypot(bar_length / 2, skadis.CLIP_THICKNESS / 2) + 0.4
    seat_z = FLOOR + bar_sweep + 0.4
    seat_xs = (width / 2 - SEAT_PITCH / 2, width / 2 + SEAT_PITCH / 2)

    if wall - GROOVE_DEPTH < 0.8:
        raise ValueError("wall_mm too thin for the lid groove: need wall - 1.4 >= 0.8")
    if seat_z + skadis.SLOT_LENGTH / 2 >= groove_bottom - 0.5 or seat_z + bar_sweep >= groove_bottom - 0.5:
        raise ValueError(
            f"height_mm too small: slot top {seat_z + skadis.SLOT_LENGTH / 2:.1f} and bar sweep "
            f"{seat_z + bar_sweep:.1f} must stay below the groove at {groove_bottom:.1f}"
        )
    if width < SEAT_PITCH + seat_diameter + 4:
        raise ValueError(f"width_mm must be at least {SEAT_PITCH + seat_diameter + 4:.0f} for two seats")

    # shell
    box = Box(width, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))
    box -= Pos(wall, wall, FLOOR) * Box(
        width - 2 * wall, depth - 2 * wall, height, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    # lid grooves in both long walls, running out through the right end wall
    box -= Pos(wall, wall - GROOVE_DEPTH, groove_bottom) * Box(
        width - wall + 1, depth - 2 * (wall - GROOVE_DEPTH), groove_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    # open the right end wall above the groove so the raised lid body enters
    box -= Pos(width - wall - 0.5, wall - GROOVE_DEPTH, groove_bottom) * Box(
        wall + 1.5, depth - 2 * (wall - GROOVE_DEPTH), height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    # Skadis seats on the back long wall, slots through wall + boss
    for x_c in seat_xs:
        box += Pos(x_c, depth, seat_z) * skadis.seat_boss(standoff, diameter=seat_diameter)
        box -= Pos(x_c, depth - wall - 0.5, seat_z) * skadis.rounded_slot(wall + standoff + 1.0)

    # probe check (ported idea from Codex main): prove each slot stayed open
    probe_volumes = []
    for x_c in seat_xs:
        probe = Pos(x_c, depth - wall + 0.1, seat_z) * skadis.rounded_slot(
            wall + standoff, width=2.0, length=10.0
        )
        probe_volumes.append(float((box & probe).volume) if (box & probe) else 0.0)

    # lid: tongue plate + raised center, floated 0.1 mm for measurable clearance
    tongue_y0 = wall - GROOVE_DEPTH + clearance
    tongue_width = depth - 2 * (wall - GROOVE_DEPTH) - 2 * clearance
    lid_x0 = wall + clearance
    lid_length = width - wall - clearance
    lid = Pos(lid_x0, tongue_y0, groove_bottom + 0.1) * Box(
        lid_length, tongue_width, TONGUE, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    body_top = height - LID_RECESS
    lid += Pos(lid_x0, wall + clearance, groove_bottom + 0.1 + TONGUE) * Box(
        lid_length,
        depth - 2 * wall - 2 * clearance,
        body_top - (groove_bottom + 0.1 + TONGUE),
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    lid_height = body_top - (groove_bottom + 0.1)

    # verification bodies: board coupon with two slots at the horizontal pitch
    board = Box(width, skadis.BOARD_THICKNESS, 60.0, align=(Align.CENTER, Align.MIN, Align.CENTER))
    for x_c in seat_xs:
        board -= Pos(x_c - width / 2, -0.5, 0) * skadis.rounded_slot(skadis.BOARD_THICKNESS + 1.0)
    board = Pos(width / 2, depth + standoff, seat_z) * board

    stem_length = skadis.stem_length_for(wall, standoff)
    clip_seated = Pos(
        seat_xs[0], depth - wall - 0.1 - skadis.BAR_HEIGHT, seat_z
    ) * skadis.t_clip(stem_length, clearance_per_side=measured, bar_length=bar_length)
    stem_axis = ((seat_xs[0], 0.0, seat_z), (0.0, 1.0, 0.0))
    clip_locked = clip_seated.rotate(Axis(stem_axis[0], stem_axis[1]), 90)

    fixture = box + board

    lid_slide = MotionSpec(
        name="lid_slide_out_right",
        fixed=box,
        moving=lid,
        translations_mm=tuple((dx, 0.0, 0.0) for dx in (60.0, 40.0, 20.0, 8.0, 0.0)),
        min_clearance_mm=0.05,
    )
    clip_twist_lock = MotionSpec(
        name="t_clip_insert_and_twist_lock",
        fixed=fixture,
        moving=clip_seated,
        translations_mm=((0, -30, 0), (0, -12, 0), (0, -5, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)),
        rotations_deg=(0.0, 0.0, 0.0, 0.0, 45.0, 90.0),
        rotation_axis=stem_axis,
        min_clearance_mm=0.03,
    )

    return DesignSpec(
        name="skadis_slide_box",
        parts=(
            PartSpec("box_body", box, expected_bbox_mm=(width, depth + standoff, height)),
            PartSpec(
                "sliding_lid",
                lid,
                expected_bbox_mm=(lid_length, tongue_width, lid_height),
                preferred_build_up=(0, 0, 1),
            ),
            PartSpec(
                "t_clip",
                clip_seated,
                expected_bbox_mm=(
                    skadis.CLIP_THICKNESS,
                    skadis.BAR_HEIGHT + stem_length + skadis.FOOT_HEIGHT,
                    bar_length,
                ),
                preferred_build_up=(1, 0, 0),
            ),
        ),
        parameters={
            **parameters,
            "lid_style": "original_top_slide_full_footprint_raised_center",
            "tongue_mm": TONGUE,
            "groove_depth_mm": GROOVE_DEPTH,
            "seat_pitch_mm": SEAT_PITCH,
            "seat_center_z_mm": seat_z,
            "seat_diameter_mm": seat_diameter,
            "t_clip_stem_length_mm": stem_length,
            "sliding_clearance_mm_per_side": clearance,
            "printer": profile["printer"]["name"],
            "material": profile["material"]["type"],
        },
        motions=(lid_slide, clip_twist_lock),
        clearances=(
            ClearanceSpec("locked_clip_vs_board", clip_locked, board, min_mm=0.02, max_mm=0.5),
            ClearanceSpec("box_seats_on_board", box, board, min_mm=0.0, max_mm=0.05),
            ClearanceSpec("lid_in_groove", lid, box, min_mm=0.05, max_mm=0.4),
        ),
        checks=(
            DesignCheckSpec(
                name="clip_seat_slots_through_open",
                passed=max(probe_volumes) <= 0.001,
                measured={"probe_intersection_volumes_mm3": probe_volumes},
                expected="each <= 0.001 mm3",
            ),
        ),
    )
