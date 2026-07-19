from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_PATHS = (
    ("printer", "name"),
    ("printer", "nozzle_diameter_mm"),
    ("process", "layer_height_mm"),
    ("process", "line_width_mm"),
    ("process", "wall_loops"),
    ("material", "type"),
)


def load_profile(path: Path) -> dict[str, Any]:
    profile = json.loads(path.read_text(encoding="utf-8"))
    if profile.get("schema_version") != 1:
        raise ValueError("Only printer profile schema_version 1 is supported")

    for section, key in REQUIRED_PATHS:
        if profile.get(section, {}).get(key) is None:
            raise ValueError(f"Printer profile requires {section}.{key}")

    return profile
