"""
MCP_CAM_11_Post_process_to_G_code_Haas_simulator
================================================
Group       : Manufacture
Script ID   : CAM-11
Description : Post-process to G-code (Haas simulator — per CNC Fundamentals course)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_11_Post_process_to_G_code_Haas_simulator

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam
import os

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return

    setup = cam.setups.item(0)

    # Output path — use Fusion's temp folder
    output_folder = os.path.expanduser("~/Desktop")
    output_file   = "bracket_op1"

    # Find a Haas post (common in Autodesk library — aligns with CNC Fundamentals course)
    post_url = None
    post_libs = cam.libraryManager.postLibraries.urlsByFolder(
        adsk.cam.LibraryFolders.LocalLibraryFolder
    )
    for i in range(post_libs.count):
        url_str = post_libs.item(i).toString()
        if "haas" in url_str.lower():
            post_url = post_libs.item(i)
            print(f"Post processor: {url_str}")
            break

    if not post_url:
        print("Haas post not found in local library.")
        print("Available post libraries:")
        for i in range(post_libs.count):
            print(f"  {post_libs.item(i).toString()}")
        return

    post_input                    = adsk.cam.PostProcessInput.create(
        output_file, post_url, output_folder,
        adsk.cam.PostProcessOutputUnitOptions.DocumentUnitsOutput
    )
    post_input.isOpenInEditor = False

    ops = adsk.core.ObjectCollection.create()
    for i in range(setup.allOperations.count):
        if setup.allOperations.item(i).hasToolpath:
            ops.add(setup.allOperations.item(i))

    if ops.count == 0:
        print("No operations with toolpaths. Run CAM-10 first to generate.")
        return

    cam.postProcess(ops, post_input)
    print(f"G-code posted to: {output_folder}/{output_file}.nc")
    print("Open that file to verify Haas G/M code output.")
