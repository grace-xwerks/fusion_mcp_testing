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
            dia_mm = dia_param.value * 10 if dia_param else float('nan')
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
        if not is_mill_param or not is_mill_param.value:
            continue
        dia_param = t.parameters.itemByName('tool_diameter')
        if not dia_param:
            continue
        dia_mm = dia_param.value * 10
        if dia_mm < 10:
            continue
        desc = (t.description or '').lower()
        if 'face' in desc or 'flat' in desc:
            chosen_tool = t
            break

    if not chosen_tool:
        print("ERROR: No suitable face/flat mill (>=10 mm) found in sample library.")
        return

    dia_mm = chosen_tool.parameters.itemByName('tool_diameter').value * 10
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

    # Select a flat end mill (prefer 3/8" or 10mm diameter)
    for i in range(cam.documentToolLibrary.count):
        t = cam.documentToolLibrary.item(i)
        dia = t.parameters.itemByName('tool_diameter').value * 10  # mm
        if t.typeName == "flat end mill" and 8 <= dia <= 12:
            op_input.tool = t
            print(f"Tool: {t.description}  Ø{dia:.1f} mm")
            break

    params = op_input.parameters

    # HEM parameters: high ADOC (full flute), low RDOC (~10% D)
    # Per HEM Guidebook — lower RDOC + higher ADOC = consistent chip load
    params.itemByName("tolerance").value           = adsk.core.ValueInput.createByString("0.02 mm")
    params.itemByName("optimalLoad").value         = adsk.core.ValueInput.createByString("10%")   # RDOC = 10% D
    params.itemByName("maximumStepdown").value     = adsk.core.ValueInput.createByString("8 mm")  # full flute ADOC
    params.itemByName("stockToLeave").value        = adsk.core.ValueInput.createByString("0.3 mm")
    params.itemByName("bothWays").value            = adsk.core.ValueInput.createByReal(0)          # climb only

    op = setup.operations.add(op_input)
    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print("HEM params: 10% RDOC / 8mm ADOC — constant chip load roughing")


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

    for i in range(cam.documentToolLibrary.count):
        t = cam.documentToolLibrary.item(i)
        dia = t.parameters.itemByName('tool_diameter').value * 10
        if t.typeName == "flat end mill" and 6 <= dia <= 8:
            op_input.tool = t
            print(f"Tool: {t.description}  Ø{dia:.1f} mm")
            break

    params = op_input.parameters
    params.itemByName("tolerance").value           = adsk.core.ValueInput.createByString("0.01 mm")
    params.itemByName("stepover").value            = adsk.core.ValueInput.createByString("40%")
    params.itemByName("maximumStepdown").value     = adsk.core.ValueInput.createByString("2 mm")
    params.itemByName("stockToLeave").value        = adsk.core.ValueInput.createByString("0 mm")   # finish pass
    params.itemByName("finishingPasses").value     = adsk.core.ValueInput.createByReal(1)
    params.itemByName("finishStepover").value      = adsk.core.ValueInput.createByString("0.2 mm")

    op = setup.operations.add(op_input)
    print(f"Operation added: {op.name}  strategy={op.strategy}")


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

    for i in range(cam.documentToolLibrary.count):
        t = cam.documentToolLibrary.item(i)
        dia = t.parameters.itemByName('tool_diameter').value * 10
        if t.typeName == "flat end mill" and 8 <= dia <= 12:
            op_input.tool = t
            print(f"Tool: {t.description}  Ø{dia:.1f} mm")
            break

    params = op_input.parameters
    params.itemByName("tolerance").value          = adsk.core.ValueInput.createByString("0.01 mm")
    params.itemByName("maximumStepdown").value    = adsk.core.ValueInput.createByString("5 mm")
    params.itemByName("stockToLeave").value       = adsk.core.ValueInput.createByString("0 mm")
    params.itemByName("direction").value          = adsk.core.ValueInput.createByString("climb")
    # Compensation: CDC (Cutter Diameter Compensation) — standard for contours
    params.itemByName("compensation").value       = adsk.core.ValueInput.createByString("left")

    op = setup.operations.add(op_input)
    print(f"Operation added: {op.name}  strategy={op.strategy}")
    print("CDC direction: left (climb milling, outside contour)")


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

    # ── Spot drill ───────────────────────────────────────────────────────────
    sd_input = setup.operations.createInput("drill")
    sd_input.displayName = "5a_SpotDrill"

    for i in range(cam.documentToolLibrary.count):
        t = cam.documentToolLibrary.item(i)
        if t.typeName in ("spot drill", "center drill"):
            sd_input.tool = t
            print(f"Spot drill tool: {t.description}")
            break

    sd_params = sd_input.parameters
    sd_params.itemByName("tolerance").value     = adsk.core.ValueInput.createByString("0.02 mm")
    sd_params.itemByName("tipDepth").value      = adsk.core.ValueInput.createByString("1 mm")
    setup.operations.add(sd_input)

    # ── Through-drill ────────────────────────────────────────────────────────
    dr_input = setup.operations.createInput("drill")
    dr_input.displayName = "5b_Drill_6mm_Through"

    for i in range(cam.documentToolLibrary.count):
        t = cam.documentToolLibrary.item(i)
        dia = t.parameters.itemByName('tool_diameter').value * 10
        if t.typeName == "drill" and abs(dia - 6.0) < 0.1:
            dr_input.tool = t
            print(f"Drill tool: {t.description}  Ø{dia:.1f} mm")
            break

    dr_params = dr_input.parameters
    dr_params.itemByName("tolerance").value       = adsk.core.ValueInput.createByString("0.02 mm")
    dr_params.itemByName("cycleType").value       = adsk.core.ValueInput.createByString("chip_breaking")
    dr_params.itemByName("peckingincrements").value = adsk.core.ValueInput.createByString("3 mm")
    # Through all: set bottomHeight below stock
    dr_params.itemByName("bottomHeight").value    = adsk.core.ValueInput.createByString("-22 mm")

    dr_op = setup.operations.add(dr_input)
    print(f"Drill operation added: {dr_op.name}")


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
    op_input = setup.operations.createInput("contour2d")   # chamfer uses 2D Contour in Fusion
    op_input.displayName = "6_Chamfer_Top"

    # Chamfer mill or center drill as cutter
    for i in range(cam.documentToolLibrary.count):
        t = cam.documentToolLibrary.item(i)
        if t.typeName in ("chamfer mill", "dovetail mill", "center drill"):
            op_input.tool = t
            print(f"Chamfer tool: {t.description}")
            break

    params = op_input.parameters
    params.itemByName("chamfer").value          = adsk.core.ValueInput.createByReal(1)  # enable chamfer mode
    params.itemByName("chamferWidth").value     = adsk.core.ValueInput.createByString("1 mm")
    params.itemByName("tolerance").value        = adsk.core.ValueInput.createByString("0.01 mm")

    op = setup.operations.add(op_input)
    print(f"Operation added: {op.name}")


# =============================================================================
# CAM-10  Generate toolpaths for all operations in setup 0
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return

    setup = cam.setups.item(0)
    print(f"Generating toolpaths for setup: {setup.name}")
    print(f"Operations to generate: {setup.allOperations.count}")

    # Build collection of all operations
    ops = adsk.core.ObjectCollection.create()
    for i in range(setup.allOperations.count):
        ops.add(setup.allOperations.item(i))

    # Generate (synchronous)
    future = cam.generateToolpaths(ops)
    # Wait for completion
    while not future.isGenerationCompleted:
        adsk.core.Application.get().userInterface.messageBox("Generating...", "Wait")
        # Note: in MCP scripts there's no event loop — generation may be sync
        break

    print(f"Toolpath generation submitted.")
    print("Check the Manufacture workspace — toolpaths should appear in green/yellow.")

    # Report operation statuses
    for i in range(setup.allOperations.count):
        op = setup.allOperations.item(i)
        print(f"  {op.name:35s} hasToolpath={op.hasToolpath}  isValid={op.isValid}")


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
        print(f"  Operations: {setup.allOperations.count}")

        for o_idx in range(setup.allOperations.count):
            op = setup.allOperations.item(o_idx)
            tool_info = ""
            if op.tool:
                dia = op.tool.parameters.itemByName('tool_diameter')
                tool_info = f"Ø{dia.value*10:.1f}mm {op.tool.typeName}" if dia else op.tool.typeName
            status = "✓" if op.hasToolpath and op.isValid else "✗"
            print(f"  {status} [{o_idx}] {op.name:35s}  {op.strategy:20s}  {tool_info}")
