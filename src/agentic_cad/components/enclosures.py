from __future__ import annotations

from dataclasses import dataclass

from build123d import Align, Box, Pos, Shape


@dataclass(frozen=True)
class SlidingLidBoxParameters:
    width_mm: float = 76.0
    height_mm: float = 50.0
    depth_mm: float = 40.0
    wall_mm: float = 2.0
    back_wall_mm: float = 2.0
    lid_thickness_mm: float = 1.6
    lid_cover_floor_mm: float = 1.4
    lid_recess_depth_mm: float = 0.8
    lid_recess_border_mm: float = 1.6
    support_rail_depth_mm: float = 2.5
    front_rail_depth_mm: float = 1.2


@dataclass(frozen=True)
class SlidingLidBoxGeometry:
    body: Shape
    lid: Shape
    lid_bbox_mm: tuple[float, float, float]
    assembled_translation_mm: tuple[float, float, float]
    insertion_path_mm: tuple[tuple[float, float, float], ...]


def build_sliding_lid_box(
    params: SlidingLidBoxParameters,
    sliding_clearance_mm_per_side: float,
) -> SlidingLidBoxGeometry:
    width = params.width_mm
    height = params.height_mm
    depth = params.depth_mm
    wall = params.wall_mm
    back_wall = params.back_wall_mm
    lid_thickness = params.lid_thickness_mm
    cover_floor = params.lid_cover_floor_mm
    recess_depth = params.lid_recess_depth_mm
    recess_border = params.lid_recess_border_mm
    channel_gap = lid_thickness + 2 * sliding_clearance_mm_per_side
    support_rail_thickness = 1.0
    front_rail_thickness = 1.0
    channel_back = depth - front_rail_thickness - channel_gap

    if min(width, height, depth, wall, back_wall, lid_thickness, cover_floor) <= 0:
        raise ValueError("Sliding-lid box dimensions must be positive")
    if recess_depth < 0 or recess_border <= 0:
        raise ValueError("Lid recess dimensions must be non-negative with a positive border")
    if depth <= back_wall + channel_gap + 4:
        raise ValueError("depth_mm leaves no usable container depth")

    body = Box(width, height, depth, align=(Align.MIN, Align.MIN, Align.MIN))
    body -= Pos(wall, wall, back_wall) * Box(
        width - 2 * wall,
        height - 2 * wall,
        depth - back_wall + 0.1,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    rail_height = height - wall
    support_rail_width = wall + params.support_rail_depth_mm
    for x in (0.0, width - support_rail_width):
        body += Pos(x, wall, channel_back - support_rail_thickness) * Box(
            support_rail_width,
            rail_height,
            support_rail_thickness,
            align=(Align.MIN, Align.MIN, Align.MIN),
        )
    front_rail_width = wall + params.front_rail_depth_mm
    for x in (0.0, width - front_rail_width):
        body += Pos(x, wall, depth - front_rail_thickness) * Box(
            front_rail_width,
            rail_height,
            front_rail_thickness,
            align=(Align.MIN, Align.MIN, Align.MIN),
        )

    body -= Pos(wall - 0.05, height - wall - 0.05, channel_back - 0.05) * Box(
        width - 2 * wall + 0.1,
        wall + 0.1,
        depth - channel_back + 0.15,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )

    lid_width = width - 2 * wall - 2 * sliding_clearance_mm_per_side
    lid_height = height - wall - sliding_clearance_mm_per_side
    assembled = (
        wall + sliding_clearance_mm_per_side,
        wall + sliding_clearance_mm_per_side,
        channel_back + sliding_clearance_mm_per_side,
    )
    if min(width - 2 * recess_border, height - 2 * recess_border) <= 0:
        raise ValueError("Lid recess border leaves no recessed center")

    lid = Box(lid_width, lid_height, lid_thickness, align=(Align.MIN, Align.MIN, Align.MIN))
    cover_z = depth - assembled[2]
    bridge_inset_x = front_rail_width - assembled[0] + sliding_clearance_mm_per_side
    if cover_z <= lid_thickness or lid_width <= 2 * bridge_inset_x:
        raise ValueError("Lid channel dimensions leave no valid concealed bridge")
    lid += Pos(bridge_inset_x, 0, lid_thickness - 0.05) * Box(
        lid_width - 2 * bridge_inset_x,
        lid_height,
        cover_z - lid_thickness + 0.1,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    cover_height = cover_floor + recess_depth
    cover = Box(width, height, cover_height, align=(Align.MIN, Align.MIN, Align.MIN))
    if recess_depth > 0:
        cover -= Pos(recess_border, recess_border, cover_floor) * Box(
            width - 2 * recess_border,
            height - 2 * recess_border,
            recess_depth + 0.1,
            align=(Align.MIN, Align.MIN, Align.MIN),
        )
    lid += Pos(-assembled[0], -assembled[1], cover_z) * cover

    insertion_y = (height + 5.0, height, 0.8 * height, 0.6 * height, 0.4 * height, 0.2 * height, assembled[1])
    path = tuple((assembled[0], y, assembled[2]) for y in insertion_y)
    return SlidingLidBoxGeometry(
        body=body,
        lid=lid,
        lid_bbox_mm=(width, height, cover_z + cover_height),
        assembled_translation_mm=assembled,
        insertion_path_mm=path,
    )
