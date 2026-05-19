"""
MCP_DESIGN_04_Inspect_the_completed_part_body_face
==================================================
Group       : Design
Script ID   : DESIGN-04
Description : Inspect the completed part — body/face/edge/hole inventory
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_04_Inspect_the_completed_part_body_face

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    if root.bRepBodies.count == 0:
        print("No bodies found. Run DESIGN-03 first.")
        return

    body = root.bRepBodies.item(0)
    print(f"=== Part Inventory: {body.name} ===")
    print(f"  Faces  : {body.faces.count}")
    print(f"  Edges  : {body.edges.count}")
    print(f"  Vertices: {body.vertices.count}")

    bb = body.boundingBox
    dx = (bb.maxPoint.x - bb.minPoint.x) * 10
    dy = (bb.maxPoint.y - bb.minPoint.y) * 10
    dz = (bb.maxPoint.z - bb.minPoint.z) * 10
    print(f"\n  Bounding box: {dx:.1f} x {dy:.1f} x {dz:.1f} mm")
    # body.volume is in Fusion internal units (cm^3). Convert to mm^3 for display.
    print(f"  Volume      : {body.volume * 1000:.1f} mm³  ({body.volume:.2f} cm³)")

    print(f"\n  Feature timeline ({root.features.count} features):")
    for i in range(root.features.count):
        feat = root.features.item(i)
        print(f"    [{i+1}] {feat.classType().split('::')[-1]:30s}  {feat.name}")

    print(f"\n  User parameters ({des.userParameters.count}):")
    for i in range(des.userParameters.count):
        p = des.userParameters.item(i)
        print(f"    {p.name:15s} = {p.expression}")
