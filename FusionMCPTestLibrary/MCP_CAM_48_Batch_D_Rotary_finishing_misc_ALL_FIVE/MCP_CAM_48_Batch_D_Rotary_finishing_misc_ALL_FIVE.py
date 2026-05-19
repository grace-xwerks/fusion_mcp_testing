"""
MCP_CAM_48_Batch_D_Rotary_finishing_misc_ALL_FIVE
=================================================
Group       : Manufacture
Script ID   : CAM-48
Description : Batch D — Rotary + finishing-misc — ALL FIVE strategies in one run
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_48_Batch_D_Rotary_finishing_misc_ALL_FIVE

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first.")
        return
    setup = next((s for s in cam.setups if s.name == 'RotorRotarySetup'), None)
    if setup is None:
        print("RotorRotarySetup not found — run CAM-47 first.")
        return

    batch_d = ['rotary_contour', 'rotary_pocket', 'rotary_finishing',
               'deburr', 'geodesic']

    # First, sanity-check that each strategy is recognized + allowed under the
    # current license/preview flags.
    strat_objs = {}
    for name in batch_d:
        s = adsk.cam.OperationStrategy.createFromString(name)
        strat_objs[name] = s
        print(f"  {name:18s}  allowed={s.isGenerationAllowed}  "
              f"rotary={s.isRotaryStrategy}  finishing={s.isFinishingStrategy}")

    # Then create one OperationInput per strategy and add it to the setup.
    # This is the exact pattern that crashed Fusion in earlier sessions.
    print("\nCreating OperationInputs...")
    for name in batch_d:
        op_in = setup.operations.createInput(name)
        op_in.displayName = f"Batch_D_{name}"
        op = setup.operations.add(op_in)
        print(f"  added: {op.name}  strategy={op.strategy}")

    print(f"\nTotal operations on setup: {setup.operations.count}")
    print("If you see this line, quirk #9 may have softened — update memory.")
