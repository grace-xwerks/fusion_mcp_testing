"""
MCP_DESIGN_02_Set_up_manufacturing_parameters
=============================================
Group       : Design
Script ID   : DESIGN-02
Description : Set up manufacturing parameters
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_02_Set_up_manufacturing_parameters

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app    = adsk.core.Application.get()
    des    = adsk.fusion.Design.cast(app.activeProduct)
    params = des.userParameters

    # Clear any existing test params first (skip if they don't exist)
    for name in ["part_length", "part_width", "part_height",
                 "pocket_depth", "hole_dia", "chamfer_size", "corner_rad"]:
        existing = params.itemByName(name)
        if existing:
            existing.deleteMe()

    defs = [
        ("part_length",  "100 mm", "mm", "Overall X dimension"),
        ("part_width",   "60 mm",  "mm", "Overall Y dimension"),
        ("part_height",  "20 mm",  "mm", "Stock thickness / Z height"),
        ("pocket_depth", "8 mm",   "mm", "Rectangular pocket depth"),
        ("hole_dia",     "6 mm",   "mm", "Through-hole drill diameter"),
        ("chamfer_size", "1 mm",   "mm", "Top edge chamfer"),
        ("corner_rad",   "2 mm",   "mm", "Inside pocket corner radius (min tool r)"),
    ]

    for name, expr, unit, comment in defs:
        p = params.add(name, adsk.core.ValueInput.createByString(expr), unit, comment)
        print(f"  {p.name:15s} = {p.expression:8s}  ({p.value*10:.2f} mm)")

    print("\nManufacturing parameters created.")
