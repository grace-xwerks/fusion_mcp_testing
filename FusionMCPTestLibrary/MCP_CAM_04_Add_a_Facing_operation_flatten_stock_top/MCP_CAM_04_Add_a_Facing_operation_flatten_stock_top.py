"""
MCP_CAM_04_Add_a_Facing_operation_flatten_stock_top
===================================================
Group       : Manufacture
Script ID   : CAM-04
Description : Add a Facing operation (flatten stock top)
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_04_Add_a_Facing_operation_flatten_stock_top

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

    if cam.setups.count == 0:
        print("No setups found — run CAM-03 first.")
        return

    setup = cam.setups.item(0)

    op_input = setup.operations.createInput("face")
    op_input.displayName = "1_Facing"

    # Tool: first flat endmill or face mill in library
    for i in range(cam.documentToolLibrary.count):
        t = cam.documentToolLibrary.item(i)
        if t.typeName in ("flat end mill", "face mill"):
            op_input.tool = t
            print(f"Tool selected: {t.description}  Ø{t.parameters.itemByName('tool_diameter').value*10:.1f} mm")
            break

    # Facing parameters
    params = op_input.parameters
    params.itemByName("tolerance").value        = adsk.core.ValueInput.createByString("0.01 mm")
    params.itemByName("stepover").value         = adsk.core.ValueInput.createByString("75%")
    params.itemByName("stockToLeave").value     = adsk.core.ValueInput.createByString("0 mm")
    params.itemByName("bottomHeight").value     = adsk.core.ValueInput.createByString("0 mm")  # machine to exact Z0

    op = setup.operations.add(op_input)
    print(f"Operation added: {op.name}  strategy={op.strategy}")
