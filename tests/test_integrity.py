import trimesh

from agentic_cad.integrity import integrity_checks, self_intersections, wall_thickness


def test_clean_box_has_no_self_intersections() -> None:
    result = self_intersections(trimesh.creation.box((10, 10, 10)))
    assert result["intersecting_pairs"] == 0


def test_transversal_overlap_is_detected() -> None:
    a = trimesh.creation.box((10, 10, 10))
    b = trimesh.creation.box((10, 10, 10))
    b.apply_translation((4, 3, 5))
    result = self_intersections(trimesh.util.concatenate([a, b]))
    assert result["intersecting_pairs"] > 0
    assert result["sample_locations_mm"]


def test_face_to_face_touch_is_not_an_intersection() -> None:
    a = trimesh.creation.box((10, 10, 10))
    b = trimesh.creation.box((10, 10, 10))
    b.apply_translation((10, 0, 0))
    result = self_intersections(trimesh.util.concatenate([a, b]))
    assert result["intersecting_pairs"] == 0


def test_wall_thickness_measures_plate() -> None:
    result = wall_thickness(trimesh.creation.box((20, 20, 2)), 0.8)
    assert abs(result["minimum_measured_mm"] - 2.0) < 0.05
    assert result["samples_below_minimum"] == 0


def test_thin_wall_fails_gate() -> None:
    checks, metrics = integrity_checks(trimesh.creation.box((20, 20, 0.5)), 0.8)
    by_name = {item["name"]: item for item in checks}
    assert by_name["mesh_self_intersection_max_penetration_mm"]["status"] == "pass"
    assert by_name["minimum_wall_thickness_p05_mm"]["status"] == "fail"
    assert metrics["wall_thickness"]["samples_below_minimum"] > 0


def test_wall_thickness_is_deterministic() -> None:
    mesh = trimesh.creation.box((20, 20, 2))
    first = wall_thickness(mesh, 0.8)
    second = wall_thickness(mesh, 0.8)
    assert first["minimum_measured_mm"] == second["minimum_measured_mm"]
