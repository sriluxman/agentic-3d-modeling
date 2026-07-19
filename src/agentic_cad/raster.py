"""Rasterize SVG evidence to PNG with a local headless browser.

Multimodal agents consume PNG screenshots directly; humans get thumbnails.
Uses Edge or Chrome in headless mode - no Python imaging dependency. Returns
None quietly when no browser is available so the pipeline stays optional.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

_BROWSER_CANDIDATES = (
    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
)


def find_browser() -> Path | None:
    for name in ("msedge", "chrome", "chromium"):
        found = shutil.which(name)
        if found:
            return Path(found)
    local = os.environ.get("LOCALAPPDATA", "")
    candidates = list(_BROWSER_CANDIDATES)
    if local:
        candidates.append(f"{local}/Google/Chrome/Application/chrome.exe")
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    return None


def _svg_size(svg_path: Path) -> tuple[int, int]:
    header = svg_path.read_text(encoding="utf-8")[:400]
    match = re.search(r'width="(\d+)" height="(\d+)"', header)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 800, 600


def rasterize_svg(svg_path: Path, png_path: Path | None = None, timeout_s: int = 60) -> Path | None:
    """Render an SVG file to PNG; returns the PNG path or None if unavailable."""
    browser = find_browser()
    if browser is None:
        return None
    png_path = png_path or svg_path.with_suffix(".png")
    width, height = _svg_size(svg_path)
    command = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        f"--screenshot={png_path.resolve()}",
        f"--window-size={width},{height}",
        svg_path.resolve().as_uri(),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_s, check=False)
    if completed.returncode != 0 or not png_path.exists():
        return None
    return png_path
