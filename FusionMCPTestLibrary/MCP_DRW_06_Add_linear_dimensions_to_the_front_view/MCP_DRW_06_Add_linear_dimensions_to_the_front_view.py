"""
MCP_DRW_06_Add_linear_dimensions_to_the_front_view
==================================================
Group       : Drawings
Script ID   : DRW-06
Description : Add linear dimensions to the front view
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_06_Add_linear_dimensions_to_the_front_view

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active.")
        return

    sheet     = drw.sheets.item(0)
    views_col = sheet.drawingViews
    if views_col.count == 0:
        print("No views on sheet — run DRW-04 first.")
        return
    base_view = views_col.item(0)
    curves    = base_view.curves
    print(f"Base view: {base_view.name}  curves={curves.count}")
    if curves.count < 2:
        print("Not enough curves in view to dimension.")
        return

    dim_input = sheet.drawingDimensions.createLinearDimensionInput(
        curves.item(0),
        curves.item(1),
        adsk.core.Point3D.create(7.0, 7.5, 0),
        adsk.drawing.DrawingLinearDimensionOrientations.HorizontalLinearDimension,
    )
    dim = sheet.drawingDimensions.addLinearDimension(dim_input)
    print(f"Linear dimension added: {dim.text.formattedText}")
