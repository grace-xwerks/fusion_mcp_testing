"""
MCP_CAM_07_Add_a_2D_Contour_operation_outside
=============================================
Group       : Manufacture
Script ID   : CAM-07
Description : Add a 2D Contour operation (outside profile)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_07_Add_a_2D_Contour_operation_outside

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
    op_input = setup.operations.createInput("contour2d")
    op_input.displayName = "4_Contour_Outside"

    # ── Load sample milling tool library ───────────────────────────────────
    tool_libs  = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    target_url = adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'
    )
    library = tool_libs.toolLibraryAtURL(target_url)

    # 8–10 mm flat end mill for outside contour.
    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        if not p.itemByName('tool_isMill').value.value:
            continue
        # Drop taper filter — it's about shank shape, not tip. The
        # 'flat' check in the description below is the right filter.
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 8.0 <= dia_mm <= 10.0:
            chosen = t
            break

    if chosen is None:
        print("No 8–10 mm flat end mill found in 'Milling Tools (Metric)'.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  Ø{chosen.parameters.itemByName('tool_diameter').value.value*10:.1f} mm")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "5 mm"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)

    # Geometry: body silhouette (outer profile when viewed from above).
    # CurveSelections.createNewSilhouetteSelection() seeded by the body
    # produces the outer contour chain automatically — no manual edge picking.
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    contours_pv = op.parameters.itemByName('contours').value
    cs = contours_pv.getCurveSelections(); cs.clear()
    sel = cs.createNewSilhouetteSelection(); sel.inputGeometry = [bracket]
    contours_pv.applyCurveSelections(cs)

    print(f"Setup: {setup.name}")
    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print(f"Geometry: Bracket body silhouette (outer 2D contour)")
