"""
MCP_CAM_19_Engrave_traces_top_face_outer_contour
================================================
Group       : Manufacture
Script ID   : CAM-19
Description : Engrave (traces top-face outer contour as if it were a sketch line)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_19_Engrave_traces_top_face_outer_contour

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
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("engrave")
    op_input.displayName = "10_Engrave_TopContour"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    # Prefer a chamfer mill (V-bit) for engraving.
    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        if not p.itemByName('tool_isMill').value.value:
            continue
        desc = (t.description or '').lower()
        if 'chamfer' in desc:
            chosen = t
            break
    if chosen is None:
        for i in range(library.count):
            t = library.item(i)
            p = t.parameters
            if not p.itemByName('tool_isMill').value.value:
                continue
            dia_mm = p.itemByName('tool_diameter').value.value * 10
            if 2.0 <= dia_mm <= 4.0:
                chosen = t
                break
    if chosen is None:
        print("No chamfer mill or 2-4 mm flat end mill found.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "0.5 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    top_candidates = [f for f in bracket.faces if abs(f.centroid.z - 2.0) < 0.05]
    top_face = max(top_candidates,
                   key=lambda f: (f.boundingBox.maxPoint.x - f.boundingBox.minPoint.x)
                               * (f.boundingBox.maxPoint.y - f.boundingBox.minPoint.y))
    contours_pv = op.parameters.itemByName('contours').value
    cs = contours_pv.getCurveSelections(); cs.clear()
    sel = cs.createNewFaceContourSelection(); sel.inputGeometry = [top_face]
    contours_pv.applyCurveSelections(cs)

    print(f"Operation added: {op.name}  strategy={op.strategy}")
