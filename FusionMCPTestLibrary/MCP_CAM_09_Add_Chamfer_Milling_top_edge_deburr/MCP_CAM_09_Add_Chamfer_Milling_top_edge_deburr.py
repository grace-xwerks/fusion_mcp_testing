"""
MCP_CAM_09_Add_Chamfer_Milling_top_edge_deburr
==============================================
Group       : Manufacture
Script ID   : CAM-09
Description : Add Chamfer Milling (top edge deburr / chamfer)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_09_Add_Chamfer_Milling_top_edge_deburr

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
    op_input = setup.operations.createInput("contour2d")   # chamfer uses 2D Contour in Fusion
    op_input.displayName = "6_Chamfer_Top"

    # Chamfer mill or center drill as cutter
    for i in range(cam.documentToolLibrary.count):
        t = cam.documentToolLibrary.item(i)
        if t.typeName in ("chamfer mill", "dovetail mill", "center drill"):
            op_input.tool = t
            print(f"Chamfer tool: {t.description}")
            break

    params = op_input.parameters
    params.itemByName("chamfer").value          = adsk.core.ValueInput.createByReal(1)  # enable chamfer mode
    params.itemByName("chamferWidth").value     = adsk.core.ValueInput.createByString("1 mm")
    params.itemByName("tolerance").value        = adsk.core.ValueInput.createByString("0.01 mm")

    op = setup.operations.add(op_input)
    print(f"Operation added: {op.name}")
