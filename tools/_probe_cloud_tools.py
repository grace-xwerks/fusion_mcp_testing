"""Cross-library tool inventory — look for thread mills, probes, small balls,
   turning tools, taps. Sums across Cloud + Local + Fusion360 sample libraries."""
import adsk.core, adsk.cam

WANT = (
    ('thread_mill_le6mm', lambda t: t == 'thread mill', lambda d: d < 6.0),
    ('thread_mill_any',   lambda t: t == 'thread mill', lambda d: True),
    ('tap',               lambda t: 'tap' in t,        lambda d: True),
    ('ball_le_3mm',       lambda t: t == 'ball end mill', lambda d: d <= 3.0),
    ('chamfer_mill',      lambda t: t == 'chamfer mill', lambda d: True),
    ('probe',             lambda t: t == 'probe',       lambda d: True),
    ('turning_general',   lambda t: t == 'turning general', lambda d: True),
    ('turning_grooving',  lambda t: t == 'turning grooving', lambda d: True),
    ('turning_threading', lambda t: t == 'turning threading', lambda d: True),
    ('slot_mill',         lambda t: t == 'slot mill',   lambda d: True),
    ('lollipop',          lambda t: t == 'lollipop mill', lambda d: True),
    ('dovetail',          lambda t: t == 'dovetail mill', lambda d: True),
)

def run(_context: str):
    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    locs = [
        ('Cloud',    adsk.cam.LibraryLocations.CloudLibraryLocation),
        ('Fusion360', adsk.cam.LibraryLocations.Fusion360LibraryLocation),
        ('Local',    adsk.cam.LibraryLocations.LocalLibraryLocation),
    ]
    # Aggregate counts per category per library
    totals = {}     # (category, location_label) -> count
    by_location = {}  # location_label -> {category: [(url, dia, desc)]}

    for label, loc in locs:
        root = tl.urlByLocation(loc)
        if not root:
            continue
        assets = tl.childAssetURLs(root)
        for ai in range(len(assets)):
            url = assets[ai]
            try:
                lib = tl.toolLibraryAtURL(url)
            except Exception:
                continue
            if not lib or lib.count == 0:
                continue
            for ti in range(lib.count):
                t = lib.item(ti)
                p = t.parameters
                tt_p = p.itemByName('tool_type')
                if not tt_p: continue
                tt = tt_p.value.value
                dia_p = p.itemByName('tool_diameter')
                dia_mm = (dia_p.value.value * 10) if dia_p else 0.0
                desc = (t.description or t.productId or '')[:60]
                for cat, type_match, dia_match in WANT:
                    if type_match(tt) and dia_match(dia_mm):
                        key = (cat, label)
                        totals[key] = totals.get(key, 0) + 1
                        by_location.setdefault(label, {}).setdefault(cat, []).append(
                            (url.toString(), dia_mm, desc, tt))
                        break  # first matching category wins

    # Summary table
    print(f"{'category':22s} {'Cloud':>8s} {'F360':>8s} {'Local':>8s}")
    cats = [c for c, _, _ in WANT]
    for cat in cats:
        c_c = totals.get((cat, 'Cloud'), 0)
        c_f = totals.get((cat, 'Fusion360'), 0)
        c_l = totals.get((cat, 'Local'), 0)
        print(f"  {cat:20s} {c_c:8d} {c_f:8d} {c_l:8d}")

    # Show first 5 matches per priority category
    show = ('thread_mill_le6mm', 'ball_le_3mm', 'probe',
            'turning_general', 'turning_threading', 'tap')
    for cat in show:
        print(f"\n=== {cat} ===")
        for label in ('Cloud', 'Fusion360', 'Local'):
            entries = by_location.get(label, {}).get(cat, [])
            if not entries: continue
            print(f"  [{label}]")
            for url, d, desc, tt in entries[:5]:
                lib_short = url.split('/')[-1][:40]
                print(f"    Ø{d:5.2f}mm  {tt:18s}  {desc:40s}  ({lib_short})")
