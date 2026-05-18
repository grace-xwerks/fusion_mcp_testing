"""
MCP_DESIGN_12_Draft_feature
===========================
Group       : Design
Script ID   : DESIGN-12
Description : Draft feature
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_12_Draft_feature

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    # 30×30×30 mm cube offset further back (y<0, beyond the shell test).
    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(0))
    plane = root.constructionPlanes.add(cpi); plane.name = "Plane_DraftBase"
    sk = root.sketches.add(plane); sk.name = "Sketch_DraftCube"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0.0, -10.0, 0),
        adsk.core.Point3D.create(3.0, -7.0, 0))
    ein = root.features.extrudeFeatures.createInput(
        sk.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ein.setDistanceExtent(False, adsk.core.ValueInput.createByReal(3.0))
    test_body = root.features.extrudeFeatures.add(ein).bodies.item(0)
    test_body.name = "DraftTestBox"

    # Draft the four side faces 5° relative to the bottom face
    bottom = next(f for f in test_body.faces
                  if abs(f.centroid.z - 0.0) < 0.001)
    # DraftFeatures.createInput wants a plain list[BRepFace], not an
    # ObjectCollection. The 3rd arg (isTangentChain) is required positional.
    side_faces = []
    for f in test_body.faces:
        ok, nrm = f.evaluator.getNormalAtPoint(f.centroid)
        if ok and abs(nrm.z) < 0.001:
            side_faces.append(f)

    df_in = root.features.draftFeatures.createInput(side_faces, bottom, False)
    df_in.setSingleAngle(False, adsk.core.ValueInput.createByString("5 deg"))
    draft = root.features.draftFeatures.add(df_in)
    draft.name = "Draft_TestCube_5deg"
    print(f"DraftTestBox: {len(side_faces)} side faces drafted 5° from bottom")
    print(f"  faces={test_body.faces.count}  vol={test_body.volume:.3f} cm³")
