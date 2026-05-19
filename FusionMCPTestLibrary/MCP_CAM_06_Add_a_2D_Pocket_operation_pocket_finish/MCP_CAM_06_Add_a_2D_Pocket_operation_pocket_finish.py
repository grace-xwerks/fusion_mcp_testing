"""
MCP_CAM_06_Add_a_2D_Pocket_operation_pocket_finish
==================================================
Group       : Manufacture
Script ID   : CAM-06
Description : Add a 2D Pocket operation (pocket finish pass)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_06_Add_a_2D_Pocket_operation_pocket_finish

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

    setup    = cam.setups.item(0)
    op_input = setup.operations.createInput("pocket2d")
    op_input.displayName = "3_Pocket_Finish"

    for i in range(cam.documentToolLibrary.count):
        t = cam.documentToolLibrary.item(i)
        dia = t.parameters.itemByName('tool_diameter').value * 10
        if t.typeName == "flat end mill" and 6 <= dia <= 8:
            op_input.tool = t
            print(f"Tool: {t.description}  Ø{dia:.1f} mm")
            break

    params = op_input.parameters
    params.itemByName("tolerance").value           = adsk.core.ValueInput.createByString("0.01 mm")
    params.itemByName("stepover").value            = adsk.core.ValueInput.createByString("40%")
    params.itemByName("maximumStepdown").value     = adsk.core.ValueInput.createByString("2 mm")
    params.itemByName("stockToLeave").value        = adsk.core.ValueInput.createByString("0 mm")   # finish pass
    params.itemByName("finishingPasses").value     = adsk.core.ValueInput.createByReal(1)
    params.itemByName("finishStepover").value      = adsk.core.ValueInput.createByString("0.2 mm")

    op = setup.operations.add(op_input)
    print(f"Operation added: {op.name}  strategy={op.strategy}")
