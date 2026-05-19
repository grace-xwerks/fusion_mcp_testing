"""
MCP_DRW_11_Audit_existing_views_find_parent_views
=================================================
Group       : Drawings
Script ID   : DRW-11
Description : Audit existing views — find parent views suitable for section cuts
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_11_Audit_existing_views_find_parent_views

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active. Open a drawing document first.")
        return

    sheet = drw.sheets.item(0)
    print(f"Sheet: {sheet.name}  ({sheet.drawingViews.count} views)")
    print()

    # DrawingViewType enum values:
    #   BaseDrawingViewType      = 0
    #   ProjectedDrawingViewType = 1
    #   SectionDrawingViewType   = 2
    #   DetailDrawingViewType    = 3
    #   BreakDrawingViewType     = 4

    base_views    = []
    section_views = []
    other_views   = []

    for i in range(sheet.drawingViews.count):
        v = sheet.drawingViews.item(i)
        vtype = v.drawingViewType
        pos   = v.position

        info = (f"  [{i}] {v.name:25s}  "
                f"type={vtype}  "
                f"scale={v.scale:.3f}  "
                f"pos=({pos.x*10:.1f}, {pos.y*10:.1f}) mm")
        print(info)

        if vtype == adsk.fusion.DrawingViewTypes.BaseDrawingViewType:
            base_views.append((i, v))
        elif vtype == adsk.fusion.DrawingViewTypes.SectionDrawingViewType:
            section_views.append((i, v))
        else:
            other_views.append((i, v))

    print(f"\nBase views    : {len(base_views)}   ← use these as section parents")
    print(f"Section views : {len(section_views)}")
    print(f"Other views   : {len(other_views)}")

    if not base_views:
        print("\nNo base views found — run DRW-04 first to add a front view.")
    else:
        print(f"\nRecommended parent for section cut: view [{base_views[0][0]}] '{base_views[0][1].name}'")
