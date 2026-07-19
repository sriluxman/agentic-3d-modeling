"""Parametric C-clip for a round cable - reference model for the new contracts.

Demonstrates the full evidence set: a static ClearanceSpec grip band (a loose
fit fails just like an interfering one), a MotionSpec axial insertion with a
demanded minimum running clearance, and an overridable parameter set so
`agentic-cad-study` can search the design space.

The radial snap-in through the opening needs compliant flexing, which rigid
translation sampling cannot prove; the verified insertion path is axial.
"""

from __future__ import annotations

import math
from typing import Any

from build123d import Align, Cylinder, Pos, Rot

from agentic_cad.contracts import ClearanceSpec, DesignSpec, MotionSpec, PartSpec

DEFAULTS: dict[str, Any] = {
    "cable_diameter_mm": 6.0,
    "grip_clearance_mm": 0.2,  # diametral
    "wall_mm": 2.0,
    "opening_deg": 60.0,
    "clip_length_mm": 10.0,
}


def build_design(profile: dict, overrides: dict[str, Any] | None = None) -> DesignSpec:
    parameters = dict(DEFAULTS)
    unknown = set(overrides or {}) - set(parameters)
    if unknown:
        raise KeyError(f"Unknown override(s) {sorted(unknown)}; supported: {sorted(parameters)}")
    parameters.update(overrides or {})

    cable_d = parameters["cable_diameter_mm"]
    grip = parameters["grip_clearance_mm"]
    wall = parameters["wall_mm"]
    opening = parameters["opening_deg"]
    length = parameters["clip_length_mm"]

    inner_r = (cable_d + grip) / 2
    outer_r = inner_r + wall

    clip = Cylinder(outer_r, length) - Cylinder(inner_r, length)
    # Align.NONE keeps the sector apex on the cylinder axis; bbox-centering
    # (the default) would shift the wedge off-center and miss the wall.
    wedge = Rot(0, 0, -opening / 2) * Cylinder(
        outer_r + 1.0,
        length,
        arc_size=opening,
        align=(Align.NONE, Align.NONE, Align.CENTER),
    )
    clip -= wedge

    # The raw wedge-to-bore intersection leaves feather-edge lips that the
    # wall-thickness gate rejects (~0.6 mm knife edges). Round lip beads,
    # flush with the bore, restore printable thickness and guide the cable in.
    half_opening = math.radians(opening / 2)
    lip_center_r = (inner_r + outer_r) / 2
    lip_r = lip_center_r - inner_r
    for sign in (1.0, -1.0):
        angle = sign * half_opening
        clip += Pos(lip_center_r * math.cos(angle), lip_center_r * math.sin(angle), 0) * Cylinder(
            lip_r, length
        )

    cable = Cylinder(cable_d / 2, 20.0)

    expected_bbox = (
        max(outer_r * (1 + math.cos(half_opening)), outer_r + math.cos(half_opening) * lip_center_r + lip_r),
        2 * outer_r,
        length,
    )

    insertion = MotionSpec(
        name="cable_axial_insertion",
        fixed=clip,
        moving=cable,
        translations_mm=tuple((0.0, 0.0, z) for z in (20.0, 14.0, 8.0, 4.0, 0.0)),
        min_clearance_mm=0.05,
    )
    grip_band = ClearanceSpec(
        name="cable_grip_band",
        a=clip,
        b=cable,
        min_mm=0.03,
        max_mm=0.15,
    )

    return DesignSpec(
        name="cable_clip",
        parts=(
            PartSpec(
                "cable_clip",
                clip,
                expected_bbox_mm=expected_bbox,
                preferred_build_up=(0, 0, 1),
            ),
        ),
        parameters={
            **parameters,
            "printer": profile["printer"]["name"],
            "material": profile["material"]["type"],
        },
        motions=(insertion,),
        clearances=(grip_band,),
    )
