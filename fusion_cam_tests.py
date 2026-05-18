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
    prod = app.activeProduct

    print(f"Active product type: {prod.productType}")

    cam = adsk.cam.CAM.cast(prod)
    if not cam:
        print("ERROR: Not in the Manufacture workspace.")
        print("Switch to Manufacture in Fusion before running CAM scripts.")
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
#         Lists tools available in the local (document) library.
# =============================================================================

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


# =============================================================================
# CAM-03  Create a milling setup for the Bracket part
#         Sets up WCS at top-left corner of stock (typical VMC setup).
# =============================================================================

import adsk.core, adsk.cam, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first.")
        return

    des  = adsk.fusion.Design.cast(
        app.documents.itemByName(cam.designRootName).products.item(0)
    ) if False else None  # we'll use cam's linked design

    # Get the body from the active design linked to this CAM product
    # The CAM product has a reference to the design
    setup_input = cam.setups.createInput(adsk.cam.OperationTypes.MillingOperation)
    setup_input.name = "Op1_Top_Side"

    # Stock: use bounding box + 2 mm offset on sides, 1 mm on top
    stock_input = setup_input.stockInput
    stock_input.stockSelectionType = adsk.cam.StockSelectionTypes.RelativeBoxStockType
    stock_offsets = adsk.cam.BoxStockOffsets.create(
        adsk.core.ValueInput.createByString("0.1 mm"),  # +X
        adsk.core.ValueInput.createByString("0.1 mm"),  # -X
        adsk.core.ValueInput.createByString("0.1 mm"),  # +Y
        adsk.core.ValueInput.createByString("0.1 mm"),  # -Y
        adsk.core.ValueInput.createByString("1 mm"),    # +Z (top stock)
        adsk.core.ValueInput.createByString("0 mm"),    # -Z (bottom fixed)
    )
    stock_input.setRelativeBoxStock(stock_offsets)

    setup = cam.setups.add(setup_input)
    print(f"Setup created: {setup.name}")
    print(f"Operation type: Milling")
    print(f"Stock: bounding box + 1 mm top, 0.1 mm sides")
    print(f"\nNow use CAM-04 through CAM-09 to add operations.")


# =============================================================================
# CAM-04  Add a Facing operation (flatten stock top)
#         First op in any milling sequence per CNC Fundamentals lesson 7.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first.")
        return

    if cam.setups.count == 0:
        print("No setups found — run CAM-03 first.")
        return

    setup = cam.setups.item(0)

    op_input = setup.operations.createInput("face")
    op_input.displayName = "1_Facing"

    # Tool: first flat endmill or face mill in library
    for i in range(cam.documentToolLibrary.count):
        t = cam.documentToolLibrary.item(i)
        if t.typeName in ("flat end mill", "face mill"):
            op_input.tool = t
            print(f"Tool selected: {t.description}  Ø{t.parameters.itemByName('tool_diameter').value*10:.1f} mm")
            break

    # Facing parameters
    params = op_input.parameters
    params.itemByName("tolerance").value        = adsk.core.ValueInput.createByString("0.01 mm")
    params.itemByName("stepover").value         = adsk.core.ValueInput.createByString("75%")
    params.itemByName("stockToLeave").value     = adsk.core.ValueInput.createByString("0 mm")
    params.itemByName("bottomHeight").value     = adsk.core.ValueInput.createByString("0 mm")  # machine to exact Z0

    op = setup.operations.add(op_input)
    print(f"Operation added: {op.name}  strategy={op.strategy}")


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
