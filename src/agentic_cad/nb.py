"""Notebook helpers: one-liners for the project-notebook workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from IPython.display import HTML, Image, display


def show_run(report: dict[str, Any]) -> None:
    """Display a run's verdict, check summary, and part renders inline."""
    color = "#17692c" if report["status"] == "pass" else "#9c1f2e"
    lines = [f"<h3 style='color:{color}'>{report['design']}: {report['status'].upper()}</h3><ul>"]
    for section in ("design_checks", "motion_checks", "clearance_checks"):
        for item in report.get(section, []):
            lines.append(f"<li>{item['name']}: <b>{item['status']}</b></li>")
    for part in report.get("parts", []):
        fails = [c["name"] for c in part["checks"] if c["status"] == "fail"]
        lines.append(f"<li>{part['name']}: {'FAIL: ' + ', '.join(fails) if fails else 'all checks pass'}</li>")
    lines.append("</ul>")
    if "html_report" in report:
        lines.append(f"<p>review: <code>{report['html_report']}</code>")
    if "annotate_html" in report:
        lines.append(f" &middot; annotate: <code>{report['annotate_html']}</code></p>")
    display(HTML("".join(lines)))
    for part in report.get("parts", []):
        png = part.get("renders", {}).get("views", {}).get("png")
        if png and Path(png).exists():
            display(Image(filename=png, width=620))


def show_annotations(path: str | Path) -> list[dict[str, Any]]:
    """Load and display an exported annotations.json; returns the pins."""
    from .annotate import load_annotations

    pins = load_annotations(Path(path))
    rows = "".join(
        f"<tr><td>#{p['id']}</td><td>{p['part']}</td><td>{p['view']}</td>"
        f"<td>{p['mm_from_view_center']}</td><td>{p['note']}</td></tr>"
        for p in pins
    )
    display(HTML(
        "<table><tr><th>pin</th><th>part</th><th>view</th><th>mm from view center</th><th>note</th></tr>"
        + rows + "</table>"
    ))
    return pins
