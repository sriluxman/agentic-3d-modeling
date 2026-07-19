from pathlib import Path

import trimesh

from agentic_cad.render import render_sections_svg, render_views_svg


def test_views_svg_written(tmp_path: Path) -> None:
    mesh = trimesh.creation.box((10, 6, 4))
    result = render_views_svg(mesh, tmp_path / "box.views.svg", "box")
    content = (tmp_path / "box.views.svg").read_text(encoding="utf-8")
    assert result["views"] == ["isometric", "front (-Y)", "top (+Z)", "right (+X)"]
    assert content.startswith("<svg")
    assert "<polygon" in content
    assert "10 mm" in content


def test_sections_svg_written(tmp_path: Path) -> None:
    mesh = trimesh.creation.box((10, 6, 4))
    result = render_sections_svg(mesh, tmp_path / "box.sections.svg", "box")
    assert result is not None
    content = (tmp_path / "box.sections.svg").read_text(encoding="utf-8")
    assert "<polyline" in content
    assert len(result["sections"]) == 3
