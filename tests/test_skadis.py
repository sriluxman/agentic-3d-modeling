from pathlib import Path

import pytest
from build123d import Box, Pos

from agentic_cad.contracts import MotionSpec
from agentic_cad.evaluate import motion_check
from agentic_cad.interfaces import skadis
from agentic_cad.runner import run

ROOT = Path(__file__).resolve().parents[1]


def test_board_coupon_geometry() -> None:
    board = skadis.board_coupon()
    bbox = board.bounding_box().size
    assert abs(bbox.Y - skadis.BOARD_THICKNESS) < 1e-6
    assert board.is_valid
    assert len(board.solids()) == 1


def test_t_clip_replica_envelope() -> None:
    clip = skadis.t_clip(skadis.stem_length_for(wall=2.4, standoff=3.0))
    bbox = clip.bounding_box().size
    assert abs(bbox.Z - skadis.BAR_LENGTH) < 1e-6
    assert abs(bbox.X - skadis.CLIP_THICKNESS) < 1e-6
    assert len(clip.solids()) == 1


def test_rotation_sampling_detects_twist_collision() -> None:
    # bar fits a slot lengthwise but collides when twisted 90 degrees inside it
    plate = Box(30, 4, 30) - Box(20, 5, 6)
    bar = Box(18, 4, 4)
    spec = MotionSpec(
        name="twist",
        fixed=plate,
        moving=bar,
        translations_mm=((0, 0, 0), (0, 0, 0)),
        rotations_deg=(0.0, 90.0),
        rotation_axis=((0, 0, 0), (0, 1, 0)),
    )
    result = motion_check(spec)
    assert result["status"] == "fail"
    assert result["samples"][0]["intersection_volume_mm3"] == 0.0
    assert result["samples"][1]["intersection_volume_mm3"] > 0
    assert result["samples"][1]["rotation_deg"] == 90.0


def test_rotation_validation() -> None:
    bar = Box(5, 5, 5)
    with pytest.raises(ValueError, match="rotation_axis"):
        motion_check(
            MotionSpec(
                name="bad",
                fixed=Pos(20, 0, 0) * Box(5, 5, 5),
                moving=bar,
                translations_mm=((0, 0, 0),),
                rotations_deg=(90.0,),
            )
        )
    with pytest.raises(ValueError, match="length"):
        motion_check(
            MotionSpec(
                name="bad",
                fixed=Pos(20, 0, 0) * Box(5, 5, 5),
                moving=bar,
                translations_mm=((0, 0, 0), (0, 1, 0)),
                rotations_deg=(90.0,),
                rotation_axis=((0, 0, 0), (0, 1, 0)),
            )
        )


def test_skadis_container_pipeline(tmp_path: Path) -> None:
    _, report = run(
        ROOT / "experiments" / "skadis-container" / "model.py",
        ROOT / "profiles" / "elegoo_cc2_pla.json",
        tmp_path,
        enable_slicer=False,
        enable_render=False,
        enable_freecad=False,
    )
    assert report["status"] == "pass"
    assert {part["name"] for part in report["parts"]} == {"container", "lid", "t_clip"}

    twist = next(m for m in report["motion_checks"] if m["name"] == "t_clip_insert_and_twist_lock")
    assert twist["status"] == "pass"
    assert twist["samples"][-1]["rotation_deg"] == 90.0
    assert twist["minimum_clearance_mm"] >= 0.03 - 1e-9

    assert {c["name"] for c in report["clearance_checks"]} == {
        "locked_clip_vs_board",
        "container_seats_on_board",
        "lid_in_groove",
    }
    assert all(c["status"] == "pass" for c in report["clearance_checks"])


def test_container_rejects_impossible_height(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="height_mm too small"):
        run(
            ROOT / "experiments" / "skadis-container" / "model.py",
            ROOT / "profiles" / "elegoo_cc2_pla.json",
            tmp_path,
            enable_slicer=False,
            enable_render=False,
            enable_freecad=False,
            overrides={"height_mm": 60.0},
        )


def test_skadis_slide_box_pipeline(tmp_path: Path) -> None:
    _, report = run(
        ROOT / "experiments" / "skadis-slide-box" / "model.py",
        ROOT / "profiles" / "elegoo_cc2_pla.json",
        tmp_path,
        enable_slicer=False,
        enable_render=False,
        enable_freecad=False,
    )
    assert report["status"] == "pass"
    assert {part["name"] for part in report["parts"]} == {"box_body", "sliding_lid"}
    # lid slides on TOP along the long axis - the original mechanism
    assert report["parameters"]["lid_style"].startswith("original_top_slide")
    assert "vendor part, unmodified" in report["parameters"]["print_clip"]
    # clearances come from the physically measured calibration
    assert report["parameters"]["sliding_clearance_mm_per_side"] == 0.25
    probe = next(c for c in report["design_checks"] if c["name"] == "clip_slots_through_open")
    assert probe["status"] == "pass"
    twist = next(m for m in report["motion_checks"] if m["name"] == "t_clip_insert_from_inside_and_twist")
    assert twist["status"] == "pass" and twist["samples"][-1]["rotation_deg"] == 90.0
