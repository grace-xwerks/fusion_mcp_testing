"""Bump stock offset and retry 3D adaptive/pocket_clearing."""
import adsk.core, adsk.cam, time

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    setup = cam.setups.item(0)

    # Save original; bump offsets to 10mm to give real roughing volume.
    ps = setup.parameters
    orig_sides = ps.itemByName('job_stockOffsetSides').expression
    orig_top   = ps.itemByName('job_stockOffsetTop').expression
    ps.itemByName('job_stockOffsetSides').expression = '10 mm'
    ps.itemByName('job_stockOffsetTop').expression   = '10 mm'
    print(f"Bumped stock offsets: sides={ps.itemByName('job_stockOffsetSides').expression}, "
          f"top={ps.itemByName('job_stockOffsetTop').expression}")

    # Delete prior 3D rough ops if present.
    for i in range(setup.allOperations.count - 1, -1, -1):
        op = setup.allOperations.item(i)
        if op.name in ('13_Adaptive3D_Rough', '14_PocketClearing3D_Rough'):
            op.deleteMe()

    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    lib = tl.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))
    flat6 = None
    for i in range(lib.count):
        t = lib.item(i); pp = t.parameters
        tt = pp.itemByName('tool_type')
        if not tt or tt.value.value != 'flat end mill': continue
        d = pp.itemByName('tool_diameter').value.value * 10
        if 5.5 <= d <= 6.5: flat6 = t; break

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')

    # Re-add adaptive with model assignment
    oi = setup.operations.createInput("adaptive")
    oi.displayName = "13_Adaptive3D_Rough"
    oi.tool = flat6
    pp = oi.parameters
    pp.itemByName("tolerance").expression       = "0.1 mm"
    pp.itemByName("optimalLoad").expression     = "tool_diameter * 0.1"
    pp.itemByName("maximumStepdown").expression = "8 mm"
    pp.itemByName("stockToLeave").expression    = "0.3 mm"
    op1 = setup.operations.add(oi)
    op1.parameters.itemByName('model').value.value = [bracket]

    oi2 = setup.operations.createInput("pocket_clearing")
    oi2.displayName = "14_PocketClearing3D_Rough"
    oi2.tool = flat6
    pp2 = oi2.parameters
    pp2.itemByName("tolerance").expression       = "0.1 mm"
    pp2.itemByName("maximumStepdown").expression = "2 mm"
    pp2.itemByName("stockToLeave").expression    = "0.3 mm"
    op2 = setup.operations.add(oi2)
    op2.parameters.itemByName('model').value.value = [bracket]

    future = cam.generateAllToolpaths(True)
    while not future.isGenerationCompleted: time.sleep(0.5)

    for op in (op1, op2):
        ok = "ok" if op.hasToolpath else "no"
        secs = cam.getMachiningTime(op, 1.0, 1.0, 5.0).machiningTime if op.hasToolpath else 0.0
        print(f"  [{ok}] {op.name:30s} cycle={secs:.1f}s")

    # Restore original offsets (don't permanently change the demo setup).
    ps.itemByName('job_stockOffsetSides').expression = orig_sides
    ps.itemByName('job_stockOffsetTop').expression   = orig_top
    print(f"Restored stock offsets to original.")
