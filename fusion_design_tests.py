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


# =============================================================================
# DESIGN-13 — Revolve a sketch profile around an axis
#             Builds a stepped axisymmetric ring offset from the Bracket.
# =============================================================================

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


# =============================================================================
# DESIGN-14 — Sweep a profile along a path
#             Cylindrical rod following a 90° arc.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    # PATH sketch: 90° arc on the XY plane (Z=0), in free space at +X, -Y
    sk_path = root.sketches.add(root.xYConstructionPlane)
    sk_path.name = "Sketch_SweepPath"
    arcs = sk_path.sketchCurves.sketchArcs
    # Arc from (20, -10) to (25, -5), center (20, -5), radius 5
    arc = arcs.addByCenterStartSweep(
        adsk.core.Point3D.create(20.0, -5.0, 0),    # center
        adsk.core.Point3D.create(20.0, -10.0, 0),   # start  (3 o'clock from center = wrong: start is at -90°)
        # sweep 90° to (25, -5)
        1.5708)   # 90° in radians
    # path collection
    path_curves = adsk.core.ObjectCollection.create()
    path_curves.add(arc)
    path = root.features.createPath(arc)

    # PROFILE sketch: circle in a plane perpendicular to the arc start.
    # Arc start at (20, -10, 0); tangent there points along +X (since arc
    # sweeps from start toward (25, -5) going counterclockwise). The plane
    # perpendicular to +X at (20, -10, 0) is YZ-parallel — use yZ plane
    # offset to X=20.
    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.yZConstructionPlane, adsk.core.ValueInput.createByReal(20.0))
    perp_plane = root.constructionPlanes.add(cpi)
    perp_plane.name = "Plane_SweepProfile"
    sk_prof = root.sketches.add(perp_plane)
    sk_prof.name = "Sketch_SweepProfile"
    # Sketch on YZ-offset plane: local (X_local, Y_local) = world (Y, Z)
    # Profile center should be at world (20, -10, 0) → local (-10, 0)
    sk_prof.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(-10.0, 0, 0), 0.4)   # 8 mm Ø rod
    profile = sk_prof.profiles.item(0)

    sw_in = root.features.sweepFeatures.createInput(
        profile, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    sw = root.features.sweepFeatures.add(sw_in)
    rod = sw.bodies.item(0)
    rod.name = "SweepRod"
    # Expected vol: π × 0.4² × (arc length = 5 × π/2) = π × 0.16 × 7.854
    #             = 3.95 cm³
    print(f"SweepRod: faces={rod.faces.count} vol={rod.volume:.3f} cm³ "
          f"(expected ~3.95)")


# =============================================================================
# DESIGN-15 — Rib-equivalent gusset on an L-shaped body (via symmetric extrude)
#
# Quirk discovered: in Fusion 2703.x Insider, RibFeatures is read-only via
# the Python API — RibFeatures has no createInput / add methods (only cast,
# count, item, itemByName). To produce a rib programmatically we sketch the
# gusset cross-section as a closed triangle and extrude it symmetrically
# with a thin wall thickness. Same resulting geometry; just a different
# feature in the timeline.
# =============================================================================

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


# =============================================================================
# DESIGN-16 — Offset construction plane from a body face
#             Run AFTER DESIGN-03. Creates a plane 25 mm above the Bracket
#             top face. Useful as a sketch host for subsequent operations.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    body = root.bRepBodies.itemByName("Bracket")
    if body is None:
        print("Bracket not found. Run DESIGN-03 first.")
        return

    H = des.userParameters.itemByName("part_height").value
    top_face = next(f for f in body.faces
                    if abs(f.centroid.z - H) < 0.001 and
                       (f.boundingBox.maxPoint.x - f.boundingBox.minPoint.x) > 8.0)

    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(top_face, adsk.core.ValueInput.createByReal(2.5))   # 25 mm above
    plane = root.constructionPlanes.add(cpi)
    plane.name = "Plane_25mmAboveTop"

    # Expected: plane origin at z = H + 2.5 = 4.5 cm
    print(f"Plane '{plane.name}' origin z={plane.geometry.origin.z:.3f} cm "
          f"(expect {H + 2.5:.3f})")


# =============================================================================
# DESIGN-17 — Construction axis perpendicular to a face at a sketch point
#             Run AFTER DESIGN-03. Creates a Z-axis through (5, 3) at the top
#             face center. Quirk: setByPerpendicularAtPoint(face, point) —
#             face FIRST, point second.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    body = root.bRepBodies.itemByName("Bracket")
    if body is None:
        print("Bracket not found. Run DESIGN-03 first.")
        return

    H = des.userParameters.itemByName("part_height").value
    top_face = next(f for f in body.faces
                    if abs(f.centroid.z - H) < 0.001 and
                       (f.boundingBox.maxPoint.x - f.boundingBox.minPoint.x) > 8.0)

    # Sketch point on a construction plane offset to H (avoids quirk #8b's
    # face-bound silent issues with downstream usage).
    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(H))
    sketch_plane = root.constructionPlanes.add(cpi)
    sketch_plane.name = "Plane_AxisPointSketch"
    sk = root.sketches.add(sketch_plane)
    sk.name = "Sketch_AxisPoint"
    pt = sk.sketchPoints.add(adsk.core.Point3D.create(5.0, 3.0, 0))

    ai = root.constructionAxes.createInput()
    ai.setByPerpendicularAtPoint(top_face, pt)   # face FIRST, point SECOND
    axis = root.constructionAxes.add(ai)
    axis.name = "Axis_CenterOfTop"

    d = axis.geometry.direction
    print(f"Axis '{axis.name}' direction=({d.x:.3f}, {d.y:.3f}, {d.z:.3f}) "
          f"(expect (0, 0, ±1))")


# =============================================================================
# DESIGN-18 — Construction point at intersection of three offset planes
#             Run AFTER DESIGN-02. Creates a point at (5, 3, H) = the Bracket
#             top-face center, without needing the Bracket body present.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    H = des.userParameters.itemByName("part_height").value

    p1_in = root.constructionPlanes.createInput()
    p1_in.setByOffset(root.yZConstructionPlane, adsk.core.ValueInput.createByReal(5.0))
    plane_X5 = root.constructionPlanes.add(p1_in); plane_X5.name = "Plane_X5"
    p2_in = root.constructionPlanes.createInput()
    p2_in.setByOffset(root.xZConstructionPlane, adsk.core.ValueInput.createByReal(3.0))
    plane_Y3 = root.constructionPlanes.add(p2_in); plane_Y3.name = "Plane_Y3"
    p3_in = root.constructionPlanes.createInput()
    p3_in.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(H))
    plane_Ztop = root.constructionPlanes.add(p3_in); plane_Ztop.name = "Plane_Ztop"

    pti = root.constructionPoints.createInput()
    pti.setByThreePlanes(plane_X5, plane_Y3, plane_Ztop)
    cpt = root.constructionPoints.add(pti)
    cpt.name = "Pt_TopCenter"

    p = cpt.geometry
    print(f"Point '{cpt.name}' at ({p.x:.3f}, {p.y:.3f}, {p.z:.3f}) "
          f"(expect (5.000, 3.000, {H:.3f}))")


# =============================================================================
# DESIGN-19 — Project geometry from a body face onto an offset sketch
#             Run AFTER DESIGN-03. Projects the Bracket top face's edges
#             (4 perimeter + 4 fillet arcs + 8 hole circles = 16 curves)
#             onto a sketch on a plane 30 mm above the top face.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    body = root.bRepBodies.itemByName("Bracket")
    if body is None:
        print("Bracket not found. Run DESIGN-03 first.")
        return

    H = des.userParameters.itemByName("part_height").value
    top_face = next(f for f in body.faces
                    if abs(f.centroid.z - H) < 0.001 and
                       (f.boundingBox.maxPoint.x - f.boundingBox.minPoint.x) > 8.0)

    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(H + 3.0))
    plane = root.constructionPlanes.add(cpi)
    plane.name = "Plane_ProjectionTarget"
    sk = root.sketches.add(plane)
    sk.name = "Sketch_ProjectedTopEdges"

    proj = sk.project(top_face)
    print(f"Projected {proj.count} entities onto '{sk.name}' "
          f"(sketch curves now: {sk.sketchCurves.count})")


# =============================================================================
# DESIGN-20 — Suppress / unsuppress a timeline feature
#             Run AFTER DESIGN-03. Toggles the Chamfer1 feature and verifies
#             body.volume changes by the chamfer's removed-material delta.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    body = root.bRepBodies.itemByName("Bracket")
    if body is None:
        print("Bracket not found. Run DESIGN-03 first.")
        return

    chamfer = next((root.features.item(i) for i in range(root.features.count)
                    if root.features.item(i).classType().endswith("ChamferFeature")),
                   None)
    if chamfer is None:
        print("No ChamferFeature found.")
        return

    v_full = body.volume
    chamfer.isSuppressed = True
    v_suppressed = body.volume
    chamfer.isSuppressed = False
    v_restored = body.volume

    print(f"{chamfer.name}: full={v_full:.4f} → suppressed={v_suppressed:.4f} "
          f"(+{v_suppressed - v_full:.4f}) → unsuppressed={v_restored:.4f}")
    print(f"Roundtrip exact: {abs(v_restored - v_full) < 0.0005}")


# =============================================================================
# DESIGN-21 — Combine: cut tool body from target body (boolean subtract)
#             Builds two overlapping cubes in unused space (X = -20..-14)
#             and cuts the tool from the target. No dependency on DESIGN-03.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    # Target cube A: 4×4×4 cm at (-20..-16, 0..4, 0..4)
    skA = root.sketches.add(root.xYConstructionPlane); skA.name = "Sketch_CubeA"
    skA.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-20.0, 0, 0),
        adsk.core.Point3D.create(-16.0, 4.0, 0))
    eA = root.features.extrudeFeatures.createInput(
        skA.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    eA.setDistanceExtent(False, adsk.core.ValueInput.createByReal(4.0))
    cubeA = root.features.extrudeFeatures.add(eA).bodies.item(0)
    cubeA.name = "CombineTarget"

    # Tool cube B: overlaps A by 2×2×2 = 8 cm³
    skB = root.sketches.add(root.xYConstructionPlane); skB.name = "Sketch_CubeB"
    skB.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-18.0, 2.0, 0),
        adsk.core.Point3D.create(-14.0, 6.0, 0))
    eB = root.features.extrudeFeatures.createInput(
        skB.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    eB.startExtent = adsk.fusion.OffsetStartDefinition.create(
        adsk.core.ValueInput.createByReal(2.0))
    eB.setDistanceExtent(False, adsk.core.ValueInput.createByReal(4.0))
    cubeB = root.features.extrudeFeatures.add(eB).bodies.item(0)
    cubeB.name = "CombineTool"

    tools = adsk.core.ObjectCollection.create()
    tools.add(cubeB)
    cmb = root.features.combineFeatures.createInput(cubeA, tools)
    cmb.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
    cmb.isKeepToolBodies = False
    root.features.combineFeatures.add(cmb)

    # Expected: 64 − 8 (overlap) = 56 cm³
    print(f"CombineTarget after cut: vol={cubeA.volume:.3f} cm³ (expect 56.000)")


# =============================================================================
# DESIGN-22 — Move body (translate + rotate via Matrix3D)
#             Builds a 2×2×2 cm cube and moves it +3,+3,+1 cm while rotating
#             45° about Z through its own center. Volume invariant under
#             rigid motion; bbox should rotate to 2√2 cm wide.
# =============================================================================

import adsk.core, adsk.fusion, math

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    sk = root.sketches.add(root.xYConstructionPlane); sk.name = "Sketch_MoveCube"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-20.0, 0, 0),
        adsk.core.Point3D.create(-18.0, 2.0, 0))
    ein = root.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ein.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.0))
    cube = root.features.extrudeFeatures.add(ein).bodies.item(0)
    cube.name = "MoveCube"

    tf = adsk.core.Matrix3D.create()
    rot = adsk.core.Matrix3D.create()
    rot.setToRotation(math.radians(45),
                      adsk.core.Vector3D.create(0, 0, 1),
                      adsk.core.Point3D.create(-19.0, 1.0, 1.0))   # cube center
    trans = adsk.core.Matrix3D.create()
    trans.translation = adsk.core.Vector3D.create(3.0, 3.0, 1.0)
    tf.transformBy(rot)
    tf.transformBy(trans)

    bodies = adsk.core.ObjectCollection.create()
    bodies.add(cube)
    mv_in = root.features.moveFeatures.createInput(bodies, tf)
    mv = root.features.moveFeatures.add(mv_in)
    mv.name = "Move_Cube_T3R45"

    bb = cube.boundingBox
    print(f"MoveCube vol={cube.volume:.3f} (expect 8.000), bbox width="
          f"{max(bb.maxPoint.x - bb.minPoint.x, bb.maxPoint.y - bb.minPoint.y):.3f} "
          f"(expect ~2.828 = 2√2)")


# =============================================================================
# DESIGN-23 — Split body by a construction plane
#             Builds a 4×4×4 cm cube and splits it at z=2 into two halves.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    sk = root.sketches.add(root.xYConstructionPlane); sk.name = "Sketch_SplitCube"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-20.0, 0, 0),
        adsk.core.Point3D.create(-16.0, 4.0, 0))
    ein = root.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ein.setDistanceExtent(False, adsk.core.ValueInput.createByReal(4.0))
    cube = root.features.extrudeFeatures.add(ein).bodies.item(0)
    cube.name = "SplitCube"
    v_before = cube.volume

    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(2.0))
    splitter = root.constructionPlanes.add(cpi)
    splitter.name = "Plane_SplitMid"

    sp_in = root.features.splitBodyFeatures.createInput(cube, splitter, True)
    root.features.splitBodyFeatures.add(sp_in).name = "Split_AtMid"

    halves = [b for b in root.bRepBodies if b.name.startswith("SplitCube")]
    total = sum(b.volume for b in halves)
    print(f"Split: {len(halves)} bodies, halves={[round(b.volume, 3) for b in halves]}, "
          f"total={total:.3f} (expect {v_before:.3f})")


# =============================================================================
# DESIGN-24 — Rigid joint between two peg sub-components
#             Two PegA/PegB occurrences with a rigid joint between PegA's top
#             face and PegB's bottom face. Note: the joint creates the
#             constraint relationship but does NOT visually snap geometry —
#             that's a Joint API behavior. The joint counts/types confirm it.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    def make_peg(name, x_world):
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component; comp.name = name
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(x_world, -15.0, 0), 0.5)   # 10mm Ø
        ein = comp.features.extrudeFeatures.createInput(
            sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ein.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.0))   # 20mm tall
        comp.features.extrudeFeatures.add(ein)
        return occ

    occA = make_peg("PegA", -20.0)
    occB = make_peg("PegB", -16.0)
    bodyA = occA.bRepBodies.item(0)
    bodyB = occB.bRepBodies.item(0)
    topA = next(f for f in bodyA.faces if abs(f.centroid.z - 2.0) < 0.001)
    botB = next(f for f in bodyB.faces if abs(f.centroid.z - 0.0) < 0.001)

    geomA = adsk.fusion.JointGeometry.createByPlanarFace(
        topA, None, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
    geomB = adsk.fusion.JointGeometry.createByPlanarFace(
        botB, None, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)

    j_in = root.joints.createInput(geomA, geomB)
    j_in.setAsRigidJointMotion()
    joint = root.joints.add(j_in)
    joint.name = "PegA_to_PegB_rigid"

    print(f"joints={root.joints.count}  type={joint.jointMotion.jointType} "
          f"(expect 0 = RigidJointType)  name='{joint.name}'")


# =============================================================================
# DESIGN-25 — Thread feature on a cylinder
#             Builds a 10 mm Ø × 30 mm cylinder and applies an M10×1.5 / 4g6g
#             external modeled thread, 20 mm thread length.
#             Quirk #18: ThreadDataQuery.allClasses(isInternal, type, designation)
#             — isInternal FIRST.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    sk = root.sketches.add(root.xYConstructionPlane); sk.name = "Sketch_ThreadCylinder"
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(-20.0, -20.0, 0), 0.5)
    ein = root.features.extrudeFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ein.setDistanceExtent(False, adsk.core.ValueInput.createByReal(3.0))
    cyl = root.features.extrudeFeatures.add(ein).bodies.item(0)
    cyl.name = "ThreadCylinder"

    side_face = next(f for f in cyl.faces if isinstance(f.geometry, adsk.core.Cylinder))

    threads = root.features.threadFeatures
    q = threads.threadDataQuery
    cls = list(q.allClasses(False, "ISO Metric profile", "M10x1.5"))[0]   # external
    info = threads.createThreadInfo(False, "ISO Metric profile", "M10x1.5", cls)
    faces = adsk.core.ObjectCollection.create(); faces.add(side_face)
    t_in = threads.createInput(faces, info)
    t_in.isModeled = True
    t_in.threadLength = adsk.core.ValueInput.createByReal(2.0)
    thread = threads.add(t_in)
    thread.name = "M10_Thread"

    print(f"Thread '{thread.name}' M10x1.5 / {info.threadClass}: "
          f"cyl faces 3 → {cyl.faces.count}")


# =============================================================================
# DESIGN-26 — Material assignment from the Fusion Material Library
#             Run AFTER DESIGN-03. Assigns Aluminum 6061 to the Bracket from
#             the canonical 'Fusion Material Library' (NOT Additive — see #5).
#             Never fall through to alphabetical-first 'Fusion Additive
#             Material Library'.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    body = root.bRepBodies.itemByName("Bracket")
    if body is None:
        print("Bracket not found. Run DESIGN-03 first.")
        return

    print(f"Bracket material before: {body.material.name}")

    libs = app.materialLibraries
    material_lib = next((l for l in libs if l.name == "Fusion Material Library"), None)
    if material_lib is None:
        print("FAIL: 'Fusion Material Library' not available.")
        return

    alu = next((m for m in material_lib.materials if "Aluminum 6061" in m.name), None)
    if alu is None:
        avail = [m.name for m in material_lib.materials if "Aluminum" in m.name]
        print(f"FAIL: Aluminum 6061 not in Fusion Material Library. Options: {avail}")
        return

    body.material = alu
    print(f"Bracket material after:  {body.material.name}")


# =============================================================================
# DESIGN-27 — Appearance assignment from the Fusion Appearance Library
#             Run AFTER DESIGN-03. Applies 'Plastic - Glossy (Red)' to the
#             Bracket body — visual change only (does not affect material/mass).
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    body = root.bRepBodies.itemByName("Bracket")
    if body is None:
        print("Bracket not found. Run DESIGN-03 first.")
        return

    print(f"Bracket appearance before: {body.appearance.name}")

    app_lib = next(l for l in app.materialLibraries
                   if l.name == "Fusion Appearance Library")
    red = next((a for a in app_lib.appearances
                if "Red" in a.name and "Plastic" in a.name), None)
    if red is None:
        red = next((a for a in app_lib.appearances if "Red" in a.name), None)
    if red is None:
        print("FAIL: no red appearance available.")
        return

    body.appearance = red
    print(f"Bracket appearance after:  {body.appearance.name}")


# =============================================================================
# DESIGN-28 — Surface patch + thicken to solid
#             Patches a closed rectangle (4×3 cm) on a plane at z=10 cm into
#             a surface body, then thickens to a 5 mm solid (= 6 cm³).
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    cpi = root.constructionPlanes.createInput()
    cpi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(10.0))
    plane = root.constructionPlanes.add(cpi); plane.name = "Plane_PatchBase"
    sk = root.sketches.add(plane); sk.name = "Sketch_PatchRect"
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-20.0, -25.0, 0),
        adsk.core.Point3D.create(-16.0, -22.0, 0))

    patch_in = root.features.patchFeatures.createInput(
        sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    patch = root.features.patchFeatures.add(patch_in)
    patch.name = "Patch_Rect"
    surf = patch.bodies.item(0); surf.name = "SurfRect"

    surf_faces = adsk.core.ObjectCollection.create()
    for f in surf.faces: surf_faces.add(f)
    th_in = root.features.thickenFeatures.createInput(
        surf_faces,
        adsk.core.ValueInput.createByReal(0.5),                          # 5 mm
        False,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        True)
    root.features.thickenFeatures.add(th_in).name = "Thicken_Patch_5mm"

    solid = next((b for b in root.bRepBodies if b.isSolid and b.name not in ("Bracket",)),
                 None)
    print(f"Patch surface (1 face) → thickened solid: vol={solid.volume if solid else 0:.3f} "
          f"(expect 6.000 = 4×3×0.5)")


# =============================================================================
# DESIGN-29 — Rotor part parameters (Batch D — Rotary stock for CAM-18a..e)
#             Creates the user parameters that drive the Rotor build in
#             DESIGN-30. Independent of the Bracket params from DESIGN-02.
#             Rotor is a turned spindle along the X axis — Ø40 main body with
#             a Ø30 mounting shoulder, axial bore, OD groove, two milled
#             flats, and a quarter-sphere dome on the +X end.
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app    = adsk.core.Application.get()
    des    = adsk.fusion.Design.cast(app.activeProduct)
    params = des.userParameters

    defs = [
        ("rotor_length",       "100 mm", "mm", "Total rotor length along +X"),
        ("rotor_od",           "40 mm",  "mm", "Main body OD (Ø) — rotary stock diameter"),
        ("rotor_shoulder_od",  "30 mm",  "mm", "Mounting shoulder OD at -X end"),
        ("rotor_shoulder_len", "20 mm",  "mm", "Shoulder length along +X from -X face"),
        ("rotor_bore_dia",     "10 mm",  "mm", "Axial through-bore diameter"),
        ("rotor_bore_len",     "80 mm",  "mm", "Bore depth from -X face (stops before dome)"),
        ("rotor_dome_r",       "20 mm",  "mm", "Quarter-sphere dome radius at +X end (= rotor_od/2)"),
        ("rotor_groove_x",     "55 mm",  "mm", "Circumferential groove start X (rotary_pocket target)"),
        ("rotor_groove_w",     "6 mm",   "mm", "Groove width along X"),
        ("rotor_groove_depth", "3 mm",   "mm", "Groove radial depth"),
        ("rotor_flat_x0",      "70 mm",  "mm", "Milled flat start X (rotary_contour target)"),
        ("rotor_flat_x1",      "75 mm",  "mm", "Milled flat end X (5 mm clear of dome start)"),
        ("rotor_flat_inset",   "4 mm",   "mm", "Radial depth of milled flats from OD"),
    ]

    for name, expr, unit, comment in defs:
        existing = params.itemByName(name)
        if existing:
            existing.deleteMe()
        p = params.add(name, adsk.core.ValueInput.createByString(expr), unit, comment)
        print(f"  {p.name:22s} = {p.expression:8s}  ({p.value*10:.2f} mm)")

    print("\nRotor parameters created — run DESIGN-30 to build the body.")


# =============================================================================
# DESIGN-30 — Build the Rotor part (Batch D rotary stock)
#             Depends on DESIGN-29 parameters. Creates a new "Rotor"
#             sub-component so it coexists cleanly with the Bracket.
#
#             Feature recipe (each maps to a Batch D CAM target):
#               1. Revolve outer profile about X         → solid of revolution
#                  (Ø30 shoulder → Ø40 body → R20 dome at +X end)
#               2. Revolve-cut axial bore Ø10            → drillable bore
#               3. Revolve-cut circumferential groove    → rotary_pocket target
#               4. Symmetric extrude-cut two opposing    → rotary_contour target
#                  flats from the XZ plane               (planar pockets on OD)
#               5. Chamfer the shoulder transition edge  → deburr target
#                                                          (dome face stays
#                                                           clean for geodesic
#                                                           / rotary_finishing)
# =============================================================================

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
