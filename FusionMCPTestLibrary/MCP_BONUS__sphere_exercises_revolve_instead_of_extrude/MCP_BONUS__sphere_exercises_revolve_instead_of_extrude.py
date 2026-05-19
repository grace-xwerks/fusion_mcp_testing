"""
MCP_BONUS__sphere_exercises_revolve_instead_of_extrude
======================================================
Group       : Core
Script ID   : BONUS: sphere
Description : exercises revolve instead of extrude
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_BONUS__sphere_exercises_revolve_instead_of_extrude

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion, math

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    RADIUS_CM = 1.0   # 10 mm radius

    sketch = root.sketches.add(root.xZConstructionPlane)
    arcs   = sketch.sketchCurves.sketchArcs
    lines  = sketch.sketchCurves.sketchLines

    # Semi-circle (right half) + axis line
    center = adsk.core.Point3D.create(0, 0, 0)
    start  = adsk.core.Point3D.create(0, 0,  RADIUS_CM)
    end    = adsk.core.Point3D.create(0, 0, -RADIUS_CM)
    arcs.addByCenterStartEnd(center, start, end)
    axis_line = lines.addByTwoPoints(start, end)

    # Revolve the closed profile around the axis line
    prof     = sketch.profiles.item(0)
    revolves = root.features.revolveFeatures
    rev_in   = revolves.createInput(
        prof,
        axis_line,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    rev_in.setAngleExtent(
        False,
        adsk.core.ValueInput.createByString("360 deg")
    )
    revolves.add(rev_in)

    print(f"Sphere created: radius={RADIUS_CM*10:.0f} mm")
