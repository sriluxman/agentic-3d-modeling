"""User annotation on design renders - the feedback half of the design loop.

Generates ``annotate.html`` next to a run's ``report.json``: the user clicks
anywhere on a part's orthographic views to drop numbered pins with notes, then
exports ``annotations.json``. Each pin records the part, the view, and the
millimetre offset from that view's center (computed from the render scale),
so an agent can map every comment to a model region precisely:

    {"part": "box_body", "view": "front (-Y)", "note": "chamfer this edge",
     "mm_from_view_center": [-46.2, 11.0], ...}

Drop the exported file back into the export folder (or paste its content in
chat) and the agent reads it with ``load_annotations``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Must mirror render.py's layout constants
_CELL_W, _CELL_H, _HEADER = 360.0, 320.0, 34.0

_PAGE = """<!doctype html><html><head><meta charset="utf-8">
<title>{title} - annotate</title><style>
body {{ font-family: system-ui, sans-serif; margin: 0; background: #f2f5f8; color: #1a2733; }}
main {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
h1 {{ font-size: 22px; }} h2 {{ font-size: 17px; margin: 22px 0 6px; }}
.hint {{ color: #51606e; font-size: 13.5px; }}
.wrap {{ position: relative; display: inline-block; background: #fff; border: 1px solid #dde4ea; border-radius: 8px; }}
.wrap svg {{ display: block; max-width: 100%; height: auto; cursor: crosshair; }}
.pin {{ position: absolute; width: 22px; height: 22px; margin: -11px 0 0 -11px; border-radius: 50%;
  background: #b03a48; color: #fff; font-size: 12px; font-weight: 700; display: flex;
  align-items: center; justify-content: center; pointer-events: none; box-shadow: 0 1px 4px rgba(0,0,0,.35); }}
#notes {{ background: #fff; border: 1px solid #dde4ea; border-radius: 8px; padding: 10px 14px; }}
#notes li {{ margin: 6px 0; font-size: 13.5px; }}
button {{ background: #1a5f9c; color: #fff; border: 0; border-radius: 6px; padding: 9px 16px;
  font-size: 14px; cursor: pointer; margin: 12px 8px 0 0; }}
textarea {{ width: 100%; height: 110px; font-family: monospace; font-size: 12px; margin-top: 8px; }}
</style></head><body><main>
<h1>{title} - annotation</h1>
<p class="hint">Click a spot on any view to pin a comment. Pins record the view and the mm offset
from the view center so the agent can locate each remark on the model. When done, press
<b>Export annotations.json</b> and give the file (or the text below) back to the agent.</p>
{sections}
<h2>Annotations</h2><div id="notes"><ol id="list"></ol>
<button onclick="exportJson()">Export annotations.json</button>
<button onclick="document.getElementById('out').value = JSON.stringify(payload(), null, 1)">Show as text</button>
<textarea id="out" placeholder="annotations JSON appears here"></textarea></div>
<script>
const CELL_W = {cell_w}, CELL_H = {cell_h}, HEADER = {header};
const meta = {meta};
let pins = [];
function viewAt(part, x, y) {{
  const views = meta[part].views;
  if (y < HEADER) return null;
  const col = Math.min(1, Math.floor(x / CELL_W)), row = Math.min(1, Math.floor((y - HEADER) / CELL_H));
  const idx = row * 2 + col;
  if (idx >= views.length) return null;
  const cx = col * CELL_W + CELL_W / 2, cy = HEADER + row * CELL_H + (CELL_H - 18) / 2;
  return {{ name: views[idx], cx: cx, cy: cy }};
}}
function addPin(part, evt, wrap, svg) {{
  const pt = svg.createSVGPoint(); pt.x = evt.clientX; pt.y = evt.clientY;
  const p = pt.matrixTransform(svg.getScreenCTM().inverse());
  const view = viewAt(part, p.x, p.y);
  if (!view) return;
  const note = prompt("Note for pin " + (pins.length + 1) + " (" + part + ", " + view.name + "):");
  if (!note) return;
  const scale = meta[part].scale;
  const pin = {{
    id: pins.length + 1, part: part, view: view.name, note: note,
    svg_px: [Math.round(p.x * 10) / 10, Math.round(p.y * 10) / 10],
    mm_from_view_center: [Math.round((p.x - view.cx) / scale * 100) / 100,
                          Math.round((view.cy - p.y) / scale * 100) / 100]
  }};
  pins.push(pin);
  const rect = wrap.getBoundingClientRect(), sr = svg.getBoundingClientRect();
  const dot = document.createElement("div"); dot.className = "pin"; dot.textContent = pin.id;
  dot.style.left = (evt.clientX - rect.left) + "px"; dot.style.top = (evt.clientY - rect.top) + "px";
  wrap.appendChild(dot);
  const li = document.createElement("li");
  li.textContent = "#" + pin.id + " [" + part + " / " + view.name + "] (" +
    pin.mm_from_view_center[0] + ", " + pin.mm_from_view_center[1] + " mm from view center): " + note;
  document.getElementById("list").appendChild(li);
}}
function payload() {{ return {{ design: {design}, schema_version: 1, annotations: pins }}; }}
function exportJson() {{
  const blob = new Blob([JSON.stringify(payload(), null, 1)], {{type: "application/json"}});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
  a.download = "annotations.json"; a.click();
}}
document.querySelectorAll(".wrap").forEach(wrap => {{
  const svg = wrap.querySelector("svg");
  svg.addEventListener("click", evt => addPin(wrap.dataset.part, evt, wrap, svg));
}});
</script></main></body></html>"""


def write_annotate_html(report: dict[str, Any], output_dir: Path) -> Path | None:
    """Build annotate.html from a run report; returns None if no renders."""
    sections: list[str] = []
    meta: dict[str, Any] = {}
    for part in report.get("parts", []):
        views = part.get("renders", {}).get("views")
        if not views:
            continue
        svg_path = Path(views["path"])
        if not svg_path.exists():
            continue
        meta[part["name"]] = {"views": views["views"], "scale": views["scale_px_per_mm"]}
        sections.append(
            f"<h2>{part['name']}</h2>"
            f'<div class="wrap" data-part="{part["name"]}">'
            + svg_path.read_text(encoding="utf-8")
            + "</div>"
        )
    if not sections:
        return None
    html = _PAGE.format(
        title=report["design"],
        sections="".join(sections),
        meta=json.dumps(meta),
        design=json.dumps(report["design"]),
        cell_w=_CELL_W,
        cell_h=_CELL_H,
        header=_HEADER,
    )
    path = output_dir / "annotate.html"
    path.write_text(html, encoding="utf-8")
    return path


def load_annotations(path: Path) -> list[dict[str, Any]]:
    """Read an exported annotations.json for agent consumption."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("annotations"), list):
        raise ValueError(f"Unsupported annotations file: {path}")
    return data["annotations"]
