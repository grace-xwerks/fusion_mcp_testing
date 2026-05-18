"""
MCP_DESIGN_05_Edit_a_parameter_and_verify_model
===============================================
Group       : Design
Script ID   : DESIGN-05
Description : Edit a parameter and verify model updates (parametric test)
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_05_Edit_a_parameter_and_verify_model

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)

    param = des.userParameters.itemByName("pocket_depth")
    if not param:
        print("pocket_depth not found — run DESIGN-02 first.")
        return

    old_val = param.expression
    print(f"Before: pocket_depth = {old_val}")

    # Change pocket depth from 8 mm to 12 mm
    param.expression = "12 mm"
    print(f"After : pocket_depth = {param.expression}  ({param.value*10:.1f} mm)")
    print("Model should have updated. Check viewport.")

    # Revert
    param.expression = old_val
    print(f"Reverted to: {param.expression}")
