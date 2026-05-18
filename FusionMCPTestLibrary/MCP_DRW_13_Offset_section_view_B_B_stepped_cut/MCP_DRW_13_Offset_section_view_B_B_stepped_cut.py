"""
MCP_DRW_13_Offset_section_view_B_B_stepped_cut
==============================================
Group       : Drawings
Script ID   : DRW-13
Description : Offset section view — B-B stepped cut
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_13_Offset_section_view_B_B_stepped_cut

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw or drw.sheets.item(0).drawingViews.count == 0:
        print("No views found. Run DRW-04 first.")
        return

    sheet     = drw.sheets.item(0)
    base_view = None

    for i in range(sheet.drawingViews.count):
        v = sheet.drawingViews.item(i)
        if v.drawingViewType == adsk.fusion.DrawingViewTypes.BaseDrawingViewType:
            base_view = v
            break

    if not base_view:
        print("No base view found.")
        return

    bv_pos = base_view.position

    # Stepped cutting line: start above part, step right to pass through
    # both the pocket centre and a hole, then continue down.
    # Points are in sheet space (cm).
    #
    # The bracket is 100 mm wide in model → ~5 cm on sheet at 1:2 scale.
    # Hole centres are at 10 mm inset → 0.5 cm on sheet.
    # Pocket centre is at 50 mm → 2.5 cm from view left edge.

    half_w = 2.5   # half of view width at 1:2 scale in cm
    hole_x = bv_pos.x - half_w + 0.5   # left hole column

    pt1 = adsk.core.Point3D.create(hole_x,          bv_pos.y + 2.0, 0)  # enter above hole
    pt2 = adsk.core.Point3D.create(hole_x,          bv_pos.y,       0)  # step down to pocket level
    pt3 = adsk.core.Point3D.create(bv_pos.x,        bv_pos.y,       0)  # step right to pocket centre
    pt4 = adsk.core.Point3D.create(bv_pos.x,        bv_pos.y - 2.0, 0)  # exit below

    section_input = sheet.drawingViews.createSectionViewInput(base_view)
    section_input.sectionType = adsk.fusion.SectionTypes.OffsetSectionType

    cutting_line = adsk.core.ObjectCollection.create()
    for pt in [pt1, pt2, pt3, pt4]:
        cutting_line.add(pt)
    section_input.cuttingLine  = cutting_line

    section_input.position     = adsk.core.Point3D.create(
        bv_pos.x + 8.0, bv_pos.y - 6.0, 0   # below the A-A section view
    )
    section_input.scale        = base_view.scale
    section_input.sectionLabel = "B"   # produces "SECTION B-B"

    section_view = sheet.drawingViews.addSectionView(section_input)

    print(f"Offset section view created: {section_view.name}")
    print(f"  Label    : SECTION B-B")
    print(f"  Steps    : 4-point stepped cutting line")
    print(f"  Captures : corner hole + pocket in single section")
