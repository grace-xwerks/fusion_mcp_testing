"""
MCP_DRW_03_Create_a_new_drawing_document_from_the
=================================================
Group       : Drawings
Script ID   : DRW-03
Description : Create a new drawing document from the active Design
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_03_Create_a_new_drawing_document_from_the

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

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
