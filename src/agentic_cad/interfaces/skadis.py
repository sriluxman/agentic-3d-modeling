"""IKEA Skadis pegboard interface: slots, board coupons, T-clip system.

Published Skadis geometry: 5 x 15 mm rounded slots on a 40 mm grid, board
about 5.1 mm thick. The T-clip mechanism follows the Printables "Skadis
T-Clip System" (model 256896): a T-shaped clip inserts vertically through a
slot and twist-locks 90 degrees so its foot hooks behind the board.

All geometry here is parametric and self-contained. Dimensions marked
"measured" were taken from the vendor reference files kept locally under
models/ikea/ (not redistributed): clip 28.27 x 19.05 x 4.80 mm overall,
bar 28.3 x 5.6, round stem ~5 dia, foot 14.8 x 5.0.
"""

from __future__ import annotations

from build123d import Align, Axis, Box, Cylinder, Pos, Rot, Shape

# Skadis board (published/community-measured)
SLOT_WIDTH = 5.0
SLOT_LENGTH = 15.0
SLOT_PITCH = 40.0
BOARD_THICKNESS = 5.1

# T-clip replica (measured from vendor STL). Stem and foot are derived from
# the profile's measured sliding clearance at build time; the vendor's own
# 4.9 stem / 14.8 foot correspond to ~0.05-0.1 per side, which the dovetail
# calibration showed cannot insert on this printer once cooled.
CLIP_THICKNESS = 4.8
BAR_LENGTH = 28.3
BAR_HEIGHT = 5.6
FOOT_HEIGHT = 5.0
DEFAULT_CLEARANCE = 0.25  # per side; prefer profile measured_calibration

# Standoff a design should keep between its back wall and the board so the
# stem engagement matches the clip (vendor part is 5.4 mm thick at the seat).
SEAT_DIAMETER = 28.3


def rounded_slot(depth: float, width: float = SLOT_WIDTH, length: float = SLOT_LENGTH) -> Shape:
    """Skadis-style rounded slot cutter: width across X, length across Z,
    extruded along Y from y=0 to y=depth, centered at x=0, z=0."""
    radius = width / 2
    straight = length - width
    slot = Box(width, depth, straight, align=(Align.CENTER, Align.MIN, Align.CENTER))
    for sign in (1.0, -1.0):
        cap = Pos(0, 0, sign * straight / 2) * Rot(-90, 0, 0) * Cylinder(
            radius, depth, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        slot += cap
    return slot


def board_coupon(
    width: float = 50.0,
    height: float = 90.0,
    slot_centers_z: tuple[float, ...] = (-SLOT_PITCH / 2, SLOT_PITCH / 2),
) -> Shape:
    """Reference Skadis board segment: front face at y=0, back at y=BOARD_THICKNESS,
    centered at x=0, z=0, with vertical slots at the given z centers."""
    board = Box(
        width,
        BOARD_THICKNESS,
        height,
        align=(Align.CENTER, Align.MIN, Align.CENTER),
    )
    for center_z in slot_centers_z:
        board -= Pos(0, -0.5, center_z) * rounded_slot(BOARD_THICKNESS + 1.0)
    return board


def seat_boss(standoff: float = 3.0, diameter: float = SEAT_DIAMETER) -> Shape:
    """Cylindrical seat boss to union onto a design's back wall: axis along Y
    from y=0 (wall exterior) to y=standoff (board contact face). Cut the slot
    separately with rounded_slot through wall + boss."""
    return Rot(-90, 0, 0) * Cylinder(
        diameter / 2, standoff, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )


def t_clip(
    stem_length: float,
    clearance_per_side: float = DEFAULT_CLEARANCE,
    bar_length: float = BAR_LENGTH,
) -> Shape:
    """T-clip replica in insertion orientation, ready to travel along +Y.

    Origin: stem axis at x=0, z=0; bar front face at y=0. Bar and foot lie in
    the vertical plane (long axes along Z) so the foot passes through a
    vertical slot; a 90 degree twist about the stem axis locks it.
    ``stem_length`` spans bar underside to foot top: wall + standoff + board
    + slack. ``clearance_per_side`` sizes the stem and foot against the 5 x 15
    slot (use the profile's measured sliding clearance). ``bar_length`` may be
    shortened (>= slot length + 4) so the bar can rotate inside low enclosures.
    The vendor part is printed flat; this replica shares its functional envelope.
    """
    if bar_length < SLOT_LENGTH + 4:
        raise ValueError(f"bar_length must be >= {SLOT_LENGTH + 4} to lock across the slot")
    stem_diameter = SLOT_WIDTH - 2 * clearance_per_side
    foot_length = SLOT_LENGTH - 2 * clearance_per_side
    bar = Box(
        CLIP_THICKNESS, BAR_HEIGHT, bar_length,
        align=(Align.CENTER, Align.MIN, Align.CENTER),
    )
    stem = Pos(0, BAR_HEIGHT, 0) * Rot(-90, 0, 0) * Cylinder(
        stem_diameter / 2, stem_length, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    # Stadium-profile foot: rounded ends so it clears the slot's end arcs
    # (a square-cornered foot collides with the rounded slot - the motion
    # check caught exactly that on the first attempt).
    straight = foot_length - CLIP_THICKNESS
    foot = Box(
        CLIP_THICKNESS, FOOT_HEIGHT, straight,
        align=(Align.CENTER, Align.MIN, Align.CENTER),
    )
    for sign in (1.0, -1.0):
        foot += Pos(0, 0, sign * straight / 2) * Rot(-90, 0, 0) * Cylinder(
            CLIP_THICKNESS / 2, FOOT_HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
    return bar + stem + Pos(0, BAR_HEIGHT + stem_length, 0) * foot


def stem_length_for(wall: float, standoff: float, slack: float = 0.15) -> float:
    """Stem length so the foot clears the board back by ``slack``."""
    return wall + standoff + BOARD_THICKNESS + slack
