"""
MCP_DESIGN_19_Project_geometry_from_a_body_face_onto
====================================================
Group       : Design
Script ID   : DESIGN-19
Description : Project geometry from a body face onto an offset sketch
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_19_Project_geometry_from_a_body_face_onto

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

    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(H + 3.0))
    plane = root.constructionPlanes.add(cpi)
    plane.name = "Plane_ProjectionTarget"
    sk = root.sketches.add(plane)
    sk.name = "Sketch_ProjectedTopEdges"

    proj = sk.project(top_face)
    print(f"Projected {proj.count} entities onto '{sk.name}' "
          f"(sketch curves now: {sk.sketchCurves.count})")
