"""
MCP_DRW_15_Inspect_all_section_views_cutting_line
=================================================
Group       : Drawings
Script ID   : DRW-15
Description : Inspect all section views — cutting line geometry + labels
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_15_Inspect_all_section_views_cutting_line

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

    print(f"=== Section View Audit: {drw.parentDocument.name} ===")
    section_type = adsk.drawing.DrawingViewTypes.SectionDrawingViewType
    total = 0

    for s_idx in range(drw.sheets.count):
        sheet = drw.sheets.item(s_idx)
        sections = [sheet.drawingViews.item(i) for i in range(sheet.drawingViews.count)
                    if sheet.drawingViews.item(i).drawingViewType == section_type]
        if sections:
            print(f"\n  Sheet: {sheet.name}")
            for sv in sections:
                total += 1
                print(f"    Section: {sv.name}")
                print(f"      Label      : {sv.sectionLabel}")
                print(f"      Scale      : {sv.scale:.3f}")
                print(f"      Position   : ({sv.position.x*10:.1f}, {sv.position.y*10:.1f}) mm")
                if sv.parentView:
                    print(f"      Parent view: {sv.parentView.name}")

    print(f"\nTotal section views: {total}")
    if total == 0:
        print("Run DRW-12, DRW-13, or DRW-14 to add section views.")
