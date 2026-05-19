"""
MCP_DESIGN_13_Revolve_a_sketch_profile_around_an_axis
=====================================================
Group       : Design
Script ID   : DESIGN-13
Description : Revolve a sketch profile around an axis
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_13_Revolve_a_sketch_profile_around_an_axis

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    # Sketch a rectangular profile and an axis line on the world XZ plane.
    # Profile sits at X = 15..18 cm, Z = 1..3 cm (above the floor, offset in
    # +X away from Bracket/MountingPlate). Axis runs along world X at Z=0.
    sk = root.sketches.add(root.xZConstructionPlane)
    sk.name = "Sketch_RevolveProfile"
    lines = sk.sketchCurves.sketchLines

    # Profile rectangle (closed loop)
    p1 = adsk.core.Point3D.create(15.0, 1.0, 0)
    p2 = adsk.core.Point3D.create(18.0, 1.0, 0)
    p3 = adsk.core.Point3D.create(18.0, 3.0, 0)
    p4 = adsk.core.Point3D.create(15.0, 3.0, 0)
    lines.addByTwoPoints(p1, p2)
    lines.addByTwoPoints(p2, p3)
    lines.addByTwoPoints(p3, p4)
    lines.addByTwoPoints(p4, p1)

    # Axis line on local X (world X at Z=0)
    axis_line = lines.addByTwoPoints(
        adsk.core.Point3D.create(14.0, 0, 0),
        adsk.core.Point3D.create(19.0, 0, 0),
    )

    # Pick the rectangle profile (the one whose bbox does NOT touch the axis)
    prof = None
    for i in range(sk.profiles.count):
        pr = sk.profiles.item(i)
        bb = pr.boundingBox
        # Profile rectangle: y in 1..3 cm; axis line has y=0 endpoints
        if bb.minPoint.y >= 0.99:
            prof = pr
            break

    rev_in = root.features.revolveFeatures.createInput(
        prof, axis_line,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    rev_in.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
    rev = root.features.revolveFeatures.add(rev_in)
    ring = rev.bodies.item(0)
    ring.name = "RevolveRing"
    # Expected volume: π × (Ro² − Ri²) × width
    #                = π × (3² − 1²) × 3 = π × 8 × 3 = 75.40 cm³
    print(f"RevolveRing: faces={ring.faces.count} vol={ring.volume:.3f} cm³ "
          f"(expected ~75.40)")
