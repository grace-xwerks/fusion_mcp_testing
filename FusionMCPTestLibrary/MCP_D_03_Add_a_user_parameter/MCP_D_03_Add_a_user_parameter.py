"""
MCP_D_03_Add_a_user_parameter
=============================
Group       : Core
Script ID   : D-03
Description : Add a user parameter
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_D_03_Add_a_user_parameter

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app    = adsk.core.Application.get()
    des    = adsk.fusion.Design.cast(app.activeProduct)
    params = des.userParameters

    # createByReal takes cm; we store as an expression string for readability
    new_param = params.add(
        "test_width",
        adsk.core.ValueInput.createByString("25 mm"),
        "mm",
        "MCP test parameter"
    )

    print(f"Parameter created:  {new_param.name}")
    print(f"Value (cm):         {new_param.value}")
    print(f"Expression:         {new_param.expression}")
    print(f"Comment:            {new_param.comment}")
