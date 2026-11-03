"""
hero_prep.py - turn Leviathan hero paintings into the 2.5D textures the canvas front end plays (hero.js).

For every job id in scripts/ai/prompts/p3_leviathan_hero.json it looks for generated/inbox/p3_leviathan_hero/<id>_<n>.png|jpg|webp
(the Gemini app results, painted on pure black), picks the first (or --pick <id>=<n>), and writes to slot_engine/static/canvas/assets/hero/:
  <id>.png        RGBA cut-out (luminance key against black, same recipe as designer_pass.cutout), max 1536 px wide
  <id>_depth.png  8-bit pseudo depth: distance-from-edge of the matte (centre of the mass is nearest) blended with luminance
                  (lit, specular parts come forward), blurred. hero.js parallaxes the colour image through it.
  hero.json       manifest: id -> { file, depth, w, h, source }

    python scripts/ai/hero_prep.py                  # from the inbox
    python scripts/ai/hero_prep.py --placeholder    # procedural stand-ins (eye, jaws, rise, maw) so the layer can be tested before art lands
    python scripts/ai/hero_prep.py --pick lev_eye=2 --pick lev_jaws=1
"""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from designer_pass import cutout  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "scripts" / "ai" / "prompts" / "p3_leviathan_hero.json"
INBOX = REPO / "generated" / "inbox" / "p3_leviathan_hero"
OUT = REPO / "slot_engine" / "static" / "canvas" / "assets" / "hero"
MAX_W = 1536


def depth_from(img: Image.Image) -> Image.Image:
    """Pseudo depth from the matte: inside-distance (bulk comes forward) + luminance (lit skin comes forward)."""
    a = np.asarray(img.getchannel("A"), dtype=np.float32) / 255
    lum = np.asarray(img.convert("L"), dtype=np.float32) / 255
    mask = a > 0.3
    dist = ndimage.distance_transform_edt(mask) if mask.any() else np.zeros_like(a)
    dist = dist / (dist.max() or 1)
    dist = np.sqrt(dist)                       # bulge, not a cone
    d = 0.55 * dist + 0.45 * lum * a
    d = ndimage.gaussian_filter(d, 6)
    d = (d - d.min()) / ((d.max() - d.min()) or 1)
    return Image.fromarray((d * 255).astype(np.uint8), "L")


def placeholder(kind: str, w: int = 1536, h: int = 864) -> Image.Image:
    """Procedural stand-ins in the palette, painted straight to RGBA. Crude on purpose: they prove the pipeline, not the art."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy = (63, 245, 255)
    skin = (14, 24, 28)
    if kind == "lev_eye":
        cx, cyy, r = int(w * 0.62), int(h * 0.5), int(h * 0.42)
        d.ellipse([cx - r * 1.6, cyy - r * 1.05, cx + r * 1.6, cyy + r * 1.05], fill=skin + (255,))
        for i in range(10, 0, -1):
            k = i / 10
            col = (int(8 + 40 * k), int(60 + 150 * k), int(70 + 170 * k), 255)
            d.ellipse([cx - r * k, cyy - r * k, cx + r * k, cyy + r * k], fill=col)
        d.ellipse([cx - r * 0.16, cyy - r * 0.95, cx + r * 0.16, cyy + r * 0.95], fill=(2, 6, 10, 255))
        d.ellipse([cx - r * 0.5, cyy - r * 0.7, cx - r * 0.3, cyy - r * 0.5], fill=(220, 250, 255, 200))
        d.ellipse([cx - r * 1.7, cyy - r * 1.15, cx + r * 1.7, cyy - r * 0.55], fill=(6, 12, 15, 255))
    elif kind in ("lev_jaws", "lev_maw"):
        d.ellipse([w * 0.08, h * 0.02, w * 0.92, h * 0.98], fill=skin + (255,))
        d.ellipse([w * 0.2, h * 0.18, w * 0.8, h * 0.82], fill=(2, 5, 8, 255))
        d.ellipse([w * 0.42, h * 0.4, w * 0.58, h * 0.6], fill=(20, 110, 120, 255))
        n = 22
        for i in range(n):
            a = i / n * 2 * math.pi
            x0, y0 = w * 0.5 + math.cos(a) * w * 0.3, h * 0.5 + math.sin(a) * h * 0.32
            x1, y1 = w * 0.5 + math.cos(a) * w * 0.18, h * 0.5 + math.sin(a) * h * 0.19
            px, py = -math.sin(a) * 14, math.cos(a) * 14
            d.polygon([(x0 + px, y0 + py), (x0 - px, y0 - py), (x1, y1)], fill=(236, 226, 205, 255))
    else:  # lev_rise
        d.ellipse([w * 0.15, h * 0.42, w * 0.85, h * 1.4], fill=skin + (255,))
        d.ellipse([w * 0.36, h * 0.55, w * 0.46, h * 0.63], fill=(30, 150, 160, 255))
        d.ellipse([w * 0.4, h * 0.57, w * 0.42, h * 0.61], fill=(2, 6, 10, 255))
        for i in range(9):
            x = w * (0.3 + i * 0.05)
            d.ellipse([x - 6, h * 0.5 - 6, x + 6, h * 0.5 + 6], fill=cy + (255,))
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    # soft fade into black at the edges like a painting on #000
    a = np.asarray(img.getchannel("A"), dtype=np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.minimum.reduce([xx, w - xx, yy, h - yy]) / (0.08 * w)
    a = a * np.clip(edge, 0, 1)
    img.putalpha(Image.fromarray(a.astype(np.uint8), "L"))
    return img


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--placeholder", action="store_true")
    ap.add_argument("--pick", action="append", default=[], help="<id>=<n>: which inbox variant to use")
    a = ap.parse_args()
    jobs = [j["id"] for j in json.loads(MANIFEST.read_text(encoding="utf-8"))["jobs"]]
    picks = dict(p.split("=", 1) for p in a.pick)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for jid in jobs:
        src = None
        if not a.placeholder:
            cands = sorted(p for p in INBOX.glob(f"{jid}_*.*") if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"))
            if jid in picks:
                cands = [p for p in cands if p.stem == f"{jid}_{picks[jid]}"] or cands
            src = cands[0] if cands else None
        if src is None:
            if not a.placeholder:
                print(f"[hero] {jid}: no painting in {INBOX.relative_to(REPO)}, using placeholder")
            img = placeholder(jid)
            source = "placeholder"
        else:
            img = cutout(Image.open(src))
            source = str(src.relative_to(REPO))
        if img.width > MAX_W:
            img = img.resize((MAX_W, round(img.height * MAX_W / img.width)), Image.LANCZOS)
        dep = depth_from(img)
        img.save(OUT / f"{jid}.png", optimize=True)
        dep.save(OUT / f"{jid}_depth.png", optimize=True)
        manifest[jid] = {"file": f"{jid}.png", "depth": f"{jid}_depth.png", "w": img.width, "h": img.height, "source": source}
        print(f"[hero] {jid}: {img.width}x{img.height} from {source}")
    (OUT / "hero.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[hero] manifest -> {(OUT / 'hero.json').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
