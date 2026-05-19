"""
MCP_DESIGN_26_Material_assignment_from_the_Fusion
=================================================
Group       : Design
Script ID   : DESIGN-26
Description : Material assignment from the Fusion Material Library
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_26_Material_assignment_from_the_Fusion

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

    print(f"Bracket material before: {body.material.name}")

    libs = app.materialLibraries
    material_lib = next((l for l in libs if l.name == "Fusion Material Library"), None)
    if material_lib is None:
        print("FAIL: 'Fusion Material Library' not available.")
        return

    alu = next((m for m in material_lib.materials if "Aluminum 6061" in m.name), None)
    if alu is None:
        avail = [m.name for m in material_lib.materials if "Aluminum" in m.name]
        print(f"FAIL: Aluminum 6061 not in Fusion Material Library. Options: {avail}")
        return

    body.material = alu
    print(f"Bracket material after:  {body.material.name}")
