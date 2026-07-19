from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path


def parse_ascii_stl(path: Path) -> list[tuple[tuple[float, float, float], ...]]:
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[tuple[float, float, float], ...]] = []

    for line in path.read_text(errors="ignore").splitlines():
        fields = line.strip().split()
        if len(fields) == 4 and fields[0] == "vertex":
            vertices.append((float(fields[1]), float(fields[2]), float(fields[3])))
            if len(vertices) == 3:
                triangles.append((vertices[0], vertices[1], vertices[2]))
                vertices = []

    return triangles


def rounded_vertex(vertex: tuple[float, float, float], precision: int) -> tuple[float, float, float]:
    return tuple(round(value, precision) for value in vertex)


def edge_key(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    precision: int,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    ar = rounded_vertex(a, precision)
    br = rounded_vertex(b, precision)
    return tuple(sorted((ar, br)))


def analyze(path: Path, precision: int) -> dict[str, object]:
    triangles = parse_ascii_stl(path)
    if not triangles:
        raise ValueError(f"{path} does not look like an ASCII STL with triangles")

    points = [point for triangle in triangles for point in triangle]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]

    edges: Counter[tuple[tuple[float, float, float], tuple[float, float, float]]] = Counter()
    for a, b, c in triangles:
        edges[edge_key(a, b, precision)] += 1
        edges[edge_key(b, c, precision)] += 1
        edges[edge_key(c, a, precision)] += 1

    open_edges = sum(1 for count in edges.values() if count == 1)
    overused_edges = sum(1 for count in edges.values() if count > 2)

    return {
        "file": str(path),
        "triangles": len(triangles),
        "bbox_mm": {
            "x": [min(xs), max(xs), max(xs) - min(xs)],
            "y": [min(ys), max(ys), max(ys) - min(ys)],
            "z": [min(zs), max(zs), max(zs) - min(zs)],
        },
        "unique_edges": len(edges),
        "open_edges": open_edges,
        "overused_edges": overused_edges,
        "edge_manifold": open_edges == 0 and overused_edges == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Basic ASCII STL geometry checks.")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--precision", type=int, default=5)
    args = parser.parse_args()

    failed = False
    for path in args.files:
        result = analyze(path, args.precision)
        bbox = result["bbox_mm"]
        print(path)
        print(f"  triangles: {result['triangles']}")
        print(f"  bbox x/y/z mm: {bbox['x'][2]:.2f} / {bbox['y'][2]:.2f} / {bbox['z'][2]:.2f}")
        print(f"  open edges: {result['open_edges']}")
        print(f"  overused edges: {result['overused_edges']}")
        print(f"  edge manifold: {result['edge_manifold']}")
        if not result["edge_manifold"]:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

