"""
MCP_CAM_07_Add_a_2D_Contour_operation_outside
=============================================
Group       : Manufacture
Script ID   : CAM-07
Description : Add a 2D Contour operation (outside profile)
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_07_Add_a_2D_Contour_operation_outside

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
    op_input = setup.operations.createInput("contour2d")
    op_input.displayName = "4_Contour_Outside"

    for i in range(cam.documentToolLibrary.count):
        t = cam.documentToolLibrary.item(i)
        dia = t.parameters.itemByName('tool_diameter').value * 10
        if t.typeName == "flat end mill" and 8 <= dia <= 12:
            op_input.tool = t
            print(f"Tool: {t.description}  Ø{dia:.1f} mm")
            break

    params = op_input.parameters
    params.itemByName("tolerance").value          = adsk.core.ValueInput.createByString("0.01 mm")
    params.itemByName("maximumStepdown").value    = adsk.core.ValueInput.createByString("5 mm")
    params.itemByName("stockToLeave").value       = adsk.core.ValueInput.createByString("0 mm")
    params.itemByName("direction").value          = adsk.core.ValueInput.createByString("climb")
    # Compensation: CDC (Cutter Diameter Compensation) — standard for contours
    params.itemByName("compensation").value       = adsk.core.ValueInput.createByString("left")

    op = setup.operations.add(op_input)
    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print("CDC direction: left (climb milling, outside contour)")
