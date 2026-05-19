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

    # TODO(refactor): verify the enum is still DrawingViewTypes in adsk.drawing
    # vs. a renamed type. Probe with `dir(adsk.drawing)` from a live session.
    section_enum = getattr(
        adsk.drawing, "DrawingViewTypes", None
    )
    section_type_val = (
        section_enum.SectionDrawingViewType if section_enum else None
    )

    total = 0

    for s_idx in range(drw.sheets.count):
        sheet = drw.sheets.item(s_idx)
        sheet_sections = []

        for v_idx in range(sheet.drawingViews.count):
            v = sheet.drawingViews.item(v_idx)
            # Prefer enum equality; fall back to isinstance against
            # adsk.drawing.SectionDrawingView if the enum has been removed.
            is_section = False
            if section_type_val is not None and hasattr(v, "drawingViewType"):
                is_section = (v.drawingViewType == section_type_val)
            else:
                section_cls = getattr(adsk.drawing, "SectionDrawingView", None)
                if section_cls is not None:
                    is_section = isinstance(v, section_cls)
            if is_section:
                sheet_sections.append(v)

        if sheet_sections:
            print(f"\n  Sheet: {sheet.name}")
            for sv in sheet_sections:
                total += 1
                print(f"    Section: {sv.name}")
                print(f"      Label      : {sv.sectionLabel if hasattr(sv, 'sectionLabel') else 'N/A'}")
                print(f"      Scale      : {sv.scale:.3f}")
                pos = sv.position
                print(f"      Position   : ({pos.x*10:.1f}, {pos.y*10:.1f}) mm")
                # Parent view (the view the cutting line was drawn on)
                if hasattr(sv, 'parentView') and sv.parentView:
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

        # TODO(refactor): confirm the collection name. Likely candidates in
        # adsk.drawing: `customTables`, `tables`, `partsLists`. Probe with
        # `dir(sheet)` from a live Fusion session.
        tables = getattr(sheet, "customTables", None)
        if tables is None:
            tables = getattr(sheet, "tables", None)

        print(f"\n  Sheet [{s_idx}]: {sheet.name}")
        if tables is None:
            print(f"    (no customTables / tables collection on sheet — probe sheet API)")
        else:
            print(f"    Custom tables (parts lists, etc.): {tables.count}")

            for t_idx in range(tables.count):
                tbl = tables.item(t_idx)
                print(f"      [{t_idx}] {getattr(tbl, 'name', '?')}")
                # CustomTable attribute surface — probe these in a live session.
                # Older API: tableViewType / rowCount / columnCount
                # New API likely: numberOfRows / numberOfColumns or rows / columns
                row_ct = getattr(tbl, "rowCount", None)
                col_ct = getattr(tbl, "columnCount", None)
                if row_ct is None:
                    rows = getattr(tbl, "rows", None)
                    row_ct = rows.count if rows is not None else "?"
                if col_ct is None:
                    cols = getattr(tbl, "columns", None)
                    col_ct = cols.count if cols is not None else "?"
                print(f"        Rows    : {row_ct}")
                print(f"        Columns : {col_ct}")

        # Balloons collection
        # TODO(refactor): drawingBalloons may have been renamed in adsk.drawing.
        balloons = getattr(sheet, "drawingBalloons", None)
        if balloons is None:
            balloons = getattr(sheet, "balloons", None)
        if balloons is not None:
            print(f"    Balloons: {balloons.count}")
            for b_idx in range(balloons.count):
                b = balloons.item(b_idx)
                txt = "?"
                if hasattr(b, "text") and hasattr(b.text, "formattedText"):
                    txt = b.text.formattedText
                print(f"      [{b_idx}] {txt}")
        else:
            print(f"    Balloons: (collection not found — probe sheet API)")

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

    # TODO(refactor): confirm CustomTableInput creation pattern. Likely one of:
    #   sheet.customTables.createInput(refs.item(0))
    #   sheet.customTables.createPartsListInput(refs.item(0))
    #   adsk.drawing.CustomTableInput.create(...)
    # Probe with `dir(sheet.customTables)` from a live session.
    tables = getattr(sheet, "customTables", None)
    if tables is None:
        print("sheet.customTables not found — probe API surface for BOM collection.")
        return

    create_input = (
        getattr(tables, "createPartsListInput", None)
        or getattr(tables, "createInput", None)
    )
    if create_input is None:
        print("No createPartsListInput/createInput on customTables — probe API.")
        return

    tbl_input = create_input(refs.item(0))

    # Position in lower-right corner of sheet.
    # ANSI A sheet = ~27.9 cm wide × 21.6 cm tall; table goes ~bottom-right
    tbl_input.position = adsk.core.Point3D.create(16.0, 2.0, 0)

    # TODO(refactor): confirm add method name. Likely `add` (generic) rather
    # than the old `addPartsList`.
    add_fn = (
        getattr(tables, "addPartsList", None)
        or getattr(tables, "add", None)
    )
    parts_list = add_fn(tbl_input)

    print(f"Parts list created: {getattr(parts_list, 'name', '?')}")

    # Row/column count attribute names may have shifted to `rows`/`columns`
    # collections in adsk.drawing. Try old names, then new.
    row_ct = getattr(parts_list, "rowCount", None)
    if row_ct is None and hasattr(parts_list, "rows"):
        row_ct = parts_list.rows.count
    col_ct = getattr(parts_list, "columnCount", None)
    if col_ct is None and hasattr(parts_list, "columns"):
        col_ct = parts_list.columns.count

    print(f"  Rows    : {row_ct}  (1 header + components)")
    print(f"  Columns : {col_ct}")
    print(f"  Position: lower-right of sheet (standard placement)")
    print()

    # Print the table contents — cell access API may have changed.
    # TODO(refactor): verify cell access. Old: parts_list.cell(row, col)
    # New possibilities: parts_list.rows.item(row).cells.item(col)
    print("  Contents:")
    if hasattr(parts_list, "cell") and isinstance(row_ct, int) and isinstance(col_ct, int):
        for row in range(row_ct):
            row_data = []
            for col in range(col_ct):
                cell = parts_list.cell(row, col)
                row_data.append(cell.text[:20] if cell.text else "")
            print(f"    Row {row}: {' | '.join(row_data)}")
    else:
        print("    (cell access pattern needs probing — see TODO above)")


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

    # TODO(refactor): identifying the BOM among CustomTables — the old
    # tableViewType / PartsListDrawingTableViewType enum is gone. Likely the
    # CustomTable carries a tag / role attribute (e.g. `bomConfiguration`,
    # `isPartsList`, or `tableType`). Probe with `dir(table)`.
    tables = getattr(sheet, "customTables", None)
    if tables is None:
        print("sheet.customTables not found — probe API.")
        return

    parts_list = None
    for i in range(tables.count):
        t = tables.item(i)
        # First-pass heuristic: any table whose attributes mention BOM/parts.
        if (
            getattr(t, "bomConfiguration", None) is not None
            or getattr(t, "isPartsList", False)
        ):
            parts_list = t
            break
    if parts_list is None and tables.count > 0:
        # Fallback: assume first table is the parts list (matches DRW-17 flow).
        parts_list = tables.item(0)

    if not parts_list:
        print("No parts list / CustomTable found. Run DRW-17 first.")
        return

    print(f"Parts list: {getattr(parts_list, 'name', '?')}")

    # TODO(refactor): probe new column/row API.
    #   New API likely: parts_list.columns (collection of CustomTableColumn),
    #                   parts_list.rows    (collection of CustomTableRow).
    #   Each column may expose .name / .header / .width.
    columns = getattr(parts_list, "columns", None)
    col_ct = columns.count if columns is not None else getattr(parts_list, "columnCount", 0)
    print(f"Current columns ({col_ct}):")

    if columns is not None:
        for col_idx in range(columns.count):
            c = columns.item(col_idx)
            header_text = (
                getattr(c, "name", None)
                or getattr(c, "header", None)
                or getattr(c, "headerText", "?")
            )
            print(f"  [{col_idx}] {header_text}")
    else:
        for col in range(col_ct):
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

    # TODO(refactor): the rename API likely lives on the column object:
    #   parts_list.columns.item(i).name = "ITEM"
    # Old code wrote to header-row cell text directly; preserved as fallback.
    if columns is not None:
        for col_idx in range(min(columns.count, len(desired_headers))):
            c = columns.item(col_idx)
            if hasattr(c, "name"):
                c.name = desired_headers[col_idx]
            elif hasattr(c, "header"):
                c.header = desired_headers[col_idx]
    else:
        for col in range(min(col_ct, len(desired_headers))):
            cell = parts_list.cell(0, col)
            cell.text = desired_headers[col]

    print(f"\nHeaders updated to machining drawing standard (ANSI Y14.35).")

    # TODO(refactor): column width API.
    # Old: parts_list.setColumnWidth(col, width_cm)
    # New: parts_list.columns.item(col).width = width_cm   (likely)
    col_widths = [1.0, 1.2, 3.0, 5.0, 3.0, 2.5]
    if columns is not None:
        for col_idx in range(min(columns.count, len(col_widths))):
            c = columns.item(col_idx)
            if hasattr(c, "width"):
                c.width = col_widths[col_idx]
    elif hasattr(parts_list, "setColumnWidth"):
        for col in range(min(col_ct, len(col_widths))):
            parts_list.setColumnWidth(col, col_widths[col])

    print("Column widths adjusted (where supported by API).")


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

    sheet = drw.sheets.item(0)

    # TODO(refactor): verify DrawingViewTypes still exposed under adsk.drawing.
    view_types = getattr(adsk.drawing, "DrawingViewTypes", None)
    projected_val = (
        view_types.ProjectedDrawingViewType if view_types else None
    )

    # Find the isometric view (last projected view added in DRW-05)
    iso_view = None
    for i in range(sheet.drawingViews.count):
        v = sheet.drawingViews.item(i)
        is_projected = False
        if projected_val is not None and hasattr(v, "drawingViewType"):
            is_projected = (v.drawingViewType == projected_val)
        else:
            proj_cls = getattr(adsk.drawing, "ProjectedDrawingView", None)
            if proj_cls is not None:
                is_projected = isinstance(v, proj_cls)
        if is_projected:
            iso_view = v   # take the last projected view (most likely iso)

    if not iso_view:
        print("No projected/iso view found. Run DRW-05 first.")
        return

    # Find the parts list among CustomTables.
    # TODO(refactor): identify the BOM table without the old tableViewType
    # enum — see DRW-18 TODO. Heuristic: pick first CustomTable.
    tables = getattr(sheet, "customTables", None)
    parts_list = tables.item(0) if (tables is not None and tables.count > 0) else None

    pl_rows = None
    if parts_list is not None:
        pl_rows = (
            getattr(parts_list, "rowCount", None)
            or (parts_list.rows.count if hasattr(parts_list, "rows") else None)
        )

    print(f"Adding balloons to view: {iso_view.name}")
    print(f"Parts list rows (excl. header): {pl_rows - 1 if pl_rows else 'N/A'}")

    # Balloon positions — spread around the iso view in sheet space (cm)
    vpos = iso_view.position
    balloon_offsets = [
        (-1.5,  1.5),   # item 1 — upper left of view
        ( 1.5,  1.5),   # item 2 — upper right
        ( 1.5, -1.5),   # item 3 — lower right
        (-1.5, -1.5),   # item 4 — lower left
    ]

    # TODO(refactor): confirm balloons collection name on the sheet.
    # Likely candidates: `drawingBalloons`, `balloons`.
    balloons_coll = (
        getattr(sheet, "drawingBalloons", None)
        or getattr(sheet, "balloons", None)
    )
    if balloons_coll is None:
        print("Balloons collection not found on sheet — probe API.")
        return

    for item_num, (dx, dy) in enumerate(balloon_offsets, start=1):
        balloon_pos = adsk.core.Point3D.create(
            vpos.x + dx, vpos.y + dy, 0
        )
        # Leader attachment point — closer to the view centre
        leader_pos = adsk.core.Point3D.create(
            vpos.x + dx * 0.4, vpos.y + dy * 0.4, 0
        )

        balloon_input = balloons_coll.createInput(balloon_pos)
        balloon_input.leaderPoints = adsk.core.ObjectCollection.create()
        balloon_input.leaderPoints.add(leader_pos)

        # Link to parts list row (item_num maps to data row index).
        # TODO(refactor): attribute may have been renamed from tableViewRow
        # to customTableRow now that the table type is CustomTable.
        if parts_list and isinstance(pl_rows, int) and item_num < pl_rows:
            row_ref = None
            if hasattr(parts_list, "cell"):
                row_ref = parts_list.cell(item_num, 0)
            elif hasattr(parts_list, "rows"):
                row_ref = parts_list.rows.item(item_num)
            if row_ref is not None:
                if hasattr(balloon_input, "customTableRow"):
                    balloon_input.customTableRow = row_ref
                elif hasattr(balloon_input, "tableViewRow"):
                    balloon_input.tableViewRow = row_ref

        balloon_input.balloonText = str(item_num)
        balloons_coll.add(balloon_input)
        print(f"  Balloon {item_num}: pos=({balloon_pos.x*10:.0f}, {balloon_pos.y*10:.0f}) mm  text='{item_num}'")

    print(f"\nTotal balloons on sheet: {balloons_coll.count}")


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

    # TODO(refactor): in adsk.drawing, leader notes may live on a separate
    # collection from plain notes — e.g. sheet.leaderNotes vs sheet.drawingNotes.
    # If a dedicated LeaderNote class exists, prefer that path.
    notes_coll = (
        getattr(sheet, "leaderNotes", None)
        or getattr(sheet, "drawingNotes", None)
        or getattr(sheet, "notes", None)
    )
    if notes_coll is None:
        print("Notes collection not found on sheet — probe API.")
        return

    for (nx, ny), (lx, ly), text in callouts:
        note_input = notes_coll.createInput(
            adsk.core.Point3D.create(nx, ny, 0)
        )
        note_input.text = text
        # TODO(refactor): isLeader flag may no longer exist if leader notes
        # are a distinct collection. Only set if the attribute is present.
        if hasattr(note_input, "isLeader"):
            note_input.isLeader = True
        if hasattr(note_input, "leaderPoints"):
            note_input.leaderPoints = adsk.core.ObjectCollection.create()
            note_input.leaderPoints.add(adsk.core.Point3D.create(lx, ly, 0))

        notes_coll.add(note_input)
        first_line = text.split('\n')[0]
        print(f"Leader note added: '{first_line}...'  at ({nx*10:.0f}, {ny*10:.0f}) mm")

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

    # TODO(refactor): probe `adsk.drawing` to confirm DrawingViewTypes still
    # carries the same four enum members (Base/Projected/Section/Detail).
    view_types = getattr(adsk.drawing, "DrawingViewTypes", None)
    VT_BASE      = getattr(view_types, "BaseDrawingViewType",      None) if view_types else None
    VT_SECTION   = getattr(view_types, "SectionDrawingViewType",   None) if view_types else None
    VT_PROJECTED = getattr(view_types, "ProjectedDrawingViewType", None) if view_types else None
    VT_DETAIL    = getattr(view_types, "DetailDrawingViewType",    None) if view_types else None

    grand_total = {
        "sheets":      drw.sheets.count,
        "views":       0,
        "sections":    0,
        "dims":        0,
        "notes":       0,
        "balloons":    0,
        "parts_lists": 0,
    }

    for s_idx in range(drw.sheets.count):
        sheet = drw.sheets.item(s_idx)
        print(f"  ── Sheet [{s_idx}]: {sheet.name} ({sheet.paperSize}) ──")

        # Views breakdown
        base_ct = section_ct = proj_ct = detail_ct = 0
        for i in range(sheet.drawingViews.count):
            vt = getattr(sheet.drawingViews.item(i), "drawingViewType", None)
            if   VT_BASE      is not None and vt == VT_BASE:      base_ct    += 1
            elif VT_SECTION   is not None and vt == VT_SECTION:   section_ct += 1
            elif VT_PROJECTED is not None and vt == VT_PROJECTED: proj_ct    += 1
            elif VT_DETAIL    is not None and vt == VT_DETAIL:    detail_ct  += 1

        total_views = sheet.drawingViews.count
        grand_total["views"]    += total_views
        grand_total["sections"] += section_ct

        print(f"    Views      : {total_views} total  "
              f"(base={base_ct}, projected={proj_ct}, "
              f"section={section_ct}, detail={detail_ct})")

        # Dimensions — collection name may still be drawingDimensions.
        dims_coll = getattr(sheet, "drawingDimensions", None) or getattr(sheet, "dimensions", None)
        dim_ct = dims_coll.count if dims_coll is not None else 0
        grand_total["dims"] += dim_ct
        print(f"    Dimensions : {dim_ct}")

        # Notes / leaders
        notes_coll = (
            getattr(sheet, "drawingNotes", None)
            or getattr(sheet, "notes", None)
            or getattr(sheet, "leaderNotes", None)
        )
        note_ct = notes_coll.count if notes_coll is not None else 0
        grand_total["notes"] += note_ct
        print(f"    Notes      : {note_ct}")

        # Balloons
        balloons_coll = (
            getattr(sheet, "drawingBalloons", None)
            or getattr(sheet, "balloons", None)
        )
        balloon_ct = balloons_coll.count if balloons_coll is not None else 0
        grand_total["balloons"] += balloon_ct
        print(f"    Balloons   : {balloon_ct}")

        # Parts lists — now adsk.drawing.CustomTable on sheet.customTables.
        # TODO(refactor): no more PartsListDrawingTableViewType enum; need a
        # different way to distinguish a parts-list CustomTable from a plain
        # CustomTable. Counting all customTables for now.
        tables_coll = getattr(sheet, "customTables", None) or getattr(sheet, "tables", None)
        pl_ct = 0
        if tables_coll is not None:
            for t_idx in range(tables_coll.count):
                t = tables_coll.item(t_idx)
                row_ct = (
                    getattr(t, "rowCount", None)
                    or (t.rows.count if hasattr(t, "rows") else "?")
                )
                col_ct = (
                    getattr(t, "columnCount", None)
                    or (t.columns.count if hasattr(t, "columns") else "?")
                )
                pl_ct += 1
                print(f"    Parts list : '{getattr(t, 'name', '?')}'  "
                      f"{row_ct} rows × {col_ct} cols")
        if pl_ct == 0:
            print(f"    Parts list : ✗ MISSING — run DRW-17")
        grand_total["parts_lists"] += pl_ct

        # Section view labels present?
        section_labels = []
        for i in range(sheet.drawingViews.count):
            v = sheet.drawingViews.item(i)
            vt = getattr(v, "drawingViewType", None)
            if VT_SECTION is not None and vt == VT_SECTION and hasattr(v, "sectionLabel"):
                section_labels.append(v.sectionLabel)
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
