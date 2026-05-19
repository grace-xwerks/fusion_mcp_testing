"""
MCP_DESIGN_14_Sweep_a_profile_along_a_path
==========================================
Group       : Design
Script ID   : DESIGN-14
Description : Sweep a profile along a path
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_14_Sweep_a_profile_along_a_path

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

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
