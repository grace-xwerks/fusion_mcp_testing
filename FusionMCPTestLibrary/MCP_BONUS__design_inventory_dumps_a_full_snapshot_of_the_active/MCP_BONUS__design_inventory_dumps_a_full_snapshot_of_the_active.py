"""
MCP_BONUS__design_inventory_dumps_a_full_snapshot_of_the_active
===============================================================
Group       : Core
Script ID   : BONUS: design_inventory
Description : dumps a full snapshot of the active design
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_BONUS__design_inventory_dumps_a_full_snapshot_of_the_active

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    print("=== Design Inventory ===")
    print(f"Document : {des.parentDocument.name}")
    print(f"Design   : {des.rootComponent.name}")
    print()

    print(f"Bodies ({root.bRepBodies.count}):")
    for i in range(root.bRepBodies.count):
        b = root.bRepBodies.item(i)
        print(f"  [{i}] {b.name}  visible={b.isVisible}")

    print(f"\nSketches ({root.sketches.count}):")
    for i in range(root.sketches.count):
        s = root.sketches.item(i)
        print(f"  [{i}] {s.name}  profiles={s.profiles.count}")

    print(f"\nUser Parameters ({des.userParameters.count}):")
    for i in range(des.userParameters.count):
        p = des.userParameters.item(i)
        print(f"  [{i}] {p.name} = {p.expression}  ({p.unit})")

    print(f"\nComponents ({root.occurrences.count} occurrences at root):")
    for i in range(root.occurrences.count):
        o = root.occurrences.item(i)
        print(f"  [{i}] {o.component.name}")

    print("\n=== End Inventory ===")
