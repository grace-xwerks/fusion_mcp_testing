"""
MCP_CAM_33_Ramp_3D_ramping_pass_Z_level_cuts_with
=================================================
Group       : Manufacture
Script ID   : CAM-33
Description : Ramp (3D ramping pass — Z-level cuts with smooth descent)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_33_Ramp_3D_ramping_pass_Z_level_cuts_with

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
    op_input = setup.operations.createInput("ramp")
    op_input.displayName = "24_Ramp_Finish"

    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tl.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))
    chosen = None
    for i in range(library.count):
        t = library.item(i); p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'ball end mill': continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t; break
    if chosen is None:
        print("No ~6 mm ball end mill."); return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "1 mm"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")
