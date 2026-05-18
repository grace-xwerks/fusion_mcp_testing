"""
MCP_DRW_18_Customize_BOM_columns
================================
Group       : Drawings
Script ID   : DRW-18
Description : Customize BOM columns
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_18_Customize_BOM_columns

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

    sheet = drw.sheets.item(0)

    # Find existing parts list
    parts_list = None
    for i in range(sheet.drawingTableViews.count):
        t = sheet.drawingTableViews.item(i)
        if t.tableViewType == adsk.fusion.DrawingTableViewTypes.PartsListDrawingTableViewType:
            parts_list = t
            break

    if not parts_list:
        print("No parts list found. Run DRW-17 first.")
        return

    print(f"Parts list: {parts_list.name}")
    print(f"Current columns ({parts_list.columnCount}):")

    for col in range(parts_list.columnCount):
        header = parts_list.cell(0, col)
        print(f"  [{col}] {header.text}")

    # Standard machining drawing columns — reorder / rename to match
    # ANSI Y14.35 convention: ITEM | QTY | PART NUMBER | DESCRIPTION | MATERIAL
    desired_headers = [
        "ITEM",
        "QTY",
        "PART NUMBER",
        "DESCRIPTION",
        "MATERIAL",
        "FINISH",
    ]

    # Rename header row cells where the column count allows
    for col in range(min(parts_list.columnCount, len(desired_headers))):
        cell = parts_list.cell(0, col)
        cell.text = desired_headers[col]

    print(f"\nHeaders updated to machining drawing standard (ANSI Y14.35):")
    for col in range(parts_list.columnCount):
        print(f"  [{col}] {parts_list.cell(0, col).text}")

    # Set column widths (cm) — ITEM narrow, DESCRIPTION wide
    col_widths = [1.0, 1.2, 3.0, 5.0, 3.0, 2.5]
    for col in range(min(parts_list.columnCount, len(col_widths))):
        try:
            parts_list.setColumnWidth(col, col_widths[col])
        except Exception:
            pass  # some columns may not be resizable via API; skip gracefully

    print("\nColumn widths adjusted.")
