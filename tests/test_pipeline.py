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
    assert profile["measured_calibration"]["xy_clearance_sliding_evaluated_state"] == (
        "fully_cooled_off_build_plate"
    )
    assert len(profile["measured_calibration"]["xy_clearance_sliding_observations"]) == 3


def test_fit_calibration_pipeline(tmp_path: Path) -> None:
    report_path, report = run(
        ROOT / "models" / "python" / "fit_calibration.py",
        ROOT / "profiles" / "elegoo_cc2_pla.json",
        tmp_path,
        enable_slicer=False,
    )

    assert report_path.exists()
    assert report["status"] == "pass"
    assert len(report["parts"]) == 2
    assert all(part["freecad_step_roundtrip"]["status"] in {"pass", "not_run"} for part in report["parts"])
    assert len(report["motion_checks"]) == 5
    assert all(check["status"] == "pass" for check in report["motion_checks"])
