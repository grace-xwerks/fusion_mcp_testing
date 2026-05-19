"""
Fusion MCP — Drawings Workspace Test Scripts
============================================
Tests the Fusion Drawings product type: creating drawing documents,
adding sheets, placing views (base, projected, section, detail),
adding dimensions and annotations, and exporting to PDF/DXF.

PREREQUISITE: The Bracket part from Design scripts should be open.
Fusion Drawings work on a separate DrawingDocument that references
the Design document.

adsk.fusion namespace covers Drawings (no separate adsk.drawing module).
Key classes: Drawing, DrawingSheet, DrawingView, DrawingDimension,
             DrawingNote, DrawingBalloon, DrawingTableView
"""

# =============================================================================
# DRW-01  Check if a drawing document is currently active
#         If not, prints how to create one.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    docs = app.documents

    print(f"Open documents ({docs.count}):")
    drawing_docs = []
    design_docs  = []

    for i in range(docs.count):
        doc = docs.item(i)
        ptype = doc.products.item(0).productType if doc.products.count > 0 else "unknown"
        print(f"  [{i}] {doc.name:40s}  type={ptype}")
        if "Drawing" in ptype:
            drawing_docs.append(doc)
        if "DesignProductType" in ptype:
            design_docs.append(doc)

    print(f"\nDesign docs  : {len(design_docs)}")
    print(f"Drawing docs : {len(drawing_docs)}")

    prod = app.activeProduct
    print(f"\nActive product: {prod.productType}")

    if "Drawing" not in prod.productType:
        print("\nNot in a Drawing document.")
        print("To create one: File > New Drawing > From Design")
        print("Then run DRW-02 to inspect it via MCP.")
    else:
        drw = adsk.fusion.Drawing.cast(prod)
        print(f"Drawing sheets: {drw.sheets.count}")


# =============================================================================
# DRW-02  Inspect an active Drawing document
#         Run after opening a drawing in Fusion.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active. Open or create a drawing document first.")
        return

    print(f"=== Drawing Inventory ===")
    print(f"Document : {drw.parentDocument.name}")
    print(f"Sheets   : {drw.sheets.count}")

    for s_idx in range(drw.sheets.count):
        sheet = drw.sheets.item(s_idx)
        print(f"\n  Sheet [{s_idx}]: {sheet.name}")
        print(f"    Size   : {sheet.paperSize}")
        print(f"    Views  : {sheet.drawingViews.count}")

        for v_idx in range(sheet.drawingViews.count):
            view = sheet.drawingViews.item(v_idx)
            print(f"      View [{v_idx}]: {view.name:25s}  "
                  f"type={view.drawingViewType}  "
                  f"scale=1:{int(1/view.scale) if view.scale < 1 else int(view.scale)}")

            # Dimensions within this view
            dims = view.drawingDimensions
            print(f"        Dimensions: {dims.count}")
            for d_idx in range(min(dims.count, 5)):
                d = dims.item(d_idx)
                print(f"          [{d_idx}] {d.drawingDimensionType}  "
                      f"value={d.text.formattedText if hasattr(d.text, 'formattedText') else '?'}")


# =============================================================================
# DRW-03  Create a new drawing document from the active Design
#         Programmatically creates drawing + A-size sheet.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()

    # Find the active design document
    design_doc = None
    for i in range(app.documents.count):
        doc = app.documents.item(i)
        if doc.products.count > 0:
            prod = doc.products.item(0)
            if prod.productType == "DesignProductType":
                design_doc = doc
                break

    if not design_doc:
        print("No design document found. Open the Bracket part first.")
        return

    # Create a new drawing document
    drawing_doc = app.documents.add(
        adsk.core.DocumentTypes.DrawingDocumentType,
        app.data.activeProject,  # active project in hub
        True                     # open the document
    )

    print(f"Drawing document created: {drawing_doc.name}")

    drw = adsk.fusion.Drawing.cast(drawing_doc.products.item(0))
    print(f"Drawing product cast OK")
    print(f"Default sheets: {drw.sheets.count}")

    # Rename first sheet
    if drw.sheets.count > 0:
        sheet = drw.sheets.item(0)
        sheet.name = "Sheet1_Front_Side"
        print(f"Sheet renamed: {sheet.name}  size={sheet.paperSize}")


# =============================================================================
# DRW-04  Add a base view (front view) to the active drawing sheet
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active. Run DRW-03 or open a drawing first.")
        return

    sheet = drw.sheets.item(0)

    # Find the linked design's root component
    # The drawing has a reference to the source design
    refs = drw.referencedDocuments
    print(f"Referenced documents: {refs.count}")

    # Add base view input
    view_input = sheet.drawingViews.createBaseViewInput()
    view_input.referencedDocument = refs.item(0) if refs.count > 0 else None

    # Position: center of A-size sheet (in mm)
    # A-size (ANSI A) = 215.9 x 279.4 mm — place front view at ~1/3 from left
    view_input.position = adsk.core.Point3D.create(7.0, 10.0, 0)   # cm
    view_input.scale    = 0.5    # 1:2 scale — part is 100mm, sheet is ~280mm
    view_input.viewOrientation = adsk.fusion.DrawingViewOrientations.FrontViewOrientation
    view_input.viewStyle = adsk.fusion.DrawingViewStyles.VisibleAndHiddenEdgesViewStyle

    base_view = sheet.drawingViews.addBaseView(view_input)
    print(f"Base view added: {base_view.name}")
    print(f"  Orientation : Front")
    print(f"  Scale       : 1:2")
    print(f"  Position    : (70, 100) mm")


# =============================================================================
# DRW-05  Add projected views (top, right, isometric)
#         Depends on DRW-04 base view being present.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw or drw.sheets.count == 0:
        print("No drawing or sheet found.")
        return

    sheet = drw.sheets.item(0)

    if sheet.drawingViews.count == 0:
        print("No base view found. Run DRW-04 first.")
        return

    base_view = sheet.drawingViews.item(0)

    # Top view — above the base view
    top_input          = sheet.drawingViews.createProjectedViewInput(base_view)
    top_input.position = adsk.core.Point3D.create(7.0, 17.0, 0)  # above
    top_view           = sheet.drawingViews.addProjectedView(top_input)
    print(f"Top view added: {top_view.name}")

    # Right view — to the right of base view
    right_input          = sheet.drawingViews.createProjectedViewInput(base_view)
    right_input.position = adsk.core.Point3D.create(14.0, 10.0, 0)  # right
    right_view           = sheet.drawingViews.addProjectedView(right_input)
    print(f"Right view added: {right_view.name}")

    # Isometric view — upper right
    iso_input                = sheet.drawingViews.createProjectedViewInput(base_view)
    iso_input.position       = adsk.core.Point3D.create(20.0, 17.0, 0)
    iso_input.viewOrientation = adsk.fusion.DrawingViewOrientations.HomeViewOrientation
    iso_view                 = sheet.drawingViews.addProjectedView(iso_input)
    print(f"Iso view added: {iso_view.name}")

    print(f"\nTotal views on sheet: {sheet.drawingViews.count}")


# =============================================================================
# DRW-06  Add linear dimensions to the front view
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw or drw.sheets.count == 0:
        print("No drawing found.")
        return

    sheet     = drw.sheets.item(0)
    base_view = sheet.drawingViews.item(0)

    print(f"Base view: {base_view.name}")
    print(f"Visible edges in view: {base_view.curves.count}")

    # Auto-detect the two leftmost and rightmost points to drive a width dim
    # In practice you'd select specific edges by their 3D geometry match;
    # here we demonstrate the API pattern with the bounding geometry.
    curves = base_view.curves
    if curves.count < 2:
        print("Not enough curves in view to dimension. Ensure DRW-04 ran correctly.")
        return

    # Add a linear dimension between first two visible edges
    dim_input = sheet.drawingDimensions.createLinearDimensionInput(
        curves.item(0),   # first edge
        curves.item(1),   # second edge (Fusion picks nearest parallel pair)
        adsk.core.Point3D.create(7.0, 7.5, 0),   # dimension line position
        adsk.fusion.DrawingLinearDimensionOrientations.HorizontalLinearDimension
    )
    dim = sheet.drawingDimensions.addLinearDimension(dim_input)
    print(f"Linear dimension added: {dim.text.formattedText if hasattr(dim, 'text') else 'OK'}")


# =============================================================================
# DRW-07  Add a drawing note (title block / general tolerance note)
# =============================================================================

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


# =============================================================================
# DRW-08  Export drawing sheet to PDF
#         Refactored for Fusion 2703.x: Drawings live in adsk.drawing
#         (Issue #10 / quirk #27). DrawingExportManager + PDF options
#         now hang off the adsk.drawing namespace.
# =============================================================================

import adsk.core, adsk.drawing
import os

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active.")
        return

    sheet       = drw.sheets.item(0)
    output_path = os.path.expanduser(f"~/Desktop/{drw.parentDocument.name}_Sheet1.pdf")

    # TODO(refactor): confirm exportManager is exposed on DrawingDocument or on
    # the Drawing product itself in 2703.x. dir(adsk.drawing.DrawingDocument)
    # and dir(drw) should show a DrawingExportManager — adjust accordingly.
    export_mgr  = drw.exportManager if hasattr(drw, "exportManager") else drw.parentDocument.exportManager

    # TODO(refactor): verify createPDFExportOptions signature on
    # adsk.drawing.DrawingExportManager — it may now require (filename, sheet)
    # or (filename) only. Probe dir(export_mgr) to confirm.
    pdf_options = export_mgr.createPDFExportOptions(output_path, sheet)
    pdf_options.filename = output_path

    # Export the configured sheet
    export_mgr.execute(pdf_options)
    print(f"PDF exported: {output_path}")


# =============================================================================
# DRW-09  Export drawing to DXF (for 2D manufacturing / laser / waterjet)
#         Refactored for Fusion 2703.x: adsk.drawing namespace (Issue #10).
# =============================================================================

import adsk.core, adsk.drawing
import os

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active.")
        return

    sheet       = drw.sheets.item(0)
    output_path = os.path.expanduser(f"~/Desktop/{drw.parentDocument.name}_Sheet1.dxf")

    # TODO(refactor): confirm exportManager surface on adsk.drawing.Drawing /
    # DrawingDocument in 2703.x (see DRW-08 note).
    export_mgr  = drw.exportManager if hasattr(drw, "exportManager") else drw.parentDocument.exportManager

    # TODO(refactor): verify createDXFExportOptions signature on
    # adsk.drawing.DrawingExportManager — likely (filename, sheet).
    dxf_options = export_mgr.createDXFExportOptions(output_path, sheet)
    dxf_options.filename = output_path

    export_mgr.execute(dxf_options)
    print(f"DXF exported: {output_path}")
    print("Use this DXF for 2D programming, laser cutting, or waterjet.")


# =============================================================================
# DRW-10  Full drawing audit — counts views, dims, notes across all sheets
#         Refactored for Fusion 2703.x: adsk.drawing namespace (Issue #10).
#         Read-only port; no behavioural change.
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active.")
        return

    print(f"=== Drawing Audit: {drw.parentDocument.name} ===")
    total_views = total_dims = total_notes = 0

    for s in range(drw.sheets.count):
        sheet = drw.sheets.item(s)
        v     = sheet.drawingViews.count
        d     = sheet.drawingDimensions.count
        n     = sheet.drawingNotes.count
        total_views += v
        total_dims  += d
        total_notes += n
        print(f"\n  Sheet: {sheet.name} ({sheet.paperSize})")
        print(f"    Views      : {v}")
        print(f"    Dimensions : {d}")
        print(f"    Notes      : {n}")

        for v_idx in range(v):
            view = sheet.drawingViews.item(v_idx)
            print(f"      View: {view.name:25s}  "
                  f"type={view.drawingViewType}  "
                  f"scale={view.scale:.3f}")

    print(f"\nTotals — Views: {total_views}  Dims: {total_dims}  Notes: {total_notes}")


# =============================================================================
# DRW-11  Audit existing views, find parent / projected-view relationships
#         Probes drawing view parent links (base view -> projected views).
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw or drw.sheets.count == 0:
        print("No drawing active.")
        return

    for s_idx in range(drw.sheets.count):
        sheet = drw.sheets.item(s_idx)
        print(f"\nSheet [{s_idx}]: {sheet.name}  views={sheet.drawingViews.count}")

        for v_idx in range(sheet.drawingViews.count):
            view = sheet.drawingViews.item(v_idx)

            # TODO(refactor): verify the parent-view attribute name on
            # adsk.drawing.DrawingView in 2703.x — it may be `parentView`,
            # `parent`, or exposed via the view's `drawingViewType`. Try
            # dir(view) and look for parent / base references.
            parent = None
            for attr in ("parentView", "parent", "baseView"):
                if hasattr(view, attr):
                    parent = getattr(view, attr)
                    break

            parent_name = parent.name if parent else "<none / base view>"
            print(f"  View [{v_idx}]: {view.name:25s}  "
                  f"type={view.drawingViewType}  "
                  f"parent={parent_name}")


# =============================================================================
# DRW-12  Full section view A-A through the active base view
#         Cuts straight across the part; produces a section view labelled A-A.
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw or drw.sheets.count == 0:
        print("No drawing active.")
        return

    sheet = drw.sheets.item(0)
    if sheet.drawingViews.count == 0:
        print("No base view to section. Run DRW-04 first.")
        return

    base_view = sheet.drawingViews.item(0)
    print(f"Base view: {base_view.name}")

    # TODO(refactor): adsk.drawing.DrawingViews likely exposes
    # createSectionViewInput(parentView) returning a SectionViewInput. Probe
    # dir(sheet.drawingViews) for the exact factory name.
    #
    # The cutting line for a *full* section A-A is a single straight segment
    # that crosses the entire base view. The API typically wants either:
    #   - a list of Point3D defining the cutting-line polyline, or
    #   - two endpoints + a direction, in the parent view's sheet-space
    # Geometry must be supplied in cm (Fusion API convention).
    #
    # Placeholder cutting line: horizontal through the centre of the base view.
    # Replace once the actual SectionViewInput surface is confirmed.
    bbox      = base_view.boundingBox if hasattr(base_view, "boundingBox") else None
    if bbox:
        y_mid = (bbox.minPoint.y + bbox.maxPoint.y) / 2.0
        p_start = adsk.core.Point3D.create(bbox.minPoint.x - 1.0, y_mid, 0)
        p_end   = adsk.core.Point3D.create(bbox.maxPoint.x + 1.0, y_mid, 0)
    else:
        p_start = adsk.core.Point3D.create(5.0, 10.0, 0)
        p_end   = adsk.core.Point3D.create(12.0, 10.0, 0)

    print(f"Cutting line A-A: {p_start.asArray()} -> {p_end.asArray()}")

    # TODO(refactor): replace the block below with the confirmed call once the
    # API is introspected, e.g.:
    #   sec_input = sheet.drawingViews.createSectionViewInput(base_view)
    #   sec_input.cuttingLinePoints = [p_start, p_end]
    #   sec_input.identifier        = "A"
    #   sec_input.position          = adsk.core.Point3D.create(20.0, 10.0, 0)
    #   sec_view = sheet.drawingViews.addSectionView(sec_input)
    print("TODO(refactor): section view A-A creation pending live API probe.")
    print("  Need: dir(sheet.drawingViews) -> createSectionViewInput / addSectionView")
    print("  Need: dir(<SectionViewInput>)  -> cuttingLinePoints / identifier / position")


# =============================================================================
# DRW-13  Offset section view B-B (multi-segment / stepped cutting line)
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw or drw.sheets.count == 0:
        print("No drawing active.")
        return

    sheet = drw.sheets.item(0)
    if sheet.drawingViews.count == 0:
        print("No base view to section. Run DRW-04 first.")
        return

    base_view = sheet.drawingViews.item(0)
    print(f"Base view: {base_view.name}")

    # An offset section uses a stepped (multi-segment) cutting line so the
    # section plane jogs to catch features that don't lie on one plane.
    # Three segments => four points.
    bbox = base_view.boundingBox if hasattr(base_view, "boundingBox") else None
    if bbox:
        x_min, x_max = bbox.minPoint.x - 1.0, bbox.maxPoint.x + 1.0
        y_lo, y_hi   = (bbox.minPoint.y + bbox.maxPoint.y) / 2.0 - 1.0, \
                       (bbox.minPoint.y + bbox.maxPoint.y) / 2.0 + 1.0
        x_jog        = (bbox.minPoint.x + bbox.maxPoint.x) / 2.0
    else:
        x_min, x_max, x_jog = 5.0, 12.0, 8.5
        y_lo, y_hi = 9.0, 11.0

    cutting_pts = [
        adsk.core.Point3D.create(x_min, y_lo, 0),
        adsk.core.Point3D.create(x_jog, y_lo, 0),
        adsk.core.Point3D.create(x_jog, y_hi, 0),
        adsk.core.Point3D.create(x_max, y_hi, 0),
    ]
    print(f"Offset cutting line B-B: {len(cutting_pts)} points")
    for p in cutting_pts:
        print(f"  {p.asArray()}")

    # TODO(refactor): confirm adsk.drawing.DrawingViews.createSectionViewInput
    # accepts a multi-point cuttingLinePoints list for offset sections, or if
    # offset sections use a separate factory (e.g. createOffsetSectionViewInput).
    # Probe dir(sheet.drawingViews).
    #
    # Expected pattern once confirmed:
    #   sec_input = sheet.drawingViews.createSectionViewInput(base_view)
    #   sec_input.cuttingLinePoints = cutting_pts
    #   sec_input.identifier        = "B"
    #   sec_input.position          = adsk.core.Point3D.create(20.0, 17.0, 0)
    #   sec_view = sheet.drawingViews.addSectionView(sec_input)
    print("TODO(refactor): offset section B-B creation pending live API probe.")


# =============================================================================
# DRW-14  Half section view C-C (cutting plane stops at the part centreline)
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw or drw.sheets.count == 0:
        print("No drawing active.")
        return

    sheet = drw.sheets.item(0)
    if sheet.drawingViews.count == 0:
        print("No base view to section. Run DRW-04 first.")
        return

    base_view = sheet.drawingViews.item(0)
    print(f"Base view: {base_view.name}")

    # Half section: the cutting line goes from the edge of the view to the
    # part centreline, then turns 90 degrees to exit along the centreline.
    bbox = base_view.boundingBox if hasattr(base_view, "boundingBox") else None
    if bbox:
        x_min  = bbox.minPoint.x - 1.0
        x_mid  = (bbox.minPoint.x + bbox.maxPoint.x) / 2.0
        y_mid  = (bbox.minPoint.y + bbox.maxPoint.y) / 2.0
        y_top  = bbox.maxPoint.y + 1.0
    else:
        x_min, x_mid = 5.0, 8.5
        y_mid, y_top = 10.0, 13.5

    cutting_pts = [
        adsk.core.Point3D.create(x_min, y_mid, 0),   # left edge, on centreline
        adsk.core.Point3D.create(x_mid, y_mid, 0),   # to centre
        adsk.core.Point3D.create(x_mid, y_top, 0),   # up the centreline
    ]
    print(f"Half-section cutting line C-C: {len(cutting_pts)} points")
    for p in cutting_pts:
        print(f"  {p.asArray()}")

    # TODO(refactor): half sections may be a flag on SectionViewInput
    # (e.g. sec_input.isHalfSection = True) or a dedicated factory
    # (createHalfSectionViewInput). Probe dir(sheet.drawingViews) and
    # dir(<SectionViewInput>) on a live drawing to confirm.
    #
    # Expected pattern once confirmed:
    #   sec_input = sheet.drawingViews.createSectionViewInput(base_view)
    #   sec_input.cuttingLinePoints = cutting_pts
    #   sec_input.identifier        = "C"
    #   sec_input.isHalfSection     = True   # or similar
    #   sec_input.position          = adsk.core.Point3D.create(20.0, 5.0, 0)
    #   sec_view = sheet.drawingViews.addSectionView(sec_input)
    print("TODO(refactor): half section C-C creation pending live API probe.")
