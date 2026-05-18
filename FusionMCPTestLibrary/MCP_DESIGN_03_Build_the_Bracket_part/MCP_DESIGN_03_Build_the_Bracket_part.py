"""
MCP_DESIGN_03_Build_the_Bracket_part
====================================
Group       : Design
Script ID   : DESIGN-03
Description : Build the Bracket part
Generated   : 2026-05-18

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_03_Build_the_Bracket_part

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion, math

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    p    = des.userParameters   # shorthand

    def pv(name):
        """Return parameter value in cm."""
        return p.itemByName(name).value

    L  = pv("part_length")   # 10 cm
    W  = pv("part_width")    # 6 cm
    H  = pv("part_height")   # 2 cm
    PD = pv("pocket_depth")  # 0.8 cm
    HD = pv("hole_dia")      # 0.6 cm
    CH = pv("chamfer_size")  # 0.1 cm
    CR = pv("corner_rad")    # 0.2 cm

    # ── 1. Base body ─────────────────────────────────────────────────────────
    sk_base = root.sketches.add(root.xYConstructionPlane)
    sk_base.name = "Sketch_Base"
    sk_base.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(L, W, 0)
    )
    ext_in = root.features.extrudeFeatures.createInput(
        sk_base.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(H))
    base_ext = root.features.extrudeFeatures.add(ext_in)
    body = base_ext.bodies.item(0)
    body.name = "Bracket"
    print(f"Base body created: {L*10:.0f} x {W*10:.0f} x {H*10:.0f} mm")

    # ── 2. Rectangular pocket ────────────────────────────────────────────────
    # Centered on the top face, leaving a 15 mm wall all around
    wall  = 1.5   # cm
    pk_l  = L - 2*wall
    pk_w  = W - 2*wall

    # Quirk: in Fusion 2703.x, a CutFeature whose sketch sits on a body face
    # silently fails when its extent is a DistanceExtentDefinition — it returns
    # 0 faces and removes no volume (ThroughAll works fine on a face, but
    # fixed-depth does not). Workaround: sketch on a construction plane
    # offset to the same Z as the top face.
    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(H))
    pocket_plane = root.constructionPlanes.add(cpi)
    pocket_plane.name = "Plane_Pocket"

    sk_pocket = root.sketches.add(pocket_plane)
    sk_pocket.name = "Sketch_Pocket"
    sk_pocket.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(wall, wall, 0),
        adsk.core.Point3D.create(wall+pk_l, wall+pk_w, 0)
    )
    # Fillet the pocket sketch corners (inside corner radius = CR)
    segs = list(sk_pocket.sketchCurves.sketchLines)
    for i in range(4):
        l1 = segs[i]
        l2 = segs[(i+1) % 4]
        sk_pocket.sketchCurves.sketchArcs.addFillet(
            l1, l1.endSketchPoint.geometry,
            l2, l2.startSketchPoint.geometry,
            CR
        )
    # Sketched on a construction plane: there's exactly one profile (the
    # filleted rectangle). No outer-region profile to filter out.
    inner_pocket = sk_pocket.profiles.item(0)
    pocket_ext_in = root.features.extrudeFeatures.createInput(
        inner_pocket,
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    pocket_ext_in.participantBodies = [body]
    pocket_ext_in.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByReal(PD)
        ),
        adsk.fusion.ExtentDirections.NegativeExtentDirection
    )
    root.features.extrudeFeatures.add(pocket_ext_in)
    print(f"Pocket cut: {pk_l*10:.0f} x {pk_w*10:.0f} mm, depth {PD*10:.0f} mm, r={CR*10:.0f} mm corners")

    # ── 3. 4x through holes (counterbore pattern) ────────────────────────────
    hole_inset = 1.0   # cm from edge to hole center
    hole_positions = [
        (hole_inset,       hole_inset      ),
        (L - hole_inset,   hole_inset      ),
        (hole_inset,       W - hole_inset  ),
        (L - hole_inset,   W - hole_inset  ),
    ]

    # Re-find the top face after the pocket cut altered the body topology.
    top_face = None
    for face in body.faces:
        if abs(face.centroid.z - H) < 0.001:
            bbox = face.boundingBox
            if (bbox.maxPoint.x - bbox.minPoint.x) > 0.9 * L:
                top_face = face
                break

    sk_holes = root.sketches.add(top_face)
    sk_holes.name = "Sketch_Holes"
    for (x, y) in hole_positions:
        sk_holes.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(x, y, H),
            HD / 2
        )

    # Sketching circles on a face produces N+1 profiles (the N circles plus
    # the outer face-region). Keep only the circle profiles (small bbox).
    circle_profiles = adsk.core.ObjectCollection.create()
    for i in range(sk_holes.profiles.count):
        pr = sk_holes.profiles.item(i)
        bb = pr.boundingBox
        if (bb.maxPoint.x - bb.minPoint.x) < HD * 1.5:
            circle_profiles.add(pr)
    holes_ext_in = root.features.extrudeFeatures.createInput(
        circle_profiles,
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    holes_ext_in.participantBodies = [body]
    holes_ext_in.setOneSideExtent(
        adsk.fusion.ThroughAllExtentDefinition.create(),
        adsk.fusion.ExtentDirections.NegativeExtentDirection
    )
    root.features.extrudeFeatures.add(holes_ext_in)
    print(f"4x Ø{HD*10:.0f} mm through holes added at corners")

    # ── 4. Chamfer top perimeter edges ───────────────────────────────────────
    top_edges = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        # Top perimeter edges: both endpoints at Z = H and it's a horizontal edge
        pt1 = edge.startVertex.geometry
        pt2 = edge.endVertex.geometry
        if abs(pt1.z - H) < 0.001 and abs(pt2.z - H) < 0.001:
            top_edges.add(edge)

    if top_edges.count > 0:
        cham_in = root.features.chamferFeatures.createInput(top_edges, True)
        cham_in.setToEqualDistance(adsk.core.ValueInput.createByReal(CH))
        root.features.chamferFeatures.add(cham_in)
        print(f"Chamfer: {CH*10:.1f} mm on {top_edges.count} top edges")

    print("\nBracket part complete — ready for Manufacture workspace.")
