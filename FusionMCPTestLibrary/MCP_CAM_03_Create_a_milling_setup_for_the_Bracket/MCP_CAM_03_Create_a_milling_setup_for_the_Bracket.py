"""
MCP_CAM_03_Create_a_milling_setup_for_the_Bracket
=================================================
Group       : Manufacture
Script ID   : CAM-03
Description : Create a milling setup for the Bracket part
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_03_Create_a_milling_setup_for_the_Bracket

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first.")
        return

    des  = adsk.fusion.Design.cast(
        app.documents.itemByName(cam.designRootName).products.item(0)
    ) if False else None  # we'll use cam's linked design

    # Get the body from the active design linked to this CAM product
    # The CAM product has a reference to the design
    setup_input = cam.setups.createInput(adsk.cam.OperationTypes.MillingOperation)
    setup_input.name = "Op1_Top_Side"

    # Stock: use bounding box + 2 mm offset on sides, 1 mm on top
    stock_input = setup_input.stockInput
    stock_input.stockSelectionType = adsk.cam.StockSelectionTypes.RelativeBoxStockType
    stock_offsets = adsk.cam.BoxStockOffsets.create(
        adsk.core.ValueInput.createByString("0.1 mm"),  # +X
        adsk.core.ValueInput.createByString("0.1 mm"),  # -X
        adsk.core.ValueInput.createByString("0.1 mm"),  # +Y
        adsk.core.ValueInput.createByString("0.1 mm"),  # -Y
        adsk.core.ValueInput.createByString("1 mm"),    # +Z (top stock)
        adsk.core.ValueInput.createByString("0 mm"),    # -Z (bottom fixed)
    )
    stock_input.setRelativeBoxStock(stock_offsets)

    setup = cam.setups.add(setup_input)
    print(f"Setup created: {setup.name}")
    print(f"Operation type: Milling")
    print(f"Stock: bounding box + 1 mm top, 0.1 mm sides")
    print(f"\nNow use CAM-04 through CAM-09 to add operations.")
