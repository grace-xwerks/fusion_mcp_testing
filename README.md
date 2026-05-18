# FusionMCPTestLibrary

A library of Autodesk Fusion 360 scripts used to exercise the Fusion MCP server across the Design, Manufacture, and Drawings workspaces.

## Sources

Hand-written modules at the repo root:

- `fusion_mcp_tests.py` — core smoke tests (`MCP_D_*`)
- `fusion_design_tests.py` — Design workspace (`MCP_DESIGN_*`)
- `fusion_cam_tests.py` — Manufacture workspace (`MCP_CAM_*`)
- `fusion_drawings_tests.py` — Drawings workspace (`MCP_DRW_01..10`)
- `fusion_drawings_section_bom.py` — Drawings section views + BOM (`MCP_DRW_11..21`)
- `build_fusion_mcp_library.py` — parses the modules above and emits the runnable script library

## Generated library

`FusionMCPTestLibrary/` contains 48 runnable Fusion scripts (one folder per test, each with a `.py` + `.manifest`). See its inner `README.md` for run instructions and the recommended run order.

## Regenerating

```bash
python build_fusion_mcp_library.py
```

Set `INSTALL_TO_FUSION = True` in the builder to copy directly into Fusion's `API/Scripts` directory.
