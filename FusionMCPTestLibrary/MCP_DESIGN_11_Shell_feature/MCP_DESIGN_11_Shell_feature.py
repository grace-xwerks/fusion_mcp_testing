"""
MCP_DESIGN_11_Shell_feature
===========================
Group       : Design
Script ID   : DESIGN-11
Description : Shell feature
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_11_Shell_feature

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    # Build a 40×30×20 mm closed box offset to the front of the Bracket
    # (so y<0). Position: x=0..4, y=-5..-2, z=0..2.
    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(0))
    base_plane = root.constructionPlanes.add(cpi); base_plane.name = "Plane_ShellBase"
    sk = root.sketches.add(base_plane); sk.name = "Sketch_ShellBox"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0.0, -5.0, 0),
        adsk.core.Point3D.create(4.0, -2.0, 0))
    ein = root.features.extrudeFeatures.createInput(
        sk.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ein.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.0))
    test_body = root.features.extrudeFeatures.add(ein).bodies.item(0)
    test_body.name = "ShellTestBox"

    # Shell removing the top face (the +Z one), wall = 2 mm
    top = next(f for f in test_body.faces
               if abs(f.centroid.z - 2.0) < 0.001)
    faces_to_remove = adsk.core.ObjectCollection.create()
    faces_to_remove.add(top)
    sh_in = root.features.shellFeatures.createInput(faces_to_remove)
    sh_in.insideThickness = adsk.core.ValueInput.createByReal(0.2)   # 2 mm inside
    shell = root.features.shellFeatures.add(sh_in)
    shell.name = "Shell_TestBox_2mm"
    print(f"ShellTestBox: shelled (top removed, 2 mm wall inside)")
    print(f"  faces={test_body.faces.count}  vol={test_body.volume:.3f} cm³")
