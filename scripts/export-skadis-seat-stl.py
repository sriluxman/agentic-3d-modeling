from pathlib import Path

from build123d import Axis, export_stl, import_step


ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "models" / "ikea" / "Clip Seat.step"
output = ROOT / "exports" / "components" / "skadis_clip_seat_rotated.stl"
output.parent.mkdir(parents=True, exist_ok=True)

seat = import_step(source).rotate(Axis.X, -90)
export_stl(seat, output, tolerance=0.08, angular_tolerance=0.18)

print(output)
