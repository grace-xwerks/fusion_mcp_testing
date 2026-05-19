import adsk.core, adsk.cam

NAMES = {
    '7_Bore_M6_holes', '8_Circular_M6_holes', '9_Slot_Pocket',
    '10_Engrave_TopContour', '11_Trace_TopPerimeter', '12_Thread_M6'
}

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("No CAM."); return
    setup = cam.setups.item(0)
    # Walk backwards so indices stay valid as we delete.
    n = setup.allOperations.count
    deleted = []
    for i in range(n - 1, -1, -1):
        op = setup.allOperations.item(i)
        if op.name in NAMES:
            deleted.append(op.name)
            op.deleteMe()
    print(f"Deleted {len(deleted)} ops: {deleted}")
    print(f"Remaining ops: {setup.allOperations.count}")
