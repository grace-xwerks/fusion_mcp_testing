"""
MCP_DRW_17_Create_a_parts_list_BOM_table_on_sheet_1
===================================================
Group       : Drawings
Script ID   : DRW-17
Description : Create a parts list (BOM table) on sheet 1
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_17_Create_a_parts_list_BOM_table_on_sheet_1

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

    # Can only create a parts list if the drawing references an assembly
    refs = drw.referencedDocuments
    if refs.count == 0:
        print("No referenced documents found. Drawing must reference a design.")
        return

    tbl_input          = sheet.customTables.createInput(refs.item(0))
    tbl_input.position = adsk.core.Point3D.create(16.0, 2.0, 0)
    parts_list         = sheet.customTables.add(tbl_input)

    print(f"Parts list created: {parts_list.name}")
    print(f"  Rows    : {parts_list.rows.count}  (1 header + components)")
    print(f"  Columns : {parts_list.columns.count}")
    print(f"  Position: lower-right of sheet (standard placement)\n")
    print("  Contents:")
    for r in range(parts_list.rows.count):
        row = parts_list.rows.item(r)
        cells = [row.cells.item(c).text[:20] for c in range(parts_list.columns.count)]
        print(f"    Row {r}: {' | '.join(cells)}")
