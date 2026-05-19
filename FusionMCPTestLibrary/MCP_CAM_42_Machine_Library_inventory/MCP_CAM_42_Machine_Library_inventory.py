"""
MCP_CAM_42_Machine_Library_inventory
====================================
Group       : Manufacture
Script ID   : CAM-42
Description : Machine Library inventory
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_42_Machine_Library_inventory

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

def run(_context: str):
    ml = adsk.cam.CAMManager.get().libraryManager.machineLibrary
    print(f"machineLibrary: {ml}")
    for label in ('CloudLibraryLocation', 'Fusion360LibraryLocation',
                  'LocalLibraryLocation', 'HubLibraryLocation',
                  'OnlineSamplesLibraryLocation'):
        loc = getattr(adsk.cam.LibraryLocations, label, None)
        if loc is None: continue
        try:
            root = ml.urlByLocation(loc)
        except Exception as e:
            print(f"  {label:32s}  urlByLocation FAILED: {e}")
            continue
        if not root:
            print(f"  {label:32s}  (no root)")
            continue
        try:
            assets = ml.childAssetURLs(root)
        except Exception as e:
            print(f"  {label:32s}  childAssetURLs FAILED: {e}")
            continue
        # Bucket the URLs by their first path segment (manufacturer / vendor).
        buckets = {}
        for i in range(len(assets)):
            u = assets[i].toString()
            # system://VENDOR/Model.mch → VENDOR
            try:
                vendor = u.split('://', 1)[1].split('/', 1)[0]
            except Exception:
                vendor = '(unknown)'
            buckets[vendor] = buckets.get(vendor, 0) + 1
        print(f"  {label:32s}  total assets={len(assets)}  vendors={len(buckets)}")
        for vendor, n in sorted(buckets.items(), key=lambda kv: -kv[1])[:20]:
            print(f"      {n:4d}  {vendor}")
        if len(buckets) > 20:
            print(f"      ... +{len(buckets) - 20} more vendors")
