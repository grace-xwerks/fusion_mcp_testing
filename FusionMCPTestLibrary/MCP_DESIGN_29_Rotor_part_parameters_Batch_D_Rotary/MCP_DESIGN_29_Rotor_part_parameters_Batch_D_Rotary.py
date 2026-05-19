"""
MCP_DESIGN_29_Rotor_part_parameters_Batch_D_Rotary
==================================================
Group       : Design
Script ID   : DESIGN-29
Description : Rotor part parameters (Batch D — Rotary stock for CAM-18a..e)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_29_Rotor_part_parameters_Batch_D_Rotary

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app    = adsk.core.Application.get()
    des    = adsk.fusion.Design.cast(app.activeProduct)
    params = des.userParameters

    defs = [
        ("rotor_length",       "100 mm", "mm", "Total rotor length along +X"),
        ("rotor_od",           "40 mm",  "mm", "Main body OD (Ø) — rotary stock diameter"),
        ("rotor_shoulder_od",  "30 mm",  "mm", "Mounting shoulder OD at -X end"),
        ("rotor_shoulder_len", "20 mm",  "mm", "Shoulder length along +X from -X face"),
        ("rotor_bore_dia",     "10 mm",  "mm", "Axial through-bore diameter"),
        ("rotor_bore_len",     "80 mm",  "mm", "Bore depth from -X face (stops before dome)"),
        ("rotor_dome_r",       "20 mm",  "mm", "Quarter-sphere dome radius at +X end (= rotor_od/2)"),
        ("rotor_groove_x",     "55 mm",  "mm", "Circumferential groove start X (rotary_pocket target)"),
        ("rotor_groove_w",     "6 mm",   "mm", "Groove width along X"),
        ("rotor_groove_depth", "3 mm",   "mm", "Groove radial depth"),
        ("rotor_flat_x0",      "70 mm",  "mm", "Milled flat start X (rotary_contour target)"),
        ("rotor_flat_x1",      "75 mm",  "mm", "Milled flat end X (5 mm clear of dome start)"),
        ("rotor_flat_inset",   "4 mm",   "mm", "Radial depth of milled flats from OD"),
    ]

    for name, expr, unit, comment in defs:
        existing = params.itemByName(name)
        if existing:
            existing.deleteMe()
        p = params.add(name, adsk.core.ValueInput.createByString(expr), unit, comment)
        print(f"  {p.name:22s} = {p.expression:8s}  ({p.value*10:.2f} mm)")

    print("\nRotor parameters created — run DESIGN-30 to build the body.")
