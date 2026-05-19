"""
MCP_CAM_04_Add_a_Facing_operation_flatten_stock_top
===================================================
Group       : Manufacture
Script ID   : CAM-04
Description : Add a Facing operation (flatten stock top)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_04_Add_a_Facing_operation_flatten_stock_top

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

    # ---- Find or create a milling setup -----------------------------------------
    setup = None
    if cam.setups.count > 0:
        setup = cam.setups.item(0)
        print(f"Using existing setup: {setup.name}")
    else:
        bracket = None
        for b in cam.designRootOccurrence.bRepBodies:
            if b.name == 'Bracket':
                bracket = b
                break
        if not bracket:
            print("ERROR: No 'Bracket' body found — run the DESIGN scripts first.")
            return
        setup_in = cam.setups.createInput(adsk.cam.OperationTypes.MillingOperation)
        setup_in.models = [bracket]
        setup = cam.setups.add(setup_in)
        setup.name = 'BracketMillingSetup'
        print(f"Setup created: {setup.name}")

    # ---- Load Milling Tools (Metric) sample library -----------------------------
    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    lib_url = adsk.core.URL.create('systemlibraryroot://Samples/Milling Tools (Metric)')
    mill_lib = tl.toolLibraryAtURL(lib_url)
    if not mill_lib:
        print("ERROR: Could not load 'Milling Tools (Metric)' sample library.")
        return
    print(f"Sample mill library tools: {mill_lib.count}")

    # ---- Pick first face / flat mill with diameter >= 10 mm ---------------------
    chosen_tool = None
    for i in range(mill_lib.count):
        t = mill_lib.item(i)
        is_mill_param = t.parameters.itemByName('tool_isMill')
        if not is_mill_param or not is_mill_param.value.value:
            continue
        dia_param = t.parameters.itemByName('tool_diameter')
        if not dia_param:
            continue
        dia_mm = dia_param.value.value * 10
        if dia_mm < 10:
            continue
        desc = (t.description or '').lower()
        if 'face' in desc or 'flat' in desc:
            chosen_tool = t
            break

    if not chosen_tool:
        print("ERROR: No suitable face/flat mill (>=10 mm) found in sample library.")
        return

    dia_mm = chosen_tool.parameters.itemByName('tool_diameter').value.value * 10
    print(f"Tool selected: {chosen_tool.description}  Ø{dia_mm:.2f} mm")

    # ---- Create the 2D Facing operation -----------------------------------------
    op_input = setup.operations.createInput('face')
    op_input.tool = chosen_tool
    op = setup.operations.add(op_input)

    print(f"Operation added  : {op.name}")
    print(f"Tool description : {chosen_tool.description}")
    print(f"Op parameter count: {op.parameters.count}")
