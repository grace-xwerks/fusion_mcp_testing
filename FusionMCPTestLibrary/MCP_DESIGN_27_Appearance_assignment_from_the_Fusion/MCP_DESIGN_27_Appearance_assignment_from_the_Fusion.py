"""
MCP_DESIGN_27_Appearance_assignment_from_the_Fusion
===================================================
Group       : Design
Script ID   : DESIGN-27
Description : Appearance assignment from the Fusion Appearance Library
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_27_Appearance_assignment_from_the_Fusion

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

    print(f"Bracket appearance before: {body.appearance.name}")

    app_lib = next(l for l in app.materialLibraries
                   if l.name == "Fusion Appearance Library")
    red = next((a for a in app_lib.appearances
                if "Red" in a.name and "Plastic" in a.name), None)
    if red is None:
        red = next((a for a in app_lib.appearances if "Red" in a.name), None)
    if red is None:
        print("FAIL: no red appearance available.")
        return

    body.appearance = red
    print(f"Bracket appearance after:  {body.appearance.name}")
