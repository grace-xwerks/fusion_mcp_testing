"""
MCP_CAM_16_2D_Bore_helical_bore_finish_of_the_4_M6
==================================================
Group       : Manufacture
Script ID   : CAM-16
Description : 2D Bore (helical bore-finish of the 4 M6 holes)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_16_2D_Bore_helical_bore_finish_of_the_4_M6

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
    op_input = setup.operations.createInput("bore")
    op_input.displayName = "7_Bore_M6_holes"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    # Want a flat end mill smaller than the Ø6 mm bore: 3-5 mm.
    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        if not p.itemByName('tool_isMill').value.value:
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 3.0 <= dia_mm <= 5.0:
            chosen = t
            break
    if chosen is None:
        print("No 3-5 mm flat end mill in 'Milling Tools (Metric)'.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  D{chosen.parameters.itemByName('tool_diameter').value.value*10:.1f} mm")

    params = op_input.parameters
    params.itemByName("tolerance").expression    = "0.01 mm"
    params.itemByName("stockToLeave").expression = "0 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    m6_cyls = [f for f in bracket.faces
               if isinstance(f.geometry, adsk.core.Cylinder)
               and abs(f.geometry.radius - 0.3) < 0.05]
    op.parameters.itemByName('circularFaces').value.value = m6_cyls
    print(f"Operation added: {op.name}  strategy={op.strategy}  ({len(m6_cyls)} holes)")
