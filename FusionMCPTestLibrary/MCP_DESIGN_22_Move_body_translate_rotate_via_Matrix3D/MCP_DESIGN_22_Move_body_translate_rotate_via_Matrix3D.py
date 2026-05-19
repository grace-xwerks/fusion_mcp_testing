"""
MCP_DESIGN_22_Move_body_translate_rotate_via_Matrix3D
=====================================================
Group       : Design
Script ID   : DESIGN-22
Description : Move body (translate + rotate via Matrix3D)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_22_Move_body_translate_rotate_via_Matrix3D

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

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
