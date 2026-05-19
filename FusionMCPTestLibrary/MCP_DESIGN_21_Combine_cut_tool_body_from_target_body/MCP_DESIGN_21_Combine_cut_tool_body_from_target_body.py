"""
MCP_DESIGN_21_Combine_cut_tool_body_from_target_body
====================================================
Group       : Design
Script ID   : DESIGN-21
Description : Combine: cut tool body from target body (boolean subtract)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_21_Combine_cut_tool_body_from_target_body

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

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
