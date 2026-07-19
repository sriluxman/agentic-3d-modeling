import json
import sys

import Part


step_path = sys.argv[-2]
report_path = sys.argv[-1]
shape = Part.read(step_path)
box = shape.BoundBox
report = {
    "is_valid": shape.isValid(),
    "solid_count": len(shape.Solids),
    "volume_mm3": shape.Volume,
    "bounding_box_mm": [box.XLength, box.YLength, box.ZLength],
}

with open(report_path, "w", encoding="utf-8") as output:
    json.dump(report, output, indent=2)
    output.write("\n")
