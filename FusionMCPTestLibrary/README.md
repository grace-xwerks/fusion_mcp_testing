# Fusion MCP Test Library
Generated 2026-05-19 · 108 scripts

## How to use

### Running a script from Fusion
1. Open Fusion 360.
2. Go to **Tools → Scripts and Add-Ins** (or press Shift+S).
3. Click the **Scripts** tab.
4. Under **My Scripts**, find any `MCP_*` entry.
5. Select it and click **Run**.
6. Output appears in **View → Text Commands**.

### Script groups

| Group | Prefix | Prerequisite |
|-------|--------|-------------|
| Core smoke tests | `MCP_D_` | New design open |
| Design workspace | `MCP_DESIGN_` | New design open |
| Manufacture workspace | `MCP_CAM_` | Switch to Manufacture after running DESIGN-03 |
| Drawings workspace | `MCP_DRW_` | Open a Drawing document after DESIGN-03 |

### Recommended run order
```
MCP_D_01  →  MCP_D_02  →  MCP_D_03  →  MCP_D_04  →  MCP_D_05

MCP_DESIGN_01  →  ...  →  MCP_DESIGN_06

  (switch to Manufacture workspace)

MCP_CAM_01  →  MCP_CAM_02  →  MCP_CAM_03
  →  MCP_CAM_04 (Facing)
  →  MCP_CAM_05 (Adaptive/HEM)
  →  MCP_CAM_06 (Pocket)
  →  MCP_CAM_07 (Contour)
  →  MCP_CAM_08 (Drill)
  →  MCP_CAM_09 (Chamfer)
  →  MCP_CAM_10 (Generate)
  →  MCP_CAM_11 (Post → G-code)
  →  MCP_CAM_12 (Audit)

  (open a Drawing document referencing the Bracket)

MCP_DRW_01  →  ...  →  MCP_DRW_10   (base drawings)
MCP_DRW_11  →  ...  →  MCP_DRW_15   (section views)
MCP_DRW_16  →  ...  →  MCP_DRW_21   (BOM + balloons)
```

### Re-generating the library
If source files are updated, re-run the builder from your terminal:
```bash
python build_fusion_mcp_library.py
```

### Key rules (all scripts follow these)
- Entry point is always `def run(context):`
- All output via `print()` — visible in Text Commands panel
- **No try/except** — unhandled exceptions are the intended error signal
- Fusion internal units are **centimeters** (`1.0 cm = 10 mm`)
