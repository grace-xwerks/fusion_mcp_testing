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
    print(f"Sheets   : {drw.sheets.count}")

    for s_idx in range(drw.sheets.count):
        sheet = drw.sheets.item(s_idx)
        print(f"\n  Sheet [{s_idx}]: {sheet.name}  size={sheet.paperSize}")
        print(f"    Views  : {sheet.drawingViews.count}")

        for v_idx in range(sheet.drawingViews.count):
            view = sheet.drawingViews.item(v_idx)
            scale = view.scale
            scale_str = f"1:{int(1/scale)}" if 0 < scale < 1 else f"{int(scale)}:1"
            print(f"      View [{v_idx}]: {view.name:25s}  type={view.drawingViewType}  scale={scale_str}")

            dims = view.drawingDimensions
            print(f"        Dimensions: {dims.count}")
            for d_idx in range(min(dims.count, 5)):
                d = dims.item(d_idx)
                print(f"          [{d_idx}] {d.drawingDimensionType}  value={d.text.formattedText}")


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

    # Quirk #28: CreateDrawingInput has no public Python factory in
    # 2703.x Insider. The legacy enum below also doesn't exist — both
    # paths will raise. Manual UI creation is the only documented path
    # today (File → New Drawing → From Design).
    drawing_doc = app.documents.add(
        adsk.core.DocumentTypes.DrawingDocumentType,   # not defined in this build
        app.data.activeProject,
        True,
    )

    drw = adsk.drawing.Drawing.cast(drawing_doc.products.item(0))
    print(f"Drawing document created: {drawing_doc.name}")
    print(f"Default sheets: {drw.sheets.count}")
    if drw.sheets.count > 0:
        sheet = drw.sheets.item(0)
        sheet.name = "Sheet1_Front_Side"
        print(f"Sheet renamed: {sheet.name}  size={sheet.paperSize}")


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

    sheet      = drw.sheets.item(0)
    views_col  = sheet.drawingViews

    # Documented API path. Quirk #29 blocks the runtime call on
    # 2703.x Insider, but the shape is correct.
    view_input = views_col.createBaseViewInput()
    view_input.referencedDocument = drw.referencedDocuments.item(0)
    view_input.position           = adsk.core.Point3D.create(7.0, 10.0, 0)
    view_input.scale              = 0.5    # 1:2
    view_input.viewOrientation    = adsk.drawing.DrawingViewOrientations.FrontViewOrientation
    view_input.viewStyle          = adsk.drawing.DrawingViewStyles.VisibleAndHiddenEdgesViewStyle

    base_view = views_col.addBaseView(view_input)
    print(f"Base view added: {base_view.name}  (Front, 1:2, at 70/100 mm)")


# =============================================================================
# DRW-05  Add projected views (top, right, isometric)
#         Depends on DRW-04 base view being present.
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active.")
        return

    sheet     = drw.sheets.item(0)
    views_col = sheet.drawingViews
    if views_col.count == 0:
        print("No base view found. Run DRW-04 first.")
        return
    base_view = views_col.item(0)

    # Top view — above the base view
    top_input          = views_col.createProjectedViewInput(base_view)
    top_input.position = adsk.core.Point3D.create(7.0, 17.0, 0)
    top_view = views_col.addProjectedView(top_input)
    print(f"Top view added: {top_view.name}")

    # Right view — right of the base view
    right_input          = views_col.createProjectedViewInput(base_view)
    right_input.position = adsk.core.Point3D.create(14.0, 10.0, 0)
    right_view = views_col.addProjectedView(right_input)
    print(f"Right view added: {right_view.name}")

    # Isometric view — upper right
    iso_input                 = views_col.createProjectedViewInput(base_view)
    iso_input.position        = adsk.core.Point3D.create(20.0, 17.0, 0)
    iso_input.viewOrientation = adsk.drawing.DrawingViewOrientations.HomeViewOrientation
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

    if not drw:
        print("No drawing active.")
        return

    sheet     = drw.sheets.item(0)
    views_col = sheet.drawingViews
    if views_col.count == 0:
        print("No views on sheet — run DRW-04 first.")
        return
    base_view = views_col.item(0)
    curves    = base_view.curves
    print(f"Base view: {base_view.name}  curves={curves.count}")
    if curves.count < 2:
        print("Not enough curves in view to dimension.")
        return

    dim_input = sheet.drawingDimensions.createLinearDimensionInput(
        curves.item(0),
        curves.item(1),
        adsk.core.Point3D.create(7.0, 7.5, 0),
        adsk.drawing.DrawingLinearDimensionOrientations.HorizontalLinearDimension,
    )
    dim = sheet.drawingDimensions.addLinearDimension(dim_input)
    print(f"Linear dimension added: {dim.text.formattedText}")


# =============================================================================
# DRW-07  Add a drawing note (title block / general tolerance note)
# =============================================================================

import adsk.core, adsk.drawing

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.drawing.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active.")
        return

    sheet     = drw.sheets.item(0)
    notes_col = sheet.drawingNotes

    notes = [
        (adsk.core.Point3D.create(1.0, 1.5, 0), "MATERIAL: 6061-T6 ALUMINUM"),
        (adsk.core.Point3D.create(1.0, 1.0, 0), "GENERAL TOLERANCES: ±0.1 mm UNLESS OTHERWISE SPECIFIED"),
        (adsk.core.Point3D.create(1.0, 0.5, 0), "ALL SHARP EDGES 0.5 mm x 45° CHAMFER"),
    ]
    for pos, text in notes:
        note_input = notes_col.createInput(pos)
        note_input.text = text
        notes_col.add(note_input)
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

    export_mgr  = drw.exportManager
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

    export_mgr  = drw.exportManager
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


