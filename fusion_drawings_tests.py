"""
Fusion MCP — Drawings Workspace Test Scripts
============================================
Tests the Fusion Drawings product type: creating drawing documents,
adding sheets, placing views (base, projected, section, detail),
adding dimensions and annotations, and exporting to PDF/DXF.

PREREQUISITE: The Bracket part from Design scripts should be open.
Fusion Drawings work on a separate DrawingDocument that references
the Design document.

In Fusion 2703.x Insider, Drawings live in their own submodule
**adsk.drawing** (sibling of adsk.cam and adsk.fusion). This is the
same drift pattern as CAM — see issues #3 (#27, #28, #29) and #10.

Key classes (from dir(adsk.drawing)):
  Drawing, DrawingDocument, DrawingExportManager, DrawingExportOptions,
  CreateDrawingInput, DrawingCreationModes,
  CustomTable, CustomTableInput, CustomTables,
  ASMESheetSizes, DimensionStrategyTypes, ...

⚠️  RUNTIME STATUS — Fusion 2703.x Insider, May 2026
============================================================
The adsk.drawing Python bindings are largely NOT YET IMPLEMENTED on
this build. Class definitions exist, DrawingDocument.cast(doc) returns
an instance, but any data-access call raises:

    RuntimeError: 5 : API Function not yet implemented

This affects:
  - drawing.sheets / .namedViews / .exportManager / .unitsManager
  - All sheet.drawingViews.* operations
  - All view.drawingDimensions.* / .drawingNotes.* operations
  - PDF / DXF export

DRW-01 (workspace check, no data access) does run. DRW-02..21 are
blocked until Autodesk ships the Python implementation in a future
Fusion release.

Programmatic drawing creation (DRW-03) is ALSO blocked separately:
CreateDrawingInput has no public Python factory in this build (#28).
Manual creation in the UI works (File > New Drawing > From Design)
but the resulting drawing can't be programmatically inspected per #29.

The scripts below were refactored against the documented adsk.drawing
class structure so they're ready to validate the moment the bindings
ship. For now, treat the DRW group as a known-blocked future-work
section of the library.
"""

# =============================================================================
# DRW-01  Check if a drawing document is currently active
#         If not, prints how to create one.
# =============================================================================

import adsk.core, adsk.drawing

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
        drw = adsk.drawing.Drawing.cast(prod)
        print(f"Drawing sheets: {drw.sheets.count}")


# =============================================================================
# DRW-02  Inspect an active Drawing document
#         Run after opening a drawing in Fusion.
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active. Open or create a drawing document first.")
        return

    print(f"=== Drawing Inventory ===")
    print(f"Document : {drw.parentDocument.name}")

    # TODO(refactor): Probe whether Drawing exposes `sheets` directly. In
    # 2703.x Insider the attribute name may have shifted (e.g. activeSheet,
    # drawingSheets). dir(drw) will reveal the right collection name.
    print(f"Drawing attrs sample: {[a for a in dir(drw) if not a.startswith('_')][:20]}")

    sheets = getattr(drw, 'sheets', None)
    if sheets is None:
        print("TODO(refactor): adsk.drawing.Drawing has no `sheets` attribute on this build.")
        return

    print(f"Sheets   : {sheets.count}")

    for s_idx in range(sheets.count):
        sheet = sheets.item(s_idx)
        print(f"\n  Sheet [{s_idx}]: {sheet.name}")
        # TODO(refactor): DrawingSheet attribute names on adsk.drawing may differ.
        # Old assumptions: paperSize, drawingViews. Probe with dir(sheet).
        print(f"    Sheet attrs: {[a for a in dir(sheet) if not a.startswith('_')][:25]}")

        paper = getattr(sheet, 'paperSize', '?')
        views = getattr(sheet, 'drawingViews', None)
        print(f"    Size   : {paper}")
        if views is None:
            print("    TODO(refactor): no `drawingViews` collection on DrawingSheet.")
            continue
        print(f"    Views  : {views.count}")

        for v_idx in range(views.count):
            view = views.item(v_idx)
            # TODO(refactor): DrawingView attribute names. Old assumptions:
            # drawingViewType, scale, drawingDimensions. Probe with dir(view).
            vtype = getattr(view, 'drawingViewType', '?')
            vscale = getattr(view, 'scale', None)
            scale_str = (
                f"1:{int(1/vscale) if vscale < 1 else int(vscale)}"
                if isinstance(vscale, (int, float)) and vscale != 0
                else "?"
            )
            print(f"      View [{v_idx}]: {view.name:25s}  type={vtype}  scale={scale_str}")

            dims = getattr(view, 'drawingDimensions', None)
            if dims is None:
                print("        TODO(refactor): no `drawingDimensions` on DrawingView.")
                continue
            print(f"        Dimensions: {dims.count}")
            for d_idx in range(min(dims.count, 5)):
                d = dims.item(d_idx)
                dtype = getattr(d, 'drawingDimensionType', '?')
                text  = getattr(d, 'text', None)
                value = getattr(text, 'formattedText', '?') if text is not None else '?'
                print(f"          [{d_idx}] {dtype}  value={value}")


# =============================================================================
# DRW-03  Create a new drawing document from the active Design  [BLOCKED on #28]
#         Programmatically creates drawing + A-size sheet.
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    # TODO(#28): CreateDrawingInput has no public Python factory in 2703.x
    # Insider. Manual UI creation (File > New Drawing > From Design) is the
    # only known path. Run DRW-04..21 against a drawing the user has created
    # in the UI. The code below attempts the documented new-API path and
    # prints a diagnostic if it fails, so we can re-validate once Autodesk
    # exposes the factory.
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

    # Probe what's available on adsk.drawing for drawing creation.
    drw_symbols = [s for s in dir(adsk.drawing) if 'Creat' in s or 'Input' in s or 'Mode' in s]
    print(f"adsk.drawing creation-related symbols: {drw_symbols}")

    # Attempt the documented input pattern. If CreateDrawingInput has no
    # public factory, this will fail loudly — by design (no try/except).
    # Common patterns to try (any of which Autodesk may eventually expose):
    #   app.documents.add(adsk.core.DocumentTypes.DrawingDocumentType, ...)
    #   adsk.drawing.CreateDrawingInput.create(...)
    #   design_drawing_manager.createDrawingInput(...)
    print("Attempting legacy DocumentTypes.DrawingDocumentType path...")
    drawing_doc = app.documents.add(
        adsk.core.DocumentTypes.DrawingDocumentType,
        app.data.activeProject,
        True
    )

    print(f"Drawing document created: {drawing_doc.name}")

    drw = adsk.drawing.Drawing.cast(drawing_doc.products.item(0))
    if not drw:
        print("TODO(#28): cast to adsk.drawing.Drawing failed — productType drift.")
        return
    print(f"Drawing product cast OK")

    sheets = getattr(drw, 'sheets', None)
    if sheets is None:
        print("TODO(refactor): drw.sheets missing in adsk.drawing — probe dir(drw).")
        return

    print(f"Default sheets: {sheets.count}")
    if sheets.count > 0:
        sheet = sheets.item(0)
        sheet.name = "Sheet1_Front_Side"
        paper = getattr(sheet, 'paperSize', '?')
        print(f"Sheet renamed: {sheet.name}  size={paper}")


# =============================================================================
# DRW-04  Add a base view (front view) to the active drawing sheet
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active. Run DRW-03 or open a drawing first.")
        return

    sheets = getattr(drw, 'sheets', None)
    if sheets is None or sheets.count == 0:
        print("No sheets on drawing.")
        return
    sheet = sheets.item(0)

    # Find the linked design's root component
    refs = getattr(drw, 'referencedDocuments', None)
    if refs is None:
        print("TODO(refactor): drw.referencedDocuments missing on adsk.drawing.Drawing.")
        return
    print(f"Referenced documents: {refs.count}")

    views_col = getattr(sheet, 'drawingViews', None)
    if views_col is None:
        print("TODO(refactor): sheet.drawingViews missing on adsk.drawing.DrawingSheet.")
        return

    # TODO(refactor): Probe the actual base-view input class name on
    # adsk.drawing. The old name was DrawingViewInput / createBaseViewInput;
    # orientation/style enums lived under adsk.fusion.DrawingViewOrientations
    # and adsk.fusion.DrawingViewStyles. On adsk.drawing they may be flat
    # module-level enums (e.g. adsk.drawing.DrawingViewOrientations).
    print(f"drawingViews methods: {[m for m in dir(views_col) if 'Input' in m or 'add' in m or 'create' in m]}")

    view_input = views_col.createBaseViewInput()
    view_input.referencedDocument = refs.item(0) if refs.count > 0 else None

    # Position: center of A-size sheet (in cm; Fusion API uses centimeters)
    view_input.position = adsk.core.Point3D.create(7.0, 10.0, 0)
    view_input.scale    = 0.5    # 1:2

    # Orientation/style enums — try adsk.drawing first, fall back to TODO.
    orient_enum = getattr(adsk.drawing, 'DrawingViewOrientations', None)
    style_enum  = getattr(adsk.drawing, 'DrawingViewStyles', None)
    if orient_enum is not None:
        view_input.viewOrientation = orient_enum.FrontViewOrientation
    else:
        print("TODO(refactor): adsk.drawing.DrawingViewOrientations not found.")
    if style_enum is not None:
        view_input.viewStyle = style_enum.VisibleAndHiddenEdgesViewStyle
    else:
        print("TODO(refactor): adsk.drawing.DrawingViewStyles not found.")

    base_view = views_col.addBaseView(view_input)
    print(f"Base view added: {base_view.name}")
    print(f"  Orientation : Front")
    print(f"  Scale       : 1:2")
    print(f"  Position    : (70, 100) mm")


# =============================================================================
# DRW-05  Add projected views (top, right, isometric)
#         Depends on DRW-04 base view being present.
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    sheets = getattr(drw, 'sheets', None) if drw else None
    if not drw or sheets is None or sheets.count == 0:
        print("No drawing or sheet found.")
        return

    sheet     = sheets.item(0)
    views_col = getattr(sheet, 'drawingViews', None)
    if views_col is None:
        print("TODO(refactor): sheet.drawingViews missing on adsk.drawing.DrawingSheet.")
        return

    if views_col.count == 0:
        print("No base view found. Run DRW-04 first.")
        return

    base_view = views_col.item(0)

    # TODO(refactor): Probe createProjectedViewInput / addProjectedView names.
    # Orientation enum may now live at adsk.drawing.DrawingViewOrientations.
    orient_enum = getattr(adsk.drawing, 'DrawingViewOrientations', None)

    # Top view — above the base view
    top_input          = views_col.createProjectedViewInput(base_view)
    top_input.position = adsk.core.Point3D.create(7.0, 17.0, 0)
    top_view           = views_col.addProjectedView(top_input)
    print(f"Top view added: {top_view.name}")

    # Right view — to the right of base view
    right_input          = views_col.createProjectedViewInput(base_view)
    right_input.position = adsk.core.Point3D.create(14.0, 10.0, 0)
    right_view           = views_col.addProjectedView(right_input)
    print(f"Right view added: {right_view.name}")

    # Isometric view — upper right
    iso_input          = views_col.createProjectedViewInput(base_view)
    iso_input.position = adsk.core.Point3D.create(20.0, 17.0, 0)
    if orient_enum is not None:
        iso_input.viewOrientation = orient_enum.HomeViewOrientation
    else:
        print("TODO(refactor): adsk.drawing.DrawingViewOrientations not found for iso view.")
    iso_view = views_col.addProjectedView(iso_input)
    print(f"Iso view added: {iso_view.name}")

    print(f"\nTotal views on sheet: {views_col.count}")


# =============================================================================
# DRW-06  Add linear dimensions to the front view
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    sheets = getattr(drw, 'sheets', None) if drw else None
    if not drw or sheets is None or sheets.count == 0:
        print("No drawing found.")
        return

    sheet      = sheets.item(0)
    views_col  = getattr(sheet, 'drawingViews', None)
    if views_col is None or views_col.count == 0:
        print("No views on sheet — run DRW-04 first.")
        return
    base_view  = views_col.item(0)

    print(f"Base view: {base_view.name}")
    curves = getattr(base_view, 'curves', None)
    if curves is None:
        print("TODO(refactor): base_view.curves missing on adsk.drawing.DrawingView.")
        return
    print(f"Visible edges in view: {curves.count}")

    if curves.count < 2:
        print("Not enough curves in view to dimension. Ensure DRW-04 ran correctly.")
        return

    dims_col = getattr(sheet, 'drawingDimensions', None)
    if dims_col is None:
        print("TODO(refactor): sheet.drawingDimensions missing on adsk.drawing.DrawingSheet.")
        return

    # TODO(refactor): The linear-dim orientation enum used to live at
    # adsk.fusion.DrawingLinearDimensionOrientations. On adsk.drawing it
    # is likely adsk.drawing.DrawingLinearDimensionOrientations. The
    # createLinearDimensionInput signature may also have changed.
    lin_orient_enum = getattr(adsk.drawing, 'DrawingLinearDimensionOrientations', None)
    if lin_orient_enum is None:
        print("TODO(refactor): adsk.drawing.DrawingLinearDimensionOrientations not found.")
        return

    dim_input = dims_col.createLinearDimensionInput(
        curves.item(0),
        curves.item(1),
        adsk.core.Point3D.create(7.0, 7.5, 0),
        lin_orient_enum.HorizontalLinearDimension
    )
    dim = dims_col.addLinearDimension(dim_input)
    text = getattr(dim, 'text', None)
    formatted = getattr(text, 'formattedText', 'OK') if text is not None else 'OK'
    print(f"Linear dimension added: {formatted}")


# =============================================================================
# DRW-07  Add a drawing note (title block / general tolerance note)
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    sheets = getattr(drw, 'sheets', None) if drw else None
    if not drw or sheets is None or sheets.count == 0:
        print("No drawing found.")
        return

    sheet = sheets.item(0)

    # TODO(refactor): sheet.drawingNotes may have a different attr name on
    # adsk.drawing. Old API: sheet.drawingNotes.createInput(pos) -> set .text
    # -> sheet.drawingNotes.add(input). Probe with dir(sheet) for the right
    # collection name (could be `notes`, `drawingNotes`, `annotations`, ...).
    notes_col = getattr(sheet, 'drawingNotes', None)
    if notes_col is None:
        print("TODO(refactor): sheet.drawingNotes missing on adsk.drawing.DrawingSheet.")
        print(f"  Probe attrs: {[a for a in dir(sheet) if 'ote' in a.lower() or 'nnot' in a.lower()]}")
        return

    notes = [
        (adsk.core.Point3D.create(1.0, 1.5, 0),
         "MATERIAL: 6061-T6 ALUMINUM"),
        (adsk.core.Point3D.create(1.0, 1.0, 0),
         "GENERAL TOLERANCES: ±0.1 mm UNLESS OTHERWISE SPECIFIED"),
        (adsk.core.Point3D.create(1.0, 0.5, 0),
         "ALL SHARP EDGES 0.5 mm x 45° CHAMFER"),
    ]

    for pos, text in notes:
        note_input = notes_col.createInput(pos)
        note_input.text = text
        note = notes_col.add(note_input)
        print(f"Note added: {text[:50]}...")

    print(f"\nTotal notes on sheet: {notes_col.count}")


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


