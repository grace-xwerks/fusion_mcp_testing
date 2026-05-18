"""
MCP_DRW_09_Export_drawing_to_DXF_for_2D
=======================================
Group       : Drawings
Script ID   : DRW-09
Description : Export drawing to DXF (for 2D manufacturing / laser / waterjet)
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_09_Export_drawing_to_DXF_for_2D

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

    output_path = os.path.expanduser(f"~/Desktop/{drw.parentDocument.name}_Sheet1.dxf")

    export_mgr  = drw.parentDocument.exportManager
    dxf_options = export_mgr.createDXFExportOptions()
    dxf_options.filename = output_path

    export_mgr.execute(dxf_options)
    print(f"DXF exported: {output_path}")
    print("Use this DXF for 2D programming, laser cutting, or waterjet.")
