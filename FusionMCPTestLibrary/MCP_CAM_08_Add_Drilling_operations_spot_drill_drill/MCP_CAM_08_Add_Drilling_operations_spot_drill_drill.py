"""
MCP_CAM_08_Add_Drilling_operations_spot_drill_drill
===================================================
Group       : Manufacture
Script ID   : CAM-08
Description : Add Drilling operations (spot drill + drill)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_08_Add_Drilling_operations_spot_drill_drill

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

    # ── Spot drill ───────────────────────────────────────────────────────────
    sd_input = setup.operations.createInput("drill")
    sd_input.displayName = "5a_SpotDrill"

    for i in range(cam.documentToolLibrary.count):
        t = cam.documentToolLibrary.item(i)
        if t.typeName in ("spot drill", "center drill"):
            sd_input.tool = t
            print(f"Spot drill tool: {t.description}")
            break

    sd_params = sd_input.parameters
    sd_params.itemByName("tolerance").value     = adsk.core.ValueInput.createByString("0.02 mm")
    sd_params.itemByName("tipDepth").value      = adsk.core.ValueInput.createByString("1 mm")
    setup.operations.add(sd_input)

    # ── Through-drill ────────────────────────────────────────────────────────
    dr_input = setup.operations.createInput("drill")
    dr_input.displayName = "5b_Drill_6mm_Through"

    for i in range(cam.documentToolLibrary.count):
        t = cam.documentToolLibrary.item(i)
        dia = t.parameters.itemByName('tool_diameter').value * 10
        if t.typeName == "drill" and abs(dia - 6.0) < 0.1:
            dr_input.tool = t
            print(f"Drill tool: {t.description}  Ø{dia:.1f} mm")
            break

    dr_params = dr_input.parameters
    dr_params.itemByName("tolerance").value       = adsk.core.ValueInput.createByString("0.02 mm")
    dr_params.itemByName("cycleType").value       = adsk.core.ValueInput.createByString("chip_breaking")
    dr_params.itemByName("peckingincrements").value = adsk.core.ValueInput.createByString("3 mm")
    # Through all: set bottomHeight below stock
    dr_params.itemByName("bottomHeight").value    = adsk.core.ValueInput.createByString("-22 mm")

    dr_op = setup.operations.add(dr_input)
    print(f"Drill operation added: {dr_op.name}")
