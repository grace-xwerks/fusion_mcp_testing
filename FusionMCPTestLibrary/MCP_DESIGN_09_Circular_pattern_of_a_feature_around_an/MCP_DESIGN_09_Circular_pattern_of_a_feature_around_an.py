"""
MCP_DESIGN_09_Circular_pattern_of_a_feature_around_an
=====================================================
Group       : Design
Script ID   : DESIGN-09
Description : Circular pattern of a feature around an axis
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_09_Circular_pattern_of_a_feature_around_an

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    body = next((b for b in root.bRepBodies if b.name == "Bracket"), None)
    if body is None:
        print("Bracket not found. Run DESIGN-03 first.")
        return

    H = des.userParameters.itemByName("part_height").value

    # Tiny pin on the front rim, offset from the part center so the circular
    # pattern produces an interesting fan of pins. (1.5, 0.75) avoids the
    # existing M5 drill at (5, 0.75) added by DESIGN-07.
    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(H))
    plane = root.constructionPlanes.add(cpi); plane.name = "Plane_CircPatternSeed"
    sk = root.sketches.add(plane); sk.name = "Sketch_PinSeed"
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(1.5, 0.75, 0), 0.15)   # 3 mm Ø pin
    ein = root.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
    ein.participantBodies = [body]
    ein.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByReal(0.3)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection)
    seed = root.features.extrudeFeatures.add(ein); seed.name = "PinSeed"

    # ConstructionAxes.setByLine wants an existing line reference (sketch line
    # or edge), not a raw InfiniteLine3D. Define the axis as the intersection
    # of two offset construction planes instead — cleanest way to put a
    # vertical axis at an arbitrary (X, Y) in the world.
    yzo = root.constructionPlanes.createInput()
    yzo.setByOffset(root.yZConstructionPlane, adsk.core.ValueInput.createByReal(5.0))
    plane_x5 = root.constructionPlanes.add(yzo); plane_x5.name = "Plane_X5"
    xzo = root.constructionPlanes.createInput()
    xzo.setByOffset(root.xZConstructionPlane, adsk.core.ValueInput.createByReal(3.0))
    plane_y3 = root.constructionPlanes.add(xzo); plane_y3.name = "Plane_Y3"

    ai = root.constructionAxes.createInput()
    ai.setByTwoPlanes(plane_x5, plane_y3)
    axis = root.constructionAxes.add(ai)
    axis.name = "Axis_CenterZ"

    input_set = adsk.core.ObjectCollection.create()
    input_set.add(seed)
    cp_in = root.features.circularPatternFeatures.createInput(input_set, axis)
    cp_in.quantity = adsk.core.ValueInput.createByReal(8)
    cp_in.totalAngle = adsk.core.ValueInput.createByString("360 deg")
    cp_in.isSymmetric = False
    cp = root.features.circularPatternFeatures.add(cp_in)
    cp.name = "Pattern_Pins_8x"
    print(f"Circular pattern: 8 pins around Z axis at (50, 30)")
    print(f"Body faces now: {body.faces.count}  vol: {body.volume:.3f} cm³")
