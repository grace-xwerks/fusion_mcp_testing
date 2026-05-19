"""Try adaptive 3D rough WITHOUT a model param assignment (default = all)."""
import adsk.core, adsk.cam, time

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    setup = cam.setups.item(0)

    # Delete prior adaptive3D op if present
    for i in range(setup.allOperations.count - 1, -1, -1):
        op = setup.allOperations.item(i)
        if op.name in ('13_Adaptive3D_Rough', '14_PocketClearing3D_Rough'):
            op.deleteMe()

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))
    flat6 = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'flat end mill': continue
        d = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= d <= 6.5:
            flat6 = t; break

    # ---- Adaptive, no model assignment ---------------------------------------
    oi = setup.operations.createInput("adaptive")
    oi.displayName = "13_Adaptive3D_Rough"
    oi.tool = flat6
    p = oi.parameters
    p.itemByName("tolerance").expression       = "0.1 mm"
    p.itemByName("optimalLoad").expression     = "tool_diameter * 0.1"
    p.itemByName("maximumStepdown").expression = "8 mm"
    p.itemByName("stockToLeave").expression    = "0.3 mm"
    op = setup.operations.add(oi)
    # intentionally do NOT touch op.parameters.itemByName('model')

    # ---- Pocket Clearing, no model assignment --------------------------------
    oi2 = setup.operations.createInput("pocket_clearing")
    oi2.displayName = "14_PocketClearing3D_Rough"
    oi2.tool = flat6
    p2 = oi2.parameters
    p2.itemByName("tolerance").expression       = "0.1 mm"
    p2.itemByName("maximumStepdown").expression = "2 mm"
    p2.itemByName("stockToLeave").expression    = "0.3 mm"
    op2 = setup.operations.add(oi2)

    # Regenerate
    future = cam.generateAllToolpaths(True)
    while not future.isGenerationCompleted: time.sleep(0.3)

    for op in (op, op2):
        ok = "ok" if op.hasToolpath else "no"
        secs = cam.getMachiningTime(op, 1.0, 1.0, 5.0).machiningTime if op.hasToolpath else 0.0
        print(f"  [{ok}] {op.name:30s} strategy={op.strategy:18s} cycle={secs:.1f}s")
