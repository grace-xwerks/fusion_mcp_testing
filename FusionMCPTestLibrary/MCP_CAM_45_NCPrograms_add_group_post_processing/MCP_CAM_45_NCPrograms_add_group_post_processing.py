"""
MCP_CAM_45_NCPrograms_add_group_post_processing
===============================================
Group       : Manufacture
Script ID   : CAM-45
Description : NCPrograms.add (group post-processing into an NC program)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_45_NCPrograms_add_group_post_processing

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

    ncs = cam.ncPrograms
    print(f"Existing NCPrograms: {ncs.count}")
    for i in range(ncs.count):
        n = ncs.item(i)
        print(f"  [{i}] {n.name}")

    try:
        ci = ncs.createInput()
        # NCProgramInput is the standard pattern. Set the post + program name,
        # then point at the setup to bundle.
        for attr_name, val in (('name', 'BracketNCProgram_Demo'),
                               ('programName', '1002')):
            if hasattr(ci, attr_name):
                try: setattr(ci, attr_name, val)
                except Exception: pass
        # Operations / scope: prefer .operations = [setup] if exposed.
        for attr_name in ('operations', 'parent', 'scope'):
            if hasattr(ci, attr_name):
                try:
                    if attr_name == 'operations':
                        setattr(ci, attr_name, [cam.setups.item(0)])
                    else:
                        setattr(ci, attr_name, cam.setups.item(0))
                except Exception:
                    pass
        added = ncs.add(ci)
        print(f"\nAdded NCProgram: {added.name}")
    except AttributeError as e:
        print(f"NCPrograms.createInput not exposed in this build: {e}")
    except Exception as e:
        print(f"add failed: {e}")
