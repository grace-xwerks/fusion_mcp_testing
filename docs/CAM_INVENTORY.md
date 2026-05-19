# CAM API inventory — Fusion 2703.x Insider

Snapshot taken **2026-05-19** via `MCP_CAM_13` (strategies) and `MCP_CAM_14`
(libraries/posts) against `fusion_mcp_library_demo_cam_full`. Source-of-truth
for the CAM-test expansion in [issue #11](https://github.com/grace-xwerks/fusion_mcp_testing/issues).

The raw dumps live in [`out_cam_13.txt`](../out_cam_13.txt) and
[`out_cam_14.txt`](../out_cam_14.txt) at repo root.

## Coverage status — 2026-05-19

All 69 strategies in `OperationStrategy` now have at least an API-surface
demo (CAM-01..79):

- **Full operation tests** (createInput + add + generation): 49 — Bracket /
  Rotor scripts CAM-04..36 + CAM-48..52.
- **API-surface demos** (createFromString + createInput + try/except add):
  20 — CAM-37 (morph), CAM-38 (project), CAM-53..59 (multi-axis),
  CAM-60..62 (probing), CAM-63..79 (turning).

Demos are safe to run on the existing milling file — they instantiate the
strategy and dump parameter counts but tolerate the missing 5-axis machine /
probe tool / turning setup that full generation requires. Promote any demo
to a full test once the matching prereq lands in the file.

## OperationTypes enum — only 2 reachable

```text
MillingOperation     ok
TurningOperation     ok
JetMillingOperation  enum value missing
AdditiveFFFAMOperation  missing
AdditivePBFAMOperation  missing
InspectionOperation  missing
ProbingOperation     missing
CuttingOperation     missing
```

So in 2703.x Insider, **all** CAM strategies live under Milling or Turning
setups. Jet/Additive/Probing surface either via specific strategies inside
Milling (e.g. `probe`, `feature_construction`) or are not exposed via the
`OperationTypes` enum at all.

## Strategy catalogue — 69 unique

`setup.operations.compatibleStrategies` returns `adsk.cam.OperationStrategy`
objects. Properties: `.name`, `.title`, `.description`, plus boolean flags
`isMillingStrategy`, `isTurningStrategy`, `isDrillingStrategy`,
`isCuttingStrategy`, `isRotaryStrategy`, `is2DStrategy`, `is3DStrategy`,
`isFinishingStrategy`, `isAdditiveStrategy`, `isSupportStrategy`,
`isGenerationAllowed` (license/preview gate).

`OperationStrategy.createFromString(name)` constructs one from the string id —
useful when you want to inspect a strategy without spinning up a Setup.

### Already covered by CAM-01..12 (6)

| name         | title          | flags                  |
|--------------|----------------|------------------------|
| `face`       | Face           | Milling, 2D, Finishing |
| `adaptive2d` | 2D Adaptive    | Milling, Rotary, 2D    |
| `pocket2d`   | 2D Pocket      | Milling, Rotary, 2D    |
| `contour2d`  | 2D Contour     | Milling, Rotary, 2D, Finishing |
| `drill`      | Drill          | Drilling               |
| `chamfer2d`  | 2D Chamfer     | Milling, 2D, Finishing |

### 2D / 2.5D — uncovered (6)

| name        | title       | notes |
|-------------|-------------|-------|
| `bore`      | Bore        | helical bore — circular interpolation in a hole |
| `circular`  | Circular    | circular interpolation finish |
| `engrave`   | Engrave     | open-pocket text/logo carve |
| `profile2d` | 2D Profile  | flagged `Cutting` — waterjet/plasma/laser cut profile |
| `slot`      | Slot        | slot mill with optional widening |
| `thread`    | Thread      | thread milling (vs `turning_thread` for lathe) |
| `trace`     | Trace       | follow a 2D curve at a fixed Z |

### 3D milling — uncovered (16)

| name               | title             | allowed |
|--------------------|-------------------|---------|
| `adaptive`         | Adaptive Clearing | yes |
| `pocket_clearing`  | Pocket Clearing   | yes — non-adaptive 3D rough |
| `horizontal`       | Horizontal        | yes |
| `parallel`         | Parallel          | yes |
| `contour3d`        | Contour           | yes |
| `scallop`          | Scallop           | yes |
| `pencil`           | Pencil            | yes |
| `radial`           | Radial            | yes |
| `spiral`           | Spiral            | yes |
| `morphed_spiral`   | Morphed Spiral    | yes |
| `morph`            | Morph             | yes |
| `ramp`             | Ramp              | yes |
| `project`          | Project           | yes |
| `flat`             | Flat              | yes |
| `blend`            | Blend             | yes |
| `corner`           | Corner            | yes |
| `steep_and_shallow`| Steep and Shallow | yes |
| `chamfer`          | 3D Chamfer        | **no** (license/preview) |
| `inclined_walls`   | Wall              | **no** |
| `flow` / `flow2`   | Flow (Old) / Flow | `flow2` only |

### Multi-axis (5+2) — Batch E API-surface demos (CAM-53..59)

| name                  | title             | script |
|-----------------------|-------------------|--------|
| `three_plus_two`      | 3+2 Clearing      | CAM-53 |
| `multiaxis_roughing`  | Multi-Axis Clearing | CAM-54 |
| `multiaxis_finishing` | Multi-Axis Finishing | CAM-55 |
| `multi_axis_contour`  | Multi-Axis Contour | CAM-56 |
| `multi_axis_morph`    | Multi-Axis Morph  | CAM-57 |
| `swarf`               | Swarf             | CAM-58 |
| `advanced_swarf`      | Advanced Swarf    | CAM-59 |

Demos exercise the API via `createFromString` + `createInput` + `add` in
try/except. Live toolpath generation requires a 5-axis machine assignment +
strategy-specific drive geometry. Promote to full operation tests once a
5-axis-capable part (blade / impeller) is added.

### Rotary — uncovered (3)

| name                | title           |
|---------------------|-----------------|
| `rotary_contour`    | Rotary Contour  |
| `rotary_pocket`     | Rotary Pocket   |
| `rotary_finishing`  | Rotary Parallel |

### Finishing-misc — uncovered (2)

| name      | title    |
|-----------|----------|
| `deburr`  | Deburr   |
| `geodesic`| Geodesic |

### Probing & inspection — Batch F API-surface demos (CAM-60..62)

| name              | title           | script |
|-------------------|-----------------|--------|
| `probe`           | Probe WCS       | CAM-60 |
| `probe_geometry`  | Probe Geometry  | CAM-61 |
| `inspect_surface` | Inspect Surface | CAM-62 |

Live runs need a probe tool from the Fusion Samples / Probes library (6 assets).

### Construction / organizational — covered by CAM-49..52 (4)

| name                   | title                | script  | notes |
|------------------------|----------------------|---------|-------|
| `folder`               | Folder               | CAM-49  | Returns `CAMFolder`, NOT `CAMOperation`. Does not increment `setup.operations.count`. |
| `manual`               | Manual NC            | CAM-50  | Params: `manualType` (ChoiceParameterValue, 22 commands) + `comment` / `dwell`. Default `manualType='comment'`. |
| `hole_recognition`     | Hole Recognition     | CAM-51  | Returns `CAMHoleRecognition`, NOT `CAMOperation`. No `hasToolpath` — produces hole groups for downstream drill ops, not a toolpath. |
| `feature_construction` | Feature Construction | CAM-52  | Additive flag, but `isGenerationAllowed=True` and `add()` succeeds on a milling Setup. Generation needs real additive geometry. |

(CAM-47 = rotor rotary setup, CAM-48 = Batch D 5-strategy retest — both landed via PR #12.)

### Turning (lathe) — Batch G API-surface demos (CAM-63..79)

| name                         | title                       | script |
|------------------------------|-----------------------------|--------|
| `turning_face`               | Turning Face                | CAM-63 |
| `turning_profile`            | Turning Profile             | CAM-64 |
| `turning_profile_roughing`   | Turning Profile Roughing    | CAM-65 |
| `turning_profile_finishing`  | Turning Profile Finishing   | CAM-66 |
| `turning_adaptive_roughing`  | Turning Adaptive Roughing   | CAM-67 |
| `turning_chamfer`            | Turning Chamfer             | CAM-68 |
| `turning_part`               | Turning Part                | CAM-69 |
| `turning_single_groove`      | Turning Single Groove       | CAM-70 |
| `turning_groove_roughing`    | Turning Groove Roughing     | CAM-71 |
| `turning_groove_finishing`   | Turning Groove Finishing    | CAM-72 |
| `turning_profile_groove`     | Turning Groove (profile)    | CAM-73 |
| `turning_thread`             | Turning Thread              | CAM-74 |
| `turning_trace`              | Turning Trace               | CAM-75 |
| `turning_stock_transfer`     | Turning Stock Transfer      | CAM-76 |
| `subspindle_grab`            | Subspindle Grab             | CAM-77 |
| `subspindle_return`          | Subspindle Return           | CAM-78 |
| `bar_pull`                   | Bar Pull                    | CAM-79 |

All turning demos probe for a TurningOperation Setup; without one they print
the metadata and stop. Adding a revolved-stock design + turning setup
unblocks full operation tests (see Batch G in the expansion plan below).

## Non-Setup API surface (from CAM-14)

`adsk.cam.CAMManager.get().libraryManager` exposes seven sub-libraries plus
folder paths:

| attr                  | type                |
|-----------------------|---------------------|
| `toolLibraries`       | `ToolLibraries`     |
| `postLibrary`         | `PostLibrary`       |
| `printSettingLibrary` | `PrintSettingLibrary` (additive) |
| `stockMaterialLibrary`| `StockMaterialLibrary` |
| `templateLibrary`     | `CAMTemplateLibrary` |
| `machineLibrary`      | `MachineLibrary`    |
| `fusion360PostFolder` | `C:\…\CAM\cache\posts` |
| `localPostFolder`     | `C:\…\Fusion 360 CAM\Posts` |
| `fusion360MachineFolder` | `C:\…\CAM\cache\machines` |
| `localMachineFolder`  | `C:\…\CAM360\machines` |
| `networkMachineFolder`| `C:\…\CAM360\network\machines` |

### Tool library locations (CAMLibraryManager.toolLibraries)

| location | assets | highlights |
|----------|--------|------------|
| `CloudLibraryLocation` | 10 | HAAS VF2SSYT (34), HSM (62), MAZAK C600 (40), Brother Speedio Steel/Aluminum (27/27), Mikron (27) |
| `Fusion360LibraryLocation` | 15 | Hole-Making 258/266, Milling 62/66, Turning 11/11, Holders 30/31, Tutorial 20/26, Probes 6, Cutting (jet) 3/3, Depositing 3 |
| `LocalLibraryLocation` | 12 | Multi_Vendor_Tool_Library_20260108 (254), CAT40 Holders (63), BT30 Holders (64), SVW (45), Library (12) |
| `ExternalLibraryLocation` | 0 | — |
| `HubLibraryLocation` | 0 | — |
| `NetworkLibraryLocation` | 0 | — |
| `OnlineSamplesLibraryLocation` | 0 | — |

### Posts present

- **Generic cache** (8): `brother multi-tasking`, `brother speedio`, `haas next generation`,
  `machinesimulation`, `mazak`, `mazak integrex i-100s`, `tsugami mo8sy mill-turn fanuc`,
  `setup-sheet`
- **Personal** (15): SVW Mazak Integrex variants (1–9), Brother Speedio, Brother Speedio
  inspection, Haas, Mazak Integrex i-100s, Tsugami

### Machine library

- 961 system machine assets (5AXISMAKER, Aconity3D, …)
- 4 local machine assets — incl. user-defined Generic dual-spindle Y-axis lathe

### NCPrograms / ManufacturingModels

Both empty in this doc (`count = 0`). Surface exists but no programs/MMs are
created on this file.

## Expansion plan — proposed batches

Order by setup complexity (Bracket-only first, then parts that need lathe
stock, then probe/inspect cycles, then library/manager scripts).

**Batch A — 2D extensions (6 scripts, Bracket-friendly)**
CAM-15a..f: `bore`, `circular`, `slot`, `engrave`, `trace`, `thread`.

**Batch B — 3D milling (10 scripts, Bracket-friendly)**
CAM-16a..j: `adaptive`, `pocket_clearing`, `horizontal`, `parallel`, `contour3d`,
`scallop`, `pencil`, `radial`, `spiral`, `morphed_spiral`. Skip `chamfer` and
`inclined_walls` for now (allowed=False on this license).

**Batch C — 3D milling extras (6 scripts)**
CAM-17a..f: `morph`, `ramp`, `project`, `flat`, `blend`, `corner`, `steep_and_shallow`.

**Batch D — Rotary + finishing-misc (5 scripts, need cylindrical stock)**
CAM-18a..e: `rotary_contour`, `rotary_pocket`, `rotary_finishing`, `deburr`,
`geodesic`. Will need a new part with rotary geometry.

**Batch E — Multi-axis (7 scripts, need a 5-axis machine setup)**
CAM-19a..g: `three_plus_two`, `multiaxis_roughing`, `multiaxis_finishing`,
`multi_axis_contour`, `multi_axis_morph`, `swarf`, `advanced_swarf`. Pick a
machine from the local 5-axis library.

**Batch F — Probing & inspection (3 scripts)**
CAM-20a..c: `probe`, `probe_geometry`, `inspect_surface`. Needs a probe tool
loaded from the Probes sample library.

**Batch G — Turning (17 scripts, need a Bracket-equivalent turning blank)**
CAM-21..23: `turning_face`, `turning_profile_roughing/_finishing`,
`turning_adaptive_roughing`, `turning_chamfer`, `turning_part`,
`turning_single_groove`, `turning_groove_roughing/_finishing`,
`turning_profile_groove`, `turning_thread`, `turning_trace`,
`turning_stock_transfer`, `subspindle_grab/_return`, `bar_pull`. Needs a
revolved-stock design.

**Batch H — Library/manager scripts (4 scripts, no part needed)**
CAM-24a `stockMaterialLibrary` inventory, b `templateLibrary` browsing,
c `printSettingLibrary` (additive), d `machineLibrary` query + assignment.

**Batch I — Manufacturing model + multi-setup (3 scripts)**
CAM-25a `manufacturingModels.add` (separate CAM model), b two-Setup project
(rough + finish split), c NC program creation via `cam.ncPrograms.add`.

That's **~61 new test scripts** to bring CAM coverage to ~73 total.

## How to use CAM-15 (per-strategy parameter dump)

CAM-15 takes a single strategy name and dumps its parameter table without
touching the rest of the surface. Edit the `STRATEGY = ` line in the source
or call via MCP with the script content patched, then run.

```python
STRATEGY = "scallop"   # any name from the catalogue above
```

This is the safe way to probe parameters one strategy at a time — the
"dump all 122" pattern crashed Fusion (report **941722456**), now logged as
quirk **#30** in [issue #3](https://github.com/grace-xwerks/fusion_mcp_testing/issues/3).
