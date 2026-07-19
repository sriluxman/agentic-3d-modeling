"""IKEA-style box with sliding TOP lid, mountable on Skadis - reworked from
user annotations (annotations.json round 1):

- Pin 1: the box's flat BOTTOM sits flush on the board; clip reception pads
  protrude INSIDE. Assembly: hold the box on the board, insert each T-clip
  from inside the box down through floor + board, twist 90 to lock. Inside
  the box the bar is horizontal, so it has the whole footprint to rotate in.
- Pin 2: geometry stays true to the reference: all four walls full height,
  lid enters through a letter-slot in one end wall at groove level (measured
  on the reference STL - the wall continues above as a bridge).
- Pin 3: the T-clip is NOT redesigned. Print the vendor STL as-is
  (models/ikea/T-Clip for Painted Skadis.stl). The replica here is only the
  motion-check surrogate: vendor bar and stem stack (floor 2.4 + pad 1.0
  + board 5.1 + slack = the vendor's measured 8.65 mm stem), stem/foot sized
  to the profile's measured print clearance (the vendor's 5.15 stem is an
  intentional elastic snug fit that a rigid check cannot represent).

Wall-mounted: bottom against board, lid faces the user and slides sideways.
"""

from __future__ import annotations

from typing import Any

from build123d import Align, Axis, Box, Cylinder, Pos, Rot

from agentic_cad.contracts import ClearanceSpec, DesignCheckSpec, DesignSpec, MotionSpec, PartSpec
from agentic_cad.interfaces import skadis

DEFAULTS: dict[str, Any] = {
    "width_mm": 100.0,
    "depth_mm": 60.0,
    "height_mm": 30.0,
    "wall_mm": 2.4,
    "floor_mm": 2.4,
    "lid_clearance_mm": None,  # None -> profile measured sliding clearance
    "pad_mm": 1.0,  # interior pad so floor + pad matches the vendor 3.4 stack
}

TONGUE = 1.8
GROOVE_DEPTH = 1.4
RAIL_TOP = 1.5
SEAT_PITCH = 40.0
PAD_DIAMETER = 24.0


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
    floor = parameters["floor_mm"]
    pad = parameters["pad_mm"]
    measured = profile["measured_calibration"]["xy_clearance_sliding_mm"]
    if parameters["lid_clearance_mm"] is None:
        parameters["lid_clearance_mm"] = measured
    clearance = parameters["lid_clearance_mm"]

    groove_height = TONGUE + 2 * clearance
    groove_top = height - RAIL_TOP
    groove_bottom = groove_top - groove_height
    seat_xs = (width / 2 - SEAT_PITCH / 2, width / 2 + SEAT_PITCH / 2)
    seat_y = depth / 2
    bar_sweep = skadis.BAR_LENGTH / 2 + 0.5

    if wall - GROOVE_DEPTH < 0.8:
        raise ValueError("wall_mm too thin for the lid groove: need wall - 1.4 >= 0.8")
    if min(seat_xs[0], depth / 2) < bar_sweep + wall:
        raise ValueError(f"footprint too small: the clip bar needs {bar_sweep:.1f} mm around each seat")

    # shell, true to the reference: full-height walls all around
    box = Box(width, depth, height, align=(Align.MIN, Align.MIN, Align.MIN))
    box -= Pos(wall, wall, floor) * Box(
        width - 2 * wall, depth - 2 * wall, height, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    # lid grooves along both long walls
    box -= Pos(wall, wall - GROOVE_DEPTH, groove_bottom) * Box(
        width - 2 * wall, depth - 2 * (wall - GROOVE_DEPTH), groove_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    # letter-slot lid entry through the right end wall; bridge stays above
    box -= Pos(width - wall - 0.5, wall - GROOVE_DEPTH, groove_bottom) * Box(
        wall + 1.5, depth - 2 * (wall - GROOVE_DEPTH), groove_height,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    # clip reception: interior pads + slots through floor and pad (pin 1);
    # Rot(90) turns the slot cutter's +Y extrusion upward through the floor,
    # slot length ends up along Y (vertical on the board, box hung landscape)
    for x_c in seat_xs:
        box += Pos(x_c, seat_y, floor) * Cylinder(
            PAD_DIAMETER / 2, pad, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        box -= Pos(x_c, seat_y, -0.5) * Rot(90, 0, 0) * skadis.rounded_slot(floor + pad + 1.0)

    probe_volumes = []
    for x_c in seat_xs:
        probe = Pos(x_c, seat_y, -0.2) * Rot(90, 0, 0) * skadis.rounded_slot(
            floor + pad + 0.4, width=2.0, length=10.0
        )
        section = box & probe
        probe_volumes.append(float(section.volume) if section else 0.0)

    # flat tongue lid entering through the letter slot (reference mechanism)
    tongue_y0 = wall - GROOVE_DEPTH + clearance
    tongue_width = depth - 2 * (wall - GROOVE_DEPTH) - 2 * clearance
    lid_x0 = wall + clearance
    lid_length = width - wall - clearance
    lid = Pos(lid_x0, tongue_y0, groove_bottom + 0.1) * Box(
        lid_length, tongue_width, TONGUE, align=(Align.MIN, Align.MIN, Align.MIN)
    )

    # verification bodies: board below the floor, vendor-stack clip replica
    board = Box(width, skadis.BOARD_THICKNESS, 60.0, align=(Align.CENTER, Align.MIN, Align.CENTER))
    for x_c in seat_xs:
        board -= Pos(x_c - width / 2, -0.5, 0) * skadis.rounded_slot(skadis.BOARD_THICKNESS + 1.0)
    # board plane: front face on the box bottom (z=0), slots along Y
    board = Pos(width / 2, seat_y, 0) * Rot(90, 0, 0) * Pos(0, -skadis.BOARD_THICKNESS, 0) * board

    stem_length = skadis.stem_length_for(floor, pad)  # = vendor 8.65 for defaults
    clip = skadis.t_clip(stem_length, clearance_per_side=measured)
    # orient for downward insertion: local +Y (insertion axis) -> world -Z
    clip_seated = Pos(seat_xs[0], seat_y, floor + pad + 0.1 + skadis.BAR_HEIGHT) * Rot(-90, 0, 0) * clip
    stem_axis = ((seat_xs[0], seat_y, 0.0), (0.0, 0.0, 1.0))
    clip_locked = clip_seated.rotate(Axis(stem_axis[0], stem_axis[1]), 90)

    fixture = box + board

    lid_slide = MotionSpec(
        name="lid_slide_through_letter_slot",
        fixed=box,
        moving=lid,
        translations_mm=tuple((dx, 0.0, 0.0) for dx in (60.0, 40.0, 20.0, 8.0, 0.0)),
        min_clearance_mm=0.05,
    )
    clip_twist_lock = MotionSpec(
        name="t_clip_insert_from_inside_and_twist",
        fixed=fixture,
        moving=clip_seated,
        translations_mm=((0, 0, 18), (0, 0, 8), (0, 0, 3), (0, 0, 0), (0, 0, 0), (0, 0, 0)),
        rotations_deg=(0.0, 0.0, 0.0, 0.0, 45.0, 90.0),
        rotation_axis=stem_axis,
        min_clearance_mm=0.03,
    )

    return DesignSpec(
        name="skadis_slide_box",
        parts=(
            PartSpec("box_body", box, expected_bbox_mm=(width, depth, height)),
            PartSpec(
                "sliding_lid",
                lid,
                expected_bbox_mm=(lid_length, tongue_width, TONGUE),
                preferred_build_up=(0, 0, 1),
            ),
        ),
        parameters={
            **parameters,
            "lid_style": "original_top_slide_letter_slot_entry",
            "mounting": "bottom_flush_on_board_clips_inserted_from_inside",
            "print_clip": "models/ikea/T-Clip for Painted Skadis.stl (vendor part, unmodified)",
            "clip_replica_stem_length_mm": stem_length,
            "seat_pitch_mm": SEAT_PITCH,
            "pad_diameter_mm": PAD_DIAMETER,
            "sliding_clearance_mm_per_side": clearance,
            "printer": profile["printer"]["name"],
            "material": profile["material"]["type"],
        },
        motions=(lid_slide, clip_twist_lock),
        clearances=(
            ClearanceSpec("locked_clip_vs_board", clip_locked, board, min_mm=0.02, max_mm=0.5),
            ClearanceSpec("box_bottom_flush_on_board", box, board, min_mm=0.0, max_mm=0.05),
            ClearanceSpec("lid_in_groove", lid, box, min_mm=0.05, max_mm=0.4),
        ),
        checks=(
            DesignCheckSpec(
                name="clip_slots_through_open",
                passed=max(probe_volumes) <= 0.001,
                measured={"probe_intersection_volumes_mm3": probe_volumes},
                expected="each <= 0.001 mm3",
            ),
        ),
    )
