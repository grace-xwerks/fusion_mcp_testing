import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    setup = cam.setups.item(0)
    print(f"Setup: {setup.name}")
    print(f"  operationType: {setup.operationType}")
    print(f"  models: {len(setup.models)} entries")
    for m in setup.models:
        print(f"    - {m.objectType}")
    # Setup parameters reveal stock mode
    ps = setup.parameters
    print(f"  parameters: {ps.count}")
    for nm in ('stockMode','stockOffsetMode','stockOffsetSides','stockOffsetTop',
              'stockOffsetBottom','stockFixedX','stockFixedY','stockFixedZ',
              'stockXMode','stockYMode','stockZMode'):
        p = ps.itemByName(nm)
        if p is not None:
            print(f"    {nm:20s} expr={getattr(p,'expression','?')!r}")
