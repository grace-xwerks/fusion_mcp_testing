"""
MCP_CAM_15_Parameter_table_for_a_SINGLE_strategy
================================================
Group       : Manufacture
Script ID   : CAM-15
Description : Parameter table for a SINGLE strategy
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_15_Parameter_table_for_a_SINGLE_strategy

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

STRATEGY = "pocket2d"   # ← edit to the strategy name you want dumped

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first (run CAM-01).")
        return

    # Resolve OperationStrategy to know which OperationType setup to use.
    strat_obj = adsk.cam.OperationStrategy.createFromString(STRATEGY)
    if not strat_obj:
        print(f"Unknown strategy: {STRATEGY!r}")
        return
    if strat_obj.isTurningStrategy:
        op_type = adsk.cam.OperationTypes.TurningOperation
    else:
        op_type = adsk.cam.OperationTypes.MillingOperation

    seed_body = next((b for b in cam.designRootOccurrence.bRepBodies), None)
    if seed_body is None:
        print("No bRepBody — open a design with at least one body.")
        return

    si = cam.setups.createInput(op_type)
    si.models = [seed_body]
    setup = cam.setups.add(si)
    try:
        oi = setup.operations.createInput(STRATEGY)
        params = oi.parameters
        print(f"Strategy: {STRATEGY}")
        print(f"  title       : {strat_obj.title}")
        print(f"  description : {strat_obj.description}")
        print(f"  isMilling/Turning/Drilling/Cutting/Rotary = "
              f"{strat_obj.isMillingStrategy}/{strat_obj.isTurningStrategy}/"
              f"{strat_obj.isDrillingStrategy}/{strat_obj.isCuttingStrategy}/"
              f"{strat_obj.isRotaryStrategy}")
        print(f"  is2D/3D/Finishing/Additive/Support       = "
              f"{strat_obj.is2DStrategy}/{strat_obj.is3DStrategy}/"
              f"{strat_obj.isFinishingStrategy}/"
              f"{strat_obj.isAdditiveStrategy}/{strat_obj.isSupportStrategy}")
        print(f"  parameter count: {params.count}")
        for i in range(params.count):
            p = params.item(i)
            expr  = getattr(p, 'expression', '')
            title = getattr(p, 'title', '')
            v = getattr(p, 'value', None)
            vt = type(v).__name__ if v is not None else ''
            print(f"  - {p.name:32s}  title={title!r}  expr={expr!r}  valueType={vt}")
    finally:
        # Always clean up the throwaway setup, even on error.
        setup.deleteMe()
