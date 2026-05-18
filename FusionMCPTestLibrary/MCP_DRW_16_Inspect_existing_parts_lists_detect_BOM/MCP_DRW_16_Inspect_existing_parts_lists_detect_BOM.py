"""
MCP_DRW_16_Inspect_existing_parts_lists_detect_BOM
==================================================
Group       : Drawings
Script ID   : DRW-16
Description : Inspect existing parts lists / detect BOM presence
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_16_Inspect_existing_parts_lists_detect_BOM

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

    print(f"=== BOM / Parts List Audit: {drw.parentDocument.name} ===")

    for s_idx in range(drw.sheets.count):
        sheet = drw.sheets.item(s_idx)
        tables = sheet.drawingTableViews

        print(f"\n  Sheet [{s_idx}]: {sheet.name}")
        print(f"    Table views (parts lists, etc.): {tables.count}")

        for t_idx in range(tables.count):
            tbl = tables.item(t_idx)
            print(f"      [{t_idx}] {tbl.name}")
            print(f"        Type    : {tbl.tableViewType}")
            print(f"        Rows    : {tbl.rowCount}")
            print(f"        Columns : {tbl.columnCount}")

        # Also check for balloons
        balloons = sheet.drawingBalloons
        print(f"    Balloons: {balloons.count}")
        for b_idx in range(balloons.count):
            b = balloons.item(b_idx)
            print(f"      [{b_idx}] {b.text.formattedText if hasattr(b, 'text') else 'balloon'}")

    # Check if referenced design is an assembly (needed for non-trivial BOM)
    refs = drw.referencedDocuments
    print(f"\n  Referenced documents: {refs.count}")
    for i in range(refs.count):
        ref = refs.item(i)
        des = adsk.fusion.Design.cast(ref.products.item(0)) if ref.products.count > 0 else None
        if des:
            comp_count = des.rootComponent.occurrences.count
            print(f"    [{i}] {ref.name}  "
                  f"root_occurrences={comp_count}  "
                  f"{'ASSEMBLY' if comp_count > 0 else 'single-body part'}")
