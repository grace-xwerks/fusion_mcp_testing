"""
MCP_CAM_10_Generate_toolpaths_for_all_operations
================================================
Group       : Manufacture
Script ID   : CAM-10
Description : Generate toolpaths for all operations in setup 0
Generated   : 2026-05-19

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → MCP_CAM_10_Generate_toolpaths_for_all_operations

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

import adsk.core, adsk.cam
import time

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first.")
        return

    setup = cam.setups.item(0)
    print(f"Generating toolpaths for setup: {setup.name}")
    print(f"Operations in setup: {setup.allOperations.count}")

    # generateAllToolpaths(skipValid=True) — only regen invalid/missing paths
    future = cam.generateAllToolpaths(True)
    print(f"Operations queued: {future.numberOfOperations}")

    # Block until generation completes; stay defensive even though Fusion
    # typically serializes the call.
    while not future.isGenerationCompleted:
        time.sleep(0.2)

    print("Toolpath generation completed.")

    # Report per-op status
    success = 0
    failed  = 0
    for i in range(setup.allOperations.count):
        op = setup.allOperations.item(i)
        ok = op.hasToolpath
        if ok:
            success += 1
        else:
            failed += 1
        print(f"  {op.name:35s} hasToolpath={op.hasToolpath}")

    print(f"\nSuccess: {success}   Failed/unsupported: {failed}")

    # Total cycle time (across all generated ops in this setup)
    total_seconds = 0.0
    for i in range(setup.allOperations.count):
        op = setup.allOperations.item(i)
        if op.hasToolpath:
            # Signature: getMachiningTime(op, feedScale, rapidScale, toolChangeTime)
            # Returned MachiningTime exposes .machiningTime (seconds), .feedDistance
            # (cm), .rapidDistance (cm), .totalFeedTime, .totalRapidTime,
            # .toolChangeCount, .totalToolChangeTime — NOT machiningTimeInSeconds.
            mt = cam.getMachiningTime(op, 1.0, 1.0, 5.0)
            total_seconds += mt.machiningTime

    print(f"Total cycle time: {total_seconds:.1f} s "
          f"({total_seconds/60:.2f} min)")
