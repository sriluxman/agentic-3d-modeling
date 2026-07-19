"""Deep mesh interrogation: self-intersection and minimum wall thickness.

These fill the two checks the report previously declared ``not_run``:

- ``mesh_self_intersection``: exact triangle/triangle transversal-intersection
  test (Moller interval method) over KD-tree broadphase candidates. Pairs that
  share a vertex or merely touch within tolerance are not intersections.
  Coplanar overlaps are intentionally not flagged; they do not break slicing
  the way transversal self-intersections do.
- ``minimum_wall_thickness``: seeded surface sampling with inward ray-cast
  thickness, compared against a per-part or profile-derived minimum wall.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import trimesh
import trimesh.proximity
import trimesh.sample
from scipy.spatial import cKDTree

from .evaluate import check


_PAIR_CHUNK = 100_000


def _exclude_shared_vertex_pairs(faces: np.ndarray, pairs: np.ndarray) -> np.ndarray:
    left = faces[pairs[:, 0]]
    right = faces[pairs[:, 1]]
    shared = (left[:, :, None] == right[:, None, :]).any(axis=(1, 2))
    return pairs[~shared]


def _interval_on_line(projected: np.ndarray, distances: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Interval where each triangle crosses the intersection line.

    ``projected`` are the three vertices projected on the line, ``distances``
    are strictly nonzero signed distances to the other triangle's plane.
    """
    positive = distances > 0
    lone_is_positive = positive.sum(axis=1) == 1
    lone = np.where(lone_is_positive, positive.argmax(axis=1), (~positive).argmax(axis=1))
    rows = np.arange(len(projected))
    others = np.array([[1, 2], [0, 2], [0, 1]])[lone]
    apex = projected[rows, lone]
    apex_distance = distances[rows, lone]
    ends = []
    for column in (0, 1):
        base = projected[rows, others[:, column]]
        base_distance = distances[rows, others[:, column]]
        ends.append(apex + (base - apex) * apex_distance / (apex_distance - base_distance))
    return np.minimum(*ends), np.maximum(*ends)


def _transversal_pairs(triangles: np.ndarray, pairs: np.ndarray, tolerance: float) -> np.ndarray:
    first = triangles[pairs[:, 0]]
    second = triangles[pairs[:, 1]]
    normal_1 = np.cross(first[:, 1] - first[:, 0], first[:, 2] - first[:, 0])
    normal_2 = np.cross(second[:, 1] - second[:, 0], second[:, 2] - second[:, 0])
    length_1 = np.linalg.norm(normal_1, axis=1)
    length_2 = np.linalg.norm(normal_2, axis=1)
    valid = (length_1 > 0) & (length_2 > 0)

    safe_1 = np.where(length_1 == 0, 1.0, length_1)
    safe_2 = np.where(length_2 == 0, 1.0, length_2)
    distance_1 = np.einsum("ij,ikj->ik", normal_2, first - second[:, :1]) / safe_2[:, None]
    distance_2 = np.einsum("ij,ikj->ik", normal_1, second - first[:, :1]) / safe_1[:, None]
    # Clamp near-plane vertices to +tolerance: touching does not count as
    # intersecting, and coplanar pairs collapse to "same side".
    distance_1 = np.where(np.abs(distance_1) < tolerance, tolerance, distance_1)
    distance_2 = np.where(np.abs(distance_2) < tolerance, tolerance, distance_2)
    split_1 = ~(np.all(distance_1 > 0, axis=1) | np.all(distance_1 < 0, axis=1))
    split_2 = ~(np.all(distance_2 > 0, axis=1) | np.all(distance_2 < 0, axis=1))
    candidate = valid & split_1 & split_2
    if not candidate.any():
        return np.zeros(len(pairs), dtype=bool)

    direction = np.cross(normal_1[candidate], normal_2[candidate])
    direction_length = np.linalg.norm(direction, axis=1)
    parallel_safe = direction_length > tolerance
    direction = direction / np.where(direction_length == 0, 1.0, direction_length)[:, None]

    projected_1 = np.einsum("ij,ikj->ik", direction, first[candidate])
    projected_2 = np.einsum("ij,ikj->ik", direction, second[candidate])
    low_1, high_1 = _interval_on_line(projected_1, distance_1[candidate])
    low_2, high_2 = _interval_on_line(projected_2, distance_2[candidate])
    overlap = np.minimum(high_1, high_2) - np.maximum(low_1, low_2)

    result = np.zeros(len(pairs), dtype=bool)
    result[np.flatnonzero(candidate)] = parallel_safe & (overlap > tolerance)
    return result


def self_intersections(mesh: trimesh.Trimesh) -> dict[str, Any]:
    """Find transversal triangle/triangle self-intersections."""
    triangles = mesh.triangles
    tolerance = max(1e-9, 1e-6 * float(mesh.scale))
    centers = triangles.mean(axis=1)
    radii = np.linalg.norm(triangles - centers[:, None, :], axis=2).max(axis=1)
    pairs = cKDTree(centers).query_pairs(2.0 * float(radii.max()), output_type="ndarray")
    if len(pairs):
        near = np.linalg.norm(centers[pairs[:, 0]] - centers[pairs[:, 1]], axis=1)
        pairs = pairs[near <= radii[pairs[:, 0]] + radii[pairs[:, 1]]]
    if len(pairs):
        low = triangles.min(axis=1)
        high = triangles.max(axis=1)
        boxes_overlap = np.all(
            (low[pairs[:, 0]] <= high[pairs[:, 1]] + tolerance)
            & (low[pairs[:, 1]] <= high[pairs[:, 0]] + tolerance),
            axis=1,
        )
        pairs = pairs[boxes_overlap]
    if len(pairs):
        pairs = _exclude_shared_vertex_pairs(mesh.faces, pairs)

    intersecting: list[np.ndarray] = []
    for start in range(0, len(pairs), _PAIR_CHUNK):
        chunk = pairs[start : start + _PAIR_CHUNK]
        hits = _transversal_pairs(triangles, chunk, tolerance)
        intersecting.append(chunk[hits])
    hit_pairs = np.concatenate(intersecting) if intersecting else np.zeros((0, 2), dtype=int)

    locations = centers[hit_pairs[:, 0]][:10].tolist() if len(hit_pairs) else []
    return {
        "candidate_pairs": int(len(pairs)),
        "intersecting_pairs": int(len(hit_pairs)),
        "sample_locations_mm": locations,
    }


def wall_thickness(
    mesh: trimesh.Trimesh,
    minimum_required_mm: float,
    sample_count: int = 800,
    seed: int = 7,
) -> dict[str, Any]:
    """Sampled inward ray-cast wall thickness statistics."""
    points, face_index = trimesh.sample.sample_surface(mesh, sample_count, seed=seed)
    normals = mesh.face_normals[face_index]
    measured = trimesh.proximity.thickness(mesh, points, normals=normals, method="ray")
    measured = np.asarray(measured, dtype=float)
    finite = measured[np.isfinite(measured) & (measured > 0)]
    if len(finite) == 0:
        return {
            "status": "not_run",
            "reason": "No thickness rays returned a finite hit",
            "sample_count": sample_count,
        }
    return {
        "minimum_required_mm": minimum_required_mm,
        "minimum_measured_mm": float(finite.min()),
        "p05_mm": float(np.percentile(finite, 5)),
        "median_mm": float(np.percentile(finite, 50)),
        "samples_used": int(len(finite)),
        "samples_below_minimum": int((finite < minimum_required_mm).sum()),
        "seed": seed,
    }


def integrity_checks(
    mesh: trimesh.Trimesh,
    minimum_wall_mm: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run both interrogations and return (checks, metrics) like evaluate.*"""
    intersections = self_intersections(mesh)
    thickness = wall_thickness(mesh, minimum_wall_mm)

    results = [
        check(
            "mesh_self_intersection_free",
            intersections["intersecting_pairs"] == 0,
            intersections["intersecting_pairs"],
            0,
        )
    ]
    if thickness.get("status") == "not_run":
        results.append({"name": "minimum_wall_thickness_mm", **thickness})
    else:
        results.append(
            check(
                "minimum_wall_thickness_mm",
                thickness["minimum_measured_mm"] >= minimum_wall_mm,
                thickness["minimum_measured_mm"],
                f">= {minimum_wall_mm}",
            )
        )
    metrics = {"self_intersection": intersections, "wall_thickness": thickness}
    return results, metrics


def load_mesh(path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load_mesh(path, force="mesh", process=True, validate=True)
    if not isinstance(loaded, trimesh.Trimesh):
        raise TypeError(f"Expected one Trimesh from {path}")
    return loaded
