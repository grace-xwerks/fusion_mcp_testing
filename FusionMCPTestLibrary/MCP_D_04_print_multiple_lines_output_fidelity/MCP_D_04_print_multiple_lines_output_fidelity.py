"""
MCP_D_04_print_multiple_lines_output_fidelity
=============================================
Group       : Core
Script ID   : D-04
Description : print() multiple lines (output fidelity check)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_D_04_print_multiple_lines_output_fidelity

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    print("=== Multi-line output test ===")
    print(f"Design name:      {des.parentDocument.name}")
    print(f"Root component:   {root.name}")
    print(f"Bodies count:     {root.bRepBodies.count}")
    print(f"Sketches count:   {root.sketches.count}")
    print(f"Features count:   {root.features.count}")
    print(f"Parameters count: {des.userParameters.count}")
    print("=== Done ===")
