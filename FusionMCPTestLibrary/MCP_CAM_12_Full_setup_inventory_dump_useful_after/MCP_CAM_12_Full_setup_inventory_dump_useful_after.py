"""
MCP_CAM_12_Full_setup_inventory_dump_useful_after
=================================================
Group       : Manufacture
Script ID   : CAM-12
Description : Full setup inventory dump — useful after a session to audit state
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_12_Full_setup_inventory_dump_useful_after

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Not in Manufacture workspace.")
        return

    print(f"=== CAM Setup Inventory ===")
    print(f"Total setups: {cam.setups.count}")

    for s_idx in range(cam.setups.count):
        setup = cam.setups.item(s_idx)
        print(f"\nSetup [{s_idx}]: {setup.name}")
        print(f"  Operation type : {setup.operationType}")
        print(f"  Operations     : {setup.allOperations.count}")

        for o_idx in range(setup.allOperations.count):
            op = setup.allOperations.item(o_idx)

            # Tool description via the parameter table (quirk #25 — no typeName)
            if op.tool:
                desc_param = op.tool.parameters.itemByName('tool_description')
                tool_desc  = desc_param.value.value if desc_param else (op.tool.description or '(tool)')
            else:
                tool_desc = "(no tool)"

            valid = "ok " if op.hasToolpath else "no "
            print(f"  [{valid}] [{o_idx}] {op.name:35s}  strategy={op.strategy}")
            print(f"         tool      : {tool_desc}")

            # Pull a couple of common operation parameters if present
            for pname in ('tolerance', 'stockToLeave', 'stepover',
                          'maximumStepdown', 'feedrate', 'spindleSpeed',
                          'spindle_speed'):
                p = op.parameters.itemByName(pname)
                if p is None:
                    continue
                # Parameter.value is a ValueInput-ish wrapper — try to read it
                # via .expression which is always a printable string.
                expr = getattr(p, 'expression', None)
                if expr is None:
                    expr = str(getattr(p, 'value', ''))
                print(f"         {pname:16s}: {expr}")
