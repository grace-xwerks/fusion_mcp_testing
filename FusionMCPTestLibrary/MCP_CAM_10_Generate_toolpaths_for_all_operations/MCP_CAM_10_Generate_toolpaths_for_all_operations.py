"""
MCP_CAM_10_Generate_toolpaths_for_all_operations
================================================
Group       : Manufacture
Script ID   : CAM-10
Description : Generate toolpaths for all operations in setup 0
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_10_Generate_toolpaths_for_all_operations

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return

    setup = cam.setups.item(0)
    print(f"Generating toolpaths for setup: {setup.name}")
    print(f"Operations to generate: {setup.allOperations.count}")

    # Build collection of all operations
    ops = adsk.core.ObjectCollection.create()
    for i in range(setup.allOperations.count):
        ops.add(setup.allOperations.item(i))

    # Generate (synchronous)
    future = cam.generateToolpaths(ops)
    # Wait for completion
    while not future.isGenerationCompleted:
        adsk.core.Application.get().userInterface.messageBox("Generating...", "Wait")
        # Note: in MCP scripts there's no event loop — generation may be sync
        break

    print(f"Toolpath generation submitted.")
    print("Check the Manufacture workspace — toolpaths should appear in green/yellow.")

    # Report operation statuses
    for i in range(setup.allOperations.count):
        op = setup.allOperations.item(i)
        print(f"  {op.name:35s} hasToolpath={op.hasToolpath}  isValid={op.isValid}")
