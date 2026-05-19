"""
MCP_DESIGN_20_Suppress_unsuppress_a_timeline_feature
====================================================
Group       : Design
Script ID   : DESIGN-20
Description : Suppress / unsuppress a timeline feature
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_20_Suppress_unsuppress_a_timeline_feature

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

    chamfer = next((root.features.item(i) for i in range(root.features.count)
                    if root.features.item(i).classType().endswith("ChamferFeature")),
                   None)
    if chamfer is None:
        print("No ChamferFeature found.")
        return

    v_full = body.volume
    chamfer.isSuppressed = True
    v_suppressed = body.volume
    chamfer.isSuppressed = False
    v_restored = body.volume

    print(f"{chamfer.name}: full={v_full:.4f} → suppressed={v_suppressed:.4f} "
          f"(+{v_suppressed - v_full:.4f}) → unsuppressed={v_restored:.4f}")
    print(f"Roundtrip exact: {abs(v_restored - v_full) < 0.0005}")
