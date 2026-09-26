#!/usr/bin/env python3
"""
Scaffolder CLI for Studio-Grade 3D WebGL Slot Engine.
Usage:
    python3 scaffold_slot_3d.py --target-dir /path/to/slot/static
"""

import os
import sys
import shutil
from pathlib import Path
import argparse

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_DIR / "templates"


def scaffold(target_dir: Path, creature_name: str = "Leviathan", rows: int = 5, cols: int = 5):
    target_dir = Path(target_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Scaffolding 3D WebGL Slot Engine into: {target_dir}")
    print(f"[*] Mascot / Creature: {creature_name} ({rows}x{cols} Grid)")

    # 1. Copy webgl_viewport.js
    viewport_src = TEMPLATES_DIR / "webgl_viewport.template.js"
    viewport_dest = target_dir / "webgl_viewport.js"
    content = viewport_src.read_text()
    content = content.replace("rows: 5", f"rows: {rows}").replace("cols: 5", f"cols: {cols}")
    viewport_dest.write_text(content)
    print(f"    [+] Created: {viewport_dest.name}")

    # 2. Copy creature_rig_3d.js
    creature_src = TEMPLATES_DIR / "creature_rig_3d.template.js"
    creature_dest = target_dir / "creature_rig_3d.js"
    creature_content = creature_src.read_text()
    creature_content = creature_content.replace("CreatureRig3D", f"{creature_name}Rig3D")
    creature_dest.write_text(creature_content)
    print(f"    [+] Created: {creature_dest.name}")

    # 3. Copy shader
    shader_src = TEMPLATES_DIR / "fluid_refraction.frag.glsl"
    shader_dest = target_dir / "fluid_refraction.frag.glsl"
    shutil.copyfile(shader_src, shader_dest)
    print(f"    [+] Created: {shader_dest.name}")

    print("\n[SUCCESS] 3D WebGL Slot Engine scaffolded successfully!")
    print("Next steps:")
    print("1. Add Three.js to HTML: <script src=\"https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js\"></script>")
    print("2. Add scripts to HTML: <script src=\"/static/creature_rig_3d.js\"></script> and <script src=\"/static/webgl_viewport.js\"></script>")
    print("3. Wire game timeline events to window.webglSlotViewport")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold 3D WebGL Slot Engine")
    parser.add_argument("--target-dir", default="./slot_engine/static", help="Target static folder")
    parser.add_argument("--creature-name", default="Leviathan", help="Name of creature mascot")
    parser.add_argument("--rows", type=int, default=5, help="Reels rows")
    parser.add_argument("--cols", type=int, default=5, help="Reels cols")
    args = parser.parse_args()

    scaffold(Path(args.target_dir), args.creature_name, args.rows, args.cols)
