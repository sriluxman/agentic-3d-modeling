"""Self-contained HTML design review generated from a run report.

One file, no external assets: renders (SVG) are inlined, every check is a
color-coded row, and motion samples show measured clearance. Written for two
readers - the human reviewing a design, and an agent screenshotting evidence.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

_CSS = """
body { font-family: system-ui, sans-serif; margin: 0; background: #f2f5f8; color: #1a2733; }
main { max-width: 1180px; margin: 0 auto; padding: 24px; }
h1 { font-size: 26px; margin: 8px 0 2px; }
h2 { font-size: 19px; margin: 28px 0 10px; }
h3 { font-size: 16px; margin: 20px 0 8px; }
.banner { padding: 14px 18px; border-radius: 10px; font-weight: 600; font-size: 17px; margin: 14px 0; }
.banner.pass { background: #e2f4e6; color: #17692c; border: 1px solid #b9e2c3; }
.banner.fail { background: #fbe4e6; color: #9c1f2e; border: 1px solid #f2c3c8; }
.card { background: #fff; border: 1px solid #dde4ea; border-radius: 10px; padding: 16px 18px; margin: 14px 0; }
table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid #e8edf2; }
th { color: #51606e; font-weight: 600; }
.status { font-weight: 700; padding: 1px 9px; border-radius: 9px; font-size: 12px; display: inline-block; }
.status.pass { background: #e2f4e6; color: #17692c; }
.status.fail { background: #fbe4e6; color: #9c1f2e; }
.status.not_run { background: #eef1f4; color: #51606e; }
.meta { color: #51606e; font-size: 13px; }
.render { overflow-x: auto; margin: 8px 0; }
.render svg { max-width: 100%; height: auto; }
code { background: #eef1f4; padding: 1px 5px; border-radius: 4px; font-size: 12.5px; }
"""


def _status(value: str) -> str:
    return f'<span class="status {html.escape(value)}">{html.escape(value)}</span>'


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    if isinstance(value, list):
        return ", ".join(_fmt(item) for item in value)
    return html.escape(str(value))


def _check_rows(checks: list[dict[str, Any]]) -> str:
    rows = []
    for item in checks:
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['name'])}</td>"
            f"<td>{_status(item['status'])}</td>"
            f"<td>{_fmt(item.get('measured', ''))}</td>"
            f"<td>{_fmt(item.get('expected', item.get('reason', '')))}</td>"
            "</tr>"
        )
    return (
        "<table><tr><th>check</th><th>status</th><th>measured</th><th>expected</th></tr>"
        + "".join(rows)
        + "</table>"
    )


def _inline_svg(path_value: str | None) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    if not path.exists():
        return f'<p class="meta">render missing: {html.escape(path_value)}</p>'
    return f'<div class="render">{path.read_text(encoding="utf-8")}</div>'


def _part_section(part: dict[str, Any]) -> str:
    metrics = part.get("mesh_metrics", {})
    integrity = part.get("integrity_metrics", {})
    wall = integrity.get("wall_thickness", {})
    orientation = metrics.get("recommended_build_up")
    facts = [
        f"volume <code>{_fmt(metrics.get('volume_mm3'))} mm&#179;</code>",
        f"area <code>{_fmt(metrics.get('surface_area_mm2'))} mm&#178;</code>",
        f"triangles <code>{_fmt(metrics.get('triangles'))}</code>",
    ]
    if wall.get("minimum_measured_mm") is not None:
        facts.append(f"min wall <code>{_fmt(wall['minimum_measured_mm'])} mm</code>")
    if orientation:
        facts.append(f"recommended build-up <code>{_fmt(orientation)}</code>")

    chunks = [
        f"<div class='card'><h3>{html.escape(part['name'])}</h3>",
        f"<p class='meta'>{' &middot; '.join(facts)}</p>",
        _inline_svg(part.get("renders", {}).get("views", {}).get("path")),
        _inline_svg(part.get("renders", {}).get("sections", {}).get("path")),
        _check_rows(part.get("checks", [])),
    ]
    freecad = part.get("freecad_step_roundtrip", {})
    slicer = part.get("slicer", {})
    chunks.append(
        f"<p class='meta'>FreeCAD STEP round-trip: {_status(freecad.get('status', 'not_run'))}"
        f" &nbsp; Slicer: {_status(slicer.get('status', 'not_run'))}"
    )
    slicer_metrics = slicer.get("metrics", {})
    if slicer_metrics:
        chunks.append(
            f" &nbsp; layers <code>{_fmt(slicer_metrics.get('layer_count'))}</code>"
            f" filament <code>{_fmt(slicer_metrics.get('filament_length_mm'))} mm</code>"
            f" time <code>{_fmt(slicer_metrics.get('estimated_time'))}</code>"
        )
    chunks.append("</p></div>")
    return "".join(chunks)


def _motion_section(motions: list[dict[str, Any]]) -> str:
    if not motions:
        return ""
    chunks = ["<h2>Motion checks</h2>"]
    for motion in motions:
        rows = "".join(
            "<tr>"
            f"<td><code>{_fmt(sample['translation_mm'])}</code></td>"
            f"<td>{_fmt(sample['intersection_volume_mm3'])}</td>"
            f"<td>{_fmt(sample.get('clearance_mm', ''))}</td>"
            "</tr>"
            for sample in motion.get("samples", [])
        )
        chunks.append(
            f"<div class='card'><h3>{html.escape(motion['name'])} {_status(motion['status'])}</h3>"
            f"<p class='meta'>minimum clearance <code>{_fmt(motion.get('minimum_clearance_mm'))} mm</code>"
            f" (required &ge; <code>{_fmt(motion.get('required_clearance_mm', 0))}</code>)</p>"
            "<table><tr><th>translation (mm)</th><th>intersection (mm&#179;)</th>"
            f"<th>clearance (mm)</th></tr>{rows}</table></div>"
        )
    return "".join(chunks)


def _clearance_section(clearances: list[dict[str, Any]]) -> str:
    if not clearances:
        return ""
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(item['name'])}</td>"
        f"<td>{_status(item['status'])}</td>"
        f"<td>{_fmt(item['measured_gap_mm'])}</td>"
        f"<td>{_fmt(item['required_gap_mm'])}</td>"
        f"<td>{_fmt(item['interference_volume_mm3'])}</td>"
        "</tr>"
        for item in clearances
    )
    return (
        "<h2>Static clearance bands</h2><div class='card'>"
        "<table><tr><th>interface</th><th>status</th><th>gap (mm)</th>"
        f"<th>required [min, max]</th><th>interference (mm&#179;)</th></tr>{rows}</table></div>"
    )


def write_html_report(report: dict[str, Any], output_dir: Path) -> Path:
    status = report.get("status", "fail")
    parameters = json.dumps(report.get("parameters", {}), indent=0)
    body = [
        f"<main><h1>{html.escape(report['design'])}</h1>",
        f"<p class='meta'>generated {html.escape(report.get('generated_at', ''))} &middot; "
        f"model <code>{html.escape(report.get('model_source', ''))}</code> &middot; "
        f"profile <code>{html.escape(report.get('printer_profile', ''))}</code></p>",
        f"<div class='banner {status}'>{status.upper()}: "
        f"{len(report.get('parts', []))} part(s), "
        f"{len(report.get('motion_checks', []))} motion check(s), "
        f"{len(report.get('clearance_checks', []))} clearance band(s)</div>",
        f"<p class='meta'>parameters <code>{html.escape(parameters)}</code></p>",
        "<h2>Parts</h2>",
        *(_part_section(part) for part in report.get("parts", [])),
        _motion_section(report.get("motion_checks", [])),
        _clearance_section(report.get("clearance_checks", [])),
    ]
    unavailable = report.get("unavailable_checks", [])
    if unavailable:
        body.append("<h2>Not run</h2><div class='card'>" + _check_rows(unavailable) + "</div>")
    body.append("</main>")

    document = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{html.escape(report['design'])} design review</title>"
        f"<style>{_CSS}</style></head><body>"
        + "".join(body)
        + "</body></html>"
    )
    path = output_dir / "report.html"
    path.write_text(document, encoding="utf-8")
    return path
