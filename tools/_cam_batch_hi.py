

# =============================================================================
# CAM-39  Stock Material Library inventory
#         Walks adsk.cam.CAMManager.libraryManager.stockMaterialLibrary and
#         dumps every location + child asset. Stock materials power feed/speed
#         lookups and machining-power estimates per material.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    sml = adsk.cam.CAMManager.get().libraryManager.stockMaterialLibrary
    print(f"stockMaterialLibrary: {sml}")
    for label in ('CloudLibraryLocation', 'Fusion360LibraryLocation',
                  'LocalLibraryLocation', 'HubLibraryLocation',
                  'OnlineSamplesLibraryLocation', 'ExternalLibraryLocation',
                  'NetworkLibraryLocation'):
        loc = getattr(adsk.cam.LibraryLocations, label, None)
        if loc is None: continue
        try:
            root = sml.urlByLocation(loc)
        except Exception as e:
            print(f"  {label:32s}  urlByLocation FAILED: {e}")
            continue
        if not root:
            print(f"  {label:32s}  (no root)")
            continue
        try:
            assets = sml.childAssetURLs(root)
        except Exception as e:
            print(f"  {label:32s}  childAssetURLs FAILED: {e}")
            continue
        print(f"  {label:32s}  assets={len(assets)}")
        for i in range(min(len(assets), 20)):
            print(f"      {assets[i].toString()}")
        if len(assets) > 20:
            print(f"      ... +{len(assets) - 20} more")


# =============================================================================
# CAM-40  CAM Template Library inventory
#         CAM templates are saved Setup configurations (machine + WCS + stock
#         conventions). They drive the "Apply Template" UI in the CAM browser.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    tl = adsk.cam.CAMManager.get().libraryManager.templateLibrary
    print(f"templateLibrary: {tl}")
    for label in ('CloudLibraryLocation', 'Fusion360LibraryLocation',
                  'LocalLibraryLocation', 'HubLibraryLocation',
                  'OnlineSamplesLibraryLocation'):
        loc = getattr(adsk.cam.LibraryLocations, label, None)
        if loc is None: continue
        try:
            root = tl.urlByLocation(loc)
        except Exception as e:
            print(f"  {label:32s}  urlByLocation FAILED: {e}")
            continue
        if not root:
            print(f"  {label:32s}  (no root)")
            continue
        try:
            assets = tl.childAssetURLs(root)
        except Exception as e:
            print(f"  {label:32s}  childAssetURLs FAILED: {e}")
            continue
        print(f"  {label:32s}  assets={len(assets)}")
        for i in range(min(len(assets), 20)):
            print(f"      {assets[i].toString()}")
        if len(assets) > 20:
            print(f"      ... +{len(assets) - 20} more")


# =============================================================================
# CAM-41  Print Setting Library inventory (additive)
#         Print settings power the FFF/PBF additive workflows. Stored as
#         per-material profiles in the print-setting library.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    psl = adsk.cam.CAMManager.get().libraryManager.printSettingLibrary
    print(f"printSettingLibrary: {psl}")
    for label in ('CloudLibraryLocation', 'Fusion360LibraryLocation',
                  'LocalLibraryLocation', 'HubLibraryLocation',
                  'OnlineSamplesLibraryLocation'):
        loc = getattr(adsk.cam.LibraryLocations, label, None)
        if loc is None: continue
        try:
            root = psl.urlByLocation(loc)
        except Exception as e:
            print(f"  {label:32s}  urlByLocation FAILED: {e}")
            continue
        if not root:
            print(f"  {label:32s}  (no root)")
            continue
        try:
            assets = psl.childAssetURLs(root)
        except Exception as e:
            print(f"  {label:32s}  childAssetURLs FAILED: {e}")
            continue
        print(f"  {label:32s}  assets={len(assets)}")
        for i in range(min(len(assets), 20)):
            print(f"      {assets[i].toString()}")
        if len(assets) > 20:
            print(f"      ... +{len(assets) - 20} more")


# =============================================================================
# CAM-42  Machine Library inventory
#         Machine definitions drive multi-axis kinematics, post selection,
#         simulation. CAM-14 already touches this; CAM-42 is the focused
#         per-location dump showing categories of machines available.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    ml = adsk.cam.CAMManager.get().libraryManager.machineLibrary
    print(f"machineLibrary: {ml}")
    for label in ('CloudLibraryLocation', 'Fusion360LibraryLocation',
                  'LocalLibraryLocation', 'HubLibraryLocation',
                  'OnlineSamplesLibraryLocation'):
        loc = getattr(adsk.cam.LibraryLocations, label, None)
        if loc is None: continue
        try:
            root = ml.urlByLocation(loc)
        except Exception as e:
            print(f"  {label:32s}  urlByLocation FAILED: {e}")
            continue
        if not root:
            print(f"  {label:32s}  (no root)")
            continue
        try:
            assets = ml.childAssetURLs(root)
        except Exception as e:
            print(f"  {label:32s}  childAssetURLs FAILED: {e}")
            continue
        # Bucket the URLs by their first path segment (manufacturer / vendor).
        buckets = {}
        for i in range(len(assets)):
            u = assets[i].toString()
            # system://VENDOR/Model.mch → VENDOR
            try:
                vendor = u.split('://', 1)[1].split('/', 1)[0]
            except Exception:
                vendor = '(unknown)'
            buckets[vendor] = buckets.get(vendor, 0) + 1
        print(f"  {label:32s}  total assets={len(assets)}  vendors={len(buckets)}")
        for vendor, n in sorted(buckets.items(), key=lambda kv: -kv[1])[:20]:
            print(f"      {n:4d}  {vendor}")
        if len(buckets) > 20:
            print(f"      ... +{len(buckets) - 20} more vendors")


# =============================================================================
# CAM-43  Manufacturing Models (separate machining body)
#         A ManufacturingModel is a CAM-side body that diverges from the
#         design body (e.g. with fixturing tabs added). Demo creates one if
#         the doc has none, otherwise reports the existing ones.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam:
        print("Switch to Manufacture workspace first."); return

    mms = cam.manufacturingModels
    print(f"manufacturingModels.count = {mms.count}")
    for i in range(mms.count):
        m = mms.item(i)
        print(f"  [{i}] {m.name}")

    # Try to add a new one if API is available.
    try:
        ci = mms.createInput()
        ci.name = "CAM_Mfg_Model_Demo"
        # Source the design body as a baseline; ManufacturingModelInput typically
        # takes the design body via .designModel or models list.
        body = next((b for b in cam.designRootOccurrence.bRepBodies), None)
        if body is not None:
            for attr in ('models', 'designModel', 'body', 'sourceBody'):
                if hasattr(ci, attr):
                    try:
                        if attr == 'models':
                            setattr(ci, attr, [body])
                        else:
                            setattr(ci, attr, body)
                    except Exception:
                        pass
        added = mms.add(ci)
        print(f"  added: {added.name}")
    except AttributeError as e:
        print(f"  ManufacturingModels.createInput not exposed in this build: {e}")
    except Exception as e:
        print(f"  add failed: {e}")


# =============================================================================
# CAM-44  Two-Setup project (Roughing + Finishing split)
#         Real shops separate roughing and finishing into distinct Setups so
#         the operator can swap tools/stock between phases. Demo: add a
#         second Setup named 'BracketFinishingSetup' alongside the existing
#         BracketMillingSetup.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first."); return

    name = 'BracketFinishingSetup'
    existing = None
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        if s.name == name:
            existing = s; break
    if existing:
        print(f"Reusing: {existing.name}")
    else:
        bracket = next((b for b in cam.designRootOccurrence.bRepBodies
                        if b.name == 'Bracket'), None)
        if bracket is None:
            print("Need a body named 'Bracket' under designRootOccurrence."); return
        si = cam.setups.createInput(adsk.cam.OperationTypes.MillingOperation)
        si.models = [bracket]
        setup = cam.setups.add(si)
        setup.name = name
        print(f"Created: {setup.name}")

    print(f"\nAll setups in this CAM product:")
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        print(f"  [{i}] {s.name}  ops={s.allOperations.count}")


# =============================================================================
# CAM-45  NCPrograms.add (group post-processing into an NC program)
#         An NCProgram bundles one or more Setups/Operations into a named
#         post target. Demo: create an NC program covering the existing
#         BracketMillingSetup.
# =============================================================================

import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeProduct)
    if not cam or cam.setups.count == 0:
        print("Run CAM-03 first."); return

    ncs = cam.ncPrograms
    print(f"Existing NCPrograms: {ncs.count}")
    for i in range(ncs.count):
        n = ncs.item(i)
        print(f"  [{i}] {n.name}")

    try:
        ci = ncs.createInput()
        # NCProgramInput is the standard pattern. Set the post + program name,
        # then point at the setup to bundle.
        for attr_name, val in (('name', 'BracketNCProgram_Demo'),
                               ('programName', '1002')):
            if hasattr(ci, attr_name):
                try: setattr(ci, attr_name, val)
                except Exception: pass
        # Operations / scope: prefer .operations = [setup] if exposed.
        for attr_name in ('operations', 'parent', 'scope'):
            if hasattr(ci, attr_name):
                try:
                    if attr_name == 'operations':
                        setattr(ci, attr_name, [cam.setups.item(0)])
                    else:
                        setattr(ci, attr_name, cam.setups.item(0))
                except Exception:
                    pass
        added = ncs.add(ci)
        print(f"\nAdded NCProgram: {added.name}")
    except AttributeError as e:
        print(f"NCPrograms.createInput not exposed in this build: {e}")
    except Exception as e:
        print(f"add failed: {e}")
