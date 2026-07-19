from pathlib import Path

from agentic_cad.runner import run


ROOT = Path(__file__).resolve().parents[1]


def test_skadis_box_generation_and_lid_motion(tmp_path: Path) -> None:
    report_path, report = run(
        ROOT / "models" / "python" / "skadis_sliding_box.py",
        ROOT / "profiles" / "elegoo_cc2_pla.json",
        tmp_path,
        enable_slicer=False,
    )

    assert report_path.exists()
    assert report["status"] == "pass"
    assert [part["name"] for part in report["parts"]] == ["box_body", "sliding_lid"]
    assert report["parameters"]["sliding_clearance_mm_per_side"] == 0.15
    assert report["parameters"]["lid_style"] == "raised_perimeter_stackable"
    assert report["parameters"]["lid_total_thickness_mm"] == 3.4
    assert report["parameters"]["seat_count"] == 2
    assert report["design_checks"][0]["name"] == "clip_seat_slots_through_open"
    assert report["design_checks"][0]["status"] == "pass"
    assert report["motion_checks"][0]["status"] == "pass"
