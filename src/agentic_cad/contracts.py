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
    # Minimum printable wall for this part; None uses the profile default
    # (2 x nozzle diameter). Coupons with intentional thin webs declare their
    # own limit instead of silencing the gate.
    min_wall_mm: float | None = None


@dataclass(frozen=True)
class MotionSpec:
    name: str
    fixed: Shape
    moving: Shape
    translations_mm: tuple[tuple[float, float, float], ...]
    max_intersection_volume_mm3: float = 0.001
    # Required minimum B-rep distance at every sample. 0.0 keeps the check
    # collision-only; a positive value demands measured running clearance.
    min_clearance_mm: float = 0.0
    # Optional rotation per sample (twist-locks, bayonets): rotations_deg must
    # be empty or match translations_mm in length; the moving body is rotated
    # about rotation_axis (origin, direction) before the translation applies.
    rotations_deg: tuple[float, ...] = ()
    rotation_axis: tuple[tuple[float, float, float], tuple[float, float, float]] | None = None


@dataclass(frozen=True)
class ClearanceSpec:
    """Static mating-fit contract between two bodies in assembled position.

    Fails on interference, on a gap below ``min_mm``, and - when ``max_mm``
    is set - on a gap above it: a fit that rattles is also a failed fit.
    """

    name: str
    a: Shape
    b: Shape
    min_mm: float = 0.0
    max_mm: float | None = None


@dataclass(frozen=True)
class DesignCheckSpec:
    """Model-computed check (ported from Codex's main-branch design): lets a
    model assert domain facts the generic gates cannot know, e.g. probe
    volumes proving a slot stayed open after a boolean."""

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
    clearances: tuple[ClearanceSpec, ...] = ()
    checks: tuple[DesignCheckSpec, ...] = ()
