import adsk.core, adsk.cam

NAMES = {'12_Thread_M6', '19_Pencil_Cleanup', '26_Corner_Cleanup'}

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    setup = cam.setups.item(0)
    n_before = setup.allOperations.count
    for i in range(n_before - 1, -1, -1):
        op = setup.allOperations.item(i)
        if op.name in NAMES:
            op.deleteMe()
    print(f"Removed {n_before - setup.allOperations.count} ops; remaining: {setup.allOperations.count}")
