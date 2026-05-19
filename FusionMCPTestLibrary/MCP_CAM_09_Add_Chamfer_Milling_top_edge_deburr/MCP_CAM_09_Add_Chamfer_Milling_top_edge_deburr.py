"""
MCP_CAM_09_Add_Chamfer_Milling_top_edge_deburr
==============================================
Group       : Manufacture
Script ID   : CAM-09
Description : Add Chamfer Milling (top edge deburr / chamfer)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_09_Add_Chamfer_Milling_top_edge_deburr

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return

    setup    = cam.setups.item(0)
    # Fusion exposes a dedicated 'chamfer2d' strategy in current API
    op_input = setup.operations.createInput("chamfer2d")
    op_input.displayName = "6_Chamfer_Top"

    # Load the Metric Milling Tools sample library (quirk #21, #24)
    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    sample_url = adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'
    )
    sample_lib = tool_libs.toolLibraryAtURL(sample_url)

    chamfer_tool = None
    # ToolLibrary IS a Collection — iterate directly (quirk #22)
    for i in range(sample_lib.count):
        t = sample_lib.item(i)
        is_mill_param = t.parameters.itemByName('tool_isMill')
        is_mill = bool(is_mill_param.value.value) if is_mill_param else False
        desc_p = t.parameters.itemByName('tool_description')
        desc = (desc_p.value.value
                if desc_p else
                (t.description or ''))
        if is_mill and 'chamfer' in desc.lower():
            chamfer_tool = t
            print(f"Chamfer tool: {desc}")
            break

    if chamfer_tool is None:
        print("No chamfer mill found in 'Milling Tools (Metric)'. Aborting.")
        return

    op_input.tool = chamfer_tool

    params = op_input.parameters
    # Chamfer width ≈ Bracket's 1 mm chamfer parameter
    params.itemByName("chamferWidth").expression = "1 mm"
    params.itemByName("tolerance").expression    = "0.01 mm"

    op = setup.operations.add(op_input)

    # Geometry: top face's outer contour. Use createNewFaceContourSelection
    # — picking the top face automatically gives its outer perimeter chain.
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    top_candidates = [f for f in bracket.faces if abs(f.centroid.z - 2.0) < 0.05]
    top_face = max(top_candidates,
                   key=lambda f: (f.boundingBox.maxPoint.x - f.boundingBox.minPoint.x)
                               * (f.boundingBox.maxPoint.y - f.boundingBox.minPoint.y))
    contours_pv = op.parameters.itemByName('contours').value
    cs = contours_pv.getCurveSelections(); cs.clear()
    sel = cs.createNewFaceContourSelection(); sel.inputGeometry = [top_face]
    contours_pv.applyCurveSelections(cs)

    print(f"Operation added: {op.name}")
    print(f"Geometry: top face contour (outer perimeter)")
