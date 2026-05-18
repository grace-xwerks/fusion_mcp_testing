"""
Fusion MCP Test Scripts
=======================
Organized by the test coverage matrix in INSTRUCTIONS.md.

HOW TO USE:
  Each script is a standalone function you paste into fusion_mcp_execute
  with featureType: "script". Copy the body of whichever test you want to run.

RULES (from Fusion MCP docs):
  - Entry point MUST be: def run(_context: str):
  - Use print() for all output
  - Do NOT use try/except — unhandled exceptions are the debug signal
  - Fusion API only runs on the main thread (MCP handles this for you)

Units reminder: Fusion internal units are CENTIMETERS.
  10mm = 1.0 cm  |  1 inch = 2.54 cm
"""

# =============================================================================
# D-01 — Print Fusion version (smoke test / connectivity check)
# =============================================================================

import adsk.core

def run(_context: str):
    app = adsk.core.Application.get()
    print(f"Fusion version: {app.version}")
    print(f"Active user:    {app.currentUser.displayName}")
    print(f"Active product: {app.activeProduct.productType if app.activeProduct else 'None'}")


# =============================================================================
# D-02 — Create a 10 mm cube
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    # Sketch on XY plane
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(1.0, 1.0, 0)   # 1.0 cm = 10 mm
    )

    # Extrude 10 mm
    prof     = sketch.profiles.item(0)
    extrudes = root.features.extrudeFeatures
    ext_in   = extrudes.createInput(
        prof,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1.0))
    body = extrudes.add(ext_in)

    print(f"Created body: {body.bodies.item(0).name}")
    print(f"Bounding box volume check: 10x10x10 mm cube")


# =============================================================================
# D-03 — Add a user parameter
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app    = adsk.core.Application.get()
    des    = adsk.fusion.Design.cast(app.activeProduct)
    params = des.userParameters

    # createByReal takes cm; we store as an expression string for readability
    new_param = params.add(
        "test_width",
        adsk.core.ValueInput.createByString("25 mm"),
        "mm",
        "MCP test parameter"
    )

    print(f"Parameter created:  {new_param.name}")
    print(f"Value (cm):         {new_param.value}")
    print(f"Expression:         {new_param.expression}")
    print(f"Comment:            {new_param.comment}")


# =============================================================================
# D-04 — print() multiple lines (output fidelity check)
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    print("=== Multi-line output test ===")
    print(f"Design name:      {des.parentDocument.name}")
    print(f"Root component:   {root.name}")
    print(f"Bodies count:     {root.bRepBodies.count}")
    print(f"Sketches count:   {root.sketches.count}")
    print(f"Features count:   {root.features.count}")
    print(f"Parameters count: {des.userParameters.count}")
    print("=== Done ===")


# =============================================================================
# D-05 — Intentional exception (error signal test — NO try/except by design)
# =============================================================================

import adsk.fusion

def run(_context: str):
    # Casting None as a Design should raise AttributeError immediately.
    # Expected: MCP returns a traceback. That's the correct error behavior.
    des = adsk.fusion.Design.cast(None)
    print(des.rootComponent.name)   # never reached


# =============================================================================
# D-03b — Parameterized box using the user parameter
#         (run AFTER D-03 so test_width exists)
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app    = adsk.core.Application.get()
    des    = adsk.fusion.Design.cast(app.activeProduct)
    root   = des.rootComponent

    # Pull the parameter we created in D-03
    w_param = des.userParameters.itemByName("test_width")
    if not w_param:
        print("ERROR: test_width parameter not found — run D-03 first")
        return

    w = w_param.value   # already in cm
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(w, w, 0)
    )

    prof   = sketch.profiles.item(0)
    ext_in = root.features.extrudeFeatures.createInput(
        prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(w))
    root.features.extrudeFeatures.add(ext_in)

    print(f"Parameterized cube created: {w*10:.1f} mm sides (driven by test_width)")


# =============================================================================
# BONUS: design_inventory — dumps a full snapshot of the active design
#        Great first-run diagnostic to understand what's loaded
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    print("=== Design Inventory ===")
    print(f"Document : {des.parentDocument.name}")
    print(f"Design   : {des.rootComponent.name}")
    print()

    print(f"Bodies ({root.bRepBodies.count}):")
    for i in range(root.bRepBodies.count):
        b = root.bRepBodies.item(i)
        print(f"  [{i}] {b.name}  visible={b.isVisible}")

    print(f"\nSketches ({root.sketches.count}):")
    for i in range(root.sketches.count):
        s = root.sketches.item(i)
        print(f"  [{i}] {s.name}  profiles={s.profiles.count}")

    print(f"\nUser Parameters ({des.userParameters.count}):")
    for i in range(des.userParameters.count):
        p = des.userParameters.item(i)
        print(f"  [{i}] {p.name} = {p.expression}  ({p.unit})")

    print(f"\nComponents ({root.occurrences.count} occurrences at root):")
    for i in range(root.occurrences.count):
        o = root.occurrences.item(i)
        print(f"  [{i}] {o.component.name}")

    print("\n=== End Inventory ===")


# =============================================================================
# BONUS: viewport_screenshot_all_directions
#        Not a script — use these as fusion_mcp_READ calls:
#
#   queryType: "screenshot"
#   direction: "iso-top-left"   (or any of the 10 directions below)
#   width: 1920
#   height: 1080
#   antiAliasing: true
#   transparentBackground: false
#
#   Directions: current | front | back | top | bottom | left | right
#               iso-top-left | iso-top-right | iso-bottom-left | iso-bottom-right
# =============================================================================


# =============================================================================
# BONUS: sphere — exercises revolve instead of extrude
# =============================================================================

import adsk.core, adsk.fusion, math

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    RADIUS_CM = 1.0   # 10 mm radius

    sketch = root.sketches.add(root.xZConstructionPlane)
    arcs   = sketch.sketchCurves.sketchArcs
    lines  = sketch.sketchCurves.sketchLines

    # Semi-circle (right half) + axis line
    center = adsk.core.Point3D.create(0, 0, 0)
    start  = adsk.core.Point3D.create(0, 0,  RADIUS_CM)
    end    = adsk.core.Point3D.create(0, 0, -RADIUS_CM)
    arcs.addByCenterStartEnd(center, start, end)
    axis_line = lines.addByTwoPoints(start, end)

    # Revolve the closed profile around the axis line
    prof     = sketch.profiles.item(0)
    revolves = root.features.revolveFeatures
    rev_in   = revolves.createInput(
        prof,
        axis_line,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    rev_in.setAngleExtent(
        False,
        adsk.core.ValueInput.createByString("360 deg")
    )
    revolves.add(rev_in)

    print(f"Sphere created: radius={RADIUS_CM*10:.0f} mm")


# =============================================================================
# BONUS: fillet_all_edges — run AFTER D-02 (needs a body to fillet)
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app  = adsk.core.Application.get()
    des  = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    if root.bRepBodies.count == 0:
        print("No bodies found — run D-02 first to create a cube")
        return

    body   = root.bRepBodies.item(0)
    edges  = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        edges.add(edge)

    fillets    = root.features.filletFeatures
    fillet_in  = fillets.createInput()
    fillet_in.addConstantRadiusEdgeSet(
        edges,
        adsk.core.ValueInput.createByReal(0.1),   # 1 mm radius
        True
    )
    fillets.add(fillet_in)

    print(f"Filleted {edges.count} edges with 1 mm radius")
