"""
MCP_DESIGN_07_Hole_feature_proper_HoleFeatures_API
==================================================
Group       : Design
Script ID   : DESIGN-07
Description : Hole feature (proper HoleFeatures API): simple + counterbore
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_07_Hole_feature_proper_HoleFeatures_API

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

    H = des.userParameters.itemByName("part_height").value   # 2 cm

    # Quirk #8 applies to HoleFeatures too: sketch points placed on a body
    # face cause the hole to silently no-op. Sketch the drill points on a
    # construction plane offset to the top instead.
    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(H))
    drill_plane = root.constructionPlanes.add(cpi)
    drill_plane.name = "Plane_HoleSeed"
    sk = root.sketches.add(drill_plane)
    sk.name = "Sketch_HolePoints"
    pt_drill = sk.sketchPoints.add(adsk.core.Point3D.create(5.0, 0.75, 0))
    pt_cbore = sk.sketchPoints.add(adsk.core.Point3D.create(5.0, 5.25, 0))

    holes = root.features.holeFeatures
    vol0 = body.volume

    # ── Simple drilled hole: Ø5 mm × 10 mm deep ───────────────────────────────
    simple_in = holes.createSimpleInput(adsk.core.ValueInput.createByReal(0.5))
    simple_in.participantBodies = [body]
    simple_in.setPositionBySketchPoint(pt_drill)
    simple_in.setDistanceExtent(adsk.core.ValueInput.createByReal(1.0))
    drilled = holes.add(simple_in)
    drilled.name = "Drilled_5mm"
    print(f"Drilled Ø5 mm × 10 mm at (50, 7.5, top): "
          f"faces={drilled.faces.count} Δvol={vol0 - body.volume:+.3f} cm³")
    vol1 = body.volume

    # ── Counterbored hole: Ø4 mm shaft, Ø8 mm × 3 mm cbore, 15 mm deep ────────
    cbore_in = holes.createCounterboreInput(
        adsk.core.ValueInput.createByReal(0.4),    # hole Ø  = 4 mm
        adsk.core.ValueInput.createByReal(0.8),    # cbore Ø = 8 mm
        adsk.core.ValueInput.createByReal(0.3),    # cbore depth = 3 mm
    )
    cbore_in.participantBodies = [body]
    cbore_in.setPositionBySketchPoint(pt_cbore)
    cbore_in.setDistanceExtent(adsk.core.ValueInput.createByReal(1.5))
    cbored = holes.add(cbore_in)
    cbored.name = "Counterbore_M4"
    print(f"Counterbore Ø4 mm × 15 mm with Ø8 mm × 3 mm at (50, 52.5, top): "
          f"faces={cbored.faces.count} Δvol={vol1 - body.volume:+.3f} cm³")

    print(f"\nTotal hole features: {holes.count}  body faces: {body.faces.count}  "
          f"final vol: {body.volume:.3f} cm³")
