import json
import sys

import Part


step_path = sys.argv[-2]
report_path = sys.argv[-1]
shape = Part.read(step_path)

# Shape.BoundBox is the loose control-point hull for B-spline surfaces
# (helical thread sweeps read back ~30% oversized); measure the tight box
# from tessellation instead.
vertices, _ = shape.tessellate(0.01)
xs = [v.x for v in vertices]
ys = [v.y for v in vertices]
zs = [v.z for v in vertices]
report = {
    "is_valid": shape.isValid(),
    "solid_count": len(shape.Solids),
    "volume_mm3": shape.Volume,
    "bounding_box_mm": [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)],
}

with open(report_path, "w", encoding="utf-8") as output:
    json.dump(report, output, indent=2)
    output.write("\n")
