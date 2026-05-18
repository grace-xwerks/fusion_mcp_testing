"""
MCP_D_03b_Parameterized_box_using_the_user
==========================================
Group       : Core
Script ID   : D-03b
Description : Parameterized box using the user parameter
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_D_03b_Parameterized_box_using_the_user

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app    = adsk.core.Application.get()
    des    = adsk.fusion.Design.cast(app.activeProduct)
    root   = des.rootComponent

    # Pull the parameter we created in D-03
    w_param = des.userParameters.itemByName("test_width")
    if not w_param:
        print("ERROR: test_width parameter not found — run D-03 first")
        return

    w = w_param.value   # already in cm
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(w, w, 0)
    )

    prof   = sketch.profiles.item(0)
    ext_in = root.features.extrudeFeatures.createInput(
        prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(w))
    root.features.extrudeFeatures.add(ext_in)

    print(f"Parameterized cube created: {w*10:.1f} mm sides (driven by test_width)")
