"""
MCP_DRW_02_Inspect_an_active_Drawing_document
=============================================
Group       : Drawings
Script ID   : DRW-02
Description : Inspect an active Drawing document
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DRW_02_Inspect_an_active_Drawing_document

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

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
