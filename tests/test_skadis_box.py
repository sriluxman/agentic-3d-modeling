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
    assert report["parameters"]["sliding_clearance_mm_per_side"] == 0.25
    assert report["parameters"]["lid_style"] == "full_footprint_flat_print_optimized"
    assert report["parameters"]["lid_print_orientation"] == "cover_face_down"
    assert report["parameters"]["lid_tongue_thickness_mm"] == 1.4
    assert report["parameters"]["lid_total_thickness_mm"] == 4.65
    assert report["parameters"]["seat_count"] == 2
    assert report["design_checks"][0]["name"] == "clip_seat_slots_through_open"
    assert report["design_checks"][0]["status"] == "pass"
    assert report["motion_checks"][0]["status"] == "pass"
    assert report["parts"][1]["print_orientation"] == "custom"
    lid_print_metrics = report["parts"][1]["mesh_metrics"]["preferred_orientation"]
    assert lid_print_metrics["bed_contact_area_mm2"] >= 3750
    assert lid_print_metrics["overhang_area_mm2"] <= 120
