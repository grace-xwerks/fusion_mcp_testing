"""
MCP_DRW_04_Add_a_base_view_front_view_to_the
============================================
Group       : Drawings
Script ID   : DRW-04
Description : Add a base view (front view) to the active drawing sheet
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_04_Add_a_base_view_front_view_to_the

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active. Run DRW-03 or open a drawing first.")
        return

    sheet      = drw.sheets.item(0)
    views_col  = sheet.drawingViews

    # Documented API path. Quirk #29 blocks the runtime call on
    # 2703.x Insider, but the shape is correct.
    view_input = views_col.createBaseViewInput()
    view_input.referencedDocument = drw.referencedDocuments.item(0)
    view_input.position           = adsk.core.Point3D.create(7.0, 10.0, 0)
    view_input.scale              = 0.5    # 1:2
    view_input.viewOrientation    = adsk.drawing.DrawingViewOrientations.FrontViewOrientation
    view_input.viewStyle          = adsk.drawing.DrawingViewStyles.VisibleAndHiddenEdgesViewStyle

    base_view = views_col.addBaseView(view_input)
    print(f"Base view added: {base_view.name}  (Front, 1:2, at 70/100 mm)")
