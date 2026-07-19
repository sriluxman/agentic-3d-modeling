import argparse
from pathlib import Path

import trimesh


parser = argparse.ArgumentParser(description="Fail when an intersection mesh has meaningful volume")
parser.add_argument("mesh", type=Path)
parser.add_argument("--max-volume-mm3", type=float, default=0.01)
args = parser.parse_args()

if not args.mesh.exists():
    print(f"PASS: no intersection mesh ({args.mesh})")
    raise SystemExit(0)

mesh = trimesh.load_mesh(args.mesh, force="mesh", process=True)
volume = 0.0 if min(mesh.extents) <= 1e-9 else abs(float(mesh.volume))
print(f"intersection_volume_mm3={volume:.6f}")
raise SystemExit(0 if volume <= args.max_volume_mm3 else 1)
