"""
MCP_CAM_03_Create_a_milling_setup_for_the_Bracket
=================================================
Group       : Manufacture
Script ID   : CAM-03
Description : Create a milling setup for the Bracket part
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_03_Create_a_milling_setup_for_the_Bracket

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first (run CAM-01).")
        return

    # Idempotent: reuse an existing milling setup if one is already present.
    existing = None
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        if s.name == 'BracketMillingSetup':
            existing = s
            break

    if existing:
        print(f"Reusing existing setup: {existing.name}")
        setup = existing
    else:
        setups = cam.setups
        setup_in = setups.createInput(adsk.cam.OperationTypes.MillingOperation)

        # Find the Bracket body off the CAM-linked design root occurrence.
        bracket = None
        for b in cam.designRootOccurrence.bRepBodies:
            if b.name == 'Bracket':
                bracket = b
                break
        if not bracket:
            print("ERROR: Could not find a body named 'Bracket' under the design root.")
            print("Run the DESIGN scripts first to build the Bracket part.")
            return

        setup_in.models = [bracket]
        setup = setups.add(setup_in)
        setup.name = 'BracketMillingSetup'
        print(f"Setup created: {setup.name}")

    # TODO: position the WCS at the top-left corner vertex of the stock.
    # The Fusion 2703.x API surface for WCS-via-vertex is non-obvious — using
    # the default WCS origin for now; CAM-04+ operations work either way.

    print(f"Operation type   : {setup.operationType}")
    print(f"Operations count : {setup.operations.count}")
