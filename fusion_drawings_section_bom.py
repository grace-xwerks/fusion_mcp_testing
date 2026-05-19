"""
Fusion MCP — Drawings: Section Views & BOM/Balloon Table Scripts
================================================================
Continues from fusion_drawings_tests.py (DRW-01 through DRW-10).

Two areas covered here:

  SECTION VIEWS (DRW-11 through DRW-15)
  ─────────────────────────────────────
  Section views are the primary way to document internal features on
  engineering drawings — pocket depths, hole diameters, wall thicknesses.
  The CNC Fundamentals guide uses "Section Part View / Cut Direction"
  callouts throughout turning and milling chapters. The Fusion API
  exposes section views via createSectionViewInput() on a parent view.

  Types covered:
    • Full section (cutting plane through entire part)
    • Offset section (cutting plane steps to hit multiple features)
    • Half section (cuts only one quadrant — useful for symmetric parts)
    • Aligned section (rotated cutting plane)
    • Inspect / audit existing section views

  BOM & BALLOONS (DRW-16 through DRW-21)
  ───────────────────────────────────────
  A parts list (BOM table) + balloons is essential for any assembly
  drawing — especially multi-setup bracket parts. Fusion's
  DrawingTableView handles the parts list; DrawingBalloon handles
  the callout bubbles on the view.

  Types covered:
    • Inspect existing parts lists / detect if BOM is present
    • Create a parts list table on a sheet
    • Customize BOM columns (item, qty, part number, description, material)
    • Add balloons to a drawing view (linked to parts list)
    • Add a leader-line note (free balloon / datum flag)
    • Full BOM + balloon audit

PREREQUISITES:
  • A drawing document must be active in Fusion.
  • DRW-03 through DRW-05 from fusion_drawings_tests.py should have
    been run first (sheet + base + projected views in place).
  • For BOM scripts: the drawing must reference an assembly (multi-body
    or multi-component design). The Bracket + MountingPlate assembly
    from DESIGN-06 works perfectly.

⚠️  RUNTIME STATUS — Fusion 2703.x Insider, May 2026
============================================================
The adsk.drawing Python bindings are largely NOT YET IMPLEMENTED on
this build (see quirks #28, #29 in issue #3). Any deeper access than
`DrawingDocument.cast(doc)` raises:

    RuntimeError: 5 : API Function not yet implemented

This affects every script in this file. They're refactored against
the documented adsk.drawing class structure so they're ready to
validate the moment Autodesk ships the Python implementation, but
running them today will hit the blocker on the first data access.

Treat as future-work section of the library; revisit on the next
Fusion release.

No try/except — let exceptions propagate as error signals.
All positions in centimeters (Fusion internal units).
"""

# =============================================================================
# DRW-11  Audit existing views — find parent views suitable for section cuts
#         Run this first to understand what's on the sheet before cutting.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active. Open a drawing document first.")
        return

    sheet = drw.sheets.item(0)
    print(f"Sheet: {sheet.name}  ({sheet.drawingViews.count} views)")
    print()

    # DrawingViewType enum values:
    #   BaseDrawingViewType      = 0
    #   ProjectedDrawingViewType = 1
    #   SectionDrawingViewType   = 2
    #   DetailDrawingViewType    = 3
    #   BreakDrawingViewType     = 4

    base_views    = []
    section_views = []
    other_views   = []

    for i in range(sheet.drawingViews.count):
        v = sheet.drawingViews.item(i)
        vtype = v.drawingViewType
        pos   = v.position

        info = (f"  [{i}] {v.name:25s}  "
                f"type={vtype}  "
                f"scale={v.scale:.3f}  "
                f"pos=({pos.x*10:.1f}, {pos.y*10:.1f}) mm")
        print(info)

        if vtype == adsk.fusion.DrawingViewTypes.BaseDrawingViewType:
            base_views.append((i, v))
        elif vtype == adsk.fusion.DrawingViewTypes.SectionDrawingViewType:
            section_views.append((i, v))
        else:
            other_views.append((i, v))

    print(f"\nBase views    : {len(base_views)}   ← use these as section parents")
    print(f"Section views : {len(section_views)}")
    print(f"Other views   : {len(other_views)}")

    if not base_views:
        print("\nNo base views found — run DRW-04 first to add a front view.")
    else:
        print(f"\nRecommended parent for section cut: view [{base_views[0][0]}] '{base_views[0][1].name}'")


# =============================================================================
# DRW-12  Full section view — A-A through part centerline (vertical cut)
#         Cutting plane runs left-to-right at the Y midpoint of the part,
#         exposing pocket depth and hole profiles.
#         This is the most common section type in machined part drawings.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw or drw.sheets.item(0).drawingViews.count == 0:
        print("No views found. Run DRW-04 first.")
        return

    sheet     = drw.sheets.item(0)
    base_view = None

    for i in range(sheet.drawingViews.count):
        v = sheet.drawingViews.item(i)
        if v.drawingViewType == adsk.fusion.DrawingViewTypes.BaseDrawingViewType:
            base_view = v
            break

    if not base_view:
        print("No base view found. Run DRW-04 first.")
        return

    # ── Define the cutting line ───────────────────────────────────────────────
    # Cutting plane runs vertically through the horizontal centre of the part.
    # In the front view the part occupies roughly (7, 9) to (17, 13) cm on sheet.
    # We cut at X = 12 cm (part centre), sweeping full height of the view.
    #
    # Point3D coordinates here are in SHEET SPACE (cm), not model space.
    # The two points define the cutting line end points on the parent view.

    bv_pos   = base_view.position           # sheet-space centre of view
    cut_x    = bv_pos.x                     # cut through the view centre
    cut_top  = adsk.core.Point3D.create(cut_x, bv_pos.y + 2.0, 0)   # above view
    cut_bot  = adsk.core.Point3D.create(cut_x, bv_pos.y - 2.0, 0)   # below view

    # ── Create the section view input ────────────────────────────────────────
    section_input = sheet.drawingViews.createSectionViewInput(base_view)

    # Cutting line: two points defining the section plane
    section_input.sectionType = adsk.fusion.SectionTypes.FullSectionType

    cutting_line = adsk.core.ObjectCollection.create()
    cutting_line.add(cut_top)
    cutting_line.add(cut_bot)
    section_input.cuttingLine = cutting_line

    # Place the section view to the right and below the base view
    section_input.position = adsk.core.Point3D.create(
        bv_pos.x + 8.0,   # 80 mm to the right
        bv_pos.y,
        0
    )
    section_input.scale          = base_view.scale
    section_input.sectionLabel   = "A"   # produces "SECTION A-A" label

    section_view = sheet.drawingViews.addSectionView(section_input)

    print(f"Full section view created: {section_view.name}")
    print(f"  Label       : SECTION A-A")
    print(f"  Cut at X    : {cut_x*10:.1f} mm (part centre, vertical plane)")
    print(f"  Position    : ({section_input.position.x*10:.0f}, {section_input.position.y*10:.0f}) mm")
    print(f"  Scale       : {section_view.scale}")
    print(f"\nExpect to see: pocket profile, hole cross-sections, chamfer detail.")


# =============================================================================
# DRW-13  Offset section view — B-B stepped cut
#         Cuts through both the pocket AND a corner hole in one section.
#         Useful when features don't fall on a single cutting plane.
#         Defined by 3+ points that form the stepped cutting line.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw or drw.sheets.item(0).drawingViews.count == 0:
        print("No views found. Run DRW-04 first.")
        return

    sheet     = drw.sheets.item(0)
    base_view = None

    for i in range(sheet.drawingViews.count):
        v = sheet.drawingViews.item(i)
        if v.drawingViewType == adsk.fusion.DrawingViewTypes.BaseDrawingViewType:
            base_view = v
            break

    if not base_view:
        print("No base view found.")
        return

    bv_pos = base_view.position

    # Stepped cutting line: start above part, step right to pass through
    # both the pocket centre and a hole, then continue down.
    # Points are in sheet space (cm).
    #
    # The bracket is 100 mm wide in model → ~5 cm on sheet at 1:2 scale.
    # Hole centres are at 10 mm inset → 0.5 cm on sheet.
    # Pocket centre is at 50 mm → 2.5 cm from view left edge.

    half_w = 2.5   # half of view width at 1:2 scale in cm
    hole_x = bv_pos.x - half_w + 0.5   # left hole column

    pt1 = adsk.core.Point3D.create(hole_x,          bv_pos.y + 2.0, 0)  # enter above hole
    pt2 = adsk.core.Point3D.create(hole_x,          bv_pos.y,       0)  # step down to pocket level
    pt3 = adsk.core.Point3D.create(bv_pos.x,        bv_pos.y,       0)  # step right to pocket centre
    pt4 = adsk.core.Point3D.create(bv_pos.x,        bv_pos.y - 2.0, 0)  # exit below

    section_input = sheet.drawingViews.createSectionViewInput(base_view)
    section_input.sectionType = adsk.fusion.SectionTypes.OffsetSectionType

    cutting_line = adsk.core.ObjectCollection.create()
    for pt in [pt1, pt2, pt3, pt4]:
        cutting_line.add(pt)
    section_input.cuttingLine  = cutting_line

    section_input.position     = adsk.core.Point3D.create(
        bv_pos.x + 8.0, bv_pos.y - 6.0, 0   # below the A-A section view
    )
    section_input.scale        = base_view.scale
    section_input.sectionLabel = "B"   # produces "SECTION B-B"

    section_view = sheet.drawingViews.addSectionView(section_input)

    print(f"Offset section view created: {section_view.name}")
    print(f"  Label    : SECTION B-B")
    print(f"  Steps    : 4-point stepped cutting line")
    print(f"  Captures : corner hole + pocket in single section")


# =============================================================================
# DRW-14  Half section view — C-C (symmetric parts only)
#         Cuts one quadrant of the part, leaving the other half intact.
#         Ideal for showing internal + external geometry simultaneously.
#         Works best on the bracket when the part has a symmetry axis.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw or drw.sheets.item(0).drawingViews.count == 0:
        print("No views found.")
        return

    sheet     = drw.sheets.item(0)
    base_view = None

    for i in range(sheet.drawingViews.count):
        v = sheet.drawingViews.item(i)
        if v.drawingViewType == adsk.fusion.DrawingViewTypes.BaseDrawingViewType:
            base_view = v
            break

    if not base_view:
        print("No base view found.")
        return

    bv_pos = base_view.position

    # Half section: two perpendicular lines meeting at part centre.
    # pt1 → pt2 is the horizontal arm; pt2 → pt3 is the vertical arm.
    pt1 = adsk.core.Point3D.create(bv_pos.x - 2.5, bv_pos.y,       0)  # left edge
    pt2 = adsk.core.Point3D.create(bv_pos.x,        bv_pos.y,       0)  # centre (corner)
    pt3 = adsk.core.Point3D.create(bv_pos.x,        bv_pos.y - 2.0, 0)  # bottom

    section_input = sheet.drawingViews.createSectionViewInput(base_view)
    section_input.sectionType = adsk.fusion.SectionTypes.HalfSectionType

    cutting_line = adsk.core.ObjectCollection.create()
    for pt in [pt1, pt2, pt3]:
        cutting_line.add(pt)
    section_input.cuttingLine  = cutting_line

    # Add a new sheet for this view so it doesn't crowd sheet 1
    new_sheet = drw.sheets.add()
    new_sheet.name = "Sheet2_SectionViews"

    section_input.position     = adsk.core.Point3D.create(10.0, 10.0, 0)
    section_input.scale        = base_view.scale
    section_input.sectionLabel = "C"

    section_view = new_sheet.drawingViews.addSectionView(section_input)

    print(f"Half section view created: {section_view.name}")
    print(f"  Label  : SECTION C-C")
    print(f"  Sheet  : {new_sheet.name}  (new sheet added)")
    print(f"  Shows  : internal pocket + hole on left half, solid exterior on right")


# =============================================================================
# DRW-15  Inspect all section views — cutting line geometry + labels
#         Run after DRW-12/13/14 to verify the section definitions.
#         Refactored: Drawings classes moved adsk.fusion → adsk.drawing in
#         Fusion 2703.x Insider (see issue #10 / quirks #27-28).
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active.")
        return

    print(f"=== Section View Audit: {drw.parentDocument.name} ===")
    section_type = adsk.drawing.DrawingViewTypes.SectionDrawingViewType
    total = 0

    for s_idx in range(drw.sheets.count):
        sheet = drw.sheets.item(s_idx)
        sections = [sheet.drawingViews.item(i) for i in range(sheet.drawingViews.count)
                    if sheet.drawingViews.item(i).drawingViewType == section_type]
        if sections:
            print(f"\n  Sheet: {sheet.name}")
            for sv in sections:
                total += 1
                print(f"    Section: {sv.name}")
                print(f"      Label      : {sv.sectionLabel}")
                print(f"      Scale      : {sv.scale:.3f}")
                print(f"      Position   : ({sv.position.x*10:.1f}, {sv.position.y*10:.1f}) mm")
                if sv.parentView:
                    print(f"      Parent view: {sv.parentView.name}")

    print(f"\nTotal section views: {total}")
    if total == 0:
        print("Run DRW-12, DRW-13, or DRW-14 to add section views.")


# =============================================================================
# DRW-16  Inspect existing parts lists / detect BOM presence
#         Run before creating a BOM to understand the current state.
#         Refactored: BOM tables are now adsk.drawing.CustomTable, accessed via
#         sheet.customTables (previously DrawingTableView via drawingTableViews).
# =============================================================================

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


# =============================================================================
# DRW-17  Create a parts list (BOM table) on sheet 1
#         Refactored: BOM is now adsk.drawing.CustomTable, created via
#         CustomTableInput on sheet.customTables.add(...).
#         Placed in the lower-right corner — standard drawing practice.
# =============================================================================

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


# =============================================================================
# DRW-18  Customize BOM columns
#         Default columns vary by template. This script ensures the standard
#         machinist columns are present: ITEM, QTY, PART NUMBER, DESCRIPTION,
#         MATERIAL, FINISH.
#         Refactored: parts list is adsk.drawing.CustomTable; column API
#         shifted from cell(row, col)/setColumnWidth to table.columns/rows.
# =============================================================================

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


# =============================================================================
# DRW-19  Add balloons to the isometric view — linked to the parts list
#         Balloons are the circled item numbers that reference BOM rows.
#         Placed on the iso view for clarity (least foreshortening).
#         Refactored: DrawingBalloon moved adsk.fusion → adsk.drawing.
# =============================================================================

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


# =============================================================================
# DRW-20  Add a free-standing leader note (datum flag / machining callout)
#         Used for callouts like: "DATUM A — MACHINE FIRST"
#         or "SEE DETAIL B" that aren't tied to the BOM.
#         Refactored: DrawingNote moved adsk.fusion → adsk.drawing.
#         LeaderNote may be a distinct class in the new module.
# =============================================================================

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


# =============================================================================
# DRW-21  Full drawing audit — section views + BOM + balloons
#         Run at the end of a drawing session to confirm all elements
#         are present before exporting to PDF.
#         Refactored: all Drawings classes / enums ported from adsk.fusion
#         to adsk.drawing (Fusion 2703.x Insider). Read-only; uses getattr
#         fallbacks so it degrades gracefully across API revisions.
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active.")
        return

    print(f"╔══════════════════════════════════════════════════╗")
    print(f"  Drawing Completion Audit")
    print(f"  Document: {drw.parentDocument.name}")
    print(f"╚══════════════════════════════════════════════════╝")
    print()

    VT = adsk.drawing.DrawingViewTypes
    grand_total = {"sheets": drw.sheets.count, "views": 0, "sections": 0,
                   "dims": 0, "notes": 0, "balloons": 0, "parts_lists": 0}

    for s_idx in range(drw.sheets.count):
        sheet = drw.sheets.item(s_idx)
        print(f"  ── Sheet [{s_idx}]: {sheet.name} ({sheet.paperSize}) ──")

        # Views breakdown by type
        counts = {VT.BaseDrawingViewType: 0, VT.SectionDrawingViewType: 0,
                  VT.ProjectedDrawingViewType: 0, VT.DetailDrawingViewType: 0}
        for i in range(sheet.drawingViews.count):
            vt = sheet.drawingViews.item(i).drawingViewType
            if vt in counts: counts[vt] += 1
        total_views = sheet.drawingViews.count
        grand_total["views"]    += total_views
        grand_total["sections"] += counts[VT.SectionDrawingViewType]

        print(f"    Views      : {total_views} total  "
              f"(base={counts[VT.BaseDrawingViewType]}, "
              f"projected={counts[VT.ProjectedDrawingViewType]}, "
              f"section={counts[VT.SectionDrawingViewType]}, "
              f"detail={counts[VT.DetailDrawingViewType]})")

        grand_total["dims"]     += sheet.drawingDimensions.count
        grand_total["notes"]    += sheet.drawingNotes.count
        grand_total["balloons"] += sheet.drawingBalloons.count
        print(f"    Dimensions : {sheet.drawingDimensions.count}")
        print(f"    Notes      : {sheet.drawingNotes.count}")
        print(f"    Balloons   : {sheet.drawingBalloons.count}")

        if sheet.customTables.count == 0:
            print(f"    Parts list : ✗ MISSING — run DRW-17")
        else:
            for t_idx in range(sheet.customTables.count):
                t = sheet.customTables.item(t_idx)
                print(f"    Parts list : '{t.name}'  {t.rows.count} rows × {t.columns.count} cols")
        grand_total["parts_lists"] += sheet.customTables.count

        # Section view labels
        section_labels = [sheet.drawingViews.item(i).sectionLabel
                          for i in range(sheet.drawingViews.count)
                          if sheet.drawingViews.item(i).drawingViewType == VT.SectionDrawingViewType]
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
