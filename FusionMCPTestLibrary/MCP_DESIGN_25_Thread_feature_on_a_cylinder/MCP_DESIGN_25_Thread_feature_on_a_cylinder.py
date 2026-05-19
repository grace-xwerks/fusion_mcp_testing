"""
MCP_DESIGN_25_Thread_feature_on_a_cylinder
==========================================
Group       : Design
Script ID   : DESIGN-25
Description : Thread feature on a cylinder
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_25_Thread_feature_on_a_cylinder

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

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
