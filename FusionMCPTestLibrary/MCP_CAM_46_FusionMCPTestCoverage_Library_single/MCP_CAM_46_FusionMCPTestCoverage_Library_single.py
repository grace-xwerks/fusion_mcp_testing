"""
MCP_CAM_46_FusionMCPTestCoverage_Library_single
===============================================
Group       : Manufacture
Script ID   : CAM-46
Description : FusionMCPTestCoverage Library — single-source tool inventory
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_46_FusionMCPTestCoverage_Library_single

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

def run(_context: str):
    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    url = adsk.core.URL.create('toollibraryroot://Local/FusionMCPTestCoverage')
    lib = tl.toolLibraryAtURL(url)
    if not lib:
        print("FusionMCPTestCoverage library not found.")
        print("Build it first by running tools/_build_coverage_lib.py via the")
        print("Fusion MCP, or copy the JSON from")
        print("  %APPDATA%\Autodesk\CAM360\libraries\Local\FusionMCPTestCoverage.json")
        return

    print(f"FusionMCPTestCoverage tools: {lib.count}")
    print()
    for i in range(lib.count):
        t = lib.item(i)
        p = t.parameters
        dia = p.itemByName('tool_diameter').value.value * 10
        tt  = p.itemByName('tool_type').value.value
        print(f"  D{dia:5.2f}mm  {tt:18s}  {t.description or t.productId}")
