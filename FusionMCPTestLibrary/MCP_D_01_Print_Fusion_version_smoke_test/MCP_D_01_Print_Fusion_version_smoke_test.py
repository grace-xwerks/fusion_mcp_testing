"""
MCP_D_01_Print_Fusion_version_smoke_test
========================================
Group       : Core
Script ID   : D-01
Description : Print Fusion version (smoke test / connectivity check)
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_D_01_Print_Fusion_version_smoke_test

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core

def run(_context: str):
    app = adsk.core.Application.get()
    print(f"Fusion version: {app.version}")
    print(f"Active user:    {app.currentUser.displayName}")
    print(f"Active product: {app.activeProduct.productType if app.activeProduct else 'None'}")
