"""
MCP_CAM_12_Full_setup_inventory_dump_useful_after
=================================================
Group       : Manufacture
Script ID   : CAM-12
Description : Full setup inventory dump — useful after a session to audit state
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_12_Full_setup_inventory_dump_useful_after

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Not in Manufacture workspace.")
        return

    print(f"=== CAM Setup Inventory ===")
    print(f"Total setups: {cam.setups.count}")

    for s_idx in range(cam.setups.count):
        setup = cam.setups.item(s_idx)
        print(f"\nSetup [{s_idx}]: {setup.name}")
        print(f"  Operations: {setup.allOperations.count}")

        for o_idx in range(setup.allOperations.count):
            op = setup.allOperations.item(o_idx)
            tool_info = ""
            if op.tool:
                dia = op.tool.parameters.itemByName('tool_diameter')
                tool_info = f"Ø{dia.value*10:.1f}mm {op.tool.typeName}" if dia else op.tool.typeName
            status = "✓" if op.hasToolpath and op.isValid else "✗"
            print(f"  {status} [{o_idx}] {op.name:35s}  {op.strategy:20s}  {tool_info}")
