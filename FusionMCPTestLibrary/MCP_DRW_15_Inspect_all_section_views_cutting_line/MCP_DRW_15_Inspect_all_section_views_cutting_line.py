"""
MCP_DRW_15_Inspect_all_section_views_cutting_line
=================================================
Group       : Drawings
Script ID   : DRW-15
Description : Inspect all section views — cutting line geometry + labels
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_15_Inspect_all_section_views_cutting_line

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active.")
        return

    print(f"=== Section View Audit: {drw.parentDocument.name} ===")
    total = 0

    for s_idx in range(drw.sheets.count):
        sheet = drw.sheets.item(s_idx)
        sheet_sections = []

        for v_idx in range(sheet.drawingViews.count):
            v = sheet.drawingViews.item(v_idx)
            if v.drawingViewType == adsk.fusion.DrawingViewTypes.SectionDrawingViewType:
                sheet_sections.append(v)

        if sheet_sections:
            print(f"\n  Sheet: {sheet.name}")
            for sv in sheet_sections:
                total += 1
                print(f"    Section: {sv.name}")
                print(f"      Label      : {sv.sectionLabel if hasattr(sv, 'sectionLabel') else 'N/A'}")
                print(f"      Scale      : {sv.scale:.3f}")
                pos = sv.position
                print(f"      Position   : ({pos.x*10:.1f}, {pos.y*10:.1f}) mm")
                # Parent view
                if hasattr(sv, 'parentView') and sv.parentView:
                    print(f"      Parent view: {sv.parentView.name}")

    print(f"\nTotal section views: {total}")
    if total == 0:
        print("Run DRW-12, DRW-13, or DRW-14 to add section views.")
