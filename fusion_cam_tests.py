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
        is_mill = p.itemByName('tool_isMill').value
        if not is_mill:
            continue
        taper = p.itemByName('tool_taperedType')
        if taper and taper.value not in ('flat', 'straight', ''):
            continue
        dia_mm = p.itemByName('tool_diameter').value * 10
        if 8.0 <= dia_mm <= 10.0:
            chosen = t
            break

    if chosen is None:
        print("No 8–10 mm flat end mill found in 'Milling Tools (Metric)'.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  Ø{chosen.parameters.itemByName('tool_diameter').value*10:.1f} mm")

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
        if not p.itemByName('tool_isMill').value:
            continue
        taper = p.itemByName('tool_taperedType')
        if taper and taper.value not in ('flat', 'straight', ''):
            continue
        dia_mm = p.itemByName('tool_diameter').value * 10
        if 5.5 <= dia_mm <= 6.5:
            chosen = t
            break

    if chosen is None:
        print("No ~6 mm flat end mill found in 'Milling Tools (Metric)'.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  Ø{chosen.parameters.itemByName('tool_diameter').value*10:.1f} mm")

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
        if not p.itemByName('tool_isMill').value:
            continue
        taper = p.itemByName('tool_taperedType')
        if taper and taper.value not in ('flat', 'straight', ''):
            continue
        dia_mm = p.itemByName('tool_diameter').value * 10
        if 8.0 <= dia_mm <= 10.0:
            chosen = t
            break

    if chosen is None:
        print("No 8–10 mm flat end mill found in 'Milling Tools (Metric)'.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}  Ø{chosen.parameters.itemByName('tool_diameter').value*10:.1f} mm")

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
        if is_drill is None or not is_drill.value:
            continue
        dia_mm = p.itemByName('tool_diameter').value * 10
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
              f"Ø{spot.parameters.itemByName('tool_diameter').value*10:.2f} mm")
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
              f"Ø{drill.parameters.itemByName('tool_diameter').value*10:.2f} mm")
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
