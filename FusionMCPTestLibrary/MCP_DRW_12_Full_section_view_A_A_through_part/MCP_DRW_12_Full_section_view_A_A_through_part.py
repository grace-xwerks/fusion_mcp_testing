"""
MCP_DRW_12_Full_section_view_A_A_through_part
=============================================
Group       : Drawings
Script ID   : DRW-12
Description : Full section view — A-A through part centerline (vertical cut)
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_12_Full_section_view_A_A_through_part

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
        print("No base view found. Run DRW-04 first.")
        return

    # ── Define the cutting line ───────────────────────────────────────────────
    # Cutting plane runs vertically through the horizontal centre of the part.
    # In the front view the part occupies roughly (7, 9) to (17, 13) cm on sheet.
    # We cut at X = 12 cm (part centre), sweeping full height of the view.
    #
    # Point3D coordinates here are in SHEET SPACE (cm), not model space.
    # The two points define the cutting line end points on the parent view.

    bv_pos   = base_view.position           # sheet-space centre of view
    cut_x    = bv_pos.x                     # cut through the view centre
    cut_top  = adsk.core.Point3D.create(cut_x, bv_pos.y + 2.0, 0)   # above view
    cut_bot  = adsk.core.Point3D.create(cut_x, bv_pos.y - 2.0, 0)   # below view

    # ── Create the section view input ────────────────────────────────────────
    section_input = sheet.drawingViews.createSectionViewInput(base_view)

    # Cutting line: two points defining the section plane
    section_input.sectionType = adsk.fusion.SectionTypes.FullSectionType

    cutting_line = adsk.core.ObjectCollection.create()
    cutting_line.add(cut_top)
    cutting_line.add(cut_bot)
    section_input.cuttingLine = cutting_line

    # Place the section view to the right and below the base view
    section_input.position = adsk.core.Point3D.create(
        bv_pos.x + 8.0,   # 80 mm to the right
        bv_pos.y,
        0
    )
    section_input.scale          = base_view.scale
    section_input.sectionLabel   = "A"   # produces "SECTION A-A" label

    section_view = sheet.drawingViews.addSectionView(section_input)

    print(f"Full section view created: {section_view.name}")
    print(f"  Label       : SECTION A-A")
    print(f"  Cut at X    : {cut_x*10:.1f} mm (part centre, vertical plane)")
    print(f"  Position    : ({section_input.position.x*10:.0f}, {section_input.position.y*10:.0f}) mm")
    print(f"  Scale       : {section_view.scale}")
    print(f"\nExpect to see: pocket profile, hole cross-sections, chamfer detail.")
