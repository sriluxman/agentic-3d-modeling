"""Parametric cylindrical canister with a screw-on lid.

Uses the platform's clean thread generator (agentic_cad.threads): trapezoidal
45-degree printable ridges swept along a helix with free-floating ends, and
deterministic phase math so lid and body threads interleave by construction.
That makes TRUE threaded motion checks possible: the helical unscrew samples
run the real threaded lid against the real threaded body.

(The first attempt used a vendor thread library; the integrity gates rejected
its end treatments - knife-edge fades and tangent seams - which is why the
platform now owns thread generation.)
"""

from __future__ import annotations

from typing import Any

from build123d import Align, Cylinder, Pos, Rot

from agentic_cad import threads
from agentic_cad.contracts import ClearanceSpec, DesignCheckSpec, DesignSpec, MotionSpec, PartSpec

DEFAULTS: dict[str, Any] = {
    "inner_diameter_mm": 50.0,
    "height_mm": 60.0,
    "wall_mm": 2.4,
    "pitch_mm": 4.0,
    "thread_length_mm": 12.0,
    "thread_fit_mm": None,  # diametral; None -> max(1.0, 4 x measured clearance)
}


def build_design(profile: dict, overrides: dict[str, Any] | None = None) -> DesignSpec:
    parameters = dict(DEFAULTS)
    unknown = set(overrides or {}) - set(parameters)
    if unknown:
        raise KeyError(f"Unknown override(s) {sorted(unknown)}; supported: {sorted(parameters)}")
    parameters.update(overrides or {})

    inner_d = parameters["inner_diameter_mm"]
    height = parameters["height_mm"]
    wall = parameters["wall_mm"]
    pitch = parameters["pitch_mm"]
    thread_len = parameters["thread_length_mm"]
    measured = profile["measured_calibration"]["xy_clearance_sliding_mm"]
    if parameters["thread_fit_mm"] is None:
        parameters["thread_fit_mm"] = max(1.0, 4 * measured)
    fit = parameters["thread_fit_mm"]

    body_r = (inner_d + 2 * wall) / 2
    depth = threads.thread_depth(pitch)
    crest_r = body_r + depth
    bore_r = crest_r + fit / 2
    lid_od = 2 * bore_r + 2 * wall
    thread_z = height - thread_len

    # body: straight cylinder, external ridge band on the top section
    body = Cylinder(body_r, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body += Pos(0, 0, thread_z) * threads.external_ridge(body_r, pitch, thread_len)
    body -= Pos(0, 0, wall) * Cylinder(inner_d / 2, height, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # lid: skirt + cap; internal ridge phase-matched to the body ridge
    lid_z0 = thread_z - 0.5
    lid_h = thread_len + 0.5 + 1.0 + wall
    lid = Pos(0, 0, lid_z0) * Cylinder(lid_od / 2, lid_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    lid -= Pos(0, 0, lid_z0 - 1) * Cylinder(
        bore_r, thread_len + 0.5 + 1.0 + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    phase = threads.mating_rotation_deg(pitch, 0.0)  # both ridge bands start at thread_z
    lid += Pos(0, 0, thread_z) * Rot(0, 0, phase) * threads.internal_ridge(bore_r, pitch, thread_len)

    unscrew = MotionSpec(
        name="lid_unscrews_real_threads",
        fixed=body,
        moving=lid,
        translations_mm=((0, 0, 0), (0, 0, pitch), (0, 0, 2 * pitch), (0, 0, 30)),
        rotations_deg=(0.0, 360.0, 720.0, 0.0),
        rotation_axis=((0, 0, 0), (0, 0, 1)),
        min_clearance_mm=0.05,
    )

    return DesignSpec(
        name="screw_lid_canister",
        parts=(
            PartSpec("canister_body", body, expected_bbox_mm=(2 * crest_r, 2 * crest_r, height)),
            PartSpec(
                "screw_lid",
                lid,
                expected_bbox_mm=(lid_od, lid_od, lid_h),
                preferred_build_up=(0, 0, -1),  # print cap-down
            ),
        ),
        parameters={
            **parameters,
            "body_od_mm": 2 * body_r,
            "thread_crest_diameter_mm": 2 * crest_r,
            "lid_od_mm": lid_od,
            "predicted_flank_backlash_mm": round(threads.backlash(pitch, fit), 3),
            "printer": profile["printer"]["name"],
            "material": profile["material"]["type"],
        },
        motions=(unscrew,),
        clearances=(
            ClearanceSpec("lid_thread_engagement", lid, body, min_mm=0.05, max_mm=0.6),
        ),
        checks=(
            DesignCheckSpec(
                name="positive_flank_backlash",
                passed=threads.backlash(pitch, fit) > 0.05,
                measured=round(threads.backlash(pitch, fit), 3),
                expected="> 0.05 mm",
            ),
        ),
    )
