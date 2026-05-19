"""
MCP_CAM_02_Inspect_the_tool_library
===================================
Group       : Manufacture
Script ID   : CAM-02
Description : Inspect the tool library
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_02_Inspect_the_tool_library

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first (run CAM-01).")
        return

    # ---- 1. Document tool library ------------------------------------------------
    # A fresh design has no document-local tools; tools land here once you import
    # them from a sample/cloud library or add them via the Tool Library dialog.
    doc_lib = cam.documentToolLibrary
    print(f"Document tool library tool count: {doc_lib.count}")
    print("  (expected 0 for a fresh design — tools must be imported first)")

    # ---- 2. Walk every LibraryLocation -------------------------------------------
    # Per quirks #21/#22/#23: use CAMManager.libraryManager.toolLibraries,
    # urlByLocation (singular), and treat childAssetURLs as a SWIG URLVector
    # (len() / [i], NOT .count / .item(i)).
    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries

    locations = [
        ('CloudLibraryLocation',          adsk.cam.LibraryLocations.CloudLibraryLocation),
        ('ExternalLibraryLocation',       adsk.cam.LibraryLocations.ExternalLibraryLocation),
        ('Fusion360LibraryLocation',      adsk.cam.LibraryLocations.Fusion360LibraryLocation),
        ('HubLibraryLocation',            adsk.cam.LibraryLocations.HubLibraryLocation),
        ('LocalLibraryLocation',          adsk.cam.LibraryLocations.LocalLibraryLocation),
        ('NetworkLibraryLocation',        adsk.cam.LibraryLocations.NetworkLibraryLocation),
        ('OnlineSamplesLibraryLocation',  adsk.cam.LibraryLocations.OnlineSamplesLibraryLocation),
    ]

    print("\nLibrary locations:")
    for label, loc in locations:
        root = tl.urlByLocation(loc)
        if not root:
            print(f"  {label:32s}  (no root URL)")
            continue
        assets = tl.childAssetURLs(root)
        print(f"  {label:32s}  root={root.toString()}  assets={len(assets)}")
        for i in range(len(assets)):
            print(f"      [{i}] {assets[i].toString()}")

    # ---- 3. Inspect the two real Fusion sample libraries -------------------------
    # Quirk #24: 'Cutting Tools (Metric)' has only 3 jet-cutter entries; the real
    # mill/drill libraries live under different names.
    sample_urls = [
        'systemlibraryroot://Samples/Milling Tools (Metric)',
        'systemlibraryroot://Samples/Hole Making Tools (Metric)',
    ]

    for sample_url_str in sample_urls:
        print(f"\nLibrary: {sample_url_str}")
        sample_url = adsk.core.URL.create(sample_url_str)
        lib = tl.toolLibraryAtURL(sample_url)
        if not lib:
            print("  (could not load)")
            continue
        # ToolLibrary IS a Collection — use .count / .item(i) here (quirk #22).
        print(f"  tool count: {lib.count}")
        for i in range(min(5, lib.count)):
            tool = lib.item(i)
            desc = tool.description or tool.productId or '(no description)'
            dia_param = tool.parameters.itemByName('tool_diameter')
            dia_mm = dia_param.value.value * 10 if dia_param else float('nan')
            print(f"    [{i}] {desc[:50]:50s}  Ø{dia_mm:.2f} mm")
