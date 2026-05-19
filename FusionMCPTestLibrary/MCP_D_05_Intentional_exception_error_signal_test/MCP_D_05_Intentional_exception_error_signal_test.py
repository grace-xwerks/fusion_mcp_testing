"""
MCP_D_05_Intentional_exception_error_signal_test
================================================
Group       : Core
Script ID   : D-05
Description : Intentional exception (error signal test — NO try/except by design)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_D_05_Intentional_exception_error_signal_test

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.fusion

def run(_context: str):
    # Casting None as a Design should raise AttributeError immediately.
    # Expected: MCP returns a traceback. That's the correct error behavior.
    des = adsk.fusion.Design.cast(None)
    print(des.rootComponent.name)   # never reached
