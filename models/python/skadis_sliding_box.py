from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from agentic_cad.components.enclosures import SlidingLidBoxParameters, build_sliding_lid_box
from agentic_cad.components.skadis import embed_t_clip_seats
from build123d import Pos, Rot, Shape

from agentic_cad.contracts import DesignCheckSpec, DesignSpec, MotionSpec, PartSpec


ROOT = Path(__file__).resolve().parents[2]


def lid_cover_face_down(shape: Shape) -> Shape:
    rotated = Rot(180, 0, 0) * shape
    minimum = rotated.bounding_box().min
    return Pos(-minimum.X, -minimum.Y, -minimum.Z) * rotated


@dataclass(frozen=True)
class SkadisBoxParameters:
    enclosure: SlidingLidBoxParameters = field(default_factory=SlidingLidBoxParameters)
    seat_spacing_mm: float = 40.0
    seat_cut_radius_mm: float = 13.8


def build_design(profile: dict, params: SkadisBoxParameters = SkadisBoxParameters()) -> DesignSpec:
    enclosure = params.enclosure
    minimum_width = params.seat_spacing_mm + 2 * 14.1422
    if enclosure.width_mm < minimum_width:
        raise ValueError(f"width_mm must be at least {minimum_width:.2f} for two clip seats")
    if enclosure.height_mm < 2 * 14.1422:
        raise ValueError("height_mm is too small for the clip seat diameter")

    sliding_clearance = profile["measured_calibration"]["xy_clearance_sliding_mm"]
    box = build_sliding_lid_box(enclosure, sliding_clearance)
    seat_centers_x = (
        enclosure.width_mm / 2 - params.seat_spacing_mm / 2,
        enclosure.width_mm / 2 + params.seat_spacing_mm / 2,
    )
    seat_center_y = enclosure.height_mm / 2
    embedded = embed_t_clip_seats(
        box.body,
        ROOT / "models" / "ikea" / "Clip Seat.step",
        tuple((x, seat_center_y) for x in seat_centers_x),
        enclosure.back_wall_mm,
        params.seat_cut_radius_mm,
    )

    return DesignSpec(
        name="skadis_sliding_box",
        parts=(
            PartSpec(
                "box_body",
                embedded.shape,
                expected_bbox_mm=(enclosure.width_mm, enclosure.height_mm, enclosure.depth_mm),
            ),
            PartSpec(
                "sliding_lid",
                box.lid,
                expected_bbox_mm=box.lid_bbox_mm,
                print_shape=lid_cover_face_down(box.lid),
                slicer_process_preset_project_relative="profiles/slicer/ecc2_020_flat_lid_adhesion.json",
            ),
        ),
        parameters={
            "outer_dimensions_mm": [enclosure.width_mm, enclosure.height_mm, enclosure.depth_mm],
            "wall_mm": enclosure.wall_mm,
            "lid_style": "full_footprint_flat_print_optimized",
            "lid_print_orientation": "cover_face_down",
            "lid_tongue_thickness_mm": enclosure.lid_thickness_mm,
            "lid_cover_floor_mm": enclosure.lid_cover_floor_mm,
            "lid_recess_depth_mm": enclosure.lid_recess_depth_mm,
            "lid_total_thickness_mm": round(
                enclosure.depth_mm
                - box.assembled_translation_mm[2]
                + enclosure.lid_cover_floor_mm
                + enclosure.lid_recess_depth_mm,
                3,
            ),
            "sliding_clearance_mm_per_side": sliding_clearance,
            "seat_source": "models/ikea/Clip Seat.step",
            "seat_count": len(seat_centers_x),
            "seat_pitch_mm": params.seat_spacing_mm,
            "clip_source": "models/ikea/T-Clip for Painted Skadis.stl",
            "clip_variant": "painted_skadis",
            "printer": profile["printer"]["name"],
            "material": profile["material"]["type"],
        },
        motions=(
            MotionSpec(
                name="lid_vertical_insertion",
                fixed=embedded.shape,
                moving=box.lid,
                translations_mm=box.insertion_path_mm,
            ),
        ),
        checks=(
            DesignCheckSpec(
                name="clip_seat_slots_through_open",
                passed=max(embedded.slot_intersection_volumes_mm3) <= 0.001,
                measured={"intersection_volume_mm3": list(embedded.slot_intersection_volumes_mm3)},
                expected="each <= 0.001 mm3",
            ),
        ),
    )
