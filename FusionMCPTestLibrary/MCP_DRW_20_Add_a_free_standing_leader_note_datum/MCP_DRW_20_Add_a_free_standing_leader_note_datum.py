"""
MCP_DRW_20_Add_a_free_standing_leader_note_datum
================================================
Group       : Drawings
Script ID   : DRW-20
Description : Add a free-standing leader note (datum flag / machining callout)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_20_Add_a_free_standing_leader_note_datum

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

    # Leader notes relevant to a machined bracket per CNC Fundamentals guide:
    callouts = [
        # (note_pos_cm, leader_end_cm, text)
        (
            (4.0, 14.5),
            (5.5, 13.5),
            "DATUM A\nMACHINE FACE FIRST\n(OP-1 REFERENCE)"
        ),
        (
            (12.5, 7.0),
            (11.0,  8.5),
            "TYP 4X\nØ6.0 THRU\nØ10.0 ↧ 3.0 CBORE"
        ),
        (
            (8.0, 14.5),
            (9.0, 13.0),
            "POCKET DEPTH\n8.0 ±0.05\nR2.0 CORNERS TYP"
        ),
    ]

    notes_coll = sheet.drawingNotes

    for (nx, ny), (lx, ly), text in callouts:
        note_input = notes_coll.createInput(adsk.core.Point3D.create(nx, ny, 0))
        note_input.text         = text
        note_input.isLeader     = True
        note_input.leaderPoints = adsk.core.ObjectCollection.create()
        note_input.leaderPoints.add(adsk.core.Point3D.create(lx, ly, 0))
        notes_coll.add(note_input)
        print(f"Leader note added: '{text.split(chr(10))[0]}...'  at ({nx*10:.0f}, {ny*10:.0f}) mm")

    print(f"\nTotal notes on sheet: {notes_coll.count}")
