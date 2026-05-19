

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
# CAM-18  Slot (treats the 70x30 mm Bracket pocket as a slot path)
#         Slot strategy follows the centerline of a slot-like pocket with one
#         pass per stepdown. Different motion pattern from pocket2d's spiral.
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
        print("No ~6 mm flat end mill found.")
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

    chosen = None
    for i in range(library.count):
        t = library.item(i)
        p = t.parameters
        type_param = p.itemByName('tool_type')
        if type_param and type_param.value.value == 'thread mill':
            chosen = t
            break
    if chosen is None:
        for i in range(library.count):
            t = library.item(i)
            desc = (t.description or '').lower()
            if 'thread' in desc:
                chosen = t
                break
    if chosen is None:
        print("No thread mill in 'Milling Tools (Metric)'.")
        return

    op_input.tool = chosen
    print(f"Tool: {chosen.description}")

    params = op_input.parameters
    params.itemByName("threadPitch").expression = "1 mm"
    # 'threadType' default 'ISO Metric profile' is fine.

    op = setup.operations.add(op_input)

    bracket = next(b for b in cam.designRootOccurrence.bRepBodies if b.name == 'Bracket')
    m6_cyls = [f for f in bracket.faces
               if isinstance(f.geometry, adsk.core.Cylinder)
               and abs(f.geometry.radius - 0.3) < 0.05]
    op.parameters.itemByName('circularFaces').value.value = m6_cyls
    print(f"Operation added: {op.name}  strategy={op.strategy}  ({len(m6_cyls)} holes)")
