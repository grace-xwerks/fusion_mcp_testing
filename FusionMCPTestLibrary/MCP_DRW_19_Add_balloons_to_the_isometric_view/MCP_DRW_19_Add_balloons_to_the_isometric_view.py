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

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active.")
        return

    sheet           = drw.sheets.item(0)
    projected_type  = adsk.drawing.DrawingViewTypes.ProjectedDrawingViewType

    # Find the last projected view added in DRW-05 (typically the iso).
    iso_view = None
    for i in range(sheet.drawingViews.count):
        v = sheet.drawingViews.item(i)
        if v.drawingViewType == projected_type:
            iso_view = v
    if not iso_view:
        print("No projected/iso view found. Run DRW-05 first.")
        return

    if sheet.customTables.count == 0:
        print("No parts list / CustomTable found. Run DRW-17 first.")
        return
    parts_list = sheet.customTables.item(0)
    pl_rows    = parts_list.rows.count

    print(f"Adding balloons to view: {iso_view.name}")
    print(f"Parts list data rows (excl. header): {pl_rows - 1}")

    # Balloon positions — spread around the iso view in sheet space (cm)
    vpos = iso_view.position
    balloon_offsets = [(-1.5, 1.5), (1.5, 1.5), (1.5, -1.5), (-1.5, -1.5)]

    for item_num, (dx, dy) in enumerate(balloon_offsets, start=1):
        balloon_pos = adsk.core.Point3D.create(vpos.x + dx,       vpos.y + dy,       0)
        leader_pos  = adsk.core.Point3D.create(vpos.x + dx * 0.4, vpos.y + dy * 0.4, 0)

        balloon_input = sheet.drawingBalloons.createInput(balloon_pos)
        balloon_input.leaderPoints = adsk.core.ObjectCollection.create()
        balloon_input.leaderPoints.add(leader_pos)
        if item_num < pl_rows:
            balloon_input.customTableRow = parts_list.rows.item(item_num)
        balloon_input.balloonText = str(item_num)
        sheet.drawingBalloons.add(balloon_input)
        print(f"  Balloon {item_num}: pos=({balloon_pos.x*10:.0f}, {balloon_pos.y*10:.0f}) mm")

    print(f"\nTotal balloons on sheet: {sheet.drawingBalloons.count}")
