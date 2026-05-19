"""
MCP_CAM_28_Pencil_cleanup_pass_that_follows
===========================================
Group       : Manufacture
Script ID   : CAM-28
Description : Pencil (cleanup pass that follows concave corners)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_28_Pencil_cleanup_pass_that_follows

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
    op_input = setup.operations.createInput("pencil")
    op_input.displayName = "19_Pencil_Cleanup"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))
    tutorial_metric = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Tutorial Tools (Metric)'))

    # Pencil needs a ball mill smaller than typical concave radius.
    # Bracket pocket has 2 mm corner radius — use a Ø2 mm ball if available
    # (Tutorial Tools (Metric) has one). Fall back to Ø6 mm ball.
    def find_ball(lib, lo, hi):
        if not lib: return None
        for i in range(lib.count):
            t = lib.item(i); p = t.parameters
            tt = p.itemByName('tool_type')
            if not tt or tt.value.value != 'ball end mill': continue
            d = p.itemByName('tool_diameter').value.value * 10
            if lo <= d <= hi: return t
        return None
    chosen = (find_ball(tutorial_metric, 1.5, 3.0)
              or find_ball(library, 1.5, 3.0)
              or find_ball(library, 5.5, 6.5))
    if chosen is None:
        print("No ball end mill found in metric libraries.")
        return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression    = "0.01 mm"
    params.itemByName("stockToLeave").expression = "0 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")
