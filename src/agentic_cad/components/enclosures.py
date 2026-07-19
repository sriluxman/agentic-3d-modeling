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
    lid_rim_height_mm: float = 1.8
    lid_rim_width_mm: float = 1.0
    lid_rim_inset_x_mm: float = 2.0
    lid_rim_inset_y_mm: float = 2.5
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
    rim_height = params.lid_rim_height_mm
    rim_width = params.lid_rim_width_mm
    rim_inset_x = params.lid_rim_inset_x_mm
    rim_inset_y = params.lid_rim_inset_y_mm
    channel_gap = lid_thickness + 2 * sliding_clearance_mm_per_side
    support_rail_thickness = 1.0
    front_rail_thickness = 1.0
    channel_back = depth - front_rail_thickness - channel_gap

    if min(width, height, depth, wall, back_wall, lid_thickness, rim_height, rim_width) <= 0:
        raise ValueError("Sliding-lid box dimensions must be positive")
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
    rim_outer_width = lid_width - 2 * rim_inset_x
    rim_outer_height = lid_height - 2 * rim_inset_y
    if min(rim_outer_width - 2 * rim_width, rim_outer_height - 2 * rim_width) <= 0:
        raise ValueError("Lid rim dimensions leave no open center")

    lid = Box(lid_width, lid_height, lid_thickness, align=(Align.MIN, Align.MIN, Align.MIN))
    rim_z = lid_thickness - 0.05
    rim_part_height = rim_height + 0.05
    lid += Pos(rim_inset_x, rim_inset_y, rim_z) * Box(
        rim_outer_width, rim_width, rim_part_height, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    lid += Pos(rim_inset_x, lid_height - rim_inset_y - rim_width, rim_z) * Box(
        rim_outer_width, rim_width, rim_part_height, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    lid += Pos(rim_inset_x, rim_inset_y, rim_z) * Box(
        rim_width, rim_outer_height, rim_part_height, align=(Align.MIN, Align.MIN, Align.MIN)
    )
    lid += Pos(lid_width - rim_inset_x - rim_width, rim_inset_y, rim_z) * Box(
        rim_width, rim_outer_height, rim_part_height, align=(Align.MIN, Align.MIN, Align.MIN)
    )

    assembled = (
        wall + sliding_clearance_mm_per_side,
        wall + sliding_clearance_mm_per_side,
        channel_back + sliding_clearance_mm_per_side,
    )
    insertion_y = (height + 5.0, height, 0.8 * height, 0.6 * height, 0.4 * height, 0.2 * height, assembled[1])
    path = tuple((assembled[0], y, assembled[2]) for y in insertion_y)
    return SlidingLidBoxGeometry(
        body=body,
        lid=lid,
        lid_bbox_mm=(lid_width, lid_height, lid_thickness + rim_height),
        assembled_translation_mm=assembled,
        insertion_path_mm=path,
    )
