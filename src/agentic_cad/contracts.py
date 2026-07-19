from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from build123d import Shape


@dataclass(frozen=True)
class PartSpec:
    name: str
    shape: Shape
    expected_bbox_mm: tuple[float, float, float]
    expected_bodies: int = 1
    bbox_tolerance_mm: float = 0.05
    preferred_build_up: tuple[int, int, int] = (0, 0, 1)
    print_shape: Shape | None = None
    slicer_process_preset_project_relative: str | None = None


@dataclass(frozen=True)
class MotionSpec:
    name: str
    fixed: Shape
    moving: Shape
    translations_mm: tuple[tuple[float, float, float], ...]
    max_intersection_volume_mm3: float = 0.001


@dataclass(frozen=True)
class DesignCheckSpec:
    name: str
    passed: bool
    measured: Any = None
    expected: Any = None


@dataclass(frozen=True)
class DesignSpec:
    name: str
    parts: tuple[PartSpec, ...]
    parameters: dict[str, Any] = field(default_factory=dict)
    motions: tuple[MotionSpec, ...] = ()
    checks: tuple[DesignCheckSpec, ...] = ()
