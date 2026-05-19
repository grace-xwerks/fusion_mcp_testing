"""
MCP_CAM_14_Manager_library_post_inventory_dump
==============================================
Group       : Manufacture
Script ID   : CAM-14
Description : Manager / library / post inventory dump
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_14_Manager_library_post_inventory_dump

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam
import os

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first (run CAM-01).")
        return

    mgr = adsk.cam.CAMManager.get()
    print(f"CAMManager: {mgr}")

    # ── libraryManager surface ────────────────────────────────────────────
    lm = mgr.libraryManager
    print(f"\nlibraryManager attrs (non-callable):")
    for n in sorted(dir(lm)):
        if n.startswith('_'):
            continue
        try:
            attr = getattr(lm, n)
        except Exception:
            continue
        if callable(attr):
            continue
        print(f"  {n} = {attr!r}")

    # ── Walk every tool library URL and report tool counts ────────────────
    tl = lm.toolLibraries
    print("\nTool library locations and child assets:")
    for label in ('CloudLibraryLocation', 'ExternalLibraryLocation',
                  'Fusion360LibraryLocation', 'HubLibraryLocation',
                  'LocalLibraryLocation', 'NetworkLibraryLocation',
                  'OnlineSamplesLibraryLocation'):
        loc = getattr(adsk.cam.LibraryLocations, label, None)
        if loc is None:
            continue
        root = tl.urlByLocation(loc)
        if not root:
            print(f"  {label:32s}  (no root)")
            continue
        assets = tl.childAssetURLs(root)
        print(f"  {label:32s}  assets={len(assets)}")
        for i in range(len(assets)):
            url = assets[i]
            try:
                lib = tl.toolLibraryAtURL(url)
                cnt = lib.count if lib else 0
            except Exception:
                cnt = -1
            print(f"      tools={cnt:4d}  {url.toString()}")

    # ── Post library manager (if present) ─────────────────────────────────
    plm = getattr(lm, 'postLibrary', None) or getattr(mgr, 'postLibrary', None)
    print(f"\npostLibrary: {plm}")

    # ── Post-processor folders + a sample of their .cps contents ──────────
    print(f"\nGeneric post folder : {cam.genericPostFolder}")
    print(f"Personal post folder: {cam.personalPostFolder}")
    for folder in (cam.genericPostFolder, cam.personalPostFolder):
        if not folder or not os.path.isdir(folder):
            continue
        cps = sorted(f for f in os.listdir(folder) if f.lower().endswith('.cps'))
        print(f"\n  {folder}  .cps files: {len(cps)}")
        for f in cps[:25]:
            print(f"    {f}")
        if len(cps) > 25:
            print(f"    ... +{len(cps) - 25} more")

    # ── Machine library (5-axis kinematics etc.) ──────────────────────────
    ml = getattr(lm, 'machineLibrary', None)
    print(f"\nmachineLibrary: {ml}")
    if ml is not None:
        for label in ('CloudLibraryLocation', 'Fusion360LibraryLocation',
                      'LocalLibraryLocation', 'OnlineSamplesLibraryLocation'):
            loc = getattr(adsk.cam.LibraryLocations, label, None)
            if loc is None:
                continue
            try:
                root = ml.urlByLocation(loc)
            except Exception:
                continue
            if not root:
                continue
            try:
                assets = ml.childAssetURLs(root)
            except Exception:
                assets = []
            print(f"  {label:32s}  machine-assets={len(assets)}")
            for i in range(min(len(assets), 10)):
                print(f"      {assets[i].toString()}")

    # ── NC programs (post-process targets) ────────────────────────────────
    nc_progs = getattr(cam, 'ncPrograms', None)
    print(f"\nncPrograms: {nc_progs}")
    if nc_progs is not None:
        print(f"  count = {nc_progs.count}")
        for i in range(nc_progs.count):
            p = nc_progs.item(i)
            print(f"  [{i}] name={p.name!r}  output={getattr(p, 'outputFolder', '?')}")

    # ── Manufacturing model / stock surface ───────────────────────────────
    mm = getattr(cam, 'manufacturingModels', None)
    print(f"\nmanufacturingModels: {mm}")
    if mm is not None:
        print(f"  count = {mm.count}")
        for i in range(mm.count):
            m = mm.item(i)
            print(f"  [{i}] {m.name}")
