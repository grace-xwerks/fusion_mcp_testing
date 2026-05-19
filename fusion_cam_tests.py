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

    # HEM parameters: high ADOC (full flute), low RDOC (~10% D)
    params.itemByName("tolerance").expression       = "0.02 mm"
    params.itemByName("optimalLoad").expression     = "10%"
    params.itemByName("maximumStepdown").expression = "8 mm"
    params.itemByName("stockToLeave").expression    = "0.3 mm"

    # TODO(refactor): 2D Adaptive requires pocketRegion geometry (face/sketch
    # chain pick). The 'pocketRegions' parameter is a CadContours2dParameterValue
    # and needs a chain built from a body face — defer programmatic selection
    # to the parent at validation time.
    op = setup.operations.add(op_input)
    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print(f"Setup: {setup.name}")
    print("HEM params: 10% RDOC / 8mm ADOC — constant chip load roughing")
    print("NOTE: pocketRegions geometry NOT set (TODO for parent).")


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
    params.itemByName("tolerance").expression       = "0.01 mm"
    params.itemByName("stepover").expression        = "40%"
    params.itemByName("maximumStepdown").expression = "2 mm"
    params.itemByName("stockToLeave").expression    = "0 mm"

    # TODO(refactor): 2D Pocket needs pocketRegions geometry — typically the
    # pocket's bottom face. Same CadContours2dParameterValue picking problem
    # as CAM-05. Defer to parent at validation.
    op = setup.operations.add(op_input)
    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print(f"Setup: {setup.name}")
    print("NOTE: pocketRegions geometry NOT set (TODO for parent).")


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

    # TODO(refactor): 2D Contour needs a 'contourSelection' chain — the outer
    # silhouette / bottom-edge loop of the Bracket body. CadContours2d picking
    # from a body silhouette is non-trivial; defer to parent at validation.
    op = setup.operations.add(op_input)
    print(f"Setup: {setup.name}")
    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print("NOTE: contour chain geometry NOT set (TODO for parent).")


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

    # TODO(refactor): drilling operations need a 'holes' selection — typically
    # the cylindrical faces of the four corner holes on the Bracket top face.
    # Programmatic hole-feature selection from the body is non-trivial; defer
    # to parent at validation.
    sd_op = setup.operations.add(sd_input)
    print(f"Spot drill op added: {sd_op.name}  strategy={sd_op.strategy}")

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
    print(f"Drill op added: {dr_op.name}  strategy={dr_op.strategy}")
    print(f"Setup: {setup.name}")
    print("NOTE: hole geometry NOT set on either operation (TODO for parent).")


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

    # TODO(refactor): select the top perimeter edges programmatically and pass
    # them via op_input.parameters.itemByName('chainSelections') / contour
    # selections. Without an explicit geometry selection, the operation will
    # be created but flagged invalid until edges are picked in the UI.

    op = setup.operations.add(op_input)
    print(f"Operation added: {op.name}")


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
            mt = cam.getMachiningTime(op, 1.0, 1.0)
            # MachiningTime exposes machiningTimeInSeconds
            secs = getattr(mt, 'machiningTimeInSeconds', None)
            if secs is not None:
                total_seconds += secs

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
    program_name  = "Bracket"

    pp_input = adsk.cam.PostProcessInput.create(
        program_name,
        post_path,
        output_folder,
        adsk.cam.PostOutputUnitOptions.DocumentUnitsOutput,
    )
    pp_input.isOpenInEditor = False

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
