from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from build123d import Align, Axis, Cylinder, Pos, Shape, import_step


@dataclass(frozen=True)
class EmbeddedTClipSeats:
    shape: Shape
    slot_intersection_volumes_mm3: tuple[float, ...]


def embed_t_clip_seats(
    host: Shape,
    seat_step_path: Path,
    centers_xy_mm: tuple[tuple[float, float], ...],
    host_back_wall_mm: float,
    cut_radius_mm: float = 13.8,
) -> EmbeddedTClipSeats:
    result = host
    seat = import_step(seat_step_path).rotate(Axis.X, -90)
    for x, y in centers_xy_mm:
        result -= Pos(x, y, -0.1) * Cylinder(
            cut_radius_mm,
            host_back_wall_mm + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        result += Pos(x, y, 0) * seat

    probe_volumes = []
    for x, y in centers_xy_mm:
        probe = Pos(x, y, -0.1) * Cylinder(
            1.0,
            6.0,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        probe_volumes.append(float((result & probe).volume))
    return EmbeddedTClipSeats(result, tuple(probe_volumes))
