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

    # Sketch on the top face (Z = H)
    top_face = None
    for face in body.faces:
        if abs(face.centroid.z - H) < 0.001:
            bbox = face.boundingBox
            if (bbox.maxPoint.x - bbox.minPoint.x) > 0.9 * L:
                top_face = face
                break

    sk_pocket = root.sketches.add(top_face)
    sk_pocket.name = "Sketch_Pocket"
    lines = sk_pocket.sketchCurves.sketchLines
    lines.addTwoPointRectangle(
        adsk.core.Point3D.create(wall, wall, H),
        adsk.core.Point3D.create(wall+pk_l, wall+pk_w, H)
    )

    # Fillet the pocket sketch corners (inside corner radius = CR)
    arcs    = sk_pocket.sketchCurves.sketchArcs
    corners = sk_pocket.sketchPoints
    # Use sketch fillets via the sketch API
    sk_pocket.sketchCurves  # trigger lazy load
    # Add fillets to all 4 corner pairs
    segs = list(sk_pocket.sketchCurves.sketchLines)
    for i in range(4):
        l1 = segs[i]
        l2 = segs[(i+1) % 4]
        sk_pocket.sketchCurves.sketchArcs.addFillet(
            l1, l1.endSketchPoint.geometry,
            l2, l2.startSketchPoint.geometry,
            CR
        )

    pocket_ext_in = root.features.extrudeFeatures.createInput(
        sk_pocket.profiles.item(0),
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    pocket_ext_in.setDistanceExtent(
        False, adsk.core.ValueInput.createByReal(-PD)
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

    sk_holes = root.sketches.add(top_face)
    sk_holes.name = "Sketch_Holes"
    for (x, y) in hole_positions:
        sk_holes.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(x, y, H),
            HD / 2
        )

    holes_ext_in = root.features.extrudeFeatures.createInput(
        sk_holes.profiles.item(0),   # first circle profile
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    holes_ext_in.setDistanceExtent(
        True,   # symmetric = False, through all
        adsk.core.ValueInput.createByString("-100 mm")
    )
    # Use extentOne for through-all
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
    print(f"  Volume      : {body.volume * 1000:.1f} cm³")  # cm³ from cm³

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

    # Create a new empty component
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
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
