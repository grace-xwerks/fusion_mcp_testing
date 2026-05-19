"""
MCP_CAM_21_Thread_Mill_M6x1_0_thread_mill_on_the_4
==================================================
Group       : Manufacture
Script ID   : CAM-21
Description : Thread Mill (M6x1.0 thread mill on the 4 M6 corner holes)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_21_Thread_Mill_M6x1_0_thread_mill_on_the_4

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
    op_input = setup.operations.createInput("thread")
    op_input.displayName = "12_Thread_M6"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    # The METRIC sample library only ships M8/M10/M12 thread mills (>=Ø6.35 mm)
    # — none fits the Ø6 mm M6 hole. The INCH sample library however ships a
    # Ø4.57 mm (1/4-20 TPI) thread mill, which fits. Fusion's thread strategy
    # accepts threadPitch independently of the tool's native pitch, so the
    # inch tool can cut a metric M6×1.0 thread.
    inch_lib = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Inch)'))

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    m6_cyls = [f for f in bracket.faces
               if isinstance(f.geometry, adsk.core.Cylinder)
               and abs(f.geometry.radius - 0.3) < 0.05]
    bore_dia_mm = 6.0  # M6 = Ø6 mm bore

    chosen, chosen_dia = None, 1e9
    for lib in (library, inch_lib):
        if not lib: continue
        for i in range(lib.count):
            t = lib.item(i)
            p = t.parameters
            tt = p.itemByName('tool_type')
            if not tt or tt.value.value != 'thread mill': continue
            dia_mm = p.itemByName('tool_diameter').value.value * 10
            if dia_mm < bore_dia_mm and dia_mm < chosen_dia:
                chosen, chosen_dia = t, dia_mm
    if chosen is None:
        print(f"No thread mill < Ø{bore_dia_mm} mm in Metric or Inch sample libraries.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  Ø{chosen_dia:.2f} mm")

    params = op_input.parameters
    params.itemByName("threadPitch").expression = "1 mm"
    # 'threadType' default 'ISO Metric profile' is fine.

    op = setup.operations.add(op_input)
    op.parameters.itemByName('circularFaces').value.value = m6_cyls
    print(f"Operation added: {op.name}  strategy={op.strategy}  ({len(m6_cyls)} holes)")
