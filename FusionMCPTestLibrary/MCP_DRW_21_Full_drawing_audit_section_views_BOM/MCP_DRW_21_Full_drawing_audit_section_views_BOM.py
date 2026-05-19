"""
MCP_DRW_21_Full_drawing_audit_section_views_BOM
===============================================
Group       : Drawings
Script ID   : DRW-21
Description : Full drawing audit — section views + BOM + balloons
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_21_Full_drawing_audit_section_views_BOM

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

    print(f"╔══════════════════════════════════════════════════╗")
    print(f"  Drawing Completion Audit")
    print(f"  Document: {drw.parentDocument.name}")
    print(f"╚══════════════════════════════════════════════════╝")
    print()

    VT = adsk.drawing.DrawingViewTypes
    grand_total = {"sheets": drw.sheets.count, "views": 0, "sections": 0,
                   "dims": 0, "notes": 0, "balloons": 0, "parts_lists": 0}

    for s_idx in range(drw.sheets.count):
        sheet = drw.sheets.item(s_idx)
        print(f"  ── Sheet [{s_idx}]: {sheet.name} ({sheet.paperSize}) ──")

        # Views breakdown by type
        counts = {VT.BaseDrawingViewType: 0, VT.SectionDrawingViewType: 0,
                  VT.ProjectedDrawingViewType: 0, VT.DetailDrawingViewType: 0}
        for i in range(sheet.drawingViews.count):
            vt = sheet.drawingViews.item(i).drawingViewType
            if vt in counts: counts[vt] += 1
        total_views = sheet.drawingViews.count
        grand_total["views"]    += total_views
        grand_total["sections"] += counts[VT.SectionDrawingViewType]

        print(f"    Views      : {total_views} total  "
              f"(base={counts[VT.BaseDrawingViewType]}, "
              f"projected={counts[VT.ProjectedDrawingViewType]}, "
              f"section={counts[VT.SectionDrawingViewType]}, "
              f"detail={counts[VT.DetailDrawingViewType]})")

        grand_total["dims"]     += sheet.drawingDimensions.count
        grand_total["notes"]    += sheet.drawingNotes.count
        grand_total["balloons"] += sheet.drawingBalloons.count
        print(f"    Dimensions : {sheet.drawingDimensions.count}")
        print(f"    Notes      : {sheet.drawingNotes.count}")
        print(f"    Balloons   : {sheet.drawingBalloons.count}")

        if sheet.customTables.count == 0:
            print(f"    Parts list : ✗ MISSING — run DRW-17")
        else:
            for t_idx in range(sheet.customTables.count):
                t = sheet.customTables.item(t_idx)
                print(f"    Parts list : '{t.name}'  {t.rows.count} rows × {t.columns.count} cols")
        grand_total["parts_lists"] += sheet.customTables.count

        # Section view labels
        section_labels = [sheet.drawingViews.item(i).sectionLabel
                          for i in range(sheet.drawingViews.count)
                          if sheet.drawingViews.item(i).drawingViewType == VT.SectionDrawingViewType]
        if section_labels:
            print(f"    Section IDs: {', '.join(section_labels)}")

        print()

    print(f"  ── Grand Totals ──")
    for k, v in grand_total.items():
        status = "✓" if v > 0 else "✗"
        print(f"    {status} {k:12s}: {v}")

    print()
    # Readiness check
    missing = []
    if grand_total["views"]       == 0:  missing.append("views (DRW-04/05)")
    if grand_total["sections"]    == 0:  missing.append("section views (DRW-12/13)")
    if grand_total["dims"]        == 0:  missing.append("dimensions (DRW-06)")
    if grand_total["parts_lists"] == 0:  missing.append("parts list/BOM (DRW-17)")
    if grand_total["balloons"]    == 0:  missing.append("balloons (DRW-19)")

    if missing:
        print(f"  ⚠  Incomplete drawing — missing:")
        for m in missing:
            print(f"       • {m}")
    else:
        print(f"  ✓  Drawing looks complete. Ready to export (DRW-08/09).")
