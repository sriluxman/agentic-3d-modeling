"""Clean printable trapezoidal threads: helical sweep, controlled phase.

A single trapezoid profile swept along a helix, root embedded into the host
surface for a robust fuse. The ridge starts and ends half a pitch inside the
threaded span, so its end caps sit in free air - no trimmed knife edges, no
tangent seams (the failure modes the integrity gates caught in the
bd_warehouse-generated threads).

Phase is deterministic: the ridge centerline passes angle 0 at ``z = start``.
``mating_rotation_deg`` returns the rotation that centers an internal ridge
in the external groove for a given axial position, so printed-in-place or
screwed-together threads interleave by construction and true boolean motion
checks of the threaded parts become possible.
"""

from __future__ import annotations

import math

from build123d import Align, Cylinder, Helix, Plane, Polygon, Shape, sweep

CREST_FRACTION = 0.366  # DIN trapezoidal proportions
ROOT_FRACTION = 0.634
EMBED = 0.5  # ridge root sinks well into the host so OCC imprints the seam robustly


def thread_depth(pitch: float) -> float:
    return pitch / 2


def backlash(pitch: float, fit_diametral: float) -> float:
    """Total axial flank backlash of a mated pair at the given diametral fit."""
    engagement = thread_depth(pitch) - fit_diametral / 2
    slope = (ROOT_FRACTION - CREST_FRACTION) * pitch / thread_depth(pitch)
    return pitch - 2 * CREST_FRACTION * pitch - slope * engagement


def _ridge(surface_radius: float, pitch: float, start: float, height: float, outward: bool) -> Shape:
    depth = thread_depth(pitch)
    w_crest = CREST_FRACTION * pitch
    w_root = ROOT_FRACTION * pitch
    sign = 1.0 if outward else -1.0
    profile = Polygon(
        (-sign * EMBED, -w_root / 2),
        (-sign * EMBED, w_root / 2),
        (sign * depth, w_crest / 2),
        (sign * depth, -w_crest / 2),
        align=None,
    )
    # Sweep one extra pitch past each end, then trim with horizontal planes:
    # the sweep's own end caps meet the host cylinder at a grazing 4-5 degree
    # angle whose intersection curve tessellates with amplified error (the
    # self-intersection gate measured ~0.5 mm crossings); horizontal trims
    # meet the host transversally and tessellate cleanly.
    helix = Helix(pitch=pitch, height=height + 2 * pitch, radius=surface_radius)
    plane = Plane(origin=(surface_radius, 0, 0), x_dir=(1, 0, 0), z_dir=tuple(helix % 0))
    ridge = sweep(plane * profile, path=helix, is_frenet=True).translate((0, 0, -pitch))
    slab_radius = surface_radius + depth + EMBED + 2.0
    slab = Cylinder(slab_radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return (ridge & slab).translate((0, 0, start))


def external_ridge(rod_radius: float, pitch: float, length: float) -> Shape:
    """Ridge to fuse onto a rod of ``rod_radius``; crest at rod + depth.
    Spans z in [pitch/2, length - pitch/2] with free-floating ends."""
    return _ridge(rod_radius, pitch, pitch / 2, length - pitch, outward=True)


def internal_ridge(bore_radius: float, pitch: float, length: float) -> Shape:
    """Ridge to fuse into a bore of ``bore_radius``; tip at bore - depth."""
    return _ridge(bore_radius, pitch, pitch / 2, length - pitch, outward=False)


def mating_rotation_deg(pitch: float, internal_z_offset: float) -> float:
    """Rotation for the internal ridge so it centers between external ridges.

    Both ridges follow z(theta) = start + theta/360 * pitch. An internal
    thread placed with its local z=0 at ``internal_z_offset`` needs its ridge
    centers shifted by half a pitch relative to the external ridge centers.
    """
    return ((internal_z_offset - pitch / 2) % pitch) / pitch * 360.0
