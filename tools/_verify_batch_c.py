import adsk.core, adsk.cam, time

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    setup = cam.setups.item(0)
    print(f"Setup: {setup.name}  ops: {setup.allOperations.count}")
    future = cam.generateAllToolpaths(True)
    print(f"queued: {future.numberOfOperations}")
    while not future.isGenerationCompleted: time.sleep(0.5)
    print("done.")

    batch_c = {
        '23_Flat_Finish', '24_Ramp_Finish', '25_Blend_Finish',
        '26_Corner_Cleanup', '27_SteepAndShallow_Finish',
        '28_Morph_Finish', '29_Project_Finish',
    }
    total = 0.0
    for i in range(setup.allOperations.count):
        op = setup.allOperations.item(i)
        ok = "ok " if op.hasToolpath else "no "
        mark = "*" if op.name in batch_c else " "
        secs = 0.0
        if op.hasToolpath:
            mt = cam.getMachiningTime(op, 1.0, 1.0, 5.0)
            secs = mt.machiningTime; total += secs
        print(f"  {mark} [{ok}] {op.name:30s} strategy={op.strategy:18s} cycle={secs:6.1f}s")
    print(f"Total cycle: {total:.1f}s ({total/60:.2f} min)")
