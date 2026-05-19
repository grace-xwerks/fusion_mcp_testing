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

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw or drw.sheets.count == 0:
        print("No drawing found.")
        return

    sheet     = drw.sheets.item(0)
    base_view = sheet.drawingViews.item(0)

    print(f"Base view: {base_view.name}")
    print(f"Visible edges in view: {base_view.curves.count}")

    # Auto-detect the two leftmost and rightmost points to drive a width dim
    # In practice you'd select specific edges by their 3D geometry match;
    # here we demonstrate the API pattern with the bounding geometry.
    curves = base_view.curves
    if curves.count < 2:
        print("Not enough curves in view to dimension. Ensure DRW-04 ran correctly.")
        return

    # Add a linear dimension between first two visible edges
    dim_input = sheet.drawingDimensions.createLinearDimensionInput(
        curves.item(0),   # first edge
        curves.item(1),   # second edge (Fusion picks nearest parallel pair)
        adsk.core.Point3D.create(7.0, 7.5, 0),   # dimension line position
        adsk.fusion.DrawingLinearDimensionOrientations.HorizontalLinearDimension
    )
    dim = sheet.drawingDimensions.addLinearDimension(dim_input)
    print(f"Linear dimension added: {dim.text.formattedText if hasattr(dim, 'text') else 'OK'}")
