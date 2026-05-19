"""
MCP_CAM_40_CAM_Template_Library_inventory
=========================================
Group       : Manufacture
Script ID   : CAM-40
Description : CAM Template Library inventory
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_40_CAM_Template_Library_inventory

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

def run(_context: str):
    tl = adsk.cam.CAMManager.get().libraryManager.templateLibrary
    print(f"templateLibrary: {tl}")
    for label in ('CloudLibraryLocation', 'Fusion360LibraryLocation',
                  'LocalLibraryLocation', 'HubLibraryLocation',
                  'OnlineSamplesLibraryLocation'):
        loc = getattr(adsk.cam.LibraryLocations, label, None)
        if loc is None: continue
        try:
            root = tl.urlByLocation(loc)
        except Exception as e:
            print(f"  {label:32s}  urlByLocation FAILED: {e}")
            continue
        if not root:
            print(f"  {label:32s}  (no root)")
            continue
        try:
            assets = tl.childAssetURLs(root)
        except Exception as e:
            print(f"  {label:32s}  childAssetURLs FAILED: {e}")
            continue
        print(f"  {label:32s}  assets={len(assets)}")
        for i in range(min(len(assets), 20)):
            print(f"      {assets[i].toString()}")
        if len(assets) > 20:
            print(f"      ... +{len(assets) - 20} more")
