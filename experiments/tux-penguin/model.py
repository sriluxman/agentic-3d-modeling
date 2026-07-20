"""Tux the Linux Penguin – multi-color, support-free figurine.

Three print plates split by filament color:
  body_black:         body shell + head + wings  (black filament)
  belly_white:        belly patch + eye whites    (white filament)
  accessories_yellow: beak + two feet             (yellow/orange filament)

Color segmentation: each plate = one filament = one print job.
Assembly: press-fit into matching sockets (profile clearance).
Every piece prints support-free, flat-side-down.

Multi-body plates (white, yellow) are laid out on the bed so the slicer
sees all bodies starting from z=0 with no floating regions.
"""

from __future__ import annotations

import math
from typing import Any

from build123d import Align, Box, Cone, Cylinder, Pos, Rot, Sphere

from agentic_cad.contracts import (
    ClearanceSpec,
    DesignCheckSpec,
    DesignSpec,
    PartSpec,
)

C = Align.CENTER
N = Align.MIN
X = Align.MAX

DEFAULTS: dict[str, Any] = {
    "body_radius_mm": 27.0,
    "head_radius_mm": 18.0,
    "belly_radius_mm": 15.0,
    "belly_back_y_mm": 20.0,
    "wing_length_mm": 20.0,
    "wing_width_mm": 8.0,
    "wing_thick_mm": 4.0,
    "beak_base_mm": 5.0,
    "beak_tip_mm": 1.0,
    "beak_length_mm": 8.0,
    "foot_length_mm": 18.0,
    "foot_width_mm": 10.0,
    "foot_thick_mm": 4.0,
    "eye_radius_mm": 5.0,
    "eye_depth_mm": 2.5,
    "pupil_radius_mm": 2.5,
    "pupil_depth_mm": 1.2,
    "peg_diameter_mm": 3.0,
    "peg_length_mm": 4.0,
}


def _bed_layout(bodies, spacing=5.0):
    """Move each body so its bottom touches z=0, spread along X."""
    result = None
    x_cursor = 0.0
    for body in bodies:
        bb = body.bounding_box()
        dx = x_cursor - float(bb.min.X)
        dz = -float(bb.min.Z)
        moved = Pos(dx, 0, dz) * body
        result = moved if result is None else result + moved
        x_cursor += float(bb.size.X) + spacing
    return result


def build_design(
    profile: dict, overrides: dict[str, Any] | None = None
) -> DesignSpec:
    p = dict(DEFAULTS)
    if unknown := set(overrides or {}) - set(p):
        raise KeyError(f"Unknown override(s): {sorted(unknown)}")
    p.update(overrides or {})

    cl = profile["measured_calibration"]["xy_clearance_sliding_mm"]
    body_r = p["body_radius_mm"]
    head_r = p["head_radius_mm"]
    belly_r = p["belly_radius_mm"]
    belly_back_y = p["belly_back_y_mm"]
    eye_r = p["eye_radius_mm"]
    eye_d = p["eye_depth_mm"]
    pupil_r = p["pupil_radius_mm"]
    pupil_d = p["pupil_depth_mm"]
    peg_r = p["peg_diameter_mm"] / 2
    peg_l = p["peg_length_mm"]

    body_cz = body_r
    head_cz = body_cz + body_r + head_r - 12
    total_h = head_cz + head_r
    belly_cz = body_cz

    body_front_y = math.sqrt(max(0, body_r**2 - (belly_cz - body_cz) ** 2))

    def _neg_y_cyl(radius, length, origin):
        return Pos(*origin) * Rot(90, 0, 0) * Cylinder(radius, length, align=(C, C, N))

    big = 200.0

    # ── FULL BODY (two fused spheres, flat bottom at z=0) ────
    body_ball = Pos(0, 0, body_cz) * Sphere(body_r)
    head_ball = Pos(0, 0, head_cz) * Sphere(head_r)
    full = (body_ball + head_ball) - Pos(0, 0, -big / 2) * Box(big, big, big, align=(C, C, C))

    # ── BELLY PATCH (white, assembled position) ──────────────
    belly_cyl = Pos(0, 0, belly_cz) * Rot(-90, 0, 0) * Cylinder(belly_r, big, align=(C, C, C))
    belly_raw = full & belly_cyl
    back_cut = Pos(0, belly_back_y, 0) * Box(big, big, big, align=(C, X, C))
    belly_patch = belly_raw - back_cut

    # ── EYE WHITES (white, assembled position) ───────────────
    eye_z = head_cz + head_r * 0.12
    eye_x_off = head_r * 0.38
    eye_y_surf = math.sqrt(
        max(0, head_r**2 - eye_x_off**2 - (eye_z - head_cz) ** 2)
    )
    eye_socket_d = eye_d + 1.0

    eye_bodies = []
    for sx in (1, -1):
        disc = Cylinder(eye_r, eye_d, align=(C, C, N))
        disc -= Pos(0, 0, eye_d - pupil_d) * Cylinder(pupil_r, pupil_d + 0.1, align=(C, C, N))
        placed = (
            Pos(sx * eye_x_off, eye_y_surf - eye_socket_d + head_r * 0.02, eye_z)
            * Rot(-90, 0, 0)
            * disc
        )
        eye_bodies.append(placed)

    belly_white_assembled = belly_patch
    for e in eye_bodies:
        belly_white_assembled = belly_white_assembled + e

    belly_white_print = _bed_layout([belly_patch] + eye_bodies)

    # ── BODY BLACK ───────────────────────────────────────────
    body_black = full

    belly_sock_cyl = Pos(0, 0, belly_cz) * Rot(-90, 0, 0) * Cylinder(belly_r + cl, big, align=(C, C, C))
    belly_sock_raw = full & belly_sock_cyl
    belly_sock_cut = Pos(0, belly_back_y - cl, 0) * Box(big, big, big, align=(C, X, C))
    body_black -= belly_sock_raw - belly_sock_cut

    for sx in (1, -1):
        body_black -= (
            Pos(sx * eye_x_off, eye_y_surf - eye_socket_d - 0.5, eye_z)
            * Rot(-90, 0, 0)
            * Cylinder(eye_r + cl, eye_socket_d + 1.0, align=(C, C, N))
        )

    beak_z = head_cz - head_r * 0.18
    beak_front_y = math.sqrt(max(0, head_r**2 - (beak_z - head_cz) ** 2))
    beak_peg_r = p["beak_base_mm"] * 0.5
    beak_socket_d = 3.5
    body_black -= _neg_y_cyl(
        beak_peg_r + cl, beak_socket_d + 0.5,
        (0, beak_front_y + 0.5, beak_z),
    )

    foot_x = body_r * 0.35
    foot_y = body_r * 0.25
    for sx in (1, -1):
        body_black -= Pos(sx * foot_x, foot_y, 0) * Cylinder(
            peg_r + cl, peg_l + 0.5, align=(C, C, N)
        )

    wl, ww, wt = p["wing_length_mm"], p["wing_width_mm"], p["wing_thick_mm"]
    wing_z = body_cz + 3
    for sx in (1, -1):
        wing = Box(wt, ww, wl, align=(C, C, N))
        body_black += (
            Pos(sx * (body_r - 1), -3, wing_z)
            * Rot(sx * 15, 0, 0)
            * wing
        )

    # ── YELLOW ACCESSORIES (assembled + print layout) ────────
    beak_cone = Rot(-90, 0, 0) * Cone(
        p["beak_base_mm"], p["beak_tip_mm"], p["beak_length_mm"], align=(C, C, N)
    )
    beak_peg = Rot(90, 0, 0) * Cylinder(beak_peg_r, beak_socket_d, align=(C, C, N))
    beak = Pos(0, beak_front_y, beak_z) * (beak_cone + beak_peg)

    fl, fw, ft = p["foot_length_mm"], p["foot_width_mm"], p["foot_thick_mm"]
    foot_bodies = []
    for sx in (1, -1):
        foot = Pos(0, 0, -ft) * Box(fw, fl, ft, align=(C, C, N))
        foot += Cylinder(peg_r, peg_l, align=(C, C, N))
        foot_bodies.append(Pos(sx * foot_x, foot_y, 0) * foot)

    yellow_assembled = beak
    for f in foot_bodies:
        yellow_assembled = yellow_assembled + f

    yellow_print = _bed_layout([beak] + foot_bodies)

    # ── DESIGN SPEC ──────────────────────────────────────────
    def _bb(shape):
        bb = shape.bounding_box().size
        return (round(float(bb.X), 1), round(float(bb.Y), 1), round(float(bb.Z), 1))

    return DesignSpec(
        name="tux_penguin",
        parts=(
            PartSpec("body_black", body_black,
                     expected_bbox_mm=_bb(body_black), expected_bodies=1),
            PartSpec("belly_white", belly_white_print,
                     expected_bbox_mm=_bb(belly_white_print), expected_bodies=3),
            PartSpec("accessories_yellow", yellow_print,
                     expected_bbox_mm=_bb(yellow_print), expected_bodies=3),
        ),
        parameters={
            **p,
            "clearance_mm": cl,
            "total_height_mm": round(total_h, 1),
            "colors": "black body, white belly+eyes, yellow beak+feet",
            "assembly": "press-fit dowels, no glue needed",
            "print_note": "each plate flat-side-down, no supports",
            "printer": profile["printer"]["name"],
            "material": profile["material"]["type"],
        },
        clearances=(
            ClearanceSpec("belly_fit", belly_white_assembled, body_black,
                         min_mm=0.05, max_mm=1.0),
        ),
        checks=(
            DesignCheckSpec(
                "total_height",
                passed=abs(float(full.bounding_box().size.Z) - total_h) < 1.0,
                measured=round(float(full.bounding_box().size.Z), 1),
                expected=round(total_h, 1),
            ),
        ),
    )
