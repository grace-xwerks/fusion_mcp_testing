"""
MCP_DESIGN_30_Build_the_Rotor_part_Batch_D_rotary
=================================================
Group       : Design
Script ID   : DESIGN-30
Description : Build the Rotor part (Batch D rotary stock)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_30_Build_the_Rotor_part_Batch_D_rotary

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.fusion, math

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    p    = des.userParameters

    def pv(name):
        return p.itemByName(name).value

    L         = pv("rotor_length")
    R_main    = pv("rotor_od") / 2.0
    R_shoul   = pv("rotor_shoulder_od") / 2.0
    L_shoul   = pv("rotor_shoulder_len")
    R_bore    = pv("rotor_bore_dia") / 2.0
    L_bore    = pv("rotor_bore_len")
    R_dome    = pv("rotor_dome_r")
    G_x       = pv("rotor_groove_x")
    G_w       = pv("rotor_groove_w")
    G_d       = pv("rotor_groove_depth")
    F_x0      = pv("rotor_flat_x0")
    F_x1      = pv("rotor_flat_x1")
    F_inset   = pv("rotor_flat_inset")

    # Dome begins where the main body ends (X = L - R_dome) and arcs to (L, 0).
    X_dome_start = L - R_dome

    # ── New sub-component so the Rotor is independent of the Bracket ─────────
    occ  = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = "Rotor"

    # ── 1. Revolve outer profile around the X axis ───────────────────────────
    # Profile lives in the XY sketch plane: X is axial, Y is radius.
    # Polyline starts on the rotation axis, walks the silhouette, returns.
    sk_rev = comp.sketches.add(comp.xYConstructionPlane)
    sk_rev.name = "Sketch_RotorProfile"
    lines = sk_rev.sketchCurves.sketchLines
    P1 = adsk.core.Point3D.create(0,            0,       0)
    P2 = adsk.core.Point3D.create(0,            R_shoul, 0)
    P3 = adsk.core.Point3D.create(L_shoul,      R_shoul, 0)
    P4 = adsk.core.Point3D.create(L_shoul,      R_main,  0)
    P5 = adsk.core.Point3D.create(X_dome_start, R_main,  0)
    P6 = adsk.core.Point3D.create(L,            0,       0)
    lines.addByTwoPoints(P1, P2)
    lines.addByTwoPoints(P2, P3)
    lines.addByTwoPoints(P3, P4)
    lines.addByTwoPoints(P4, P5)
    # Quarter-arc dome: center (X_dome_start, 0), radius R_dome, from P5 to P6.
    mid_dome = adsk.core.Point3D.create(
        X_dome_start + R_dome * math.cos(math.pi / 4),
        R_dome * math.sin(math.pi / 4),
        0)
    sk_rev.sketchCurves.sketchArcs.addByThreePoints(P5, mid_dome, P6)
    lines.addByTwoPoints(P6, P1)   # back along the axis to close the loop

    rev_in = comp.features.revolveFeatures.createInput(
        sk_rev.profiles.item(0),
        comp.xConstructionAxis,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    rev_in.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
    body = comp.features.revolveFeatures.add(rev_in).bodies.item(0)
    body.name = "Rotor"
    print(f"Rotor solid: revolved {sk_rev.profiles.item(0).profileLoops.count}-loop profile, "
          f"vol={body.volume:.2f} cm³")

    # ── 2. Axial bore (revolve-cut) ──────────────────────────────────────────
    sk_bore = comp.sketches.add(comp.xYConstructionPlane)
    sk_bore.name = "Sketch_RotorBore"
    sk_bore.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0,      0,      0),
        adsk.core.Point3D.create(L_bore, R_bore, 0))
    bore_in = comp.features.revolveFeatures.createInput(
        sk_bore.profiles.item(0),
        comp.xConstructionAxis,
        adsk.fusion.FeatureOperations.CutFeatureOperation)
    bore_in.participantBodies = [body]
    bore_in.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
    comp.features.revolveFeatures.add(bore_in)
    print(f"Axial bore: Ø{R_bore*20:.0f} mm × {L_bore*10:.0f} mm deep")

    # ── 3. Circumferential groove (revolve-cut on the OD) ────────────────────
    # Rectangle straddles the OD so the cut reliably clears the cylindrical
    # face (outer Y slightly past R_main avoids tangency edge cases).
    sk_grv = comp.sketches.add(comp.xYConstructionPlane)
    sk_grv.name = "Sketch_RotorGroove"
    sk_grv.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(G_x,       R_main - G_d, 0),
        adsk.core.Point3D.create(G_x + G_w, R_main + 0.1, 0))
    grv_in = comp.features.revolveFeatures.createInput(
        sk_grv.profiles.item(0),
        comp.xConstructionAxis,
        adsk.fusion.FeatureOperations.CutFeatureOperation)
    grv_in.participantBodies = [body]
    grv_in.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
    comp.features.revolveFeatures.add(grv_in)
    print(f"OD groove: {G_w*10:.0f} mm wide × {G_d*10:.0f} mm deep at X={G_x*10:.0f} mm")

    # ── 4. Two opposing milled flats (symmetric extrude-cut from XZ plane) ───
    # Sketch lives in the XZ plane (normal = +Y). Sketch axes map to (X, Z).
    # Each rectangle is a planar window cut radially into the cylinder by
    # extruding symmetrically along ±Y past the OD.
    Z_flat = R_main - F_inset
    sk_flat = comp.sketches.add(comp.xZConstructionPlane)
    sk_flat.name = "Sketch_RotorFlats"
    overshoot = R_main + 0.5   # ensure the cut clears the OD on the open side
    sk_flat.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(F_x0, Z_flat,    0),
        adsk.core.Point3D.create(F_x1, overshoot, 0))
    sk_flat.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(F_x0, -overshoot, 0),
        adsk.core.Point3D.create(F_x1, -Z_flat,    0))
    flat_profs = adsk.core.ObjectCollection.create()
    for i in range(sk_flat.profiles.count):
        flat_profs.add(sk_flat.profiles.item(i))
    flat_in = comp.features.extrudeFeatures.createInput(
        flat_profs, adsk.fusion.FeatureOperations.CutFeatureOperation)
    flat_in.participantBodies = [body]
    # Symmetric in ±Y, total length = OD + 20 mm to clear the body cleanly.
    flat_in.setSymmetricExtent(
        adsk.core.ValueInput.createByReal(2 * R_main + 2.0), True)
    comp.features.extrudeFeatures.add(flat_in)
    print(f"Flats: 2× planar pockets {(F_x1-F_x0)*10:.0f} mm long, "
          f"inset {F_inset*10:.0f} mm from OD")

    # ── 5. Chamfer the shoulder transition edge (deburr target) ──────────────
    # The shoulder step at X = L_shoul produces a circular edge where the
    # Ø30 shoulder meets the Ø40 main body. Find it by inspecting edges
    # whose vertices both sit at that X and at radius R_main.
    shoul_edges = adsk.core.ObjectCollection.create()
    for e in body.edges:
        if not isinstance(e.geometry, adsk.core.Circle3D):
            continue
        c = e.geometry.center
        r = e.geometry.radius
        if abs(c.x - L_shoul) < 1e-4 and abs(r - R_main) < 1e-4:
            shoul_edges.add(e)
    if shoul_edges.count > 0:
        cham_in = comp.features.chamferFeatures.createInput(shoul_edges, True)
        cham_in.setToEqualDistance(adsk.core.ValueInput.createByReal(0.1))   # 1 mm
        comp.features.chamferFeatures.add(cham_in)
        print(f"Chamfer: 1 mm on {shoul_edges.count} shoulder edge(s)")
    else:
        print("Warning: shoulder edge not found — chamfer skipped")

    # ── Summary ──────────────────────────────────────────────────────────────
    bb = body.boundingBox
    dx = (bb.maxPoint.x - bb.minPoint.x) * 10
    dy = (bb.maxPoint.y - bb.minPoint.y) * 10
    dz = (bb.maxPoint.z - bb.minPoint.z) * 10
    print(f"\nRotor complete: bbox {dx:.1f} × {dy:.1f} × {dz:.1f} mm, "
          f"{body.faces.count} faces, {body.edges.count} edges")
    print("Batch D targets on this part:")
    print("  rotary_contour    → milled flats on the OD")
    print("  rotary_pocket     → circumferential groove")
    print("  rotary_finishing  → quarter-sphere dome on the +X end")
    print("  geodesic          → quarter-sphere dome")
    print("  deburr            → shoulder + groove + flat edges")
