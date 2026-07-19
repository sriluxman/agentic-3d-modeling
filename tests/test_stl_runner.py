from pathlib import Path

import trimesh

from agentic_cad.stl_runner import evaluate_stl


ROOT = Path(__file__).resolve().parents[1]


def test_existing_stl_evaluation_without_slicer(tmp_path: Path) -> None:
    stl_path = tmp_path / "box.stl"
    trimesh.creation.box(extents=(10, 8, 4)).export(stl_path)

    report_path, report = evaluate_stl(
        stl_path,
        ROOT / "profiles" / "elegoo_cc2_pla.json",
        tmp_path / "report",
        expected_bodies=1,
        enable_slicer=False,
    )

    assert report_path.exists()
    assert report["status"] == "pass"
    assert report["metrics"]["body_count"] == 1
    assert report["slicer"]["status"] == "not_run"


def test_existing_stl_forwards_process_preset(tmp_path: Path, monkeypatch) -> None:
    stl_path = tmp_path / "box.stl"
    trimesh.creation.box(extents=(10, 8, 4)).export(stl_path)
    received = {}

    def fake_slice(stl, output, profile, process_preset_project_relative=None):
        received["preset"] = process_preset_project_relative
        return {"status": "pass"}

    monkeypatch.setattr("agentic_cad.stl_runner.slice_stl", fake_slice)
    _, report = evaluate_stl(
        stl_path,
        ROOT / "profiles" / "elegoo_cc2_pla.json",
        tmp_path / "report",
        process_preset_project_relative="profiles/slicer/test.json",
    )

    assert received["preset"] == "profiles/slicer/test.json"
    assert report["process_preset"] == "profiles/slicer/test.json"
