"""
MCP_CAM_05_Add_a_2D_Adaptive_Clearing_operation
===============================================
Group       : Manufacture
Script ID   : CAM-05
Description : Add a 2D Adaptive Clearing operation (HEM-style roughing)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_05_Add_a_2D_Adaptive_Clearing_operation

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
    op_input = setup.operations.createInput("adaptive2d")
    op_input.displayName = "2_Adaptive_Rough"

    # Select a flat end mill (prefer 3/8" or 10mm diameter)
    for i in range(cam.documentToolLibrary.count):
        t = cam.documentToolLibrary.item(i)
        dia = t.parameters.itemByName('tool_diameter').value * 10  # mm
        if t.typeName == "flat end mill" and 8 <= dia <= 12:
            op_input.tool = t
            print(f"Tool: {t.description}  Ø{dia:.1f} mm")
            break

    params = op_input.parameters

    # HEM parameters: high ADOC (full flute), low RDOC (~10% D)
    # Per HEM Guidebook — lower RDOC + higher ADOC = consistent chip load
    params.itemByName("tolerance").value           = adsk.core.ValueInput.createByString("0.02 mm")
    params.itemByName("optimalLoad").value         = adsk.core.ValueInput.createByString("10%")   # RDOC = 10% D
    params.itemByName("maximumStepdown").value     = adsk.core.ValueInput.createByString("8 mm")  # full flute ADOC
    params.itemByName("stockToLeave").value        = adsk.core.ValueInput.createByString("0.3 mm")
    params.itemByName("bothWays").value            = adsk.core.ValueInput.createByReal(0)          # climb only

    op = setup.operations.add(op_input)
    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print("HEM params: 10% RDOC / 8mm ADOC — constant chip load roughing")
