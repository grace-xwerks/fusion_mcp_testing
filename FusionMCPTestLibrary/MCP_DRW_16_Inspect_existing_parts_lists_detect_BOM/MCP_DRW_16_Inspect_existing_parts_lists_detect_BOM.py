"""
MCP_DRW_16_Inspect_existing_parts_lists_detect_BOM
==================================================
Group       : Drawings
Script ID   : DRW-16
Description : Inspect existing parts lists / detect BOM presence
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_16_Inspect_existing_parts_lists_detect_BOM

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.drawing, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active.")
        return

    print(f"=== BOM / Parts List Audit: {drw.parentDocument.name} ===")

    for s_idx in range(drw.sheets.count):
        sheet = drw.sheets.item(s_idx)
        print(f"\n  Sheet [{s_idx}]: {sheet.name}")
        print(f"    Custom tables: {sheet.customTables.count}")
        for t_idx in range(sheet.customTables.count):
            tbl = sheet.customTables.item(t_idx)
            print(f"      [{t_idx}] {tbl.name}  rows={tbl.rows.count}  cols={tbl.columns.count}")
        print(f"    Balloons: {sheet.drawingBalloons.count}")
        for b_idx in range(sheet.drawingBalloons.count):
            b = sheet.drawingBalloons.item(b_idx)
            print(f"      [{b_idx}] {b.text.formattedText}")

    # Check if referenced design is an assembly (needed for non-trivial BOM).
    # Design itself still lives in adsk.fusion.
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
