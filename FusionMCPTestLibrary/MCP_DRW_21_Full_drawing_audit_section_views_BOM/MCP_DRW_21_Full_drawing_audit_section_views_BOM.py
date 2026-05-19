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

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active.")
        return

    print(f"╔══════════════════════════════════════════════════╗")
    print(f"  Drawing Completion Audit")
    print(f"  Document: {drw.parentDocument.name}")
    print(f"╚══════════════════════════════════════════════════╝")
    print()

    grand_total = {
        "sheets":      drw.sheets.count,
        "views":       0,
        "sections":    0,
        "dims":        0,
        "notes":       0,
        "balloons":    0,
        "parts_lists": 0,
    }

    for s_idx in range(drw.sheets.count):
        sheet = drw.sheets.item(s_idx)
        print(f"  ── Sheet [{s_idx}]: {sheet.name} ({sheet.paperSize}) ──")

        # Views breakdown
        base_ct = section_ct = proj_ct = detail_ct = 0
        for i in range(sheet.drawingViews.count):
            vt = sheet.drawingViews.item(i).drawingViewType
            if vt == adsk.fusion.DrawingViewTypes.BaseDrawingViewType:
                base_ct += 1
            elif vt == adsk.fusion.DrawingViewTypes.SectionDrawingViewType:
                section_ct += 1
            elif vt == adsk.fusion.DrawingViewTypes.ProjectedDrawingViewType:
                proj_ct += 1
            elif vt == adsk.fusion.DrawingViewTypes.DetailDrawingViewType:
                detail_ct += 1

        total_views = sheet.drawingViews.count
        grand_total["views"]    += total_views
        grand_total["sections"] += section_ct

        print(f"    Views      : {total_views} total  "
              f"(base={base_ct}, projected={proj_ct}, "
              f"section={section_ct}, detail={detail_ct})")

        # Dimensions
        dim_ct = sheet.drawingDimensions.count
        grand_total["dims"] += dim_ct
        print(f"    Dimensions : {dim_ct}")

        # Notes / leaders
        note_ct = sheet.drawingNotes.count
        grand_total["notes"] += note_ct
        print(f"    Notes      : {note_ct}")

        # Balloons
        balloon_ct = sheet.drawingBalloons.count
        grand_total["balloons"] += balloon_ct
        print(f"    Balloons   : {balloon_ct}")

        # Parts lists / tables
        pl_ct = 0
        for t_idx in range(sheet.drawingTableViews.count):
            t = sheet.drawingTableViews.item(t_idx)
            if t.tableViewType == adsk.fusion.DrawingTableViewTypes.PartsListDrawingTableViewType:
                pl_ct += 1
                print(f"    Parts list : '{t.name}'  "
                      f"{t.rowCount} rows × {t.columnCount} cols")
        if pl_ct == 0:
            print(f"    Parts list : ✗ MISSING — run DRW-17")
        grand_total["parts_lists"] += pl_ct

        # Section view labels present?
        section_labels = []
        for i in range(sheet.drawingViews.count):
            v = sheet.drawingViews.item(i)
            if (v.drawingViewType == adsk.fusion.DrawingViewTypes.SectionDrawingViewType
                    and hasattr(v, "sectionLabel")):
                section_labels.append(v.sectionLabel)
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
