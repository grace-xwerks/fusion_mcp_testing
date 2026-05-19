"""
MCP_DESIGN_01_Inspect_active_design_workspace_and
=================================================
Group       : Design
Script ID   : DESIGN-01
Description : Inspect active design — workspace and product type check
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_01_Inspect_active_design_workspace_and

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    prod = app.activeProduct

    print(f"Product type  : {prod.productType}")
    print(f"Design type   : {adsk.fusion.Design.cast(prod).designType}")
    # designType: 0=DirectDesign, 1=ParametricDesign
    des = adsk.fusion.Design.cast(prod)
    print(f"Parametric    : {des.designType == adsk.fusion.DesignTypes.ParametricDesignType}")
    print(f"Root comp     : {des.rootComponent.name}")
    print(f"Bodies        : {des.rootComponent.bRepBodies.count}")
    print(f"User params   : {des.userParameters.count}")
    print(f"Fusion version: {app.version}")
