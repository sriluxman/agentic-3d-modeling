import json
from pathlib import Path

import pytest

from agentic_cad.annotate import load_annotations, write_annotate_html
from agentic_cad.openscad import find_openscad, render_scad
from agentic_cad.runner import run

ROOT = Path(__file__).resolve().parents[1]


def test_annotate_html_generated(tmp_path: Path) -> None:
    _, report = run(
        ROOT / "models" / "python" / "cable_clip.py",
        ROOT / "profiles" / "elegoo_cc2_pla.json",
        tmp_path,
        enable_slicer=False,
        enable_freecad=False,
    )
    path = Path(report["annotate_html"])
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "mm_from_view_center" in content
    assert "cable_clip" in content


def test_load_annotations_roundtrip(tmp_path: Path) -> None:
    payload = {
        "design": "demo",
        "schema_version": 1,
        "annotations": [
            {"id": 1, "part": "box", "view": "front (-Y)", "note": "chamfer",
             "svg_px": [100, 100], "mm_from_view_center": [-4.0, 2.0]}
        ],
    }
    path = tmp_path / "annotations.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    notes = load_annotations(path)
    assert notes[0]["note"] == "chamfer"
    with pytest.raises(ValueError):
        path.write_text(json.dumps({"nope": 1}), encoding="utf-8")
        load_annotations(path)


@pytest.mark.skipif(find_openscad() is None, reason="OpenSCAD not installed")
def test_render_scad_with_defines(tmp_path: Path) -> None:
    scad = tmp_path / "cube.scad"
    scad.write_text("size = 5;\ncube([size, size, size]);\n", encoding="utf-8")
    result = render_scad(scad, tmp_path / "cube.stl", defines={"size": 8})
    assert result["status"] == "pass"
    import trimesh

    mesh = trimesh.load_mesh(tmp_path / "cube.stl", force="mesh")
    assert abs(float(mesh.volume) - 512.0) < 1.0
