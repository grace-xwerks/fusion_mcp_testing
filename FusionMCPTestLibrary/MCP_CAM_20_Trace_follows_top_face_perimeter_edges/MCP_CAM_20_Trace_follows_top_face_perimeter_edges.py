"""
MCP_CAM_20_Trace_follows_top_face_perimeter_edges
=================================================
Group       : Manufacture
Script ID   : CAM-20
Description : Trace (follows top-face perimeter edges at fixed Z)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_20_Trace_follows_top_face_perimeter_edges

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
    op_input = setup.operations.createInput("trace")
    op_input.displayName = "11_Trace_TopPerimeter"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        if not p.itemByName('tool_isMill').value.value:
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t
            break
    if chosen is None:
        print("No ~6 mm flat end mill.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  D{chosen.parameters.itemByName('tool_diameter').value.value*10:.1f} mm")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("stepover").expression        = "tool_diameter * 0.5"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    top_candidates = [f for f in bracket.faces if abs(f.centroid.z - 2.0) < 0.05]
    top_face = max(top_candidates,
                   key=lambda f: (f.boundingBox.maxPoint.x - f.boundingBox.minPoint.x)
                               * (f.boundingBox.maxPoint.y - f.boundingBox.minPoint.y))
    curves_pv = op.parameters.itemByName('curves').value
    cs = curves_pv.getCurveSelections(); cs.clear()
    sel = cs.createNewFaceContourSelection(); sel.inputGeometry = [top_face]
    curves_pv.applyCurveSelections(cs)

    print(f"Operation added: {op.name}  strategy={op.strategy}")
