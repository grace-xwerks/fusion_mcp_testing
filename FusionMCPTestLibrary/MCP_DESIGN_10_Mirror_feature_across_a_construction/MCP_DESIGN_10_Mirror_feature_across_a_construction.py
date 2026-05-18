"""
MCP_DESIGN_10_Mirror_feature_across_a_construction
==================================================
Group       : Design
Script ID   : DESIGN-10
Description : Mirror feature across a construction plane
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_10_Mirror_feature_across_a_construction

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

    # Seed: a 3×3×2 mm boss on the +Y half of the part (y=4.5)
    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(H))
    plane = root.constructionPlanes.add(cpi); plane.name = "Plane_MirrorSeed"
    sk = root.sketches.add(plane); sk.name = "Sketch_MirrorSeed"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0.5, 4.7, 0),
        adsk.core.Point3D.create(0.8, 5.0, 0))
    ein = root.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
    ein.participantBodies = [body]
    ein.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByReal(0.2)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection)
    seed = root.features.extrudeFeatures.add(ein); seed.name = "MirrorSeed"

    # Mirror plane: construction plane at Y = part_width / 2 = 3.0 cm,
    # parallel to XZ.
    W = des.userParameters.itemByName("part_width").value
    mp_in = root.constructionPlanes.createInput()
    mp_in.setByOffset(root.xZConstructionPlane,
                      adsk.core.ValueInput.createByReal(W / 2.0))
    mirror_plane = root.constructionPlanes.add(mp_in)
    mirror_plane.name = "Plane_MirrorMid"

    input_set = adsk.core.ObjectCollection.create()
    input_set.add(seed)
    m_in = root.features.mirrorFeatures.createInput(input_set, mirror_plane)
    mirror = root.features.mirrorFeatures.add(m_in)
    mirror.name = "Mirror_Seed_acrossMid"
    print(f"Mirrored MirrorSeed across XZ plane at Y={W*10/2:.0f} mm")
    print(f"Body faces now: {body.faces.count}  vol: {body.volume:.3f} cm³")
