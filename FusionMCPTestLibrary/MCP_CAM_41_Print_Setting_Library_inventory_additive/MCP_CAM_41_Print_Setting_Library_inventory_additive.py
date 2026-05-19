"""
MCP_CAM_41_Print_Setting_Library_inventory_additive
===================================================
Group       : Manufacture
Script ID   : CAM-41
Description : Print Setting Library inventory (additive)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_41_Print_Setting_Library_inventory_additive

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

def run(_context: str):
    psl = adsk.cam.CAMManager.get().libraryManager.printSettingLibrary
    print(f"printSettingLibrary: {psl}")
    for label in ('CloudLibraryLocation', 'Fusion360LibraryLocation',
                  'LocalLibraryLocation', 'HubLibraryLocation',
                  'OnlineSamplesLibraryLocation'):
        loc = getattr(adsk.cam.LibraryLocations, label, None)
        if loc is None: continue
        try:
            root = psl.urlByLocation(loc)
        except Exception as e:
            print(f"  {label:32s}  urlByLocation FAILED: {e}")
            continue
        if not root:
            print(f"  {label:32s}  (no root)")
            continue
        try:
            assets = psl.childAssetURLs(root)
        except Exception as e:
            print(f"  {label:32s}  childAssetURLs FAILED: {e}")
            continue
        print(f"  {label:32s}  assets={len(assets)}")
        for i in range(min(len(assets), 20)):
            print(f"      {assets[i].toString()}")
        if len(assets) > 20:
            print(f"      ... +{len(assets) - 20} more")
