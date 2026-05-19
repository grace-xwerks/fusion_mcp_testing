

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
    # Prefer small ball (~2 mm) to fit pocket corner radii (~2 mm); fall back
    # to a 6 mm ball.
    chosen = None
    for i in range(library.count):
        t = library.item(i); p = t.parameters
        tt = p.itemByName('tool_type')
        if not tt or tt.value.value != 'ball end mill': continue
        dia_mm = p.itemByName('tool_diameter').value.value * 10
        if 1.5 <= dia_mm <= 3.0:
            chosen = t; break
    if chosen is None:
        for i in range(library.count):
            t = library.item(i); p = t.parameters
            tt = p.itemByName('tool_type')
            if not tt or tt.value.value != 'ball end mill': continue
            dia_mm = p.itemByName('tool_diameter').value.value * 10
            if 5.5 <= dia_mm <= 6.5:
                chosen = t; break
    if chosen is None:
        print("No ball end mill."); return
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
