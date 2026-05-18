"""
MCP_DRW_04_Add_a_base_view_front_view_to_the
============================================
Group       : Drawings
Script ID   : DRW-04
Description : Add a base view (front view) to the active drawing sheet
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_04_Add_a_base_view_front_view_to_the

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active. Run DRW-03 or open a drawing first.")
        return

    sheet = drw.sheets.item(0)

    # Find the linked design's root component
    # The drawing has a reference to the source design
    refs = drw.referencedDocuments
    print(f"Referenced documents: {refs.count}")

    # Add base view input
    view_input = sheet.drawingViews.createBaseViewInput()
    view_input.referencedDocument = refs.item(0) if refs.count > 0 else None

    # Position: center of A-size sheet (in mm)
    # A-size (ANSI A) = 215.9 x 279.4 mm — place front view at ~1/3 from left
    view_input.position = adsk.core.Point3D.create(7.0, 10.0, 0)   # cm
    view_input.scale    = 0.5    # 1:2 scale — part is 100mm, sheet is ~280mm
    view_input.viewOrientation = adsk.fusion.DrawingViewOrientations.FrontViewOrientation
    view_input.viewStyle = adsk.fusion.DrawingViewStyles.VisibleAndHiddenEdgesViewStyle

    base_view = sheet.drawingViews.addBaseView(view_input)
    print(f"Base view added: {base_view.name}")
    print(f"  Orientation : Front")
    print(f"  Scale       : 1:2")
    print(f"  Position    : (70, 100) mm")
