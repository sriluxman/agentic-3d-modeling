from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import trimesh
from build123d import Pos, Shape

from .contracts import ClearanceSpec, MotionSpec, PartSpec


def check(name: str, passed: bool, measured: Any = None, expected: Any = None) -> dict[str, Any]:
    result = {"name": name, "status": "pass" if passed else "fail"}
    if measured is not None:
        result["measured"] = measured
    if expected is not None:
        result["expected"] = expected
    return result


def brep_checks(part: PartSpec) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    bbox = part.shape.bounding_box().size
    measured_bbox = [bbox.X, bbox.Y, bbox.Z]
    expected_bbox = list(part.expected_bbox_mm)
    bbox_ok = all(
        abs(actual - expected) <= part.bbox_tolerance_mm
        for actual, expected in zip(measured_bbox, expected_bbox)
    )
    solid_count = len(part.shape.solids())
    results = [
        check("brep_valid", bool(part.shape.is_valid), bool(part.shape.is_valid), True),
        check("positive_volume", part.shape.volume > 0, part.shape.volume, "> 0"),
        check("solid_count", solid_count == part.expected_bodies, solid_count, part.expected_bodies),
        check("bounding_box_mm", bbox_ok, measured_bbox, expected_bbox),
    ]
    metrics = {"volume_mm3": part.shape.volume, "bounding_box_mm": measured_bbox}
    return results, metrics


def _orientation_metrics(mesh: trimesh.Trimesh, up: np.ndarray, overhang_deg: float = 45.0) -> dict[str, Any]:
    up = up / np.linalg.norm(up)
    center_heights = mesh.triangles_center @ up
    minimum = float((mesh.vertices @ up).min())
    normal_dot = mesh.face_normals @ up
    unsupported = (normal_dot < -math.sin(math.radians(overhang_deg))) & (center_heights > minimum + 0.05)
    bed = (normal_dot < -0.995) & (center_heights <= minimum + 0.05)
    overhang_area = float(mesh.area_faces[unsupported].sum())
    bed_area = float(mesh.area_faces[bed].sum())
    return {
        "build_up": [int(value) for value in up],
        "overhang_area_mm2": overhang_area,
        "bed_contact_area_mm2": bed_area,
        "score": overhang_area - 0.05 * bed_area,
    }


def orientation_search(mesh: trimesh.Trimesh) -> list[dict[str, Any]]:
    axes = (
        np.array((1.0, 0.0, 0.0)),
        np.array((-1.0, 0.0, 0.0)),
        np.array((0.0, 1.0, 0.0)),
        np.array((0.0, -1.0, 0.0)),
        np.array((0.0, 0.0, 1.0)),
        np.array((0.0, 0.0, -1.0)),
    )
    return sorted((_orientation_metrics(mesh, axis) for axis in axes), key=lambda item: item["score"])


def mesh_checks(path: Path, part: PartSpec) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    loaded = trimesh.load_mesh(path, force="mesh", process=True, validate=True)
    if not isinstance(loaded, trimesh.Trimesh):
        raise TypeError(f"Expected one Trimesh from {path}")

    body_count = int(loaded.body_count)
    nondegenerate = bool(np.all(loaded.nondegenerate_faces()))
    orientations = orientation_search(loaded)
    preferred = list(part.preferred_build_up)
    preferred_result = next(item for item in orientations if item["build_up"] == preferred)
    best = orientations[0]

    results = [
        check("mesh_watertight", bool(loaded.is_watertight), bool(loaded.is_watertight), True),
        check("winding_consistent", bool(loaded.is_winding_consistent), bool(loaded.is_winding_consistent), True),
        check("mesh_is_volume", bool(loaded.is_volume), bool(loaded.is_volume), True),
        check("mesh_body_count", body_count == part.expected_bodies, body_count, part.expected_bodies),
        check("nondegenerate_faces", nondegenerate, nondegenerate, True),
    ]
    metrics = {
        "triangles": len(loaded.faces),
        "surface_area_mm2": float(loaded.area),
        "volume_mm3": float(loaded.volume),
        "orientation_search": orientations,
        "preferred_orientation": preferred_result,
        "recommended_build_up": best["build_up"],
    }
    return results, metrics


def motion_check(spec: MotionSpec) -> dict[str, Any]:
    samples = []
    worst = 0.0
    tightest = math.inf
    for translation in spec.translations_mm:
        placed = Pos(*translation) * spec.moving
        intersection = spec.fixed & placed
        volume = float(intersection.volume) if intersection else 0.0
        clearance = float(spec.fixed.distance_to(placed)) if volume == 0.0 else 0.0
        worst = max(worst, volume)
        tightest = min(tightest, clearance)
        samples.append(
            {
                "translation_mm": list(translation),
                "intersection_volume_mm3": volume,
                "clearance_mm": clearance,
            }
        )

    collision_free = worst <= spec.max_intersection_volume_mm3
    # 1e-9 guard so boundary-exact fits are not decided by float noise
    clearance_ok = tightest >= spec.min_clearance_mm - 1e-9
    return {
        "name": spec.name,
        "status": "pass" if collision_free and clearance_ok else "fail",
        "maximum_intersection_volume_mm3": worst,
        "allowed_intersection_volume_mm3": spec.max_intersection_volume_mm3,
        "minimum_clearance_mm": tightest if samples else None,
        "required_clearance_mm": spec.min_clearance_mm,
        "samples": samples,
    }


def clearance_check(spec: ClearanceSpec) -> dict[str, Any]:
    intersection = spec.a & spec.b
    interference = float(intersection.volume) if intersection else 0.0
    gap = float(spec.a.distance_to(spec.b)) if interference == 0.0 else 0.0
    within_band = interference == 0.0 and gap >= spec.min_mm - 1e-9
    if spec.max_mm is not None:
        within_band = within_band and gap <= spec.max_mm + 1e-9
    return {
        "name": spec.name,
        "status": "pass" if within_band else "fail",
        "interference_volume_mm3": interference,
        "measured_gap_mm": gap,
        "required_gap_mm": [spec.min_mm, spec.max_mm],
    }
