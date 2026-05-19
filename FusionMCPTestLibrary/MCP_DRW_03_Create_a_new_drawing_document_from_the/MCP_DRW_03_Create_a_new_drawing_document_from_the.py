"""
MCP_DRW_03_Create_a_new_drawing_document_from_the
=================================================
Group       : Drawings
Script ID   : DRW-03
Description : Create a new drawing document from the active Design  [BLOCKED on #28]
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_03_Create_a_new_drawing_document_from_the

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

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
