"""
Fusion MCP — Design Workspace Test Scripts
==========================================
Focused on manufacturing-ready geometry: the kinds of features that map
directly to CAM operations (Facing, 2D Pocket, 2D Contour, Drill, Chamfer).

All units: CENTIMETERS internally. Expressions use "mm" for readability.
Entry point for every script: def run(_context: str):
No try/except — let exceptions propagate as error signals.

PART STRATEGY (from CNC Fundamentals / HEM guidebook context):
  The "Bracket" part below is a 2.5D prismatic part — the most common
  real-world case. It has:
    - A flat face (→ Facing toolpath)
    - Rectangular pocket (→ 2D Pocket)
    - Boss / outside contour (→ 2D Contour)
    - Counterbored holes (→ Drill + Circular Pocket)
    - Chamfer on top edges (→ Chamfer Mill)
    - Fillets on inside pocket corners (→ end mill corner radius constraint)
"""

# =============================================================================
# DESIGN-01  Inspect active design — workspace and product type check
#            Run this first. Verifies you're in the Design workspace.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    prod = app.activeProduct

    print(f"Product type  : {prod.productType}")
    print(f"Design type   : {adsk.fusion.Design.cast(prod).designType}")
    # designType: 0=DirectDesign, 1=ParametricDesign
    des = adsk.fusion.Design.cast(prod)
    print(f"Parametric    : {des.designType == adsk.fusion.DesignTypes.ParametricDesignType}")
    print(f"Root comp     : {des.rootComponent.name}")
    print(f"Bodies        : {des.rootComponent.bRepBodies.count}")
    print(f"User params   : {des.userParameters.count}")
    print(f"Fusion version: {app.version}")


# =============================================================================
# DESIGN-02  Set up manufacturing parameters
#            Driven parameters you'll reference across Design + CAM scripts.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app    = adsk.core.Application.get()
    des    = adsk.fusion.Design.cast(app.activeProduct)
    params = des.userParameters

    # Clear any existing test params first (skip if they don't exist)
    for name in ["part_length", "part_width", "part_height",
                 "pocket_depth", "hole_dia", "chamfer_size", "corner_rad"]:
        existing = params.itemByName(name)
        if existing:
            existing.deleteMe()

    defs = [
        ("part_length",  "100 mm", "mm", "Overall X dimension"),
        ("part_width",   "60 mm",  "mm", "Overall Y dimension"),
        ("part_height",  "20 mm",  "mm", "Stock thickness / Z height"),
        ("pocket_depth", "8 mm",   "mm", "Rectangular pocket depth"),
        ("hole_dia",     "6 mm",   "mm", "Through-hole drill diameter"),
        ("chamfer_size", "1 mm",   "mm", "Top edge chamfer"),
        ("corner_rad",   "2 mm",   "mm", "Inside pocket corner radius (min tool r)"),
    ]

    for name, expr, unit, comment in defs:
        p = params.add(name, adsk.core.ValueInput.createByString(expr), unit, comment)
        print(f"  {p.name:15s} = {p.expression:8s}  ({p.value*10:.2f} mm)")

    print("\nManufacturing parameters created.")


# =============================================================================
# DESIGN-03  Build the Bracket part
#            Depends on DESIGN-02 parameters being present.
#            Creates the full 2.5D prismatic body ready for CAM.
# =============================================================================

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


# =============================================================================
# DESIGN-04  Inspect the completed part — body/face/edge/hole inventory
#            Run after DESIGN-03. Good pre-CAM sanity check.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    if root.bRepBodies.count == 0:
        print("No bodies found. Run DESIGN-03 first.")
        return

    body = root.bRepBodies.item(0)
    print(f"=== Part Inventory: {body.name} ===")
    print(f"  Faces  : {body.faces.count}")
    print(f"  Edges  : {body.edges.count}")
    print(f"  Vertices: {body.vertices.count}")

    bb = body.boundingBox
    dx = (bb.maxPoint.x - bb.minPoint.x) * 10
    dy = (bb.maxPoint.y - bb.minPoint.y) * 10
    dz = (bb.maxPoint.z - bb.minPoint.z) * 10
    print(f"\n  Bounding box: {dx:.1f} x {dy:.1f} x {dz:.1f} mm")
    # body.volume is in Fusion internal units (cm^3). Convert to mm^3 for display.
    print(f"  Volume      : {body.volume * 1000:.1f} mm³  ({body.volume:.2f} cm³)")

    print(f"\n  Feature timeline ({root.features.count} features):")
    for i in range(root.features.count):
        feat = root.features.item(i)
        print(f"    [{i+1}] {feat.classType().split('::')[-1]:30s}  {feat.name}")

    print(f"\n  User parameters ({des.userParameters.count}):")
    for i in range(des.userParameters.count):
        p = des.userParameters.item(i)
        print(f"    {p.name:15s} = {p.expression}")


# =============================================================================
# DESIGN-05  Edit a parameter and verify model updates (parametric test)
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)

    param = des.userParameters.itemByName("pocket_depth")
    if not param:
        print("pocket_depth not found — run DESIGN-02 first.")
        return

    old_val = param.expression
    print(f"Before: pocket_depth = {old_val}")

    # Change pocket depth from 8 mm to 12 mm
    param.expression = "12 mm"
    print(f"After : pocket_depth = {param.expression}  ({param.value*10:.1f} mm)")
    print("Model should have updated. Check viewport.")

    # Revert
    param.expression = old_val
    print(f"Reverted to: {param.expression}")


# =============================================================================
# DESIGN-06  Add a component / assembly test
#            Creates a second instance of the bracket as a sub-component.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    # Create a new empty component translated +X past the Bracket so the
    # two parts don't overlap in the assembly view.
    offset_x = 12.0   # cm — beyond Bracket length (10 cm) + small gap
    placement = adsk.core.Matrix3D.create()
    placement.translation = adsk.core.Vector3D.create(offset_x, 0, 0)
    occ = root.occurrences.addNewComponent(placement)
    comp = occ.component
    comp.name = "MountingPlate"
    print(f"New sub-component: {comp.name}")

    # Add a simple sketch + extrude inside it
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(12.0, 8.0, 0)   # 120 x 80 mm
    )
    ext_in = comp.features.extrudeFeatures.createInput(
        sk.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(0.5))  # 5 mm
    comp.features.extrudeFeatures.add(ext_in)

    print(f"  Body added: 120 x 80 x 5 mm plate")
    print(f"  Root occurrences: {root.occurrences.count}")
    print(f"  Assembly is now multi-component — verify in browser tree.")


# =============================================================================
# DESIGN-07 — Hole feature (proper HoleFeatures API): simple + counterbore
#             Demonstrates the dedicated HoleFeatureInput rather than
#             extrude-cut. Run AFTER DESIGN-03 (needs the Bracket body).
# =============================================================================

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


# =============================================================================
# DESIGN-08 — Rectangular pattern of a feature
#             Creates a small boss on the Bracket, then patterns it 2×3.
# =============================================================================

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


# =============================================================================
# DESIGN-09 — Circular pattern of a feature around an axis
# =============================================================================

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


# =============================================================================
# DESIGN-10 — Mirror feature across a construction plane
# =============================================================================

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


# =============================================================================
# DESIGN-11 — Shell feature
#             Creates a separate ShellTestBox body (off to the side of the
#             Bracket) and shells it. Doesn't touch the Bracket itself.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    # Build a 40×30×20 mm closed box offset to the front of the Bracket
    # (so y<0). Position: x=0..4, y=-5..-2, z=0..2.
    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(0))
    base_plane = root.constructionPlanes.add(cpi); base_plane.name = "Plane_ShellBase"
    sk = root.sketches.add(base_plane); sk.name = "Sketch_ShellBox"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0.0, -5.0, 0),
        adsk.core.Point3D.create(4.0, -2.0, 0))
    ein = root.features.extrudeFeatures.createInput(
        sk.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ein.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.0))
    test_body = root.features.extrudeFeatures.add(ein).bodies.item(0)
    test_body.name = "ShellTestBox"

    # Shell removing the top face (the +Z one), wall = 2 mm
    top = next(f for f in test_body.faces
               if abs(f.centroid.z - 2.0) < 0.001)
    faces_to_remove = adsk.core.ObjectCollection.create()
    faces_to_remove.add(top)
    sh_in = root.features.shellFeatures.createInput(faces_to_remove)
    sh_in.insideThickness = adsk.core.ValueInput.createByReal(0.2)   # 2 mm inside
    shell = root.features.shellFeatures.add(sh_in)
    shell.name = "Shell_TestBox_2mm"
    print(f"ShellTestBox: shelled (top removed, 2 mm wall inside)")
    print(f"  faces={test_body.faces.count}  vol={test_body.volume:.3f} cm³")


# =============================================================================
# DESIGN-12 — Draft feature
#             Builds a separate DraftTestBox body and applies draft to its
#             side faces.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    # 30×30×30 mm cube offset further back (y<0, beyond the shell test).
    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(0))
    plane = root.constructionPlanes.add(cpi); plane.name = "Plane_DraftBase"
    sk = root.sketches.add(plane); sk.name = "Sketch_DraftCube"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0.0, -10.0, 0),
        adsk.core.Point3D.create(3.0, -7.0, 0))
    ein = root.features.extrudeFeatures.createInput(
        sk.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ein.setDistanceExtent(False, adsk.core.ValueInput.createByReal(3.0))
    test_body = root.features.extrudeFeatures.add(ein).bodies.item(0)
    test_body.name = "DraftTestBox"

    # Draft the four side faces 5° relative to the bottom face
    bottom = next(f for f in test_body.faces
                  if abs(f.centroid.z - 0.0) < 0.001)
    # DraftFeatures.createInput wants a plain list[BRepFace], not an
    # ObjectCollection. The 3rd arg (isTangentChain) is required positional.
    side_faces = []
    for f in test_body.faces:
        ok, nrm = f.evaluator.getNormalAtPoint(f.centroid)
        if ok and abs(nrm.z) < 0.001:
            side_faces.append(f)

    df_in = root.features.draftFeatures.createInput(side_faces, bottom, False)
    df_in.setSingleAngle(False, adsk.core.ValueInput.createByString("5 deg"))
    draft = root.features.draftFeatures.add(df_in)
    draft.name = "Draft_TestCube_5deg"
    print(f"DraftTestBox: {len(side_faces)} side faces drafted 5° from bottom")
    print(f"  faces={test_body.faces.count}  vol={test_body.volume:.3f} cm³")
