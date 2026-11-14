"""
atlas_pack.py - pack symbol cut-outs into the four atlases the game's symbol shader reads.

The shader (slot_engine/static/canvas/index.html, `shaders()`) samples a 4x4 atlas of 384 px cells four times:
albedo, normal, emissive, and aux (R = alpha mask, G = specular, B = height). This builds all four from a folder
of RGBA cut-outs, so a repainted symbol set goes into the game with one command and no hand work.

    python scripts/ai/assetgen/atlas_pack.py generated/targets/symbols --out slot_engine/static/canvas/assets/atlas

Cells with no cut-out keep whatever the current atlas has there (the pearl and the sediment block today).
Deterministic: no randomness, so a re-run byte-matches.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

REPO = Path(__file__).resolve().parents[3]
ASSETS = REPO / "slot_engine" / "static" / "canvas" / "assets"
CELL, GRID = 384, 4
# tile index in the atlas -> cut-out key; the order is fixed by `defs()` in index.html
TILES = {0: "high_leviathan", 1: "high_angler", 2: "high_viper", 3: "high_squid", 4: "mid_helmet", 5: "mid_compass",
         6: "wild_maw", 7: "pearl", 8: "dead_sediment", 9: "low_a", 10: "low_k", 11: "low_q", 12: "low_j", 13: "low_10"}
# how much of the cell each tier fills (art bible section 4): lows recede, highs press against the edge
FILL = {"low": 0.74, "mid": 0.90, "high": 0.98, "wild": 0.98, "pearl": 0.9, "dead": 0.96}
CURRENT = {"albedo": "932e6db068e183257c71db1d184f4769.jpg", "normal": "ec0c40a9a29bbc7b0af8e8c64037ff4f.jpg",
           "emissive": "cce5679e94efc084d333dd7f158a50da.jpg", "aux": "30372f0d03094629ce827ea21961a81d.jpg"}


def fit_cell(im: Image.Image, fill: float) -> Image.Image:
    """Trim to the painted pixels, scale so the longer side is `fill` of the cell, centre on transparency."""
    im = im.convert("RGBA")
    box = im.getchannel("A").point(lambda v: 255 if v > 12 else 0).getbbox()
    if box:
        im = im.crop(box)
    k = CELL * fill / max(im.size)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    cell = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    cell.paste(im, ((CELL - im.width) // 2, (CELL - im.height) // 2), im)
    return cell


def maps_for(cell: Image.Image, emissive_gain: float):
    rgba = np.asarray(cell, dtype=np.float32) / 255
    rgb, a = rgba[..., :3], rgba[..., 3]
    # feather the mask inward a touch so JPEG ringing never shows a pale fringe
    a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32) / 255
    a = np.clip((a - 0.12) / 0.88, 0, 1)
    lum = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    blur = lambda x, r: np.asarray(Image.fromarray((np.clip(x, 0, 1) * 255).astype(np.uint8))
                                   .filter(ImageFilter.GaussianBlur(r)), dtype=np.float32) / 255
    # height: the silhouette's dome (so the shape lights as a volume) plus the painting's own relief
    dome = blur(a, 14) * a
    height = np.clip(0.55 * dome + 0.45 * blur(lum, 1.2) * a, 0, 1)
    gy, gx = np.gradient(blur(height, 1.0))
    s = 9.0
    nx, ny, nz = -gx * s, gy * s, np.ones_like(gx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.dstack([nx / ln, ny / ln, nz / ln]) * 0.5 + 0.5
    normal[a < 0.02] = (0.5, 0.5, 1.0)
    # emissive: only what is both bright and saturated (lures, eyes, groove light), never the grey paint
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = (mx - mn) / (mx + 1e-4)
    glow = np.clip((mx - 0.45) / 0.4, 0, 1) * np.clip((sat - 0.35) / 0.35, 0, 1) * a
    glow = np.clip(blur(glow, 2.0) * 0.6 + glow, 0, 1)
    emissive = rgb * glow[..., None] * emissive_gain
    # specular: wet highlights follow local contrast; keep it modest so stone does not turn to chrome
    spec = np.clip((lum - blur(lum, 6)) * 3.0 + 0.18, 0, 1) * a
    aux = np.dstack([a, spec, height])
    # albedo is premultiplied onto black so the JPEG has no bright fringe; lift it a little because the shader
    # multiplies by a dim ambient and expects unlit paint
    albedo = np.clip(rgb * 1.12, 0, 1) * a[..., None]
    return albedo, normal, np.clip(emissive, 0, 1), aux


def tier_of(key: str) -> str:
    return key.split("_")[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="folder of RGBA cut-outs named <key>.png (low_10, high_angler, wild_maw, ...)")
    ap.add_argument("--out", default=str(ASSETS / "atlas"), help="output prefix; writes <prefix>_{albedo,normal,emissive,aux}.jpg")
    ap.add_argument("--quality", type=int, default=92)
    ap.add_argument("--emissive-gain", type=float, default=1.0)
    ap.add_argument("--preview", help="also write a lit preview sheet here")
    a = ap.parse_args()
    src = Path(a.src).resolve()
    sheets = {k: Image.open(ASSETS / v).convert("RGB") for k, v in CURRENT.items()}
    used = {}
    for tile, key in TILES.items():
        p = src / f"{key}.png"
        if not p.exists():
            continue
        cell = fit_cell(Image.open(p), FILL.get(tier_of(key), 0.9))
        alb, nrm, emi, aux = maps_for(cell, a.emissive_gain)
        x, y = (tile % GRID) * CELL, (tile // GRID) * CELL
        for name, arr in (("albedo", alb), ("normal", nrm), ("emissive", emi), ("aux", aux)):
            sheets[name].paste(Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGB"), (x, y))
        used[key] = {"tile": tile, "source": str(p.relative_to(REPO)).replace("\\", "/")}
        print(f"[atlas] tile {tile:>2}  {key}")
    if not used:
        sys.exit(f"no cut-outs found in {src}")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    for name, im in sheets.items():
        im.save(f"{out}_{name}.jpg", quality=a.quality, subsampling=0)
    Path(f"{out}.json").write_text(json.dumps({"cell": CELL, "grid": GRID, "tiles": used}, indent=2) + "\n", encoding="utf-8")
    if a.preview:
        sheets["albedo"].save(a.preview)
    print(f"[atlas] {len(used)} symbols -> {out}_*.jpg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
