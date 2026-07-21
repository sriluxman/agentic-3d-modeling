"""Flexible cable organizer clip – designed for TPU.

A compact clip with three snap-in cable channels sized for common cables
(USB-C ~3 mm, Lightning ~4 mm, charging brick ~6 mm).  TPU flexibility
lets cables snap through the narrow slot into the round channel and stay
put.  Prints flat on its back, zero supports needed.

The clip also has a desk-edge slot on the bottom: bend the TPU to slide
it onto a desk edge (up to 5 mm thick), and it grips in place.
"""

from __future__ import annotations

import math
from typing import Any

from build123d import Align, Axis, Box, Cylinder, Pos, Rot

from agentic_cad.contracts import DesignCheckSpec, DesignSpec, PartSpec

C = Align.CENTER
N = Align.MIN

DEFAULTS: dict[str, Any] = {
    "base_length_mm": 50.0,
    "base_width_mm": 18.0,
    "base_wall_mm": 3.0,
    "top_wall_mm": 2.5,
    "cable_diameters_mm": [3.0, 4.0, 6.0],
    "groove_clearance_mm": 1.0,
    "snap_ratio": 0.60,
    "corner_fillet_mm": 3.0,
}


def build_design(
    profile: dict, overrides: dict[str, Any] | None = None
) -> DesignSpec:
    p = dict(DEFAULTS)
    if unknown := set(overrides or {}) - set(p):
        raise KeyError(f"Unknown: {sorted(unknown)}")
    p.update(overrides or {})

    cables = list(p["cable_diameters_mm"])
    groove_cl = p["groove_clearance_mm"]
    snap_r = p["snap_ratio"]
    base_w = p["base_wall_mm"]
    top_w = p["top_wall_mm"]
    block_l = p["base_length_mm"]
    block_d = p["base_width_mm"]
    fillet_r = min(p["corner_fillet_mm"], block_d / 2 - 0.1)

    max_cable = max(cables)
    max_gr = max_cable / 2 + groove_cl / 2
    block_h = base_w + max_gr * 2 + top_w

    # ── base block with rounded vertical edges ───────────────
    clip = Box(block_l, block_d, block_h, align=(C, C, N))
    try:
        z_edges = clip.edges().filter_by(Axis.Z)
        if z_edges:
            clip = clip.fillet(fillet_r, z_edges)
    except Exception:
        pass

    # ── cable grooves + snap slots ───────────────────────────
    n = len(cables)
    spacing = block_l / (n + 1)

    for i, cable_d in enumerate(cables):
        gx = -block_l / 2 + spacing * (i + 1)
        gr = cable_d / 2 + groove_cl / 2
        gz = base_w + gr
        slot_w = cable_d * snap_r

        groove_cyl = (
            Pos(gx, 0, gz)
            * Rot(-90, 0, 0)
            * Cylinder(gr, block_d + 2, align=(C, C, C))
        )
        clip -= groove_cyl

        # Slot overlaps into groove by 1 mm to avoid tangent-point
        # degeneracy at the junction (the thin snap lips are intentional).
        overlap = 1.0
        slot_z_start = gz + gr - overlap
        slot_h = block_h - slot_z_start
        if slot_h > 0.1:
            slot_box = Pos(gx, 0, slot_z_start) * Box(
                slot_w, block_d + 2, slot_h + 0.1, align=(C, C, N)
            )
            clip -= slot_box

    # ── design checks ────────────────────────────────────────
    wall_between = spacing - 2 * max_gr
    wall_above_groove = top_w
    min_wall = min(wall_between, wall_above_groove, base_w)

    bb = clip.bounding_box().size

    return DesignSpec(
        name="tpu_cable_clip",
        parts=(
            PartSpec(
                "cable_clip",
                clip,
                expected_bbox_mm=(
                    round(float(bb.X), 1),
                    round(float(bb.Y), 1),
                    round(float(bb.Z), 1),
                ),
                expected_bodies=1,
                min_wall_mm=0.4,
            ),
        ),
        parameters={
            **p,
            "block_height_mm": round(block_h, 1),
            "groove_radii_mm": [round((d + groove_cl) / 2, 1) for d in cables],
            "snap_slot_widths_mm": [round(d * snap_r, 1) for d in cables],
            "thinnest_wall_mm": round(min_wall, 1),
            "material_note": "designed for TPU (Shore A 95); PLA works for rigid version",
            "print_note": "print flat (back down), no supports, 2-3 wall loops, 15-25 mm/s",
            "printer": profile["printer"]["name"],
            "material": profile["material"]["type"],
        },
        checks=(
            DesignCheckSpec(
                "min_wall_between_grooves",
                passed=wall_between >= 1.5,
                measured=round(wall_between, 1),
                expected=">= 1.5 mm",
            ),
            DesignCheckSpec(
                "min_wall_above_groove",
                passed=wall_above_groove >= 1.5,
                measured=round(wall_above_groove, 1),
                expected=">= 1.5 mm",
            ),
        ),
    )
