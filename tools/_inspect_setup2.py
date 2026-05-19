import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    setup = cam.setups.item(0)
    ps = setup.parameters
    # Print every param whose name contains 'stock' (case-insensitive).
    print(f"Setup params: {ps.count}")
    for i in range(ps.count):
        p = ps.item(i)
        if 'stock' in p.name.lower():
            print(f"  {p.name:35s} expr={getattr(p,'expression','?')!r}")
