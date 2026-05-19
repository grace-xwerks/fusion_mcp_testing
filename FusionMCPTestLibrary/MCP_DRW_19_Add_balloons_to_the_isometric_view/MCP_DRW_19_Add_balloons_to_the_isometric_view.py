"""
MCP_DRW_19_Add_balloons_to_the_isometric_view
=============================================
Group       : Drawings
Script ID   : DRW-19
Description : Add balloons to the isometric view — linked to the parts list
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_19_Add_balloons_to_the_isometric_view

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

    # Find the isometric view (last projected view added in DRW-05)
    iso_view = None
    for i in range(sheet.drawingViews.count):
        v = sheet.drawingViews.item(i)
        if v.drawingViewType == adsk.fusion.DrawingViewTypes.ProjectedDrawingViewType:
            iso_view = v   # take the last projected view (most likely iso)

    if not iso_view:
        print("No projected/iso view found. Run DRW-05 first.")
        return

    # Find the parts list
    parts_list = None
    for i in range(sheet.drawingTableViews.count):
        t = sheet.drawingTableViews.item(i)
        if t.tableViewType == adsk.fusion.DrawingTableViewTypes.PartsListDrawingTableViewType:
            parts_list = t
            break

    print(f"Adding balloons to view: {iso_view.name}")
    print(f"Parts list rows (excl. header): {parts_list.rowCount - 1 if parts_list else 'N/A'}")

    # Balloon positions — spread around the iso view in sheet space (cm)
    vpos = iso_view.position
    balloon_offsets = [
        (-1.5,  1.5),   # item 1 — upper left of view
        ( 1.5,  1.5),   # item 2 — upper right
        ( 1.5, -1.5),   # item 3 — lower right
        (-1.5, -1.5),   # item 4 — lower left
    ]

    for item_num, (dx, dy) in enumerate(balloon_offsets, start=1):
        balloon_pos = adsk.core.Point3D.create(
            vpos.x + dx, vpos.y + dy, 0
        )
        # Leader attachment point — closer to the view centre
        leader_pos = adsk.core.Point3D.create(
            vpos.x + dx * 0.4, vpos.y + dy * 0.4, 0
        )

        balloon_input = sheet.drawingBalloons.createInput(balloon_pos)
        balloon_input.leaderPoints = adsk.core.ObjectCollection.create()
        balloon_input.leaderPoints.add(leader_pos)

        # Link to parts list row (item_num maps to data row index)
        if parts_list and item_num < parts_list.rowCount:
            balloon_input.tableViewRow = parts_list.cell(item_num, 0)

        balloon_input.balloonText = str(item_num)
        balloon = sheet.drawingBalloons.add(balloon_input)
        print(f"  Balloon {item_num}: pos=({balloon_pos.x*10:.0f}, {balloon_pos.y*10:.0f}) mm  text='{item_num}'")

    print(f"\nTotal balloons on sheet: {sheet.drawingBalloons.count}")
