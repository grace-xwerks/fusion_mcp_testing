import adsk.core, adsk.cam, time

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    setup = cam.setups.item(0)
    print(f"Setup: {setup.name}  ops: {setup.allOperations.count}")

    future = cam.generateAllToolpaths(True)
    print(f"queued: {future.numberOfOperations}")
    while not future.isGenerationCompleted:
        time.sleep(0.5)
    print("done.")

    batch_b = {
        '13_Adaptive3D_Rough', '14_PocketClearing3D_Rough', '15_Horizontal_Finish',
        '16_Parallel3D_Finish', '17_Contour3D_Finish', '18_Scallop_Finish',
        '19_Pencil_Cleanup', '20_Radial_Finish', '21_Spiral_Finish',
        '22_MorphedSpiral_Finish',
    }
    total = 0.0
    for i in range(setup.allOperations.count):
        op = setup.allOperations.item(i)
        ok = "ok " if op.hasToolpath else "no "
        mark = "*" if op.name in batch_b else " "
        secs = 0.0
        if op.hasToolpath:
            mt = cam.getMachiningTime(op, 1.0, 1.0, 5.0)
            secs = mt.machiningTime
            total += secs
        print(f"  {mark} [{ok}] {op.name:30s}  strategy={op.strategy:18s}  cycle={secs:6.1f}s")
    print(f"Total cycle: {total:.1f}s ({total/60:.2f} min)")
