"""
MCP_DESIGN_28_Surface_patch_thicken_to_solid
============================================
Group       : Design
Script ID   : DESIGN-28
Description : Surface patch + thicken to solid
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_28_Surface_patch_thicken_to_solid

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(10.0))
    plane = root.constructionPlanes.add(cpi); plane.name = "Plane_PatchBase"
    sk = root.sketches.add(plane); sk.name = "Sketch_PatchRect"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-20.0, -25.0, 0),
        adsk.core.Point3D.create(-16.0, -22.0, 0))

    patch_in = root.features.patchFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    patch = root.features.patchFeatures.add(patch_in)
    patch.name = "Patch_Rect"
    surf = patch.bodies.item(0); surf.name = "SurfRect"

    surf_faces = adsk.core.ObjectCollection.create()
    for f in surf.faces: surf_faces.add(f)
    th_in = root.features.thickenFeatures.createInput(
        surf_faces,
        adsk.core.ValueInput.createByReal(0.5),                          # 5 mm
        False,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        True)
    root.features.thickenFeatures.add(th_in).name = "Thicken_Patch_5mm"

    solid = next((b for b in root.bRepBodies if b.isSolid and b.name not in ("Bracket",)),
                 None)
    print(f"Patch surface (1 face) → thickened solid: vol={solid.volume if solid else 0:.3f} "
          f"(expect 6.000 = 4×3×0.5)")
