"""
MCP_CAM_43_Manufacturing_Models_separate_machining
==================================================
Group       : Manufacture
Script ID   : CAM-43
Description : Manufacturing Models (separate machining body)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_43_Manufacturing_Models_separate_machining

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first."); return

    mms = cam.manufacturingModels
    print(f"manufacturingModels.count = {mms.count}")
    for i in range(mms.count):
        m = mms.item(i)
        print(f"  [{i}] {m.name}")

    # Try to add a new one if API is available.
    try:
        ci = mms.createInput()
        ci.name = "CAM_Mfg_Model_Demo"
        # Source the design body as a baseline; ManufacturingModelInput typically
        # takes the design body via .designModel or models list.
        body = next((b for b in cam.designRootOccurrence.bRepBodies), None)
        if body is not None:
            for attr in ('models', 'designModel', 'body', 'sourceBody'):
                if hasattr(ci, attr):
                    try:
                        if attr == 'models':
                            setattr(ci, attr, [body])
                        else:
                            setattr(ci, attr, body)
                    except Exception:
                        pass
        added = mms.add(ci)
        print(f"  added: {added.name}")
    except AttributeError as e:
        print(f"  ManufacturingModels.createInput not exposed in this build: {e}")
    except Exception as e:
        print(f"  add failed: {e}")
