"""
MCP_CAM_44_Two_Setup_project_Roughing_Finishing
===============================================
Group       : Manufacture
Script ID   : CAM-44
Description : Two-Setup project (Roughing + Finishing split)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_44_Two_Setup_project_Roughing_Finishing

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first."); return

    name = 'BracketFinishingSetup'
    existing = None
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        if s.name == name:
            existing = s; break
    if existing:
        print(f"Reusing: {existing.name}")
    else:
        bracket = next((b for b in cam.designRootOccurrence.bRepBodies
                        if b.name == 'Bracket'), None)
        if bracket is None:
            print("Need a body named 'Bracket' under designRootOccurrence."); return
        si = cam.setups.createInput(adsk.cam.OperationTypes.MillingOperation)
        si.models = [bracket]
        setup = cam.setups.add(si)
        setup.name = name
        print(f"Created: {setup.name}")

    print(f"\nAll setups in this CAM product:")
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        print(f"  [{i}] {s.name}  ops={s.allOperations.count}")
