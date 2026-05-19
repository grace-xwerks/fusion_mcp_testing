import adsk.core, adsk.cam

def run(_context: str):
    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    lib = tl.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))
    # Tool types of interest
    interest_types = ['thread mill', 'tap']
    print(f"Library tools: {lib.count}")
    threads, taps, slots, flats_small = [], [], [], []
    for i in range(lib.count):
        t = lib.item(i)
        p = t.parameters
        tt_p = p.itemByName('tool_type')
        tt = tt_p.value.value if tt_p else ''
        dia = p.itemByName('tool_diameter').value.value * 10
        desc = t.description or ''
        if tt == 'thread mill':
            threads.append((dia, desc))
        if tt == 'tap right hand' or tt == 'tap left hand' or 'tap' in tt:
            taps.append((tt, dia, desc))
        if tt == 'slot mill':
            slots.append((dia, desc))
        if tt == 'flat end mill' and 5.5 <= dia <= 6.5:
            flats_small.append((dia, desc))
    print(f"\nthread mills ({len(threads)}):")
    for d, dsc in threads:
        print(f"  D{d:5.2f}mm  {dsc}")
    print(f"\ntap-like ({len(taps)}):")
    for tt, d, dsc in taps:
        print(f"  {tt:20s} D{d:5.2f}mm  {dsc}")
    print(f"\nslot mills ({len(slots)}):")
    for d, dsc in slots:
        print(f"  D{d:5.2f}mm  {dsc}")
    print(f"\n5.5-6.5mm flat end mills ({len(flats_small)}):")
    for d, dsc in flats_small:
        print(f"  D{d:5.2f}mm  {dsc}")
