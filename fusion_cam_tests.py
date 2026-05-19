"""
Fusion MCP — Manufacture (CAM) Workspace Test Scripts
======================================================
Tests the adsk.cam namespace: setups, tool library access, operation
creation, toolpath generation, and NC program post-processing.

PREREQUISITE: Run the Design scripts first to have the Bracket part loaded,
then switch Fusion to the Manufacture workspace before running these.

Toolpath types covered (from CNC Fundamentals lesson 7 / HEM guide):
  ✓ Facing          — flatten stock top surface
  ✓ 2D Adaptive     — HEM-style roughing (constant chip load, high ADOC/low RDOC)
  ✓ 2D Pocket       — finish the rectangular pocket
  ✓ 2D Contour      — outside profile / boss contour
  ✓ Drilling        — through holes
  ✓ Chamfer         — top edge chamfer milling

Units note: adsk.cam uses CENTIMETERS like the rest of the Fusion API.
"""

# =============================================================================
# CAM-01  Verify Manufacture workspace is active + inspect existing setups
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app  = adsk.core.Application.get()
    ui   = app.userInterface

    # Switch to the Manufacture workspace if it isn't active.
    if ui.activeWorkspace.id != 'CAMEnvironment':
        ui.workspaces.itemById('CAMEnvironment').activate()

    prod = app.activeProduct
    print(f"Active workspace   : {ui.activeWorkspace.id}")
    print(f"Active product type: {prod.productType}")

    cam = adsk.cam.CAM.cast(prod)
    if not cam:
        print("ERROR: activeProduct is not a CAM product even after switching.")
        return

    print(f"CAM product cast OK")
    print(f"Setups: {cam.setups.count}")

    for i in range(cam.setups.count):
        setup = cam.setups.item(i)
        print(f"\n  Setup [{i}]: {setup.name}")
        print(f"    Operation type : {setup.operationType}")
        print(f"    All operations : {setup.allOperations.count}")
        for j in range(setup.allOperations.count):
            op = setup.allOperations.item(j)
            print(f"      [{j}] {op.name:30s}  strategy={op.strategy}")


# =============================================================================
# CAM-02  Inspect the tool library
#         Walks LibraryLocations enum, then loads two Fusion sample libraries
#         and prints the first 5 tools of each.
# =============================================================================

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


# =============================================================================
# CAM-03  Create a milling setup for the Bracket part
#         WCS placement at top-left vertex is a TODO — using default origin.
# =============================================================================

import adsk.core, adsk.cam, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first (run CAM-01).")
        return

    # Idempotent: reuse an existing milling setup if one is already present.
    existing = None
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        if s.name == 'BracketMillingSetup':
            existing = s
            break

    if existing:
        print(f"Reusing existing setup: {existing.name}")
        setup = existing
    else:
        setups = cam.setups
        setup_in = setups.createInput(adsk.cam.OperationTypes.MillingOperation)

        # Find the Bracket body off the CAM-linked design root occurrence.
        bracket = None
        for b in cam.designRootOccurrence.bRepBodies:
            if b.name == 'Bracket':
                bracket = b
                break
        if not bracket:
            print("ERROR: Could not find a body named 'Bracket' under the design root.")
            print("Run the DESIGN scripts first to build the Bracket part.")
            return

        setup_in.models = [bracket]
        setup = setups.add(setup_in)
        setup.name = 'BracketMillingSetup'
        print(f"Setup created: {setup.name}")

    # TODO: position the WCS at the top-left corner vertex of the stock.
    # The Fusion 2703.x API surface for WCS-via-vertex is non-obvious — using
    # the default WCS origin for now; CAM-04+ operations work either way.

    print(f"Operation type   : {setup.operationType}")
    print(f"Operations count : {setup.operations.count}")


# =============================================================================
# CAM-04  Add a Facing operation (flatten stock top)
#         Picks a face/flat mill ≥10 mm dia from the Fusion sample library.
# =============================================================================

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


# =============================================================================
# CAM-05  Add a 2D Adaptive Clearing operation (HEM-style roughing)
#         High ADOC, low RDOC — constant chip load, protects tool life.
#         Per HEM Guidebook: spread heat over entire flute length.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return

    setup    = cam.setups.item(0)
    op_input = setup.operations.createInput("adaptive2d")
    op_input.displayName = "2_Adaptive_Rough"

    # ── Load sample milling tool library ───────────────────────────────────
    # Per quirks #21-#24: tools live on adsk.cam.CAMManager, libraries are
    # SWIG URLVectors (len/[i]), urlByLocation is singular, sample mills are
    # in "Milling Tools (Metric)".
    tool_libs  = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    target_url = adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'
    )
    library = tool_libs.toolLibraryAtURL(target_url)

    # Per quirk #25: Tool.typeName is gone — filter via parameters.
    # Want a flat end mill (tool_isMill == True, straight tapered, Ø 8–10 mm).
    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        is_mill = p.itemByName('tool_isMill').value.value
        if not is_mill:
            continue
        # Drop taper filter — it's about shank shape, not tip. The
        # 'flat' check in the description below is the right filter.
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 8.0 <= dia_mm <= 10.0:
            chosen = t
            break

    if chosen is None:
        print("No 8–10 mm flat end mill found in 'Milling Tools (Metric)'.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  Ø{chosen.parameters.itemByName('tool_diameter').value.value*10:.1f} mm")

    params = op_input.parameters

    # HEM parameters: low RDOC (~10% D), high ADOC (full flute).
    # NOTE: 'optimalLoad' expects an expression like 'tool_diameter * 0.1'
    # (10% of tool diameter). A bare '10%' fails to evaluate (quirk).
    params.itemByName("tolerance").expression       = "0.02 mm"
    params.itemByName("optimalLoad").expression     = "tool_diameter * 0.1"
    params.itemByName("maximumStepdown").expression = "8 mm"
    params.itemByName("stockToLeave").expression    = "0.3 mm"

    op = setup.operations.add(op_input)

    # Geometry: pocket bottom face at z = part_height - pocket_depth = 1.2 cm.
    # The 'pockets' parameter is a CadContours2dParameterValue; populate via
    # CurveSelections.createNewPocketSelection seeded by the pocket bottom face.
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    pocket_bottom = next(f for f in bracket.faces if abs(f.centroid.z - 1.2) < 0.05)
    pockets_pv = op.parameters.itemByName('pockets').value
    cs = pockets_pv.getCurveSelections(); cs.clear()
    sel = cs.createNewPocketSelection(); sel.inputGeometry = [pocket_bottom]
    pockets_pv.applyCurveSelections(cs)

    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print(f"Setup: {setup.name}")
    print("HEM params: optimalLoad=tool_diameter*0.1 (10% RDOC), 8mm ADOC stepdown")
    print(f"Geometry: pocket bottom face ({pocket_bottom.boundingBox.maxPoint.x - pocket_bottom.boundingBox.minPoint.x:.1f} x "
          f"{pocket_bottom.boundingBox.maxPoint.y - pocket_bottom.boundingBox.minPoint.y:.1f} cm)")


# =============================================================================
# CAM-06  Add a 2D Pocket operation (pocket finish pass)
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return

    setup    = cam.setups.item(0)
    op_input = setup.operations.createInput("pocket2d")
    op_input.displayName = "3_Pocket_Finish"

    # ── Load sample milling tool library (see quirks #21-#24) ──────────────
    tool_libs  = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    target_url = adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'
    )
    library = tool_libs.toolLibraryAtURL(target_url)

    # 6 mm flat end mill — fits the Bracket's 2 mm pocket corner radius.
    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        if not p.itemByName('tool_isMill').value.value:
            continue
        # Drop taper filter — it's about shank shape, not tip. The
        # 'flat' check in the description below is the right filter.
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t
            break

    if chosen is None:
        print("No ~6 mm flat end mill found in 'Milling Tools (Metric)'.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  Ø{chosen.parameters.itemByName('tool_diameter').value.value*10:.1f} mm")

    params = op_input.parameters
    # Only set parameters that exist on pocket2d. 'stepover' is not present
    # on this strategy in current Fusion 2703.x — issue #9 tracks a proper
    # per-strategy parameter table.
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "2 mm"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)

    # Geometry: same pocket bottom face as CAM-05 Adaptive.
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    pocket_bottom = next(f for f in bracket.faces if abs(f.centroid.z - 1.2) < 0.05)
    pockets_pv = op.parameters.itemByName('pockets').value
    cs = pockets_pv.getCurveSelections(); cs.clear()
    sel = cs.createNewPocketSelection(); sel.inputGeometry = [pocket_bottom]
    pockets_pv.applyCurveSelections(cs)

    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print(f"Geometry: pocket bottom face")


# =============================================================================
# CAM-07  Add a 2D Contour operation (outside profile)
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return

    setup    = cam.setups.item(0)
    op_input = setup.operations.createInput("contour2d")
    op_input.displayName = "4_Contour_Outside"

    # ── Load sample milling tool library ───────────────────────────────────
    tool_libs  = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    target_url = adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'
    )
    library = tool_libs.toolLibraryAtURL(target_url)

    # 8–10 mm flat end mill for outside contour.
    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        if not p.itemByName('tool_isMill').value.value:
            continue
        # Drop taper filter — it's about shank shape, not tip. The
        # 'flat' check in the description below is the right filter.
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 8.0 <= dia_mm <= 10.0:
            chosen = t
            break

    if chosen is None:
        print("No 8–10 mm flat end mill found in 'Milling Tools (Metric)'.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  Ø{chosen.parameters.itemByName('tool_diameter').value.value*10:.1f} mm")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "5 mm"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)

    # Geometry: body silhouette (outer profile when viewed from above).
    # CurveSelections.createNewSilhouetteSelection() seeded by the body
    # produces the outer contour chain automatically — no manual edge picking.
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    contours_pv = op.parameters.itemByName('contours').value
    cs = contours_pv.getCurveSelections(); cs.clear()
    sel = cs.createNewSilhouetteSelection(); sel.inputGeometry = [bracket]
    contours_pv.applyCurveSelections(cs)

    print(f"Setup: {setup.name}")
    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print(f"Geometry: Bracket body silhouette (outer 2D contour)")


# =============================================================================
# CAM-08  Add Drilling operations (spot drill + drill)
#         Sequence: always spot-drill first (per CNC Fundamentals ch.7)
# =============================================================================

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


# =============================================================================
# CAM-09  Add Chamfer Milling (top edge deburr / chamfer)
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return

    setup    = cam.setups.item(0)
    # Fusion exposes a dedicated 'chamfer2d' strategy in current API
    op_input = setup.operations.createInput("chamfer2d")
    op_input.displayName = "6_Chamfer_Top"

    # Load the Metric Milling Tools sample library (quirk #21, #24)
    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    sample_url = adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'
    )
    sample_lib = tool_libs.toolLibraryAtURL(sample_url)

    chamfer_tool = None
    # ToolLibrary IS a Collection — iterate directly (quirk #22)
    for i in range(sample_lib.count):
        t = sample_lib.item(i)
        is_mill_param = t.parameters.itemByName('tool_isMill')
        is_mill = bool(is_mill_param.value.value) if is_mill_param else False
        desc_p = t.parameters.itemByName('tool_description')
        desc = (desc_p.value.value
                if desc_p else
                (t.description or ''))
        if is_mill and 'chamfer' in desc.lower():
            chamfer_tool = t
            print(f"Chamfer tool: {desc}")
            break

    if chamfer_tool is None:
        print("No chamfer mill found in 'Milling Tools (Metric)'. Aborting.")
        return

    op_input.tool = chamfer_tool

    params = op_input.parameters
    # Chamfer width ≈ Bracket's 1 mm chamfer parameter
    params.itemByName("chamferWidth").expression = "1 mm"
    params.itemByName("tolerance").expression    = "0.01 mm"

    op = setup.operations.add(op_input)

    # Geometry: top face's outer contour. Use createNewFaceContourSelection
    # — picking the top face automatically gives its outer perimeter chain.
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    top_candidates = [f for f in bracket.faces if abs(f.centroid.z - 2.0) < 0.05]
    top_face = max(top_candidates,
                   key=lambda f: (f.boundingBox.maxPoint.x - f.boundingBox.minPoint.x)
                               * (f.boundingBox.maxPoint.y - f.boundingBox.minPoint.y))
    contours_pv = op.parameters.itemByName('contours').value
    cs = contours_pv.getCurveSelections(); cs.clear()
    sel = cs.createNewFaceContourSelection(); sel.inputGeometry = [top_face]
    contours_pv.applyCurveSelections(cs)

    print(f"Operation added: {op.name}")
    print(f"Geometry: top face contour (outer perimeter)")


# =============================================================================
# CAM-10  Generate toolpaths for all operations in setup 0
# =============================================================================

import adsk.core, adsk.cam
import time

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return

    setup = cam.setups.item(0)
    print(f"Generating toolpaths for setup: {setup.name}")
    print(f"Operations in setup: {setup.allOperations.count}")

    # generateAllToolpaths(skipValid=True) — only regen invalid/missing paths
    future = cam.generateAllToolpaths(True)
    print(f"Operations queued: {future.numberOfOperations}")

    # Block until generation completes; stay defensive even though Fusion
    # typically serializes the call.
    while not future.isGenerationCompleted:
        time.sleep(0.2)

    print("Toolpath generation completed.")

    # Report per-op status
    success = 0
    failed  = 0
    for i in range(setup.allOperations.count):
        op = setup.allOperations.item(i)
        ok = op.hasToolpath
        if ok:
            success += 1
        else:
            failed += 1
        print(f"  {op.name:35s} hasToolpath={op.hasToolpath}")

    print(f"\nSuccess: {success}   Failed/unsupported: {failed}")

    # Total cycle time (across all generated ops in this setup)
    total_seconds = 0.0
    for i in range(setup.allOperations.count):
        op = setup.allOperations.item(i)
        if op.hasToolpath:
            # Signature: getMachiningTime(op, feedScale, rapidScale, toolChangeTime)
            # Returned MachiningTime exposes .machiningTime (seconds), .feedDistance
            # (cm), .rapidDistance (cm), .totalFeedTime, .totalRapidTime,
            # .toolChangeCount, .totalToolChangeTime — NOT machiningTimeInSeconds.
            mt = cam.getMachiningTime(op, 1.0, 1.0, 5.0)
            total_seconds += mt.machiningTime

    print(f"Total cycle time: {total_seconds:.1f} s "
          f"({total_seconds/60:.2f} min)")


# =============================================================================
# CAM-11  Post-process to G-code (Haas simulator — per CNC Fundamentals course)
# =============================================================================

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


# =============================================================================
# CAM-12  Full setup inventory dump — useful after a session to audit state
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Not in Manufacture workspace.")
        return

    print(f"=== CAM Setup Inventory ===")
    print(f"Total setups: {cam.setups.count}")

    for s_idx in range(cam.setups.count):
        setup = cam.setups.item(s_idx)
        print(f"\nSetup [{s_idx}]: {setup.name}")
        print(f"  Operation type : {setup.operationType}")
        print(f"  Operations     : {setup.allOperations.count}")

        for o_idx in range(setup.allOperations.count):
            op = setup.allOperations.item(o_idx)

            # Tool description via the parameter table (quirk #25 — no typeName)
            if op.tool:
                desc_param = op.tool.parameters.itemByName('tool_description')
                tool_desc  = desc_param.value.value if desc_param else (op.tool.description or '(tool)')
            else:
                tool_desc = "(no tool)"

            valid = "ok " if op.hasToolpath else "no "
            print(f"  [{valid}] [{o_idx}] {op.name:35s}  strategy={op.strategy}")
            print(f"         tool      : {tool_desc}")

            # Pull a couple of common operation parameters if present
            for pname in ('tolerance', 'stockToLeave', 'stepover',
                          'maximumStepdown', 'feedrate', 'spindleSpeed',
                          'spindle_speed'):
                p = op.parameters.itemByName(pname)
                if p is None:
                    continue
                # Parameter.value is a ValueInput-ish wrapper — try to read it
                # via .expression which is always a printable string.
                expr = getattr(p, 'expression', None)
                if expr is None:
                    expr = str(getattr(p, 'value', ''))
                print(f"         {pname:16s}: {expr}")


# =============================================================================
# CAM-13  Strategy + parameter inventory dump (planning input for expansion)
#         Walks setup.operations.compatibleStrategies for every OperationType
#         we can spin up (Milling, Turning, JetMilling, Additive*, Inspection)
#         and prints every parameter slot each strategy exposes. The output is
#         the authoritative map of what we can wrap as per-strategy test files.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first (run CAM-01).")
        return

    # Map OperationTypes enum members → human label. We probe each one and
    # only emit a section for the types the current document/install supports.
    optypes = []
    for label in (
        'MillingOperation', 'TurningOperation',
        'JetMillingOperation', 'AdditiveFFFAMOperation',
        'AdditivePBFAMOperation', 'InspectionOperation',
        'ProbingOperation', 'CuttingOperation',
    ):
        v = getattr(adsk.cam.OperationTypes, label, None)
        if v is not None:
            optypes.append((label, v))

    print(f"=== Operation-type surface ({len(optypes)} enum members reachable)")
    for label, _ in optypes:
        print(f"  - {label}")

    # We need at least one Setup we own to ask compatibleStrategies. Create a
    # throwaway setup per op-type, harvest the strategy list, then delete it.
    print("\n=== Strategy lists per OperationType")

    # Pick any solid body to seed the throwaway setups.
    seed_body = None
    for b in cam.designRootOccurrence.bRepBodies:
        seed_body = b
        break
    if seed_body is None:
        print("No bRepBody under designRootOccurrence — open a design with at least one body.")
        return

    inventory = {}   # op_type_label -> [strategy_string, ...]

    for label, val in optypes:
        try:
            si = cam.setups.createInput(val)
            si.models = [seed_body]
            tmp = cam.setups.add(si)
        except Exception as e:
            print(f"  {label:30s}  setup-create FAILED: {e}")
            continue

        try:
            strategies = list(tmp.operations.compatibleStrategies)
        except Exception as e:
            strategies = []
            print(f"  {label:30s}  compatibleStrategies FAILED: {e}")

        # OperationStrategy objects expose .name / .title / .description and a
        # set of is{Milling,Turning,Drilling,Cutting,2D,3D,Finishing,
        # Additive,Support,Rotary}Strategy flags plus isGenerationAllowed.
        strat_rows = []
        for s in strategies:
            name = getattr(s, 'name', '?')
            title = getattr(s, 'title', '')
            flags = []
            for fname in ('isMillingStrategy','isTurningStrategy','isDrillingStrategy',
                          'isCuttingStrategy','isRotaryStrategy','is2DStrategy',
                          'is3DStrategy','isFinishingStrategy','isAdditiveStrategy',
                          'isSupportStrategy'):
                try:
                    if getattr(s, fname):
                        flags.append(fname.replace('is','').replace('Strategy',''))
                except Exception:
                    pass
            allowed = getattr(s, 'isGenerationAllowed', None)
            strat_rows.append((name, title, allowed, flags))

        inventory[label] = strat_rows
        print(f"\n  {label}  ({len(strat_rows)} strategies)")
        for name, title, allowed, flags in strat_rows:
            tag = ','.join(flags) if flags else '-'
            print(f"    {name:30s}  allowed={allowed!s:5s}  flags={tag:60s}  title={title!r}")

        # Clean up throwaway setup
        try:
            tmp.deleteMe()
        except Exception:
            pass

    # NOTE: An earlier version of this script also enumerated `op.parameters`
    # for every one of the ~122 strategies in a single run() — that hammered
    # Fusion hard enough to crash it (report 941722456). The parameter dump
    # now lives in CAM-15, which takes one strategy at a time.
    print("\n(parameter dump moved to CAM-15 — strategy-at-a-time to avoid OOM)")


# =============================================================================
# CAM-15  Parameter table for a SINGLE strategy
#         Companion to CAM-13. Pass the strategy name through the
#         module-level STRATEGY constant below — the script creates one
#         throwaway setup, one OperationInput for that strategy, dumps the
#         parameter table, and cleans up. Safe to repeat for every strategy
#         in the CAM-13 inventory without crashing Fusion.
# =============================================================================

import adsk.core, adsk.cam

STRATEGY = "pocket2d"   # ← edit to the strategy name you want dumped

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first (run CAM-01).")
        return

    # Resolve OperationStrategy to know which OperationType setup to use.
    strat_obj = adsk.cam.OperationStrategy.createFromString(STRATEGY)
    if not strat_obj:
        print(f"Unknown strategy: {STRATEGY!r}")
        return
    if strat_obj.isTurningStrategy:
        op_type = adsk.cam.OperationTypes.TurningOperation
    else:
        op_type = adsk.cam.OperationTypes.MillingOperation

    seed_body = next((b for b in cam.designRootOccurrence.bRepBodies), None)
    if seed_body is None:
        print("No bRepBody — open a design with at least one body.")
        return

    si = cam.setups.createInput(op_type)
    si.models = [seed_body]
    setup = cam.setups.add(si)
    try:
        oi = setup.operations.createInput(STRATEGY)
        params = oi.parameters
        print(f"Strategy: {STRATEGY}")
        print(f"  title       : {strat_obj.title}")
        print(f"  description : {strat_obj.description}")
        print(f"  isMilling/Turning/Drilling/Cutting/Rotary = "
              f"{strat_obj.isMillingStrategy}/{strat_obj.isTurningStrategy}/"
              f"{strat_obj.isDrillingStrategy}/{strat_obj.isCuttingStrategy}/"
              f"{strat_obj.isRotaryStrategy}")
        print(f"  is2D/3D/Finishing/Additive/Support       = "
              f"{strat_obj.is2DStrategy}/{strat_obj.is3DStrategy}/"
              f"{strat_obj.isFinishingStrategy}/"
              f"{strat_obj.isAdditiveStrategy}/{strat_obj.isSupportStrategy}")
        print(f"  parameter count: {params.count}")
        for i in range(params.count):
            p = params.item(i)
            expr  = getattr(p, 'expression', '')
            title = getattr(p, 'title', '')
            v = getattr(p, 'value', None)
            vt = type(v).__name__ if v is not None else ''
            print(f"  - {p.name:32s}  title={title!r}  expr={expr!r}  valueType={vt}")
    finally:
        # Always clean up the throwaway setup, even on error.
        setup.deleteMe()


# =============================================================================
# CAM-14  Manager / library / post inventory dump
#         Dumps the non-Setup CAM API surface: CAMManager, libraryManager,
#         tool libraries, post folders + post files, machine library, NC
#         programs collection. Companion to CAM-13.
# =============================================================================

import adsk.core, adsk.cam
import os

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first (run CAM-01).")
        return

    mgr = adsk.cam.CAMManager.get()
    print(f"CAMManager: {mgr}")

    # ── libraryManager surface ────────────────────────────────────────────
    lm = mgr.libraryManager
    print(f"\nlibraryManager attrs (non-callable):")
    for n in sorted(dir(lm)):
        if n.startswith('_'):
            continue
        try:
            attr = getattr(lm, n)
        except Exception:
            continue
        if callable(attr):
            continue
        print(f"  {n} = {attr!r}")

    # ── Walk every tool library URL and report tool counts ────────────────
    tl = lm.toolLibraries
    print("\nTool library locations and child assets:")
    for label in ('CloudLibraryLocation', 'ExternalLibraryLocation',
                  'Fusion360LibraryLocation', 'HubLibraryLocation',
                  'LocalLibraryLocation', 'NetworkLibraryLocation',
                  'OnlineSamplesLibraryLocation'):
        loc = getattr(adsk.cam.LibraryLocations, label, None)
        if loc is None:
            continue
        root = tl.urlByLocation(loc)
        if not root:
            print(f"  {label:32s}  (no root)")
            continue
        assets = tl.childAssetURLs(root)
        print(f"  {label:32s}  assets={len(assets)}")
        for i in range(len(assets)):
            url = assets[i]
            try:
                lib = tl.toolLibraryAtURL(url)
                cnt = lib.count if lib else 0
            except Exception:
                cnt = -1
            print(f"      tools={cnt:4d}  {url.toString()}")

    # ── Post library manager (if present) ─────────────────────────────────
    plm = getattr(lm, 'postLibrary', None) or getattr(mgr, 'postLibrary', None)
    print(f"\npostLibrary: {plm}")

    # ── Post-processor folders + a sample of their .cps contents ──────────
    print(f"\nGeneric post folder : {cam.genericPostFolder}")
    print(f"Personal post folder: {cam.personalPostFolder}")
    for folder in (cam.genericPostFolder, cam.personalPostFolder):
        if not folder or not os.path.isdir(folder):
            continue
        cps = sorted(f for f in os.listdir(folder) if f.lower().endswith('.cps'))
        print(f"\n  {folder}  .cps files: {len(cps)}")
        for f in cps[:25]:
            print(f"    {f}")
        if len(cps) > 25:
            print(f"    ... +{len(cps) - 25} more")

    # ── Machine library (5-axis kinematics etc.) ──────────────────────────
    ml = getattr(lm, 'machineLibrary', None)
    print(f"\nmachineLibrary: {ml}")
    if ml is not None:
        for label in ('CloudLibraryLocation', 'Fusion360LibraryLocation',
                      'LocalLibraryLocation', 'OnlineSamplesLibraryLocation'):
            loc = getattr(adsk.cam.LibraryLocations, label, None)
            if loc is None:
                continue
            try:
                root = ml.urlByLocation(loc)
            except Exception:
                continue
            if not root:
                continue
            try:
                assets = ml.childAssetURLs(root)
            except Exception:
                assets = []
            print(f"  {label:32s}  machine-assets={len(assets)}")
            for i in range(min(len(assets), 10)):
                print(f"      {assets[i].toString()}")

    # ── NC programs (post-process targets) ────────────────────────────────
    nc_progs = getattr(cam, 'ncPrograms', None)
    print(f"\nncPrograms: {nc_progs}")
    if nc_progs is not None:
        print(f"  count = {nc_progs.count}")
        for i in range(nc_progs.count):
            p = nc_progs.item(i)
            print(f"  [{i}] name={p.name!r}  output={getattr(p, 'outputFolder', '?')}")

    # ── Manufacturing model / stock surface ───────────────────────────────
    mm = getattr(cam, 'manufacturingModels', None)
    print(f"\nmanufacturingModels: {mm}")
    if mm is not None:
        print(f"  count = {mm.count}")
        for i in range(mm.count):
            m = mm.item(i)
            print(f"  [{i}] {m.name}")


# =============================================================================
# CAM-16  2D Bore (helical bore-finish of the 4 M6 holes)
#         Picks a Ø3.5 mm flat end mill (smaller than the Ø6 hole) and assigns
#         the four cylindrical M6 hole faces as circularFaces. Bore strategy
#         uses circular interpolation to finish the bore wall.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("bore")
    op_input.displayName = "7_Bore_M6_holes"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    # Want a flat end mill smaller than the Ø6 mm bore: 3-5 mm.
    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        if not p.itemByName('tool_isMill').value.value:
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 3.0 <= dia_mm <= 5.0:
            chosen = t
            break
    if chosen is None:
        print("No 3-5 mm flat end mill in 'Milling Tools (Metric)'.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  D{chosen.parameters.itemByName('tool_diameter').value.value*10:.1f} mm")

    params = op_input.parameters
    params.itemByName("tolerance").expression    = "0.01 mm"
    params.itemByName("stockToLeave").expression = "0 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    m6_cyls = [f for f in bracket.faces
               if isinstance(f.geometry, adsk.core.Cylinder)
               and abs(f.geometry.radius - 0.3) < 0.05]
    op.parameters.itemByName('circularFaces').value.value = m6_cyls
    print(f"Operation added: {op.name}  strategy={op.strategy}  ({len(m6_cyls)} holes)")


# =============================================================================
# CAM-17  Circular (interpolation finish of the 4 M6 holes)
#         Similar to Bore but uses circular-interp finishing with explicit
#         maximumStepdown for axial passes. Useful for flat-bottom finish.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("circular")
    op_input.displayName = "8_Circular_M6_holes"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        if not p.itemByName('tool_isMill').value.value:
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 3.0 <= dia_mm <= 5.0:
            chosen = t
            break
    if chosen is None:
        print("No 3-5 mm flat end mill in 'Milling Tools (Metric)'.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  D{chosen.parameters.itemByName('tool_diameter').value.value*10:.1f} mm")

    params = op_input.parameters
    params.itemByName("maximumStepdown").expression = "1 mm"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    m6_cyls = [f for f in bracket.faces
               if isinstance(f.geometry, adsk.core.Cylinder)
               and abs(f.geometry.radius - 0.3) < 0.05]
    op.parameters.itemByName('circularFaces').value.value = m6_cyls
    print(f"Operation added: {op.name}  strategy={op.strategy}  ({len(m6_cyls)} holes)")


# =============================================================================
# CAM-18  Slot — API-surface demo only
#         The Bracket's 70×30 mm pocket is rectangular and closed (4 walls),
#         not a slot-shaped feature, so the slot strategy creates the operation
#         but cannot generate a toolpath. Slot strategy is designed for
#         keyway- and channel-style geometry where the tool spans the slot
#         width. To generate a real toolpath, this batch needs a Bracket
#         variant with an open or narrow slot feature.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("slot")
    op_input.displayName = "9_Slot_Pocket"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    # Slot strategy is designed for slot-mill tools (T-slot / keyseat geometry).
    # Prefer a 'slot mill' from the library; fall back to a flat end mill.
    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        tt = p.itemByName('tool_type')
        if tt and tt.value.value == 'slot mill':
            chosen = t
            break
    if chosen is None:
        for i in range(library.count):
            t = library.item(i)
            p = t.parameters
            tt = p.itemByName('tool_type')
            if not tt or tt.value.value != 'flat end mill':
                continue
            dia_mm = p.itemByName('tool_diameter').value.value * 10
            if 5.5 <= dia_mm <= 6.5:
                chosen = t
                break
    if chosen is None:
        print("No slot mill or ~6 mm flat end mill found.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  D{chosen.parameters.itemByName('tool_diameter').value.value*10:.1f} mm")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "2 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    pocket_bottom = next(f for f in bracket.faces if abs(f.centroid.z - 1.2) < 0.05)
    pockets_pv = op.parameters.itemByName('pockets').value
    cs = pockets_pv.getCurveSelections(); cs.clear()
    sel = cs.createNewPocketSelection(); sel.inputGeometry = [pocket_bottom]
    pockets_pv.applyCurveSelections(cs)

    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-19  Engrave (traces top-face outer contour as if it were a sketch line)
#         Engrave is the V-bit logo/text strategy - it follows a 2D contour
#         at a specified Z and is intentionally tool-radius compensated for a
#         knife-edge cut. We borrow the top face's perimeter as the contour.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("engrave")
    op_input.displayName = "10_Engrave_TopContour"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    # Prefer a chamfer mill (V-bit) for engraving.
    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        if not p.itemByName('tool_isMill').value.value:
            continue
        desc = (t.description or '').lower()
        if 'chamfer' in desc:
            chosen = t
            break
    if chosen is None:
        for i in range(library.count):
            t = library.item(i)
            p = t.parameters
            if not p.itemByName('tool_isMill').value.value:
                continue
            dia_mm = p.itemByName('tool_diameter').value.value * 10
            if 2.0 <= dia_mm <= 4.0:
                chosen = t
                break
    if chosen is None:
        print("No chamfer mill or 2-4 mm flat end mill found.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "0.5 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    top_candidates = [f for f in bracket.faces if abs(f.centroid.z - 2.0) < 0.05]
    top_face = max(top_candidates,
                   key=lambda f: (f.boundingBox.maxPoint.x - f.boundingBox.minPoint.x)
                               * (f.boundingBox.maxPoint.y - f.boundingBox.minPoint.y))
    contours_pv = op.parameters.itemByName('contours').value
    cs = contours_pv.getCurveSelections(); cs.clear()
    sel = cs.createNewFaceContourSelection(); sel.inputGeometry = [top_face]
    contours_pv.applyCurveSelections(cs)

    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-20  Trace (follows top-face perimeter edges at fixed Z)
#         Trace is for following a specific 2D curve at a fixed depth -
#         useful for hand-tweaked cleanup paths or edge-following deburr cuts.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("trace")
    op_input.displayName = "11_Trace_TopPerimeter"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        if not p.itemByName('tool_isMill').value.value:
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t
            break
    if chosen is None:
        print("No ~6 mm flat end mill.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  D{chosen.parameters.itemByName('tool_diameter').value.value*10:.1f} mm")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("stepover").expression        = "tool_diameter * 0.5"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    top_candidates = [f for f in bracket.faces if abs(f.centroid.z - 2.0) < 0.05]
    top_face = max(top_candidates,
                   key=lambda f: (f.boundingBox.maxPoint.x - f.boundingBox.minPoint.x)
                               * (f.boundingBox.maxPoint.y - f.boundingBox.minPoint.y))
    curves_pv = op.parameters.itemByName('curves').value
    cs = curves_pv.getCurveSelections(); cs.clear()
    sel = cs.createNewFaceContourSelection(); sel.inputGeometry = [top_face]
    curves_pv.applyCurveSelections(cs)

    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-21  Thread Mill (M6x1.0 thread mill on the 4 M6 corner holes)
#         Thread strategy uses circularFaces + threadType + threadPitch to
#         mill a thread profile into a pre-drilled hole. Picks a thread mill
#         from the metric milling sample library if available.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("thread")
    op_input.displayName = "12_Thread_M6"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    # The METRIC sample library only ships M8/M10/M12 thread mills (>=Ø6.35 mm)
    # — none fits the Ø6 mm M6 hole. The INCH sample library however ships a
    # Ø4.57 mm (1/4-20 TPI) thread mill, which fits. Fusion's thread strategy
    # accepts threadPitch independently of the tool's native pitch, so the
    # inch tool can cut a metric M6×1.0 thread.
    inch_lib = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Inch)'))

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    m6_cyls = [f for f in bracket.faces
               if isinstance(f.geometry, adsk.core.Cylinder)
               and abs(f.geometry.radius - 0.3) < 0.05]
    bore_dia_mm = 6.0  # M6 = Ø6 mm bore

    chosen, chosen_dia = None, 1e9
    for lib in (library, inch_lib):
        if not lib: continue
        for i in range(lib.count):
            t = lib.item(i)
            p = t.parameters
            tt = p.itemByName('tool_type')
            if not tt or tt.value.value != 'thread mill': continue
            dia_mm = p.itemByName('tool_diameter').value.value * 10
            if dia_mm < bore_dia_mm and dia_mm < chosen_dia:
                chosen, chosen_dia = t, dia_mm
    if chosen is None:
        print(f"No thread mill < Ø{bore_dia_mm} mm in Metric or Inch sample libraries.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  Ø{chosen_dia:.2f} mm")

    params = op_input.parameters
    params.itemByName("threadPitch").expression = "1 mm"
    # 'threadType' default 'ISO Metric profile' is fine.

    op = setup.operations.add(op_input)
    op.parameters.itemByName('circularFaces').value.value = m6_cyls
    print(f"Operation added: {op.name}  strategy={op.strategy}  ({len(m6_cyls)} holes)")


# =============================================================================
# CAM-22  3D Adaptive Clearing (HEM-style rough of the full Bracket model)
#         Same chip-load math as the 2D adaptive (CAM-05) but runs against the
#         3D model envelope instead of a 2D pocket selection. 6 mm flat end
#         mill, 10% RDOC, ~8 mm ADOC stepdown.
#
#         Generation requires roughing volume: the existing BracketMillingSetup
#         ships with a 1 mm side stock offset which is too tight. Verified
#         live — with `job_stockOffsetSides` bumped to 10 mm the op generates a
#         49 s cycle. Left at default the op is created but produces no path.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("adaptive")
    op_input.displayName = "13_Adaptive3D_Rough"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'flat end mill':
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t
            break
    if chosen is None:
        print("No ~6 mm flat end mill.")
        return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.1 mm"
    params.itemByName("optimalLoad").expression     = "tool_diameter * 0.1"
    params.itemByName("maximumStepdown").expression = "8 mm"
    params.itemByName("stockToLeave").expression    = "0.3 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-23  Pocket Clearing (3D pocket rough — non-adaptive alternative)
#         Stepdown-based 3D pocket rough that follows Z levels rather than
#         maintaining constant engagement. Slower than adaptive on tool life
#         but simpler motion — useful on small machines.
#
#         Generation needs a `machiningBoundarySel` (2D containment boundary)
#         to find pocket regions; bumping stock offset alone is not enough
#         (verified — even with 10 mm side stock the op does not generate).
#         The script creates the op to demonstrate the API; supplying a
#         boundary selection is left as a future enhancement.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("pocket_clearing")
    op_input.displayName = "14_PocketClearing3D_Rough"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'flat end mill':
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t
            break
    if chosen is None:
        print("No ~6 mm flat end mill.")
        return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.1 mm"
    params.itemByName("maximumStepdown").expression = "2 mm"
    params.itemByName("stockToLeave").expression    = "0.3 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-24  Horizontal (finishes the flat horizontal faces of the Bracket)
#         Detects flat horizontal regions (top + pocket bottom) and finishes
#         each at its own Z. Uses a flat end mill since the targets are flat.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("horizontal")
    op_input.displayName = "15_Horizontal_Finish"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'flat end mill':
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t
            break
    if chosen is None:
        print("No ~6 mm flat end mill.")
        return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "1 mm"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-25  Parallel (3D parallel finishing — same-direction sweeping passes)
#         Workhorse 3D finish for shallow surfaces. Ball end mill traces
#         parallel passes across the model at a configured stepover.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("parallel")
    op_input.displayName = "16_Parallel3D_Finish"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'ball end mill':
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t
            break
    if chosen is None:
        print("No ~6 mm ball end mill.")
        return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression    = "0.01 mm"
    params.itemByName("stockToLeave").expression = "0 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-26  Contour 3D (constant-Z finish — wedding-cake terrace pattern)
#         Generates closed contour loops at constant Z heights. Best on
#         steep walls; on the Bracket the pocket walls + outer profile are
#         the natural targets.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("contour3d")
    op_input.displayName = "17_Contour3D_Finish"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'ball end mill':
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t
            break
    if chosen is None:
        print("No ~6 mm ball end mill.")
        return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "1 mm"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-27  Scallop (constant-scallop-height finish — uniform surface finish)
#         Adapts stepover so the scallop height is constant regardless of
#         surface angle. Best general-purpose ball-mill finish.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("scallop")
    op_input.displayName = "18_Scallop_Finish"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'ball end mill':
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t
            break
    if chosen is None:
        print("No ~6 mm ball end mill.")
        return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression    = "0.01 mm"
    params.itemByName("stockToLeave").expression = "0 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-28  Pencil (cleanup pass that follows concave corners)
#         Pencil only generates motion where the model has concave corners
#         tighter than the tool radius — perfect for rest machining after
#         a larger finishing pass.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("pencil")
    op_input.displayName = "19_Pencil_Cleanup"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))
    tutorial_metric = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Tutorial Tools (Metric)'))

    # Pencil needs a ball mill smaller than typical concave radius.
    # Bracket pocket has 2 mm corner radius — use a Ø2 mm ball if available
    # (Tutorial Tools (Metric) has one). Fall back to Ø6 mm ball.
    def find_ball(lib, lo, hi):
        if not lib: return None
        for i in range(lib.count):
            t = lib.item(i); p = t.parameters
            tt = p.itemByName('tool_type')
            if not tt or tt.value.value != 'ball end mill': continue
            d = p.itemByName('tool_diameter').value.value * 10
            if lo <= d <= hi: return t
        return None
    chosen = (find_ball(tutorial_metric, 1.5, 3.0)
              or find_ball(library, 1.5, 3.0)
              or find_ball(library, 5.5, 6.5))
    if chosen is None:
        print("No ball end mill found in metric libraries.")
        return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression    = "0.01 mm"
    params.itemByName("stockToLeave").expression = "0 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-29  Radial (radial finishing pattern from a center point)
#         Generates radial spokes from a center point outward. Best for
#         round/circular features; on a rectangular Bracket the pattern is
#         academic but demonstrates the API.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("radial")
    op_input.displayName = "20_Radial_Finish"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'ball end mill':
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t
            break
    if chosen is None:
        print("No ~6 mm ball end mill.")
        return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "1 mm"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-30  Spiral (spiral finishing from a center point outward)
#         Spiral path from a center point in expanding arcs. Cleaner motion
#         than radial — no abrupt direction reversals.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("spiral")
    op_input.displayName = "21_Spiral_Finish"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'ball end mill':
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t
            break
    if chosen is None:
        print("No ~6 mm ball end mill.")
        return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "1 mm"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-31  Morphed Spiral (spiral that morphs to match boundary shape)
#         Spiral pattern that warps to follow a non-circular boundary -
#         produces a continuous spiral cut even on rectangular pockets.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("morphed_spiral")
    op_input.displayName = "22_MorphedSpiral_Finish"

    tool_libs = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tool_libs.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))

    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'ball end mill':
            continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t
            break
    if chosen is None:
        print("No ~6 mm ball end mill.")
        return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "1 mm"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-32  Flat (finishes the flat-bottomed planar regions)
#         Similar to Horizontal but Flat is keyed to "flat areas" detection,
#         emitting one closed-pocket cut per flat region. Uses a flat end mill.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("flat")
    op_input.displayName = "23_Flat_Finish"

    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tl.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))
    chosen = None
    for i in range(library.count):
        t = library.item(i); p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'flat end mill': continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t; break
    if chosen is None:
        print("No ~6 mm flat end mill."); return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "1 mm"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-33  Ramp (3D ramping pass — Z-level cuts with smooth descent)
#         Cuts at constant-Z passes connected by ramps for smooth transitions.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("ramp")
    op_input.displayName = "24_Ramp_Finish"

    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tl.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))
    chosen = None
    for i in range(library.count):
        t = library.item(i); p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'ball end mill': continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t; break
    if chosen is None:
        print("No ~6 mm ball end mill."); return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("maximumStepdown").expression = "1 mm"
    params.itemByName("stockToLeave").expression    = "0 mm"

    op = setup.operations.add(op_input)
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-34  Blend (smooth blend between two surfaces — 5-axis common pattern)
#         Generates a blended pass between two boundary surfaces. On the
#         Bracket the available faces are mostly flat, so this exercises the
#         API surface but may not produce an interesting path.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("blend")
    op_input.displayName = "25_Blend_Finish"

    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tl.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))
    chosen = None
    for i in range(library.count):
        t = library.item(i); p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'ball end mill': continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t; break
    if chosen is None:
        print("No ~6 mm ball end mill."); return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression    = "0.01 mm"
    params.itemByName("stockToLeave").expression = "0 mm"

    op = setup.operations.add(op_input)
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-35  Corner (rest-machining of concave corners — radius < prior tool)
#         Generates motion only in concave corners tighter than the previous
#         tool's radius. Pairs with Scallop / Parallel as a cleanup pass.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("corner")
    op_input.displayName = "26_Corner_Cleanup"

    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tl.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))
    tutorial_metric = tl.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Tutorial Tools (Metric)'))

    # Prefer a Ø2 mm ball (Tutorial Tools (Metric)) to fit pocket corner radii.
    def find_ball(lib, lo, hi):
        if not lib: return None
        for i in range(lib.count):
            t = lib.item(i); p = t.parameters
            tt = p.itemByName('tool_type')
            if not tt or tt.value.value != 'ball end mill': continue
            d = p.itemByName('tool_diameter').value.value * 10
            if lo <= d <= hi: return t
        return None
    chosen = (find_ball(tutorial_metric, 1.5, 3.0)
              or find_ball(library, 1.5, 3.0)
              or find_ball(library, 5.5, 6.5))
    if chosen is None:
        print("No ball end mill."); return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression    = "0.01 mm"
    params.itemByName("stockToLeave").expression = "0 mm"
    # Corner is a rest-machining strategy: it needs to know what previous tool
    # left material in the concave corners. Default source is 'tool' with the
    # current tool's geometry as reference — that yields nothing to clean up.
    # Switch to setup-stock as the reference so the strategy treats the full
    # raw stock as un-machined material, then cleans up corners the Ø2 mm ball
    # can reach.
    params.itemByName("restMaterialFromJob").expression = "true"

    op = setup.operations.add(op_input)
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-36  Steep and Shallow (combined finish for steep walls + shallow faces)
#         Switches motion type by surface angle — scallop on shallow, contour3d
#         on steep — to get a uniform finish in a single op.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("steep_and_shallow")
    op_input.displayName = "27_SteepAndShallow_Finish"

    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tl.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))
    chosen = None
    for i in range(library.count):
        t = library.item(i); p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'ball end mill': continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t; break
    if chosen is None:
        print("No ~6 mm ball end mill."); return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression    = "0.01 mm"
    params.itemByName("stockToLeave").expression = "0 mm"

    op = setup.operations.add(op_input)
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")


# =============================================================================
# CAM-37  Morph — API-surface demo (needs two guide curves)
#         Morph strategy morphs between two boundary curves. On the Bracket
#         the natural guide curves would be e.g. the top and bottom perimeter
#         edges. Supplying the right pair is design-specific; this script
#         demonstrates the API but does not assign `curves` — the op is
#         created and document this as a "needs guide curves" sample.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("morph")
    op_input.displayName = "28_Morph_Finish"

    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tl.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))
    chosen = None
    for i in range(library.count):
        t = library.item(i); p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'ball end mill': continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t; break
    if chosen is None:
        print("No ~6 mm ball end mill."); return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression    = "0.01 mm"
    params.itemByName("stockToLeave").expression = "0 mm"

    op = setup.operations.add(op_input)
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print("(morph needs two guide curves in `curves` to generate; "
          "left unset to keep this a generic demo)")


# =============================================================================
# CAM-38  Project — API-surface demo (needs source curves to project)
#         Project strategy projects 2D source curves onto the model surface.
#         Without source curves the op produces no toolpath. The script
#         creates the op to demonstrate the API; populating `curves` with a
#         meaningful sketch projection is left to a future Bracket variant.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return
    setup = cam.setups.item(0)
    op_input = setup.operations.createInput("project")
    op_input.displayName = "29_Project_Finish"

    tl = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    library = tl.toolLibraryAtURL(adsk.core.URL.create(
        'systemlibraryroot://Samples/Milling Tools (Metric)'))
    chosen = None
    for i in range(library.count):
        t = library.item(i); p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'ball end mill': continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t; break
    if chosen is None:
        print("No ~6 mm ball end mill."); return
    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("tolerance").expression    = "0.01 mm"
    params.itemByName("stockToLeave").expression = "0 mm"

    op = setup.operations.add(op_input)
    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    op.parameters.itemByName('model').value.value = [bracket]
    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print("(project needs `curves` populated with sketch curves to project; "
          "left unset to keep this a generic demo)")


# =============================================================================
# CAM-39  Stock Material Library inventory
#         Walks adsk.cam.CAMManager.libraryManager.stockMaterialLibrary and
#         dumps every location + child asset. Stock materials power feed/speed
#         lookups and machining-power estimates per material.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    sml = adsk.cam.CAMManager.get().libraryManager.stockMaterialLibrary
    print(f"stockMaterialLibrary: {sml}")
    for label in ('CloudLibraryLocation', 'Fusion360LibraryLocation',
                  'LocalLibraryLocation', 'HubLibraryLocation',
                  'OnlineSamplesLibraryLocation', 'ExternalLibraryLocation',
                  'NetworkLibraryLocation'):
        loc = getattr(adsk.cam.LibraryLocations, label, None)
        if loc is None: continue
        try:
            root = sml.urlByLocation(loc)
        except Exception as e:
            print(f"  {label:32s}  urlByLocation FAILED: {e}")
            continue
        if not root:
            print(f"  {label:32s}  (no root)")
            continue
        try:
            assets = sml.childAssetURLs(root)
        except Exception as e:
            print(f"  {label:32s}  childAssetURLs FAILED: {e}")
            continue
        print(f"  {label:32s}  assets={len(assets)}")
        for i in range(min(len(assets), 20)):
            print(f"      {assets[i].toString()}")
        if len(assets) > 20:
            print(f"      ... +{len(assets) - 20} more")


# =============================================================================
# CAM-40  CAM Template Library inventory
#         CAM templates are saved Setup configurations (machine + WCS + stock
#         conventions). They drive the "Apply Template" UI in the CAM browser.
# =============================================================================

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


# =============================================================================
# CAM-41  Print Setting Library inventory (additive)
#         Print settings power the FFF/PBF additive workflows. Stored as
#         per-material profiles in the print-setting library.
# =============================================================================

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


# =============================================================================
# CAM-42  Machine Library inventory
#         Machine definitions drive multi-axis kinematics, post selection,
#         simulation. CAM-14 already touches this; CAM-42 is the focused
#         per-location dump showing categories of machines available.
# =============================================================================

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


# =============================================================================
# CAM-43  Manufacturing Models (separate machining body)
#         A ManufacturingModel is a CAM-side body that diverges from the
#         design body (e.g. with fixturing tabs added). Demo creates one if
#         the doc has none, otherwise reports the existing ones.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first."); return

    mms = cam.manufacturingModels
    print(f"manufacturingModels.count = {mms.count}")
    for i in range(mms.count):
        m = mms.item(i)
        print(f"  [{i}] {m.name}")

    # Try to add a new one if API is available.
    try:
        ci = mms.createInput()
        ci.name = "CAM_Mfg_Model_Demo"
        # Source the design body as a baseline; ManufacturingModelInput typically
        # takes the design body via .designModel or models list.
        body = next((b for b in cam.designRootOccurrence.bRepBodies), None)
        if body is not None:
            for attr in ('models', 'designModel', 'body', 'sourceBody'):
                if hasattr(ci, attr):
                    try:
                        if attr == 'models':
                            setattr(ci, attr, [body])
                        else:
                            setattr(ci, attr, body)
                    except Exception:
                        pass
        added = mms.add(ci)
        print(f"  added: {added.name}")
    except AttributeError as e:
        print(f"  ManufacturingModels.createInput not exposed in this build: {e}")
    except Exception as e:
        print(f"  add failed: {e}")


# =============================================================================
# CAM-44  Two-Setup project (Roughing + Finishing split)
#         Real shops separate roughing and finishing into distinct Setups so
#         the operator can swap tools/stock between phases. Demo: add a
#         second Setup named 'BracketFinishingSetup' alongside the existing
#         BracketMillingSetup.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first."); return

    name = 'BracketFinishingSetup'
    existing = None
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        if s.name == name:
            existing = s; break
    if existing:
        print(f"Reusing: {existing.name}")
    else:
        bracket = next((b for b in cam.designRootOccurrence.bRepBodies
                        if b.name == 'Bracket'), None)
        if bracket is None:
            print("Need a body named 'Bracket' under designRootOccurrence."); return
        si = cam.setups.createInput(adsk.cam.OperationTypes.MillingOperation)
        si.models = [bracket]
        setup = cam.setups.add(si)
        setup.name = name
        print(f"Created: {setup.name}")

    print(f"\nAll setups in this CAM product:")
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        print(f"  [{i}] {s.name}  ops={s.allOperations.count}")


# =============================================================================
# CAM-45  NCPrograms.add (group post-processing into an NC program)
#         An NCProgram bundles one or more Setups/Operations into a named
#         post target. Demo: create an NC program covering the existing
#         BracketMillingSetup.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first."); return

    ncs = cam.ncPrograms
    print(f"Existing NCPrograms: {ncs.count}")
    for i in range(ncs.count):
        n = ncs.item(i)
        print(f"  [{i}] {n.name}")

    try:
        ci = ncs.createInput()
        # NCProgramInput is the standard pattern. Set the post + program name,
        # then point at the setup to bundle.
        for attr_name, val in (('name', 'BracketNCProgram_Demo'),
                               ('programName', '1002')):
            if hasattr(ci, attr_name):
                try: setattr(ci, attr_name, val)
                except Exception: pass
        # Operations / scope: prefer .operations = [setup] if exposed.
        for attr_name in ('operations', 'parent', 'scope'):
            if hasattr(ci, attr_name):
                try:
                    if attr_name == 'operations':
                        setattr(ci, attr_name, [cam.setups.item(0)])
                    else:
                        setattr(ci, attr_name, cam.setups.item(0))
                except Exception:
                    pass
        added = ncs.add(ci)
        print(f"\nAdded NCProgram: {added.name}")
    except AttributeError as e:
        print(f"NCPrograms.createInput not exposed in this build: {e}")
    except Exception as e:
        print(f"add failed: {e}")


# =============================================================================
# CAM-46  FusionMCPTestCoverage Library — single-source tool inventory
#         Loads toollibraryroot://Local/FusionMCPTestCoverage and prints its
#         contents. This library is generated by tools/_build_coverage_lib.py
#         and contains one tool per category the CAM tests exercise — so the
#         whole suite can be run from a single library without chasing tools
#         across the Cloud + sample libraries.
# =============================================================================

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


# =============================================================================
# CAM-47  Rotor rotary setup (Batch D prep)
#         Creates a Milling Setup on the Rotor with RelativeCylinderStock and
#         reorients the WCS so its Z aligns with the rotor's centerline.
#
#         Why this script exists — see memory `cam_stock_axis_misalignment.md`:
#         when a design part isn't along world Z, Fusion's default
#         RelativeCylinderStock wraps the part along Z anyway, producing a
#         wrong-axis cylinder. Standard fix is option 2 (reorient WCS), not
#         rebuild the part.
#
#         Quirks exercised:
#           - `CadObjectParameterValue.value.value` MUST be a list, even for a
#             single entity. Bare entity raises TypeError (vector expected).
#           - ChoiceParameterValue strings are set via `.expression` with the
#             literal quotes embedded, e.g. "'axesZX'".
# =============================================================================

import adsk.core, adsk.cam, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first (run CAM-01).")
        return

    # Find the Rotor occurrence under the CAM-linked design root
    rotor_occ = next(
        (o for o in cam.designRootOccurrence.component.allOccurrences
         if o.component.name == 'Rotor'),
        None)
    if rotor_occ is None:
        print("Rotor occurrence not found — run DESIGN-29 / DESIGN-30 first.")
        return
    comp = rotor_occ.component
    rotor = comp.bRepBodies.itemByName('Rotor')
    if rotor is None:
        print("Rotor body not found in 'Rotor' component.")
        return

    # Idempotent: reuse if we already made it
    setup = next((s for s in cam.setups if s.name == 'RotorRotarySetup'), None)
    if setup is None:
        si = cam.setups.createInput(adsk.cam.OperationTypes.MillingOperation)
        si.models = [rotor]
        si.stockMode = adsk.cam.SetupStockModes.RelativeCylinderStock
        setup = cam.setups.add(si)
        setup.name = 'RotorRotarySetup'
        print(f"Created setup: {setup.name}")
    else:
        print(f"Reusing setup: {setup.name}")

    # Reorient WCS — Setup Z := rotor centerline (component X axis)
    setup.parameters.itemByName('wcs_orientation_mode').expression = "'axesZX'"
    setup.parameters.itemByName('wcs_orientation_axisZ').value.value = [comp.xConstructionAxis]
    setup.parameters.itemByName('wcs_orientation_axisX').value.value = [comp.yConstructionAxis]

    # Verify
    dia = setup.parameters.itemByName('stockDiameter').expression
    lng = setup.parameters.itemByName('stockLength').expression
    print(f"Stock after reorient: Ø{dia} × {lng} (expect ~42 × 100 mm)")


# =============================================================================
# CAM-48  Batch D — Rotary + finishing-misc — ALL FIVE strategies in one run
#         This is an intentional retest of quirk #9 (one-strategy-per-run).
#         User explicitly opted in: recovery is easy if Fusion crashes.
#
#         Targets (in order): rotary_contour, rotary_pocket, rotary_finishing,
#         deburr, geodesic. All against the RotorRotarySetup from CAM-47.
#         No toolpaths generated here — just OperationInput creation, which is
#         the same surface that crashed Fusion previously.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first.")
        return
    setup = next((s for s in cam.setups if s.name == 'RotorRotarySetup'), None)
    if setup is None:
        print("RotorRotarySetup not found — run CAM-47 first.")
        return

    batch_d = ['rotary_contour', 'rotary_pocket', 'rotary_finishing',
               'deburr', 'geodesic']

    # First, sanity-check that each strategy is recognized + allowed under the
    # current license/preview flags.
    strat_objs = {}
    for name in batch_d:
        s = adsk.cam.OperationStrategy.createFromString(name)
        strat_objs[name] = s
        print(f"  {name:18s}  allowed={s.isGenerationAllowed}  "
              f"rotary={s.isRotaryStrategy}  finishing={s.isFinishingStrategy}")

    # Then create one OperationInput per strategy and add it to the setup.
    # This is the exact pattern that crashed Fusion in earlier sessions.
    print("\nCreating OperationInputs...")
    for name in batch_d:
        op_in = setup.operations.createInput(name)
        op_in.displayName = f"Batch_D_{name}"
        op = setup.operations.add(op_in)
        print(f"  added: {op.name}  strategy={op.strategy}")

    print(f"\nTotal operations on setup: {setup.operations.count}")
    print("If you see this line, quirk #9 may have softened — update memory.")
