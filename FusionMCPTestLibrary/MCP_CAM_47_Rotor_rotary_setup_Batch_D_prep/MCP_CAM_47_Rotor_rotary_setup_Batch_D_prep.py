"""
MCP_CAM_47_Rotor_rotary_setup_Batch_D_prep
==========================================
Group       : Manufacture
Script ID   : CAM-47
Description : Rotor rotary setup (Batch D prep)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_47_Rotor_rotary_setup_Batch_D_prep

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first (run CAM-01).")
        return

    # Find the Rotor occurrence under the CAM-linked design root
    rotor_occ = next(
        (o for o in cam.designRootOccurrence.component.allOccurrences
         if o.component.name == 'Rotor'),
        None)
    if rotor_occ is None:
        print("Rotor occurrence not found — run DESIGN-29 / DESIGN-30 first.")
        return
    comp = rotor_occ.component
    rotor = comp.bRepBodies.itemByName('Rotor')
    if rotor is None:
        print("Rotor body not found in 'Rotor' component.")
        return

    # Idempotent: reuse if we already made it
    setup = next((s for s in cam.setups if s.name == 'RotorRotarySetup'), None)
    if setup is None:
        si = cam.setups.createInput(adsk.cam.OperationTypes.MillingOperation)
        si.models = [rotor]
        si.stockMode = adsk.cam.SetupStockModes.RelativeCylinderStock
        setup = cam.setups.add(si)
        setup.name = 'RotorRotarySetup'
        print(f"Created setup: {setup.name}")
    else:
        print(f"Reusing setup: {setup.name}")

    # Reorient WCS — Setup Z := rotor centerline (component X axis)
    setup.parameters.itemByName('wcs_orientation_mode').expression = "'axesZX'"
    setup.parameters.itemByName('wcs_orientation_axisZ').value.value = [comp.xConstructionAxis]
    setup.parameters.itemByName('wcs_orientation_axisX').value.value = [comp.yConstructionAxis]

    # Verify
    dia = setup.parameters.itemByName('stockDiameter').expression
    lng = setup.parameters.itemByName('stockLength').expression
    print(f"Stock after reorient: Ø{dia} × {lng} (expect ~42 × 100 mm)")
