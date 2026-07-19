"""Multi-view SVG rendering of part meshes.

Gives the agent loop visual evidence with zero extra dependencies: four
orthographic views (isometric, front, top, right) flat-shaded with a painter's
sort, plus a shared millimetre scale bar. The output is a single standalone
SVG per part that renders in any browser or IDE preview.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import trimesh

_CELL_W = 360.0
_CELL_H = 320.0
_MARGIN = 26.0
_HEADER = 34.0
_BASE_RGB = np.array((94.0, 132.0, 180.0))
_LIGHT = np.array((0.38, 0.32, 0.87))


def _view_frame(out: np.ndarray) -> np.ndarray:
    """Rows: screen right, screen up, toward viewer."""
    out = out / np.linalg.norm(out)
    world_up = np.array((0.0, 0.0, 1.0))
    if abs(float(out @ world_up)) > 0.99:
        world_up = np.array((0.0, 1.0, 0.0))
    up = world_up - (world_up @ out) * out
    up = up / np.linalg.norm(up)
    right = np.cross(up, out)
    return np.vstack((right, up, out))


_VIEWS: tuple[tuple[str, np.ndarray], ...] = (
    ("isometric", _view_frame(np.array((1.0, -1.0, 1.0)))),
    ("front (-Y)", _view_frame(np.array((0.0, -1.0, 0.0)))),
    ("top (+Z)", _view_frame(np.array((0.0, 0.0, 1.0)))),
    ("right (+X)", _view_frame(np.array((1.0, 0.0, 0.0)))),
)


def _shade(normals_view: np.ndarray) -> list[str]:
    intensity = 0.42 + 0.58 * np.clip(normals_view @ _LIGHT, 0.0, 1.0)
    colors = np.clip(_BASE_RGB[None, :] * intensity[:, None] + 24.0, 0, 255).astype(int)
    return [f"rgb({r},{g},{b})" for r, g, b in colors]


def _view_polygons(mesh: trimesh.Trimesh, frame: np.ndarray) -> tuple[np.ndarray, list[str]]:
    vertices = mesh.vertices @ frame.T
    faces = mesh.faces
    normals = mesh.face_normals @ frame.T
    visible = normals[:, 2] > 1e-6
    faces = faces[visible]
    normals = normals[visible]
    depth = vertices[:, 2][faces].mean(axis=1)
    order = np.argsort(depth)
    faces = faces[order]
    normals = normals[order]
    polygons = vertices[:, :2][faces]
    return polygons, _shade(normals)


def render_views_svg(mesh: trimesh.Trimesh, output_path: Path, title: str) -> dict[str, Any]:
    """Render four orthographic views to one standalone SVG."""
    views = []
    all_bounds = []
    for name, frame in _VIEWS:
        polygons, colors = _view_polygons(mesh, frame)
        views.append((name, polygons, colors))
        span = polygons.reshape(-1, 2)
        all_bounds.append((span.min(axis=0), span.max(axis=0)))

    widest = max(high[0] - low[0] for low, high in all_bounds)
    tallest = max(high[1] - low[1] for low, high in all_bounds)
    scale = min(
        (_CELL_W - 2 * _MARGIN) / max(widest, 1e-6),
        (_CELL_H - 2 * _MARGIN - 18) / max(tallest, 1e-6),
    )

    total_w = 2 * _CELL_W
    total_h = _HEADER + 2 * _CELL_H + 30
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.0f}" height="{total_h:.0f}" '
        f'viewBox="0 0 {total_w:.0f} {total_h:.0f}" font-family="system-ui, sans-serif">',
        f'<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{_MARGIN}" y="24" font-size="17" font-weight="600" fill="#1a2733">{title}</text>',
    ]
    extent = mesh.bounds[1] - mesh.bounds[0]
    parts.append(
        f'<text x="{total_w - _MARGIN}" y="24" font-size="12" fill="#51606e" text-anchor="end">'
        f"bbox {extent[0]:.2f} x {extent[1]:.2f} x {extent[2]:.2f} mm | "
        f"{len(mesh.faces)} faces</text>"
    )

    for index, (name, polygons, colors) in enumerate(views):
        low, high = all_bounds[index]
        center = (low + high) / 2.0
        cell_x = (index % 2) * _CELL_W
        cell_y = _HEADER + (index // 2) * _CELL_H
        origin_x = cell_x + _CELL_W / 2.0
        origin_y = cell_y + (_CELL_H - 18) / 2.0

        parts.append(
            f'<rect x="{cell_x + 4:.1f}" y="{cell_y + 2:.1f}" width="{_CELL_W - 8:.1f}" '
            f'height="{_CELL_H - 6:.1f}" fill="#f5f8fb" stroke="#d6dee6" rx="6"/>'
        )
        parts.append(
            f'<text x="{cell_x + 14:.1f}" y="{cell_y + 20:.1f}" font-size="12" '
            f'fill="#51606e">{name}</text>'
        )
        chunks = []
        for polygon, color in zip(polygons, colors):
            x = origin_x + (polygon[:, 0] - center[0]) * scale
            y = origin_y - (polygon[:, 1] - center[1]) * scale
            points = " ".join(f"{px:.1f},{py:.1f}" for px, py in zip(x, y))
            chunks.append(f'<polygon points="{points}" fill="{color}" stroke="{color}" stroke-width="0.4"/>')
        parts.append("".join(chunks))

    bar_mm = 10.0
    bar_px = bar_mm * scale
    bar_y = total_h - 14
    parts.append(
        f'<line x1="{_MARGIN}" y1="{bar_y}" x2="{_MARGIN + bar_px:.1f}" y2="{bar_y}" '
        f'stroke="#1a2733" stroke-width="2"/>'
        f'<text x="{_MARGIN + bar_px + 8:.1f}" y="{bar_y + 4}" font-size="12" '
        f'fill="#1a2733">{bar_mm:.0f} mm</text>'
    )
    parts.append("</svg>")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(parts), encoding="utf-8")
    return {
        "path": str(output_path),
        "views": [name for name, _ in _VIEWS],
        "scale_px_per_mm": float(scale),
    }


_SECTION_PLANES: tuple[tuple[str, np.ndarray], ...] = (
    ("section X (YZ plane)", np.array((1.0, 0.0, 0.0))),
    ("section Y (XZ plane)", np.array((0.0, 1.0, 0.0))),
    ("section Z (XY plane)", np.array((0.0, 0.0, 1.0))),
)


def _section_polylines(mesh: trimesh.Trimesh, normal: np.ndarray) -> list[np.ndarray] | None:
    origin = mesh.bounds.mean(axis=0)
    section = mesh.section(plane_origin=origin, plane_normal=normal)
    if section is None:
        return None
    frame = _view_frame(normal)
    return [(line @ frame.T)[:, :2] for line in section.discrete]


def render_sections_svg(mesh: trimesh.Trimesh, output_path: Path, title: str) -> dict[str, Any] | None:
    """Render mid-plane cross-sections as stroked outlines (one SVG).

    Sections expose internal walls and fits that shaded exterior views hide.
    Returns None when no section plane intersects the mesh.
    """
    sections = []
    all_bounds = []
    for name, normal in _SECTION_PLANES:
        polylines = _section_polylines(mesh, normal)
        if not polylines:
            continue
        span = np.concatenate(polylines)
        sections.append((name, polylines))
        all_bounds.append((span.min(axis=0), span.max(axis=0)))
    if not sections:
        return None

    widest = max(high[0] - low[0] for low, high in all_bounds)
    tallest = max(high[1] - low[1] for low, high in all_bounds)
    scale = min(
        (_CELL_W - 2 * _MARGIN) / max(widest, 1e-6),
        (_CELL_H - 2 * _MARGIN - 18) / max(tallest, 1e-6),
    )

    total_w = len(sections) * _CELL_W
    total_h = _HEADER + _CELL_H + 30
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.0f}" height="{total_h:.0f}" '
        f'viewBox="0 0 {total_w:.0f} {total_h:.0f}" font-family="system-ui, sans-serif">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{_MARGIN}" y="24" font-size="17" font-weight="600" fill="#1a2733">'
        f"{title} - mid-plane sections</text>",
    ]
    for index, (name, polylines) in enumerate(sections):
        low, high = all_bounds[index]
        center = (low + high) / 2.0
        cell_x = index * _CELL_W
        cell_y = _HEADER
        origin_x = cell_x + _CELL_W / 2.0
        origin_y = cell_y + (_CELL_H - 18) / 2.0
        parts.append(
            f'<rect x="{cell_x + 4:.1f}" y="{cell_y + 2:.1f}" width="{_CELL_W - 8:.1f}" '
            f'height="{_CELL_H - 6:.1f}" fill="#f5f8fb" stroke="#d6dee6" rx="6"/>'
        )
        parts.append(
            f'<text x="{cell_x + 14:.1f}" y="{cell_y + 20:.1f}" font-size="12" fill="#51606e">{name}</text>'
        )
        for line in polylines:
            x = origin_x + (line[:, 0] - center[0]) * scale
            y = origin_y - (line[:, 1] - center[1]) * scale
            points = " ".join(f"{px:.1f},{py:.1f}" for px, py in zip(x, y))
            parts.append(
                f'<polyline points="{points}" fill="none" stroke="#b03a48" stroke-width="1.6"/>'
            )

    bar_mm = 10.0
    bar_px = bar_mm * scale
    bar_y = total_h - 14
    parts.append(
        f'<line x1="{_MARGIN}" y1="{bar_y}" x2="{_MARGIN + bar_px:.1f}" y2="{bar_y}" '
        f'stroke="#1a2733" stroke-width="2"/>'
        f'<text x="{_MARGIN + bar_px + 8:.1f}" y="{bar_y + 4}" font-size="12" '
        f'fill="#1a2733">{bar_mm:.0f} mm</text>'
    )
    parts.append("</svg>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(parts), encoding="utf-8")
    return {"path": str(output_path), "sections": [name for name, _ in sections]}
