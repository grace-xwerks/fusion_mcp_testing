import adsk.core, adsk.cam, time

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    setup = cam.setups.item(0)
    future = cam.generateAllToolpaths(True)
    while not future.isGenerationCompleted: time.sleep(0.5)

    targets = ('12_Thread_M6', '19_Pencil_Cleanup', '26_Corner_Cleanup')
    for i in range(setup.allOperations.count):
        op = setup.allOperations.item(i)
        if op.name not in targets: continue
        ok = "ok" if op.hasToolpath else "no"
        secs = cam.getMachiningTime(op,1.0,1.0,5.0).machiningTime if op.hasToolpath else 0.0
        print(f"  [{ok}] {op.name:25s} strategy={op.strategy:10s} cycle={secs:.1f}s")
