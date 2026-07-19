"""Parametric container with sliding lid, mounted on IKEA Skadis via T-clips.

Combines the reference sliding-lid box and the Skadis T-clip system from the
user's models/ikea folder into one verified parametric design:

- container with side grooves and a lid that slides in from the front under
  a retaining rim (motion-checked with demanded running clearance);
- two Skadis seat bosses on the back wall with slots cut through wall + boss;
- T-clip twist-lock insertion verified end-to-end: translate through wall,
  boss, and board slots, then rotate 90 degrees about the stem axis so the
  foot hooks behind the board (uses MotionSpec rotation sampling);
- static clearance bands for the locked clip and the board contact.

The board coupon and clip replica come from agentic_cad.interfaces.skadis;
print the vendor T-clip STL or the replica part, both share the envelope.
"""

from __future__ import annotations

import math
from typing import Any

from build123d import Align, Axis, Box, Pos

from agentic_cad.contracts import ClearanceSpec, DesignSpec, MotionSpec, PartSpec
from agentic_cad.interfaces import skadis

DEFAULTS: dict[str, Any] = {
    "width_mm": 50.0,
    "depth_mm": 40.0,
    "height_mm": 80.0,
    "wall_mm": 2.4,
    # None -> use the profile's physically measured sliding clearance
    "lid_clearance_mm": None,
    "seat_standoff_mm": 3.0,
}

GROOVE_DEPTH = 1.2
LID_THICKNESS = 2.4


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
    measured = profile["measured_calibration"]["xy_clearance_sliding_mm"]
    if parameters["lid_clearance_mm"] is None:
        parameters["lid_clearance_mm"] = measured
    clearance = parameters["lid_clearance_mm"]
    standoff = parameters["seat_standoff_mm"]

    groove_bottom = height - wall - LID_THICKNESS - clearance
    seat_low_z = height / 2 - skadis.SLOT_PITCH / 2
    seat_high_z = height / 2 + skadis.SLOT_PITCH / 2
    # swept corner radius of the rotating bar cross-section, plus margin
    bar_sweep = math.hypot(skadis.BAR_LENGTH / 2, skadis.CLIP_THICKNESS / 2) + 0.4
    if seat_high_z + bar_sweep >= groove_bottom or seat_low_z - bar_sweep <= wall:
        raise ValueError(
            "height_mm too small: the T-clip bar needs "
            f"{bar_sweep:.1f} mm of clear interior wall around each seat "
            f"(seats at z={seat_low_z:.1f}/{seat_high_z:.1f}, groove bottom {groove_bottom:.1f})"
        )
    if wall - GROOVE_DEPTH < 0.8:
        raise ValueError("wall_mm too thin for the lid groove: need wall - 1.2 >= 0.8")

    # container shell, open top
    container = Box(width, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))
    container -= Pos(wall, wall, wall) * Box(
        width - 2 * wall, depth - 2 * wall, height, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    # lid groove channel into both side walls, running to the back wall
    container -= Pos(wall - GROOVE_DEPTH, -1, groove_bottom) * Box(
        width - 2 * (wall - GROOVE_DEPTH),
        depth - wall + 1,
        LID_THICKNESS + clearance,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    # open the front wall above the groove so the lid enters from the front
    container -= Pos(wall - GROOVE_DEPTH, -1, groove_bottom) * Box(
        width - 2 * (wall - GROOVE_DEPTH), wall + 1.5, height, align=(Align.MIN, Align.MIN, Align.MIN)
    )

    # Skadis seat bosses on the back wall, slots cut through wall + boss
    for center_z in (seat_low_z, seat_high_z):
        container += Pos(width / 2, depth, center_z) * skadis.seat_boss(standoff)
        container -= Pos(width / 2, depth - wall - 0.5, center_z) * skadis.rounded_slot(
            wall + standoff + 1.0
        )

    # lid, floated 0.1 mm in the groove so running clearance is measurable
    lid_width = width - 2 * (wall - GROOVE_DEPTH) - 2 * clearance
    lid_length = depth - wall - clearance
    lid = Pos(wall - GROOVE_DEPTH + clearance, 0, groove_bottom + 0.1) * Box(
        lid_width, lid_length, LID_THICKNESS, align=(Align.MIN, Align.MIN, Align.MIN)
    )

    # reference board and clip replica (verification bodies)
    board = Pos(width / 2, depth + standoff, height / 2) * skadis.board_coupon(
        width=width, height=height + 10
    )
    stem_length = skadis.stem_length_for(wall, standoff)
    clip_seated = Pos(
        width / 2,
        depth - wall - 0.1 - skadis.BAR_HEIGHT,
        seat_high_z,
    ) * skadis.t_clip(stem_length, clearance_per_side=measured)
    stem_axis = ((width / 2, 0.0, seat_high_z), (0.0, 1.0, 0.0))
    clip_locked = clip_seated.rotate(Axis(stem_axis[0], stem_axis[1]), 90)

    fixture = container + board

    lid_slide = MotionSpec(
        name="lid_slide_from_front",
        fixed=container,
        moving=lid,
        translations_mm=tuple((0.0, -dy, 0.0) for dy in (35.0, 25.0, 12.0, 4.0, 0.0)),
        min_clearance_mm=0.03,
    )
    clip_twist_lock = MotionSpec(
        name="t_clip_insert_and_twist_lock",
        fixed=fixture,
        moving=clip_seated,
        translations_mm=((0, -26, 0), (0, -13, 0), (0, -6, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)),
        rotations_deg=(0.0, 0.0, 0.0, 0.0, 45.0, 90.0),
        rotation_axis=stem_axis,
        min_clearance_mm=0.03,
    )

    clearances = (
        ClearanceSpec("locked_clip_vs_board", clip_locked, board, min_mm=0.02, max_mm=0.2),
        ClearanceSpec("container_seats_on_board", container, board, min_mm=0.0, max_mm=0.05),
        ClearanceSpec("lid_in_groove", lid, container, min_mm=0.03, max_mm=0.3),
    )

    return DesignSpec(
        name="skadis_container",
        parts=(
            PartSpec(
                "container",
                container,
                expected_bbox_mm=(width, depth + standoff, height),
            ),
            PartSpec("lid", lid, expected_bbox_mm=(lid_width, lid_length, LID_THICKNESS)),
            PartSpec(
                "t_clip",
                clip_seated,
                expected_bbox_mm=(
                    skadis.CLIP_THICKNESS,
                    skadis.BAR_HEIGHT + stem_length + skadis.FOOT_HEIGHT,
                    skadis.BAR_LENGTH,
                ),
                preferred_build_up=(1, 0, 0),
            ),
        ),
        parameters={
            **parameters,
            "groove_depth_mm": GROOVE_DEPTH,
            "lid_thickness_mm": LID_THICKNESS,
            "t_clip_stem_length_mm": stem_length,
            "skadis_slot_pitch_mm": skadis.SLOT_PITCH,
            "printer": profile["printer"]["name"],
            "material": profile["material"]["type"],
        },
        motions=(lid_slide, clip_twist_lock),
        clearances=clearances,
    )
