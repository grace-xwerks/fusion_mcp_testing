"""
MCP_DESIGN_15_Rib_equivalent_gusset_on_an_L_shaped
==================================================
Group       : Design
Script ID   : DESIGN-15
Description : Rib-equivalent gusset on an L-shaped body (via symmetric extrude)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_15_Rib_equivalent_gusset_on_an_L_shaped

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    # ── 1. Build an L-shape body at X = -5..-1, Y = 8..11 ───────────────────
    sk_L = root.sketches.add(root.xYConstructionPlane)
    sk_L.name = "Sketch_LShape"
    lines = sk_L.sketchCurves.sketchLines
    pts = [
        adsk.core.Point3D.create(-5.0,  8.0, 0),
        adsk.core.Point3D.create(-1.0,  8.0, 0),
        adsk.core.Point3D.create(-1.0,  8.5, 0),
        adsk.core.Point3D.create(-4.5,  8.5, 0),
        adsk.core.Point3D.create(-4.5, 11.0, 0),
        adsk.core.Point3D.create(-5.0, 11.0, 0),
    ]
    for i in range(len(pts)):
        lines.addByTwoPoints(pts[i], pts[(i+1) % len(pts)])

    ein = root.features.extrudeFeatures.createInput(
        sk_L.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ein.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.0))   # 20 mm tall
    Lbody = root.features.extrudeFeatures.add(ein).bodies.item(0)
    Lbody.name = "RibTestL"
    print(f"L body: faces={Lbody.faces.count} vol={Lbody.volume:.3f} cm³")

    # ── 2. Gusset triangle in XY plane, in the inside-corner void ───────────
    # Corner edge runs along Z at (X=-4.5, Y=8.5). Triangle vertices:
    #   A (-4.5, 8.5)  — on the corner edge
    #   B (-3.5, 8.5)  — along floor's top face (Y=8.5, X∈[-5,-1])
    #   C (-4.5, 9.5)  — along back wall's inside face (X=-4.5, Y∈[8,11])
    sk_rib = root.sketches.add(root.xYConstructionPlane)
    sk_rib.name = "Sketch_RibGusset"
    rl = sk_rib.sketchCurves.sketchLines
    a = adsk.core.Point3D.create(-4.5, 8.5, 0)
    b = adsk.core.Point3D.create(-3.5, 8.5, 0)
    c = adsk.core.Point3D.create(-4.5, 9.5, 0)
    rl.addByTwoPoints(a, b)
    rl.addByTwoPoints(b, c)
    rl.addByTwoPoints(c, a)

    # The L-shape sketch on xYConstructionPlane produced its own face-region
    # profiles. Pick the small triangle profile by bbox size.
    triangle_prof = None
    for i in range(sk_rib.profiles.count):
        pr = sk_rib.profiles.item(i)
        bb = pr.boundingBox
        dx = bb.maxPoint.x - bb.minPoint.x
        dy = bb.maxPoint.y - bb.minPoint.y
        if dx < 1.5 and dy < 1.5:
            triangle_prof = pr
            break

    # ── 3. Extrude +Z by full body height = 2 cm, Join with L-body ──────────
    rib_in = root.features.extrudeFeatures.createInput(
        triangle_prof,
        adsk.fusion.FeatureOperations.JoinFeatureOperation)
    rib_in.participantBodies = [Lbody]
    rib_in.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByReal(2.0)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection)
    rib_feat = root.features.extrudeFeatures.add(rib_in)
    rib_feat.name = "Rib_Gusset"
    # Expected Δvol: triangle area 0.5 × extrusion height 2 = 1.0 cm³
    print(f"After rib gusset (Δ expected +1.00): faces={Lbody.faces.count} "
          f"vol={Lbody.volume:.3f} cm³")
