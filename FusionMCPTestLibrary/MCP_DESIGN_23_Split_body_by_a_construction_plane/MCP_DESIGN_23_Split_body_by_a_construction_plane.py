"""
MCP_DESIGN_23_Split_body_by_a_construction_plane
================================================
Group       : Design
Script ID   : DESIGN-23
Description : Split body by a construction plane
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_23_Split_body_by_a_construction_plane

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    sk = root.sketches.add(root.xYConstructionPlane); sk.name = "Sketch_SplitCube"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-20.0, 0, 0),
        adsk.core.Point3D.create(-16.0, 4.0, 0))
    ein = root.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ein.setDistanceExtent(False, adsk.core.ValueInput.createByReal(4.0))
    cube = root.features.extrudeFeatures.add(ein).bodies.item(0)
    cube.name = "SplitCube"
    v_before = cube.volume

    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(2.0))
    splitter = root.constructionPlanes.add(cpi)
    splitter.name = "Plane_SplitMid"

    sp_in = root.features.splitBodyFeatures.createInput(cube, splitter, True)
    root.features.splitBodyFeatures.add(sp_in).name = "Split_AtMid"

    halves = [b for b in root.bRepBodies if b.name.startswith("SplitCube")]
    total = sum(b.volume for b in halves)
    print(f"Split: {len(halves)} bodies, halves={[round(b.volume, 3) for b in halves]}, "
          f"total={total:.3f} (expect {v_before:.3f})")
