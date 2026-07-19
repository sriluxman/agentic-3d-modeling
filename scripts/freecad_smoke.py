import FreeCAD as App
import Part


doc = App.newDocument("agentic_3d_smoke")
box = Part.makeBox(20, 12, 6)
filleted = box.makeFillet(1.0, box.Edges)

part = doc.addObject("Part::Feature", "filleted_test_block")
part.Shape = filleted
doc.recompute()

Part.export([part], "exports/freecad_smoke.step")
Part.export([part], "exports/freecad_smoke.stl")

print("FreeCAD smoke export complete")

