"""
MCP_CAM_06_Add_a_2D_Pocket_operation_pocket_finish
==================================================
Group       : Manufacture
Script ID   : CAM-06
Description : Add a 2D Pocket operation (pocket finish pass)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_06_Add_a_2D_Pocket_operation_pocket_finish

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
    op_input = setup.operations.createInput("pocket2d")
    op_input.displayName = "3_Pocket_Finish"

    # ── Load sample milling tool library (see quirks #21-#24) ──────────────
    tool_libs  = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    target_url = adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'
    )
    library = tool_libs.toolLibraryAtURL(target_url)

    # 6 mm flat end mill — fits the Bracket's 2 mm pocket corner radius.
    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        if not p.itemByName('tool_isMill').value.value:
            continue
        # Drop taper filter — it's about shank shape, not tip. The
        # 'flat' check in the description below is the right filter.
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t
            break

    if chosen is None:
        print("No ~6 mm flat end mill found in 'Milling Tools (Metric)'.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  Ø{chosen.parameters.itemByName('tool_diameter').value.value*10:.1f} mm")

    params = op_input.parameters
    # Only set parameters that exist on pocket2d. 'stepover' is not present
    # on this strategy in current Fusion 2703.x — issue #9 tracks a proper
    # per-strategy parameter table.
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "2 mm"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)

    # Geometry: same pocket bottom face as CAM-05 Adaptive.
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    pocket_bottom = next(f for f in bracket.faces if abs(f.centroid.z - 1.2) < 0.05)
    pockets_pv = op.parameters.itemByName('pockets').value
    cs = pockets_pv.getCurveSelections(); cs.clear()
    sel = cs.createNewPocketSelection(); sel.inputGeometry = [pocket_bottom]
    pockets_pv.applyCurveSelections(cs)

    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print(f"Geometry: pocket bottom face")
