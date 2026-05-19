# Fusion MCP Testing

> A comprehensive test suite for the Autodesk Fusion 360 Model Context Protocol Server

![Python](https://img.shields.io/badge/Python-3.8+-3776ab?logo=python&logoColor=white)
![Fusion 360](https://img.shields.io/badge/Fusion%20360-Latest-0078d7)
![Tests](https://img.shields.io/badge/Tests-104-brightgreen)

---

## 🎯 Overview

**Fusion MCP Testing** is a production-grade test suite that exercises the Autodesk Fusion 360 API across all major workspaces through 104 carefully sequenced test scripts. Whether you're validating the MCP server, building CAD automation, or learning the Fusion API, this suite has you covered.

```
✓ Design workspace (parametric modeling, features, sketches)
✓ Manufacture workspace (CAM toolpaths, operations)
✓ Drawings workspace (technical drawings, BOMs, annotations)
✓ Core connectivity & error handling tests
```

## 📥 Installation

### 1. Clone the repository
```bash
git clone https://github.com/grace-xwerks/fusion_mcp_testing.git
cd fusion_mcp_testing
```

### 2. Generate the test library
```bash
python build_fusion_mcp_library.py
```

This parses the source files and generates 104 runnable Fusion scripts with proper manifests.

### 3. Install into Fusion (two options)

**Option A: Automatic (recommended)**
```python
# Edit build_fusion_mcp_library.py, set:
INSTALL_TO_FUSION = True

# Then run:
python build_fusion_mcp_library.py
```

**Option B: Manual**
Copy the generated `FusionMCPTestLibrary/` folder contents into Fusion's scripts directory:

- **Windows**: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\`
- **macOS**: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts/`

### 4. Run in Fusion

1. Open **Fusion 360**
2. Go to **Tools → Scripts and Add-Ins** (or press **Shift+S**)
3. Click the **Scripts** tab
4. Find any `MCP_*` script under **My Scripts**
5. Click **Run**
6. View output in **View → Text Commands**

## 📚 Test Organization

Tests are grouped by workspace. Follow the recommended run order to build state as you go:

### Core Smoke Tests (`MCP_D_*`)
```
MCP_D_01  →  MCP_D_02  →  MCP_D_03  →  MCP_D_04  →  MCP_D_05
```
Connectivity check, basic geometry, parameters, output fidelity, error handling.

### Design Workspace (`MCP_DESIGN_*`)
```
MCP_DESIGN_01  →  ...  →  MCP_DESIGN_06
```
Sketches, extrusions, revolves, fillets, parameters, and component hierarchies.

### Manufacture Workspace (`MCP_CAM_*`)
```
MCP_CAM_01  →  ...  →  MCP_CAM_12
```
Setup, facing, adaptive milling, pockets, contours, drilling, chamfering, postprocessing.

### Drawings Workspace (`MCP_DRW_*`)
```
MCP_DRW_01  →  ...  →  MCP_DRW_21
```
Basic views, section views, BOMs, balloons, and technical drawing annotations.

**See `FusionMCPTestLibrary/README.md` for the full run order and prerequisites.**

## 🏗️ Repository Structure

```
fusion_mcp_testing/
├── build_fusion_mcp_library.py      Generator (re-run this to rebuild)
├── fusion_mcp_tests.py               Core smoke tests (D-01 through D-05+)
├── fusion_design_tests.py            Design workspace tests
├── fusion_cam_tests.py               Manufacture/CAM workspace tests
├── fusion_drawings_tests.py          Drawing tests (views, dimensions)
├── fusion_drawings_section_bom.py   Drawing tests (sections, BOMs)
├── FusionMCPTestLibrary/             Generated scripts (do not edit)
│   ├── MCP_D_01_PrintFusionVersion/
│   ├── MCP_D_02_CreateCube/
│   ├── ...
│   └── README.md
├── ABOUT.md                         Project background & design philosophy
└── docs/                             Additional documentation
```

## 🔄 Workflow

### Editing tests

1. **Edit the source files** (e.g., `fusion_design_tests.py`)
2. **Re-run the builder**:
   ```bash
   python build_fusion_mcp_library.py
   ```
3. **Reload in Fusion** (restart or refresh the Scripts dialog)

### Creating a new test

1. Open the appropriate source file (`fusion_design_tests.py`, etc.)
2. Add a new test block with this structure:

```python
# =============================================================================
# DESIGN-99 — Brief description of what this test does
# =============================================================================

import adsk.core, adsk.fusion

def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    
    # Your test code here
    print("Test executed successfully")
```

3. Re-run the builder to generate the script

### Key rules

✅ **DO:**
- Use clear, descriptive headers
- Include ID + description in comments
- Export a `def run(context):` entry point
- Use `print()` for all output
- Let exceptions bubble up (that's the error signal!)

❌ **DON'T:**
- Use try/except (by design—unhandled exceptions are informative)
- Import outside the function
- Use threading or async code
- Rely on UI state beyond what the test sets up

## 📖 Units & Conventions

**Fusion API uses centimeters as its internal unit system.**

- `1.0 cm` = `10 mm`
- `2.54 cm` = `1.0 inch`

All test scripts follow this convention. When specifying geometry, use:
```python
adsk.core.ValueInput.createByString("25 mm")  # String expressions work too
adsk.core.ValueInput.createByReal(2.5)        # This is 2.5 cm = 25 mm
```

## 🚀 Quick Examples

### Run your first test
```bash
# Build the library
python build_fusion_mcp_library.py

# Open Fusion, go to Tools → Scripts and Add-Ins
# Select MCP_D_01_PrintFusionVersion and click Run
# Check View → Text Commands for output
```

### Create a 10mm cube
Run **MCP_D_02_CreateCube** — generates a 10×10×10 mm solid body.

### Parameterized design
Run **MCP_D_03_AddUserParameter** then **MCP_D_03b_ParameterizedBox** to see user parameters in action.

### Full CAM workflow
Run the sequence **MCP_CAM_01** through **MCP_CAM_12** to generate a complete toolpath with postprocessing to G-code.

## ❓ FAQ

**Q: Why are there no try/except blocks?**  
A: Unhandled exceptions are the intended error signal in the MCP protocol. They tell the server something failed and provide a traceback. This keeps tests honest and errors visible.

**Q: Can I run tests in any order?**  
A: Each test's prerequisites are documented. Some tests depend on previous state (e.g., you need a body before filleting it). See the run order in `FusionMCPTestLibrary/README.md`.

**Q: How do I modify or add tests?**  
A: Edit the source `.py` files at the repo root, re-run `build_fusion_mcp_library.py`, and restart Fusion. The generator handles manifest creation automatically.

**Q: What if the builder fails?**  
A: Make sure Python 3.8+ is installed and all source files are in the same directory as the builder script. Check the console output for details.

**Q: Can I use this on Linux?**  
A: Fusion 360 is not officially available on Linux, so these tests are designed for Windows and macOS only.

## 📝 License

See LICENSE file in this repository.

## 🤝 Contributing

We welcome issues, feature requests, and pull requests. Please:

1. Follow the test structure and naming conventions
2. Keep tests atomic and well-documented
3. Include prerequisites in your description
4. Test locally before submitting

## 📞 Support

- **Issues?** Open a [GitHub issue](https://github.com/grace-xwerks/fusion_mcp_testing/issues)
- **Questions?** Check the docs or [Fusion API documentation](https://help.autodesk.com/view/fusion360/latest/ENU/)
- **Want to contribute?** See CONTRIBUTING.md (coming soon)

## 🔗 Related Resources

- [Autodesk Fusion 360 API Docs](https://help.autodesk.com/view/fusion360/latest/ENU/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Fusion API Samples & Tutorials](https://github.com/autodesk-fusion-360-api-samples)

---

**Made with ❤️ for the Fusion 360 community**

*Last updated: 2026-05-19*
