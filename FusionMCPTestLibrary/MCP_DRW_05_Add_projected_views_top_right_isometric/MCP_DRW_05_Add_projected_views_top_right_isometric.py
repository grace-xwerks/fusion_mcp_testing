"""
MCP_DRW_05_Add_projected_views_top_right_isometric
==================================================
Group       : Drawings
Script ID   : DRW-05
Description : Add projected views (top, right, isometric)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_05_Add_projected_views_top_right_isometric

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw or drw.sheets.count == 0:
        print("No drawing or sheet found.")
        return

    sheet = drw.sheets.item(0)

    if sheet.drawingViews.count == 0:
        print("No base view found. Run DRW-04 first.")
        return

    base_view = sheet.drawingViews.item(0)

    # Top view — above the base view
    top_input          = sheet.drawingViews.createProjectedViewInput(base_view)
    top_input.position = adsk.core.Point3D.create(7.0, 17.0, 0)  # above
    top_view           = sheet.drawingViews.addProjectedView(top_input)
    print(f"Top view added: {top_view.name}")

    # Right view — to the right of base view
    right_input          = sheet.drawingViews.createProjectedViewInput(base_view)
    right_input.position = adsk.core.Point3D.create(14.0, 10.0, 0)  # right
    right_view           = sheet.drawingViews.addProjectedView(right_input)
    print(f"Right view added: {right_view.name}")

    # Isometric view — upper right
    iso_input                = sheet.drawingViews.createProjectedViewInput(base_view)
    iso_input.position       = adsk.core.Point3D.create(20.0, 17.0, 0)
    iso_input.viewOrientation = adsk.fusion.DrawingViewOrientations.HomeViewOrientation
    iso_view                 = sheet.drawingViews.addProjectedView(iso_input)
    print(f"Iso view added: {iso_view.name}")

    print(f"\nTotal views on sheet: {sheet.drawingViews.count}")
