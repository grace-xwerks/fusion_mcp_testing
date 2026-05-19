"""Generate toolpaths for setup 0 and report per-op success/duration."""
import adsk.core, adsk.cam, time

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("No CAM setup."); return
    setup = cam.setups.item(0)
    print(f"Setup: {setup.name}  ops: {setup.allOperations.count}")

    future = cam.generateAllToolpaths(True)
    print(f"queued: {future.numberOfOperations}")
    while not future.isGenerationCompleted:
        time.sleep(0.3)
    print("done.")

    batch_a_names = {
        '7_Bore_M6_holes', '8_Circular_M6_holes', '9_Slot_Pocket',
        '10_Engrave_TopContour', '11_Trace_TopPerimeter', '12_Thread_M6'
    }
    total = 0.0
    for i in range(setup.allOperations.count):
        op = setup.allOperations.item(i)
        ok = "ok " if op.hasToolpath else "no "
        marker = "*" if op.name in batch_a_names else " "
        secs = 0.0
        if op.hasToolpath:
            mt = cam.getMachiningTime(op, 1.0, 1.0, 5.0)
            secs = mt.machiningTime
            total += secs
        print(f"  {marker} [{ok}] {op.name:35s}  strategy={op.strategy:12s}  cycle={secs:6.1f}s")
    print(f"Total cycle: {total:.1f}s ({total/60:.2f} min)")
