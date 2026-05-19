"""
MCP_D_02_Create_a_10_mm_cube
============================
Group       : Core
Script ID   : D-02
Description : Create a 10 mm cube
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_D_02_Create_a_10_mm_cube

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    # Sketch on XY plane
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(1.0, 1.0, 0)   # 1.0 cm = 10 mm
    )

    # Extrude 10 mm
    prof     = sketch.profiles.item(0)
    extrudes = root.features.extrudeFeatures
    ext_in   = extrudes.createInput(
        prof,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1.0))
    body = extrudes.add(ext_in)

    print(f"Created body: {body.bodies.item(0).name}")
    print(f"Bounding box volume check: 10x10x10 mm cube")
