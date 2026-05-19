"""
MCP_DESIGN_17_Construction_axis_perpendicular_to_a
==================================================
Group       : Design
Script ID   : DESIGN-17
Description : Construction axis perpendicular to a face at a sketch point
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_17_Construction_axis_perpendicular_to_a

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    body = root.bRepBodies.itemByName("Bracket")
    if body is None:
        print("Bracket not found. Run DESIGN-03 first.")
        return

    H = des.userParameters.itemByName("part_height").value
    top_face = next(f for f in body.faces
                    if abs(f.centroid.z - H) < 0.001 and
                       (f.boundingBox.maxPoint.x - f.boundingBox.minPoint.x) > 8.0)

    # Sketch point on a construction plane offset to H (avoids quirk #8b's
    # face-bound silent issues with downstream usage).
    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(H))
    sketch_plane = root.constructionPlanes.add(cpi)
    sketch_plane.name = "Plane_AxisPointSketch"
    sk = root.sketches.add(sketch_plane)
    sk.name = "Sketch_AxisPoint"
    pt = sk.sketchPoints.add(adsk.core.Point3D.create(5.0, 3.0, 0))

    ai = root.constructionAxes.createInput()
    ai.setByPerpendicularAtPoint(top_face, pt)   # face FIRST, point SECOND
    axis = root.constructionAxes.add(ai)
    axis.name = "Axis_CenterOfTop"

    d = axis.geometry.direction
    print(f"Axis '{axis.name}' direction=({d.x:.3f}, {d.y:.3f}, {d.z:.3f}) "
          f"(expect (0, 0, ±1))")
