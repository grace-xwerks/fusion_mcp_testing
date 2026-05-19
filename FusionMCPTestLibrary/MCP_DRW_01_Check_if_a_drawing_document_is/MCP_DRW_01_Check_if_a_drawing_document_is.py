"""
MCP_DRW_01_Check_if_a_drawing_document_is
=========================================
Group       : Drawings
Script ID   : DRW-01
Description : Check if a drawing document is currently active
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_01_Check_if_a_drawing_document_is

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

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
