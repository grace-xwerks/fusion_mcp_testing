"""
MCP_DRW_18_Customize_BOM_columns
================================
Group       : Drawings
Script ID   : DRW-18
Description : Customize BOM columns
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_18_Customize_BOM_columns

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

    sheet = drw.sheets.item(0)

    if sheet.customTables.count == 0:
        print("No CustomTable on sheet. Run DRW-17 first.")
        return
    # Heuristic: the first CustomTable is the parts list (matches DRW-17 flow).
    parts_list = sheet.customTables.item(0)
    print(f"Parts list: {parts_list.name}")

    print(f"Current columns ({parts_list.columns.count}):")
    for col_idx in range(parts_list.columns.count):
        print(f"  [{col_idx}] {parts_list.columns.item(col_idx).name}")

    # Standard machining drawing columns — ANSI Y14.35 convention.
    desired_headers = [
        "ITEM", "QTY", "PART NUMBER", "DESCRIPTION", "MATERIAL", "FINISH",
    ]
    col_widths = [1.0, 1.2, 3.0, 5.0, 3.0, 2.5]
    n = min(parts_list.columns.count, len(desired_headers))
    for col_idx in range(n):
        col = parts_list.columns.item(col_idx)
        col.name  = desired_headers[col_idx]
        col.width = col_widths[col_idx]

    print(f"\nHeaders/widths updated to machining drawing standard (ANSI Y14.35).")
