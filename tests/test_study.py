from pathlib import Path

import pytest

from agentic_cad.study import parse_grid, parse_value, run_study

ROOT = Path(__file__).resolve().parents[1]


def test_parse_value_types() -> None:
    assert parse_value("3") == 3
    assert parse_value("0.4") == 0.4
    assert parse_value("true") is True
    assert parse_value("pla") == "pla"


def test_parse_grid() -> None:
    grid = parse_grid(["wall_mm=1.2,2.0", "grip_clearance_mm=0.2"])
    assert grid == {"wall_mm": [1.2, 2.0], "grip_clearance_mm": [0.2]}
    with pytest.raises(ValueError):
        parse_grid(["broken"])


def test_cable_clip_study_ranks_and_rejects(tmp_path: Path) -> None:
    study_path, study = run_study(
        ROOT / "models" / "python" / "cable_clip.py",
        ROOT / "profiles" / "elegoo_cc2_pla.json",
        tmp_path,
        {"wall_mm": [1.2, 2.0], "grip_clearance_mm": [0.2, 0.4]},
        minimize="total_volume_mm3",
    )
    assert study_path.exists()
    assert (tmp_path / "study.md").exists()
    assert len(study["cases"]) == 4
    # loose grip (0.4 -> 0.2 mm gap) must fail the 0.15 mm band
    loose = [case for case in study["cases"] if case["overrides"]["grip_clearance_mm"] == 0.4]
    assert all(case["status"] == "fail" for case in loose)
    assert all("cable_grip_band" in case["failed_checks"] for case in loose)
    # recommendation is the lightest feasible candidate
    recommended = study["recommended"]
    assert recommended is not None
    assert recommended["overrides"] == {"wall_mm": 1.2, "grip_clearance_mm": 0.2}


def test_unknown_override_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(KeyError):
        run_study(
            ROOT / "models" / "python" / "cable_clip.py",
            ROOT / "profiles" / "elegoo_cc2_pla.json",
            tmp_path,
            {"not_a_parameter": [1.0]},
        )
