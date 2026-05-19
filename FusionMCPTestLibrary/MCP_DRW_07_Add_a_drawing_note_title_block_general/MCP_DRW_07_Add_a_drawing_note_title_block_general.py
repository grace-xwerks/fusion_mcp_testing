"""
MCP_DRW_07_Add_a_drawing_note_title_block_general
=================================================
Group       : Drawings
Script ID   : DRW-07
Description : Add a drawing note (title block / general tolerance note)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_07_Add_a_drawing_note_title_block_general

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw or drw.sheets.count == 0:
        print("No drawing found.")
        return

    sheet = drw.sheets.item(0)

    notes = [
        (adsk.core.Point3D.create(1.0, 1.5, 0),
         "MATERIAL: 6061-T6 ALUMINUM"),
        (adsk.core.Point3D.create(1.0, 1.0, 0),
         "GENERAL TOLERANCES: ±0.1 mm UNLESS OTHERWISE SPECIFIED"),
        (adsk.core.Point3D.create(1.0, 0.5, 0),
         "ALL SHARP EDGES 0.5 mm x 45° CHAMFER"),
    ]

    for pos, text in notes:
        note_input = sheet.drawingNotes.createInput(pos)
        note_input.text = text
        note = sheet.drawingNotes.add(note_input)
        print(f"Note added: {text[:50]}...")

    print(f"\nTotal notes on sheet: {sheet.drawingNotes.count}")
