"""
MCP_DESIGN_16_Offset_construction_plane_from_a_body
===================================================
Group       : Design
Script ID   : DESIGN-16
Description : Offset construction plane from a body face
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_16_Offset_construction_plane_from_a_body

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
    cpi.setByOffset(top_face, adsk.core.ValueInput.createByReal(2.5))   # 25 mm above
    plane = root.constructionPlanes.add(cpi)
    plane.name = "Plane_25mmAboveTop"

    # Expected: plane origin at z = H + 2.5 = 4.5 cm
    print(f"Plane '{plane.name}' origin z={plane.geometry.origin.z:.3f} cm "
          f"(expect {H + 2.5:.3f})")
