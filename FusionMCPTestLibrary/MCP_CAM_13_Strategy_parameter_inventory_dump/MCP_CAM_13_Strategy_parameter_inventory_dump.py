"""
MCP_CAM_13_Strategy_parameter_inventory_dump
============================================
Group       : Manufacture
Script ID   : CAM-13
Description : Strategy + parameter inventory dump (planning input for expansion)
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_13_Strategy_parameter_inventory_dump

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first (run CAM-01).")
        return

    # Map OperationTypes enum members → human label. We probe each one and
    # only emit a section for the types the current document/install supports.
    optypes = []
    for label in (
        'MillingOperation', 'TurningOperation',
        'JetMillingOperation', 'AdditiveFFFAMOperation',
        'AdditivePBFAMOperation', 'InspectionOperation',
        'ProbingOperation', 'CuttingOperation',
    ):
        v = getattr(adsk.cam.OperationTypes, label, None)
        if v is not None:
            optypes.append((label, v))

    print(f"=== Operation-type surface ({len(optypes)} enum members reachable)")
    for label, _ in optypes:
        print(f"  - {label}")

    # We need at least one Setup we own to ask compatibleStrategies. Create a
    # throwaway setup per op-type, harvest the strategy list, then delete it.
    print("\n=== Strategy lists per OperationType")

    # Pick any solid body to seed the throwaway setups.
    seed_body = None
    for b in cam.designRootOccurrence.bRepBodies:
        seed_body = b
        break
    if seed_body is None:
        print("No bRepBody under designRootOccurrence — open a design with at least one body.")
        return

    inventory = {}   # op_type_label -> [strategy_string, ...]

    for label, val in optypes:
        try:
            si = cam.setups.createInput(val)
            si.models = [seed_body]
            tmp = cam.setups.add(si)
        except Exception as e:
            print(f"  {label:30s}  setup-create FAILED: {e}")
            continue

        try:
            strategies = list(tmp.operations.compatibleStrategies)
        except Exception as e:
            strategies = []
            print(f"  {label:30s}  compatibleStrategies FAILED: {e}")

        # OperationStrategy objects expose .name / .title / .description and a
        # set of is{Milling,Turning,Drilling,Cutting,2D,3D,Finishing,
        # Additive,Support,Rotary}Strategy flags plus isGenerationAllowed.
        strat_rows = []
        for s in strategies:
            name = getattr(s, 'name', '?')
            title = getattr(s, 'title', '')
            flags = []
            for fname in ('isMillingStrategy','isTurningStrategy','isDrillingStrategy',
                          'isCuttingStrategy','isRotaryStrategy','is2DStrategy',
                          'is3DStrategy','isFinishingStrategy','isAdditiveStrategy',
                          'isSupportStrategy'):
                try:
                    if getattr(s, fname):
                        flags.append(fname.replace('is','').replace('Strategy',''))
                except Exception:
                    pass
            allowed = getattr(s, 'isGenerationAllowed', None)
            strat_rows.append((name, title, allowed, flags))

        inventory[label] = strat_rows
        print(f"\n  {label}  ({len(strat_rows)} strategies)")
        for name, title, allowed, flags in strat_rows:
            tag = ','.join(flags) if flags else '-'
            print(f"    {name:30s}  allowed={allowed!s:5s}  flags={tag:60s}  title={title!r}")

        # Clean up throwaway setup
        try:
            tmp.deleteMe()
        except Exception:
            pass

    # NOTE: An earlier version of this script also enumerated `op.parameters`
    # for every one of the ~122 strategies in a single run() — that hammered
    # Fusion hard enough to crash it (report 941722456). The parameter dump
    # now lives in CAM-15, which takes one strategy at a time.
    print("\n(parameter dump moved to CAM-15 — strategy-at-a-time to avoid OOM)")
