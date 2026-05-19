"""
MCP_DRW_14_Half_section_view_C_C_symmetric_parts
================================================
Group       : Drawings
Script ID   : DRW-14
Description : Half section view — C-C (symmetric parts only)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_14_Half_section_view_C_C_symmetric_parts

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw or drw.sheets.item(0).drawingViews.count == 0:
        print("No views found.")
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

    # Half section: two perpendicular lines meeting at part centre.
    # pt1 → pt2 is the horizontal arm; pt2 → pt3 is the vertical arm.
    pt1 = adsk.core.Point3D.create(bv_pos.x - 2.5, bv_pos.y,       0)  # left edge
    pt2 = adsk.core.Point3D.create(bv_pos.x,        bv_pos.y,       0)  # centre (corner)
    pt3 = adsk.core.Point3D.create(bv_pos.x,        bv_pos.y - 2.0, 0)  # bottom

    section_input = sheet.drawingViews.createSectionViewInput(base_view)
    section_input.sectionType = adsk.fusion.SectionTypes.HalfSectionType

    cutting_line = adsk.core.ObjectCollection.create()
    for pt in [pt1, pt2, pt3]:
        cutting_line.add(pt)
    section_input.cuttingLine  = cutting_line

    # Add a new sheet for this view so it doesn't crowd sheet 1
    new_sheet = drw.sheets.add()
    new_sheet.name = "Sheet2_SectionViews"

    section_input.position     = adsk.core.Point3D.create(10.0, 10.0, 0)
    section_input.scale        = base_view.scale
    section_input.sectionLabel = "C"

    section_view = new_sheet.drawingViews.addSectionView(section_input)

    print(f"Half section view created: {section_view.name}")
    print(f"  Label  : SECTION C-C")
    print(f"  Sheet  : {new_sheet.name}  (new sheet added)")
    print(f"  Shows  : internal pocket + hole on left half, solid exterior on right")
