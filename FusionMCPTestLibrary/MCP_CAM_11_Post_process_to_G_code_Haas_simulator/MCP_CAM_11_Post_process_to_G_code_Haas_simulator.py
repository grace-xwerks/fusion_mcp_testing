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

    # Discover post folders
    generic_folder  = cam.genericPostFolder
    personal_folder = cam.personalPostFolder
    print(f"Generic post folder : {generic_folder}")
    print(f"Personal post folder: {personal_folder}")

    # Prefer a Haas post in the generic library
    candidate_paths = [
        os.path.join(generic_folder, 'haas.cps'),
        os.path.join(generic_folder, 'haas next generation.cps'),
        os.path.join(personal_folder, 'haas.cps'),
    ]
    post_path = next((p for p in candidate_paths if os.path.isfile(p)), None)

    if not post_path:
        print("No Haas post found in expected locations. Candidates checked:")
        for p in candidate_paths:
            print(f"  {p}")
        print("\nGeneric post folder contents:")
        if os.path.isdir(generic_folder):
            for fn in sorted(os.listdir(generic_folder))[:50]:
                print(f"  {fn}")
        # TODO(refactor): scan subfolders / personal folder more thoroughly,
        # or accept a post path via script arg.
        return

    print(f"Post processor: {post_path}")

    output_folder = cam.temporaryFolder
    # Haas posts treat programName as a numeric program number (O#####).
    # A non-numeric string raises 'Program number NaN is out of range'.
    program_name  = "1001"

    pp_input = adsk.cam.PostProcessInput.create(
        program_name,
        post_path,
        output_folder,
        adsk.cam.PostOutputUnitOptions.DocumentUnitsOutput,
    )
    pp_input.programComment   = "Bracket"
    pp_input.isOpenInEditor   = False

    # Post the whole setup (new API accepts setup/operation/program directly)
    ok = cam.postProcess(setup, pp_input)
    print(f"postProcess returned: {ok}")

    # Locate the produced .nc file
    nc_path = None
    if os.path.isdir(output_folder):
        for fn in os.listdir(output_folder):
            if fn.lower().startswith(program_name.lower()) and fn.lower().endswith(('.nc', '.tap', '.cnc')):
                nc_path = os.path.join(output_folder, fn)
                break

    if not nc_path:
        print(f"Could not locate output .nc under {output_folder}")
        return

    print(f"G-code output : {nc_path}")
    with open(nc_path, 'r') as f:
        lines = f.readlines()
    print(f"Line count    : {len(lines)}")
    print("--- first 5 lines ---")
    for line in lines[:5]:
        print(line.rstrip())
    print("--- last 5 lines ---")
    for line in lines[-5:]:
        print(line.rstrip())
