"""
MCP_DRW_10_Full_drawing_audit_counts_views_dims
===============================================
Group       : Drawings
Script ID   : DRW-10
Description : Full drawing audit — counts views, dims, notes across all sheets
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_10_Full_drawing_audit_counts_views_dims

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

    print(f"=== Drawing Audit: {drw.parentDocument.name} ===")
    total_views = total_dims = total_notes = 0

    for s in range(drw.sheets.count):
        sheet = drw.sheets.item(s)
        v     = sheet.drawingViews.count
        d     = sheet.drawingDimensions.count
        n     = sheet.drawingNotes.count
        total_views += v
        total_dims  += d
        total_notes += n
        print(f"\n  Sheet: {sheet.name} ({sheet.paperSize})")
        print(f"    Views      : {v}")
        print(f"    Dimensions : {d}")
        print(f"    Notes      : {n}")

        for v_idx in range(v):
            view = sheet.drawingViews.item(v_idx)
            print(f"      View: {view.name:25s}  "
                  f"type={view.drawingViewType}  "
                  f"scale={view.scale:.3f}")

    print(f"\nTotals — Views: {total_views}  Dims: {total_dims}  Notes: {total_notes}")
