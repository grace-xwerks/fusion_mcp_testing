"""
MCP_DESIGN_24_Rigid_joint_between_two_peg_sub
=============================================
Group       : Design
Script ID   : DESIGN-24
Description : Rigid joint between two peg sub-components
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_24_Rigid_joint_between_two_peg_sub

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

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
