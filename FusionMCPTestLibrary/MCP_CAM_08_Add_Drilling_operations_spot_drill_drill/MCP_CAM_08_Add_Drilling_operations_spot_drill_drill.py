"""
MCP_CAM_08_Add_Drilling_operations_spot_drill_drill
===================================================
Group       : Manufacture
Script ID   : CAM-08
Description : Add Drilling operations (spot drill + drill)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_08_Add_Drilling_operations_spot_drill_drill

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return

    setup = cam.setups.item(0)

    # ── Load sample hole-making library (quirk #24) ────────────────────────
    tool_libs  = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    drill_url  = adsk.core.URL.create(
        'systemlibraryroot://Samples/Hole Making Tools (Metric)'
    )
    library = tool_libs.toolLibraryAtURL(drill_url)

    # ── Find a spot drill (description contains 'spot') ────────────────────
    spot = None
    drill = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        desc = (t.description or '').lower()
        is_drill = p.itemByName('tool_isDrill')
        if is_drill is None or not is_drill.value.value:
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if spot is None and ('spot' in desc or 'spotting' in desc) and 3.0 <= dia_mm <= 10.0:
            spot = t
            continue
        if drill is None and 'drill' in desc and 'spot' not in desc and abs(dia_mm - 6.0) < 0.3:
            drill = t

    # ── Spot drill operation ───────────────────────────────────────────────
    sd_input = setup.operations.createInput("drill")
    sd_input.displayName = "5a_SpotDrill"
    if spot is not None:
        sd_input.tool = spot
        print(f"Spot drill tool: {spot.description}  "
              f"Ø{spot.parameters.itemByName('tool_diameter').value.value*10:.2f} mm")
    else:
        print("No spot drill found in 'Hole Making Tools (Metric)'.")
        return

    sd_params = sd_input.parameters
    sd_params.itemByName("tolerance").expression = "0.02 mm"
    tip = sd_params.itemByName("tipDepth")
    if tip is not None:
        tip.expression = "1 mm"

    sd_op = setup.operations.add(sd_input)

    # Geometry: 4 cylindrical hole faces filtered by radius (M6 = 0.3 cm).
    # The 'holeFaces' parameter is a CadObjectParameterValue whose inner
    # .value is an assignable list of BRepFace. Be careful to filter:
    # the Bracket also has pocket-corner fillet faces (cylindrical, r=0.2 cm)
    # which would be drilled too if not excluded.
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    m6_cyls = [f for f in bracket.faces
               if isinstance(f.geometry, adsk.core.Cylinder)
               and abs(f.geometry.radius - 0.3) < 0.05]
    sd_op.parameters.itemByName('holeFaces').value.value = m6_cyls
    print(f"Spot drill op added: {sd_op.name}  strategy={sd_op.strategy}  "
          f"({len(m6_cyls)} holes)")

    # ── Through-drill operation ────────────────────────────────────────────
    dr_input = setup.operations.createInput("drill")
    dr_input.displayName = "5b_Drill_6mm_Through"
    if drill is not None:
        dr_input.tool = drill
        print(f"Drill tool: {drill.description}  "
              f"Ø{drill.parameters.itemByName('tool_diameter').value.value*10:.2f} mm")
    else:
        print("No 6 mm drill found in 'Hole Making Tools (Metric)'.")
        return

    dr_params = dr_input.parameters
    dr_params.itemByName("tolerance").expression = "0.02 mm"
    cycle = dr_params.itemByName("cycleType")
    if cycle is not None:
        cycle.expression = "'chip-breaking'"

    dr_op = setup.operations.add(dr_input)
    # Geometry: same 4 M6 corner holes (already filtered above).
    dr_op.parameters.itemByName('holeFaces').value.value = m6_cyls
    print(f"Drill op added: {dr_op.name}  strategy={dr_op.strategy}  "
          f"({len(m6_cyls)} holes)")
    print(f"Setup: {setup.name}")
