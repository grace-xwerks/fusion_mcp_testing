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
        print("Switch to Manufacture workspace first.")
        return

    # Document tool library
    lib_mgr  = cam.documentToolLibrary
    print(f"Document tool library tool count: {lib_mgr.count}")

    for i in range(min(lib_mgr.count, 20)):   # cap at 20 for output sanity
        tool = lib_mgr.item(i)
        print(f"  [{i:2d}] {tool.description or tool.productId:40s}  "
              f"dia={tool.parameters.itemByName('tool_diameter').value*10:.2f} mm  "
              f"type={tool.typeName}")

    print(f"\n  (Showing up to 20 of {lib_mgr.count})")

    # Also report the Fusion sample library path for reference
    lib_urls = cam.libraryManager.toolLibraries.urlsByFolder(
        adsk.cam.LibraryFolders.LocalLibraryFolder
    )
    print(f"\nLocal library URLs ({lib_urls.count}):")
    for i in range(lib_urls.count):
        print(f"  {lib_urls.item(i).toString()}")
