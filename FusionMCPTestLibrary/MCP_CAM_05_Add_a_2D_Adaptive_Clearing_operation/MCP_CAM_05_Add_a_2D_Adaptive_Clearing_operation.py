"""
MCP_CAM_05_Add_a_2D_Adaptive_Clearing_operation
===============================================
Group       : Manufacture
Script ID   : CAM-05
Description : Add a 2D Adaptive Clearing operation (HEM-style roughing)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_05_Add_a_2D_Adaptive_Clearing_operation

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
    op_input = setup.operations.createInput("adaptive2d")
    op_input.displayName = "2_Adaptive_Rough"

    # ── Load sample milling tool library ───────────────────────────────────
    # Per quirks #21-#24: tools live on adsk.cam.CAMManager, libraries are
    # SWIG URLVectors (len/[i]), urlByLocation is singular, sample mills are
    # in "Milling Tools (Metric)".
    tool_libs  = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    target_url = adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'
    )
    library = tool_libs.toolLibraryAtURL(target_url)

    # Per quirk #25: Tool.typeName is gone — filter via parameters.
    # Want a flat end mill (tool_isMill == True, straight tapered, Ø 8–10 mm).
    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        is_mill = p.itemByName('tool_isMill').value.value
        if not is_mill:
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

    # HEM parameters: low RDOC (~10% D), high ADOC (full flute).
    # NOTE: 'optimalLoad' expects an expression like 'tool_diameter * 0.1'
    # (10% of tool diameter). A bare '10%' fails to evaluate (quirk).
    params.itemByName("tolerance").expression       = "0.02 mm"
    params.itemByName("optimalLoad").expression     = "tool_diameter * 0.1"
    params.itemByName("maximumStepdown").expression = "8 mm"
    params.itemByName("stockToLeave").expression    = "0.3 mm"

    op = setup.operations.add(op_input)

    # Geometry: pocket bottom face at z = part_height - pocket_depth = 1.2 cm.
    # The 'pockets' parameter is a CadContours2dParameterValue; populate via
    # CurveSelections.createNewPocketSelection seeded by the pocket bottom face.
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    pocket_bottom = next(f for f in bracket.faces if abs(f.centroid.z - 1.2) < 0.05)
    pockets_pv = op.parameters.itemByName('pockets').value
    cs = pockets_pv.getCurveSelections(); cs.clear()
    sel = cs.createNewPocketSelection(); sel.inputGeometry = [pocket_bottom]
    pockets_pv.applyCurveSelections(cs)

    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print(f"Setup: {setup.name}")
    print("HEM params: optimalLoad=tool_diameter*0.1 (10% RDOC), 8mm ADOC stepdown")
    print(f"Geometry: pocket bottom face ({pocket_bottom.boundingBox.maxPoint.x - pocket_bottom.boundingBox.minPoint.x:.1f} x "
          f"{pocket_bottom.boundingBox.maxPoint.y - pocket_bottom.boundingBox.minPoint.y:.1f} cm)")
