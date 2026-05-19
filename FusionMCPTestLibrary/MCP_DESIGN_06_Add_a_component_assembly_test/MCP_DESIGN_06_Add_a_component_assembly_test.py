"""
MCP_DESIGN_06_Add_a_component_assembly_test
===========================================
Group       : Design
Script ID   : DESIGN-06
Description : Add a component / assembly test
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_DESIGN_06_Add_a_component_assembly_test

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

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
