"""
flipbook_pack.py - pack a folder of RGBA frames into one sprite sheet for the hero layer (hero.js flipbook mode).

    python scripts/ai/flipbook_pack.py --id lev_jaws --frames generated/flipbook/lev_jaws_chomp --fps 24
    python scripts/ai/flipbook_pack.py --id lev_jaws --synthetic 12 --fps 24     # dry run: frames made from the cut-out itself

Writes slot_engine/static/canvas/assets/hero/<id>_sheet.webp (grid, max 4096 px on a side; frames are scaled down to fit)
and adds {"sheet": {"file", "cols", "rows", "count", "fps", "fw", "fh"}} to that id in assets/hero/hero.json. The first
frame must be the painting's own pose (the shader keeps the painting's depth map and rig anchors for every frame).

--synthetic N: builds N frames from <id>.png by sliding the lower jaw (below the rig hinge, feathered) up to 0.16 h and the
upper jaw down 0.05 h, i.e. the same motion the shader mask does today, so the playback path can be proven before real
interpolated frames exist.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "slot_engine" / "static" / "canvas" / "assets" / "hero"
MAX_SIDE = 4096
HINGE = {"lev_jaws": 0.58}   # image-space y of the mouth midline (matches hero.js RIG)


def synthetic(jid: str, n: int):
    src = Image.open(OUT / f"{jid}.png").convert("RGBA")
    a = np.asarray(src, dtype=np.float32)
    h, w = a.shape[:2]
    hinge = HINGE.get(jid, 0.58)
    yy = np.arange(h)[:, None] / h
    lower = np.clip((yy - (hinge - 0.035)) / 0.07, 0, 1)      # 1 below the hinge, 0 above, feathered
    frames = []
    for i in range(n):
        k = i / max(1, n - 1)
        k = k * k * (3 - 2 * k)
        dy_lo, dy_up = int(round(0.16 * h * k)), int(round(0.05 * h * k))
        lo = np.roll(a, -dy_lo, axis=0); lo[h - dy_lo:] = 0
        up = np.roll(a, dy_up, axis=0); up[:dy_up] = 0
        m = np.broadcast_to(lower, (h, w))[..., None]
        f = lo * m + up * (1 - m)
        frames.append(Image.fromarray(f.astype(np.uint8), "RGBA"))
    return frames


def pack(jid: str, frames, fps: int):
    n = len(frames)
    fw, fh = frames[0].size
    cols = math.ceil(math.sqrt(n * fh / fw)) if fw < fh else math.ceil(math.sqrt(n))
    cols = max(1, min(n, cols))
    rows = math.ceil(n / cols)
    scale = min(1.0, MAX_SIDE / (cols * fw), MAX_SIDE / (rows * fh))
    cw, ch = int(fw * scale), int(fh * scale)
    sheet = Image.new("RGBA", (cw * cols, ch * rows), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        if scale < 1:
            f = f.resize((cw, ch), Image.LANCZOS)
        sheet.paste(f, ((i % cols) * cw, (i // cols) * ch))
    # WebP keeps the alpha and is ~10x smaller than PNG for painted frames (every browser the game targets decodes it)
    fname = f"{jid}_sheet.webp"
    sheet.save(OUT / fname, format="WEBP", quality=86, method=6)
    man_p = OUT / "hero.json"
    man = json.loads(man_p.read_text(encoding="utf-8"))
    man.setdefault(jid, {})["sheet"] = {"file": fname, "cols": cols, "rows": rows, "count": n, "fps": fps, "fw": cw, "fh": ch}
    man_p.write_text(json.dumps(man, indent=2), encoding="utf-8")
    print(f"[flipbook] {jid}: {n} frames {cw}x{ch} in a {cols}x{rows} sheet ({sheet.width}x{sheet.height}, "
          f"{(OUT / fname).stat().st_size / 1e6:.2f} MB) at {fps} fps -> hero.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--frames", help="folder of RGBA PNG frames in name order")
    ap.add_argument("--synthetic", type=int, default=0)
    ap.add_argument("--fps", type=int, default=24)
    a = ap.parse_args()
    if a.synthetic:
        frames = synthetic(a.id, a.synthetic)
    elif a.frames:
        files = sorted(Path(a.frames).glob("*.png"))
        if not files:
            sys.exit(f"no frames in {a.frames}")
        frames = [Image.open(f).convert("RGBA") for f in files]
        base = Image.open(OUT / f"{a.id}.png")
        frames = [f if f.size == base.size else f.resize(base.size, Image.LANCZOS) for f in frames]
    else:
        sys.exit("give --frames <dir> or --synthetic N")
    pack(a.id, frames, a.fps)
    return 0


if __name__ == "__main__":
    sys.exit(main())
