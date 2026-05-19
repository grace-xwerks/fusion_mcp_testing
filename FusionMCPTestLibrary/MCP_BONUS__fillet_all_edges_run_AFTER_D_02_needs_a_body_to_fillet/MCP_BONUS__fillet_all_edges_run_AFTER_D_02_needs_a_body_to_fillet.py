"""
MCP_BONUS__fillet_all_edges_run_AFTER_D_02_needs_a_body_to_fillet
=================================================================
Group       : Core
Script ID   : BONUS: fillet_all_edges
Description : run AFTER D-02 (needs a body to fillet)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_BONUS__fillet_all_edges_run_AFTER_D_02_needs_a_body_to_fillet

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    if root.bRepBodies.count == 0:
        print("No bodies found — run D-02 first to create a cube")
        return

    body   = root.bRepBodies.item(0)
    edges  = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        edges.add(edge)

    fillets    = root.features.filletFeatures
    fillet_in  = fillets.createInput()
    fillet_in.addConstantRadiusEdgeSet(
        edges,
        adsk.core.ValueInput.createByReal(0.1),   # 1 mm radius
        True
    )
    fillets.add(fillet_in)

    print(f"Filleted {edges.count} edges with 1 mm radius")
