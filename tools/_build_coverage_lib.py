"""Build a single Local tool library `FusionMCPTestCoverage` containing every
tool referenced by the CAM tests. Useful so the whole test suite can run from
one library without chasing tools across Cloud + multiple Fusion360 samples.

Strategy: enumerate the source libraries below, pick the tools matching each
spec, write them to a new ToolLibrary at toollibraryroot://Local/FusionMCPTestCoverage.
"""
import adsk.core, adsk.cam

# (source_url, type_match_fn, dia_match_fn (mm), display_label) — first match wins.
SPECS = [
    # (label, source_url, tool_type, dia range in mm, optional description token)
    ('flat6',  'systemlibraryroot://Samples/Milling Tools (Metric)',  'flat end mill',     (5.5, 6.5), None),
    ('flat4',  'systemlibraryroot://Samples/Milling Tools (Metric)',  'flat end mill',     (3.5, 4.5), None),
    ('flat10', 'systemlibraryroot://Samples/Milling Tools (Metric)',  'flat end mill',     (9.5, 11.0), None),
    ('ball6',  'systemlibraryroot://Samples/Milling Tools (Metric)',  'ball end mill',     (5.5, 6.5), None),
    ('ball2',  'systemlibraryroot://Samples/Tutorial Tools (Metric)', 'ball end mill',     (1.5, 2.5), None),
    ('chamfer10','systemlibraryroot://Samples/Milling Tools (Metric)','chamfer mill',      (9.0, 11.0), None),
    ('slot10', 'systemlibraryroot://Samples/Milling Tools (Metric)',  'slot mill',         (9.5, 11.0), None),
    ('threadmill_inch', 'systemlibraryroot://Samples/Milling Tools (Inch)', 'thread mill', (3.5, 5.5), None),
    ('drill6', 'systemlibraryroot://Samples/Hole Making Tools (Metric)', 'drill',          (5.5, 6.5), None),
    ('spotdrill','systemlibraryroot://Samples/Hole Making Tools (Metric)', 'spot drill',   (3.0, 10.0), None),
    ('probe6', 'systemlibraryroot://Samples/Probes',                  'probe',             (5.5, 6.5), None),
    ('tap_m6', 'systemlibraryroot://Samples/Hole Making Tools (Metric)', 'tap right hand', (5.5, 6.5), None),
]

# Where the new library lives
TARGET_URL = 'toollibraryroot://Local/FusionMCPTestCoverage'


def run(_context: str):
    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries

    # ── Resolve every source tool ────────────────────────────────────────────
    chosen = []
    cache = {}
    for label, src, type_name, (lo, hi), desc_token in SPECS:
        if src not in cache:
            cache[src] = tl.toolLibraryAtURL(adsk.core.URL.create(src))
        lib = cache[src]
        if not lib:
            print(f"  [{label}] source library not loaded: {src}")
            continue
        match = None
        for i in range(lib.count):
            t = lib.item(i); p = t.parameters
            tt = p.itemByName('tool_type')
            if not tt or tt.value.value != type_name: continue
            d = p.itemByName('tool_diameter').value.value * 10
            if not (lo <= d <= hi): continue
            if desc_token and desc_token.lower() not in (t.description or '').lower():
                continue
            match = (t, d); break
        if match is None:
            print(f"  [{label}] NO MATCH  type={type_name!r} dia={lo}-{hi}mm in {src}")
            continue
        chosen.append((label, src, match[0], match[1]))
        print(f"  [{label}] D{match[1]:5.2f}mm  {match[0].description or match[0].productId}  ← {src.split('/')[-1]}")

    if not chosen:
        print("Nothing chosen — aborting library build."); return

    # ── Create a fresh empty target library ─────────────────────────────────
    target_url = adsk.core.URL.create(TARGET_URL)
    target_lib = adsk.cam.ToolLibrary.createEmpty()
    print(f"\nCreated empty library; adding {len(chosen)} tools...")

    # ── Add each tool to the target library ─────────────────────────────────
    added = 0
    for label, src, t, d in chosen:
        try:
            target_lib.add(t)
            added += 1
        except Exception as e:
            print(f"  [{label}] add FAILED: {e}")

    print(f"Added {added} of {len(chosen)} tools.")

    # ── Persist the library so it survives session restart ──────────────────
    # updateToolLibrary requires the library file to already exist. For a
    # brand-new local library, write the JSON directly to the on-disk path
    # that Fusion treats as toollibraryroot://Local/<name>.json — that is
    # %APPDATA%\Autodesk\Fusion 360 CAM\Tools\<name>.json (or the equivalent
    # tool-root reported by the libraryManager).
    # Fusion 2703.x maps toollibraryroot://Local/ to
    # %APPDATA%\Autodesk\CAM360\libraries\Local\.
    import os, pathlib
    target_dir = pathlib.Path(os.environ['APPDATA']) / 'Autodesk' / 'CAM360' / 'libraries' / 'Local'
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / 'FusionMCPTestCoverage.json'
    out_path.write_text(target_lib.toJson(), encoding='utf-8')
    print(f"Wrote library JSON to: {out_path}")

    # ── Read back via the ToolLibraries API to confirm Fusion sees it ──────
    try:
        final = tl.toolLibraryAtURL(target_url)
        if final is None:
            print("(toolLibraryAtURL returned None — Fusion may need a session "
                  "restart to pick up the new file.)")
        else:
            print(f"\nFinal contents ({final.count} tools):")
            for i in range(final.count):
                t = final.item(i)
                d = t.parameters.itemByName('tool_diameter').value.value * 10
                tt = t.parameters.itemByName('tool_type').value.value
                print(f"  D{d:5.2f}mm  {tt:18s}  {t.description or t.productId}")
    except Exception as e:
        print(f"verify-read failed: {e}")

    # ── Read back and confirm ───────────────────────────────────────────────
    try:
        final = tl.toolLibraryAtURL(target_url)
        print(f"\nFinal contents ({final.count} tools):")
        for i in range(final.count):
            t = final.item(i)
            d = t.parameters.itemByName('tool_diameter').value.value * 10
            tt = t.parameters.itemByName('tool_type').value.value
            print(f"  D{d:5.2f}mm  {tt:18s}  {t.description or t.productId}")
    except Exception as e:
        print(f"verify-read failed: {e}")
