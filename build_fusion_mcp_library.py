#!/usr/bin/env python3
"""
build_fusion_mcp_library.py
===========================
Reads the five MCP test source files and generates a proper Fusion script
library — one folder per script, each containing a .py file and a .manifest.

Run this from the terminal (not from inside Fusion):
    python build_fusion_mcp_library.py

Options (edit the CONFIG block below):
    INSTALL_TO_FUSION  — True: copy directly into Fusion's Scripts folder
                         False: output to OUTPUT_DIR only
    OUTPUT_DIR         — where to build the library before (optionally) installing

Fusion script directory locations:
    Windows : %APPDATA%\\Autodesk\\Autodesk Fusion 360\\API\\Scripts
    macOS   : ~/Library/Application Support/Autodesk/
                  Autodesk Fusion 360/API/Scripts

Each generated script folder:
    MCP_DESIGN_01_WorkspaceCheck/
        MCP_DESIGN_01_WorkspaceCheck.py       ← runnable Fusion script
        MCP_DESIGN_01_WorkspaceCheck.manifest ← JSON metadata for Scripts dialog
"""

import os
import re
import sys
import json
import shutil
import platform
import textwrap
import uuid
from pathlib import Path
from datetime import date

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG — edit these before running
# ─────────────────────────────────────────────────────────────────────────────

INSTALL_TO_FUSION = False   # set True to copy straight into Fusion's Scripts dir

# Where to write the library output (sibling to this script by default)
OUTPUT_DIR = Path(__file__).parent / "FusionMCPTestLibrary"

# Source files to parse, in the order they should appear in the library.
# Paths are relative to this script's directory.
SOURCE_FILES = [
    ("fusion_mcp_tests.py",            "Core"),
    ("fusion_design_tests.py",         "Design"),
    ("fusion_cam_tests.py",            "Manufacture"),
    ("fusion_drawings_tests.py",       "Drawings"),
    ("fusion_drawings_section_bom.py", "Drawings"),
]

AUTHOR  = "Fusion MCP Test Library"
VERSION = "1.0"

# ─────────────────────────────────────────────────────────────────────────────
# PARSING
# ─────────────────────────────────────────────────────────────────────────────

# A separator line is 60+ equals signs (our blocks use 77)
SEP_RE = re.compile(r'^# ={60,}\s*$')

# ID line patterns we support:
#   # DESIGN-01  Some description text
#   # CAM-01  Some description text
#   # DRW-11  Some description text
#   # D-01 — Some description
#   # D-03b — Some description
#   # BONUS: name — some description
ID_RE = re.compile(
    r'^#\s+'
    r'(?P<id>[A-Z][A-Z0-9_\-]*(?:\-\d+[a-z]?)|\bBONUS\b[^—\n]*)'
    r'(?:\s+—\s+|\s{2,})'
    r'(?P<desc>.+)$'
)


def slugify(text: str) -> str:
    """Turn arbitrary text into a safe Python identifier / folder name."""
    # Replace common punctuation with underscores
    text = re.sub(r'[^a-zA-Z0-9]+', '_', text)
    # Collapse multiple underscores, strip leading/trailing
    text = re.sub(r'_+', '_', text).strip('_')
    return text


def normalize_id(raw_id: str) -> str:
    """
    'DESIGN-01' → 'DESIGN_01'
    'CAM-01'    → 'CAM_01'
    'D-01'      → 'D_01'
    'D-03b'     → 'D_03b'
    'BONUS: design_inventory — ...' → 'BONUS'
    """
    raw_id = raw_id.strip().rstrip(':')
    return re.sub(r'[^a-zA-Z0-9]', '_', raw_id).strip('_')


def script_folder_name(script_id: str, description: str) -> str:
    """
    Build the folder/file name:  MCP_DESIGN_01_WorkspaceCheck
    Keeps total length reasonable for the filesystem.
    """
    nid  = normalize_id(script_id)          # DESIGN_01
    slug = slugify(description)             # Inspect_active_design_workspace_and_product_type_check
    # Cap slug at 40 chars at a word boundary
    if len(slug) > 40:
        slug = slug[:40].rsplit('_', 1)[0]
    return f"MCP_{nid}_{slug}"


def parse_source_file(path: Path, group: str):
    """
    Parse one source file and yield dicts:
        {id, description, group, folder_name, body}
    where `body` is the raw Python content of that script block
    (imports + run function, no outer separator lines).
    """
    text  = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    n     = len(lines)

    scripts    = []
    i          = 0

    while i < n:
        # Look for an opening separator
        if SEP_RE.match(lines[i]):
            # Next non-separator, non-empty line should be the ID line
            j = i + 1
            if j < n and SEP_RE.match(lines[j]):
                # Double separator with nothing in between — skip
                i = j + 1
                continue

            id_line = lines[j] if j < n else ""
            m = ID_RE.match(id_line)
            if not m:
                i += 1
                continue

            raw_id = m.group("id").strip()
            desc   = m.group("desc").strip()

            # Find closing separator — scan forward from j+1 (not assumed position)
            # because script headers often have a sub-note line between the two bars
            k = j + 1
            while k < n and not SEP_RE.match(lines[k]):
                k += 1
            if k >= n:
                i += 1
                continue
            close_sep = k

            # Content starts at close_sep + 1
            # Content ends at the next opening separator - 1 (or EOF)
            content_start = close_sep + 1
            content_end   = n
            for l in range(content_start, n):
                if SEP_RE.match(lines[l]):
                    content_end = l
                    break

            body_lines = lines[content_start:content_end]

            # Strip leading/trailing blank lines from body
            while body_lines and not body_lines[0].strip():
                body_lines.pop(0)
            while body_lines and not body_lines[-1].strip():
                body_lines.pop()

            # Skip pure-comment blocks (no actual code — e.g. the screenshot note)
            has_code = any(
                l.strip() and not l.strip().startswith('#')
                for l in body_lines
            )
            if not has_code:
                i = content_start
                continue

            # Skip if there's no run() function
            has_run = any(re.match(r'^def run\b', l) for l in body_lines)
            if not has_run:
                i = content_start
                continue

            fname = script_folder_name(raw_id, desc)
            scripts.append({
                "id":          raw_id,
                "description": desc,
                "group":       group,
                "folder_name": fname,
                "body":        "\n".join(body_lines),
            })

            i = content_start
        else:
            i += 1

    return scripts


# ─────────────────────────────────────────────────────────────────────────────
# GENERATION
# ─────────────────────────────────────────────────────────────────────────────

PY_HEADER = '''\
"""
{folder_name}
{underline}
Group       : {group}
Script ID   : {id}
Description : {description}
Generated   : {date}

Part of the Fusion MCP Test Library.
Run via: Fusion → Tools → Scripts and Add-Ins → Scripts tab → {folder_name}

Entry point: run(context)  — called by Fusion when the script is executed.
Output via print() — visible in the Text Commands panel (View → Text Commands).
Do NOT use try/except — unhandled exceptions are the MCP error signal.
"""

'''

MANIFEST_TEMPLATE = {
    "autodeskProduct": "Fusion",
    "type":            "script",
    "engine":          "Python",
    "license":         "None",
    "runOnStartup":    False,
    "supportedOS":     "windows|mac",
    "author":          AUTHOR,
    "version":         VERSION,
    "editEnabled":     True,
}


def write_script(script: dict, out_dir: Path) -> Path:
    """Create the folder, .py, and .manifest for one script. Return folder path."""
    fname  = script["folder_name"]
    folder = out_dir / fname
    folder.mkdir(parents=True, exist_ok=True)

    # ── .py ──────────────────────────────────────────────────────────────────
    header = PY_HEADER.format(
        folder_name = fname,
        underline   = "=" * len(fname),
        group       = script["group"],
        id          = script["id"],
        description = script["description"],
        date        = date.today().isoformat(),
    )
    py_path = folder / f"{fname}.py"
    py_path.write_text(header + script["body"] + "\n", encoding="utf-8")

    # ── .manifest ────────────────────────────────────────────────────────────
    manifest = dict(MANIFEST_TEMPLATE)
    manifest["description"] = f"[{script['group']}] {script['id']}: {script['description']}"
    manifest["id"]          = str(uuid.uuid5(uuid.NAMESPACE_DNS, fname))
    manifest_path = folder / f"{fname}.manifest"
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8"
    )

    return folder


# ─────────────────────────────────────────────────────────────────────────────
# FUSION SCRIPTS DIRECTORY DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def find_fusion_scripts_dir() -> Path | None:
    """Return the Fusion user scripts directory for this OS, or None."""
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        candidate = Path(appdata) / "Autodesk" / "Autodesk Fusion 360" / "API" / "Scripts"
    elif system == "Darwin":
        candidate = (
            Path.home()
            / "Library"
            / "Application Support"
            / "Autodesk"
            / "Autodesk Fusion 360"
            / "API"
            / "Scripts"
        )
    else:
        return None   # Linux not officially supported by Fusion desktop

    return candidate if candidate.exists() else None


# ─────────────────────────────────────────────────────────────────────────────
# README
# ─────────────────────────────────────────────────────────────────────────────

README = """\
# Fusion MCP Test Library
Generated {date} · {count} scripts

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
"""


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    script_dir = Path(__file__).parent

    # ── Parse all source files ────────────────────────────────────────────────
    all_scripts = []
    missing     = []

    for filename, group in SOURCE_FILES:
        src = script_dir / filename
        if not src.exists():
            missing.append(filename)
            print(f"  ⚠  Source not found, skipping: {filename}")
            continue
        parsed = parse_source_file(src, group)
        print(f"  Parsed {len(parsed):2d} scripts from {filename}")
        all_scripts.extend(parsed)

    if not all_scripts:
        print("\nNo scripts parsed. Make sure the source files are in the same "
              "directory as this builder script.")
        sys.exit(1)

    print(f"\n  Total scripts: {len(all_scripts)}")

    # ── Deduplicate folder names (shouldn't happen, but be safe) ─────────────
    seen   = {}
    unique = []
    for s in all_scripts:
        fn = s["folder_name"]
        if fn in seen:
            print(f"  ⚠  Duplicate folder name '{fn}' — skipping second occurrence")
        else:
            seen[fn] = True
            unique.append(s)
    all_scripts = unique

    # ── Write output ──────────────────────────────────────────────────────────
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    for script in all_scripts:
        write_script(script, OUTPUT_DIR)

    # README
    readme_text = README.format(date=date.today().isoformat(), count=len(all_scripts))
    (OUTPUT_DIR / "README.md").write_text(readme_text, encoding="utf-8")

    print(f"\n  Library written to: {OUTPUT_DIR}")
    print(f"  Script folders    : {len(all_scripts)}")

    # ── Optionally install into Fusion ────────────────────────────────────────
    if INSTALL_TO_FUSION:
        fusion_dir = find_fusion_scripts_dir()
        if fusion_dir is None:
            print("\n  ⚠  Could not locate Fusion Scripts directory.")
            print("     Copy the folders from the output directory manually:")
            print(f"     {OUTPUT_DIR}")
        else:
            print(f"\n  Installing to Fusion Scripts: {fusion_dir}")
            installed = 0
            for script in all_scripts:
                src_folder = OUTPUT_DIR / script["folder_name"]
                dst_folder = fusion_dir / script["folder_name"]
                if dst_folder.exists():
                    shutil.rmtree(dst_folder)
                shutil.copytree(src_folder, dst_folder)
                installed += 1
            print(f"  Installed {installed} scripts.")
            print("  Restart Fusion (or refresh Scripts dialog) to see them.")
    else:
        fusion_dir = find_fusion_scripts_dir()
        if fusion_dir:
            print(f"\n  To install, either:")
            print(f"    a) Set INSTALL_TO_FUSION = True and re-run this script, or")
            print(f"    b) Copy the folders from:")
            print(f"         {OUTPUT_DIR}")
            print(f"       into:")
            print(f"         {fusion_dir}")
        else:
            print(f"\n  Fusion Scripts directory not detected on this machine.")
            print(f"  Copy folders from {OUTPUT_DIR} into your Fusion Scripts folder.")

    print("\n  Done.\n")


if __name__ == "__main__":
    print(f"\nFusion MCP Test Library Builder")
    print(f"{'=' * 40}")
    main()
