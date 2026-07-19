from pathlib import Path

from agentic_cad.profile import load_profile
from agentic_cad.runner import run


ROOT = Path(__file__).resolve().parents[1]


def test_profile_is_complete() -> None:
    profile = load_profile(ROOT / "profiles" / "elegoo_cc2_pla.json")
    assert profile["printer"]["nozzle_diameter_mm"] == 0.4
    assert profile["material"]["type"] == "PLA+"
    assert profile["measured_calibration"]["xy_clearance_sliding_mm"] == 0.25
    assert profile["measured_calibration"]["xy_clearance_sliding_basis"] == "per_side"


def test_fit_calibration_pipeline(tmp_path: Path) -> None:
    report_path, report = run(
        ROOT / "models" / "python" / "fit_calibration.py",
        ROOT / "profiles" / "elegoo_cc2_pla.json",
        tmp_path,
        enable_slicer=False,
    )

    assert report_path.exists()
    assert report["schema_version"] == 2
    assert report["status"] == "pass"
    assert len(report["parts"]) == 2
    assert all(part["freecad_step_roundtrip"]["status"] in {"pass", "not_run"} for part in report["parts"])
    assert len(report["motion_checks"]) == 5
    assert all(check["status"] == "pass" for check in report["motion_checks"])

    # schema 2 evidence: integrity checks, measured clearance, renders, HTML
    for part in report["parts"]:
        names = {item["name"] for item in part["checks"]}
        assert {"mesh_self_intersection_free", "minimum_wall_thickness_mm"} <= names
        assert Path(part["renders"]["views"]["path"]).exists()
    for motion in report["motion_checks"]:
        assert "minimum_clearance_mm" in motion
        assert all("clearance_mm" in sample for sample in motion["samples"])
    assert Path(report["html_report"]).exists()


def test_fit_calibration_override_changes_geometry(tmp_path: Path) -> None:
    _, report = run(
        ROOT / "models" / "python" / "fit_calibration.py",
        ROOT / "profiles" / "elegoo_cc2_pla.json",
        tmp_path,
        enable_slicer=False,
        enable_render=False,
        enable_freecad=False,
        overrides={"plate_thickness_mm": 3.0},
    )
    assert report["status"] == "pass"
    plate = next(part for part in report["parts"] if part["name"] == "clearance_plate")
    assert abs(plate["brep_metrics"]["bounding_box_mm"][2] - 3.0) < 0.01


def test_cable_clip_pipeline_with_clearance_band(tmp_path: Path) -> None:
    _, report = run(
        ROOT / "models" / "python" / "cable_clip.py",
        ROOT / "profiles" / "elegoo_cc2_pla.json",
        tmp_path,
        enable_slicer=False,
        enable_freecad=False,
    )
    assert report["status"] == "pass"
    assert len(report["clearance_checks"]) == 1
    band = report["clearance_checks"][0]
    assert band["status"] == "pass"
    assert 0.03 <= band["measured_gap_mm"] <= 0.15
    motion = report["motion_checks"][0]
    assert motion["minimum_clearance_mm"] >= 0.05 - 1e-9
