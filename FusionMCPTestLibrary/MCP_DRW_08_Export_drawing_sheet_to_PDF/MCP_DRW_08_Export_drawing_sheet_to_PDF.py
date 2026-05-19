"""
MCP_DRW_08_Export_drawing_sheet_to_PDF
======================================
Group       : Drawings
Script ID   : DRW-08
Description : Export drawing sheet to PDF
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_08_Export_drawing_sheet_to_PDF

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion
import os

def run(_context: str):
    app = adsk.core.Application.get()
    drw = adsk.fusion.Drawing.cast(app.activeProduct)

    if not drw:
        print("No drawing active.")
        return

    sheet       = drw.sheets.item(0)
    output_path = os.path.expanduser(f"~/Desktop/{drw.parentDocument.name}_Sheet1.pdf")

    export_mgr  = drw.parentDocument.exportManager
    pdf_options = export_mgr.createPDFExportOptions()
    pdf_options.filename = output_path

    # Export all sheets
    export_mgr.execute(pdf_options)
    print(f"PDF exported: {output_path}")
