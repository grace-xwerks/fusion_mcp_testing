"""
MCP_DESIGN_08_Rectangular_pattern_of_a_feature
==============================================
Group       : Design
Script ID   : DESIGN-08
Description : Rectangular pattern of a feature
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_08_Rectangular_pattern_of_a_feature

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

    # Sketch a small 3×3 mm boss on a construction plane at top
    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(H))
    plane = root.constructionPlanes.add(cpi)
    plane.name = "Plane_PatternSeed"
    sk = root.sketches.add(plane)
    sk.name = "Sketch_BossSeed"
    # Seed boss placed on the front-rim (Y < pocket inner edge of 1.5 cm).
    # Y spacing of 5 cm puts the second pattern row on the back rim (Y > 4.5),
    # so all 6 instances actually join material instead of floating over the
    # pocket.
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0.5, 0.5, 0),
        adsk.core.Point3D.create(0.8, 0.8, 0),
    )
    ein = root.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
    ein.participantBodies = [body]
    ein.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByReal(0.2)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection)
    seed = root.features.extrudeFeatures.add(ein)
    seed.name = "BossSeed"
    print(f"Seed boss extruded (+Z 2 mm, 3×3 mm), body faces now {body.faces.count}")

    # Rectangular pattern: 3 along X (spacing 4 cm), 2 along Y (spacing 5 cm)
    input_set = adsk.core.ObjectCollection.create()
    input_set.add(seed)
    pat_in = root.features.rectangularPatternFeatures.createInput(
        input_set,
        root.xConstructionAxis,
        adsk.core.ValueInput.createByReal(3),
        adsk.core.ValueInput.createByReal(4.0),
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType,
    )
    pat_in.setDirectionTwo(
        root.yConstructionAxis,
        adsk.core.ValueInput.createByReal(2),
        adsk.core.ValueInput.createByReal(5.0),
    )
    pat = root.features.rectangularPatternFeatures.add(pat_in)
    pat.name = "Pattern_Bosses_3x2"
    print(f"Rectangular pattern: 3×2, spacing 20 mm × 40 mm")
    print(f"Body faces now: {body.faces.count}  vol: {body.volume:.3f} cm³")
