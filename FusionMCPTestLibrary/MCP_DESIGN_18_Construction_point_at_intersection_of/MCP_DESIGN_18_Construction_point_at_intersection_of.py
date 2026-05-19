"""
MCP_DESIGN_18_Construction_point_at_intersection_of
===================================================
Group       : Design
Script ID   : DESIGN-18
Description : Construction point at intersection of three offset planes
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_18_Construction_point_at_intersection_of

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    H = des.userParameters.itemByName("part_height").value

    p1_in = root.constructionPlanes.createInput()
    p1_in.setByOffset(root.yZConstructionPlane, adsk.core.ValueInput.createByReal(5.0))
    plane_X5 = root.constructionPlanes.add(p1_in); plane_X5.name = "Plane_X5"
    p2_in = root.constructionPlanes.createInput()
    p2_in.setByOffset(root.xZConstructionPlane, adsk.core.ValueInput.createByReal(3.0))
    plane_Y3 = root.constructionPlanes.add(p2_in); plane_Y3.name = "Plane_Y3"
    p3_in = root.constructionPlanes.createInput()
    p3_in.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(H))
    plane_Ztop = root.constructionPlanes.add(p3_in); plane_Ztop.name = "Plane_Ztop"

    pti = root.constructionPoints.createInput()
    pti.setByThreePlanes(plane_X5, plane_Y3, plane_Ztop)
    cpt = root.constructionPoints.add(pti)
    cpt.name = "Pt_TopCenter"

    p = cpt.geometry
    print(f"Point '{cpt.name}' at ({p.x:.3f}, {p.y:.3f}, {p.z:.3f}) "
          f"(expect (5.000, 3.000, {H:.3f}))")
