"""
symbols.py - generate the low-rune medallions procedurally, in the art bible's palette.

The low runes (10 J Q K A) are the weakest art in the game: five tinted copies of the same brass card
(docs/art_bible.md section 1). AI generation cannot keep letterforms correct and cannot keep five symbols on one
construction; code can do both. Each medallion is built the same way - cast brass ring, corroded face, the letter
*carved into* it, one cyan rim light from upper-left - so the set reads as one object at five values, and the whole
set regenerates from one command when a decision changes.

    python scripts/ai/assetgen/symbols.py --sheet            # -> generated/symbols/low_*.png + a contact sheet
    python scripts/ai/assetgen/symbols.py --size 384 --level 4   # the Hadal grade

Deterministic: the same rune always gets the same corrosion, so a re-run is a no-op unless a parameter changed.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "generated" / "symbols"
SS = 2                                            # supersample factor

RUNES = ["10", "J", "Q", "K", "A"]
# art bible: one cyan key light from upper-centre-left; brass for the metal; the water's tint comes from the depth
BIOLUME = (63, 224, 208)
BRASS_HI = (150, 124, 84)      # art bible brass, knocked back: a lit edge, not jewellery
BRASS_LO = (44, 33, 21)
TRENCH = (11, 20, 24)
LEVEL_TINT = {0: (63, 224, 208), 1: (63, 224, 208), 2: (96, 206, 255), 3: (232, 176, 74), 4: (224, 110, 70), 5: (224, 49, 75)}

FONT_CANDIDATES = [
    "C:/Windows/Fonts/seguibl.ttf",   # Segoe UI Black
    "C:/Windows/Fonts/impact.ttf",
    "C:/Windows/Fonts/ariblk.ttf",    # Arial Black
    "C:/Windows/Fonts/georgiab.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def pick_font(px: int) -> ImageFont.FreeTypeFont:
    for f in FONT_CANDIDATES:
        if Path(f).exists():
            return ImageFont.truetype(f, px)
    return ImageFont.load_default()


def rng_for(name: str) -> np.random.Generator:
    return np.random.default_rng(int(hashlib.sha256(("descent/sym/" + name).encode()).hexdigest()[:8], 16))


def value_noise(n: int, octaves: int, rng: np.random.Generator) -> np.ndarray:
    """Smooth 0..1 noise at n x n, summed over octaves. Used for corrosion and the cast-metal grain."""
    acc = np.zeros((n, n), dtype=np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        res = max(2, int(4 * 2 ** o))
        grid = rng.random((res, res)).astype(np.float32)
        img = np.asarray(Image.fromarray((grid * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC), dtype=np.float32) / 255
        acc += img * amp
        tot += amp
        amp *= 0.5
    return acc / tot


def radial(n: int):
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2
    dx, dy = (x - c) / c, (y - c) / c
    return np.sqrt(dx * dx + dy * dy), dx, dy


def medallion(rune: str, size: int, level: int) -> Image.Image:
    n = size * SS
    rng = rng_for(rune)
    r, dx, dy = radial(n)
    tint = np.array(LEVEL_TINT.get(level, BIOLUME), dtype=np.float32) / 255

    # ---- the disc: a cast ring with a recessed face ----
    ring_outer, ring_inner = 0.97, 0.76
    wear = (value_noise(n, 4, rng_for(rune + "/wear")) - 0.5) * 0.022                 # the rim is not a perfect circle
    disc = np.clip((ring_outer + wear - r) / (1.5 / n * SS * 8), 0, 1)                # antialiased edge
    is_ring = np.clip((r - ring_inner) / 0.03, 0, 1) * disc
    # lambert-ish shading from the one key light (upper-left), on a torus-shaped ring
    lx, ly = -0.6, -0.78
    bevel = np.clip((r - ring_inner) / (ring_outer - ring_inner), 0, 1) * 2 - 1      # -1 inner edge .. +1 outer edge
    nx, ny = dx / (r + 1e-5) * bevel, dy / (r + 1e-5) * bevel
    lam = np.clip(nx * lx + ny * ly, -1, 1)
    grain = value_noise(n, 5, rng)
    corrosion = value_noise(n, 3, rng_for(rune + "/corr"))

    base = np.zeros((n, n, 3), dtype=np.float32)
    hi = np.array(BRASS_HI, dtype=np.float32) / 255
    lo = np.array(BRASS_LO, dtype=np.float32) / 255
    metal = lo[None, None, :] + (hi - lo)[None, None, :] * np.clip(0.42 + 0.58 * lam, 0, 1)[..., None]
    metal *= (0.62 + 0.52 * grain)[..., None]                                        # cast texture, deeper contrast
    verd = np.clip((corrosion - 0.42) * 2.6, 0, 1)[..., None]                        # verdigris in the low spots
    metal = metal * (1 - verd * 0.72) + np.array([0.09, 0.17, 0.15], dtype=np.float32)[None, None, :] * verd * 0.9
    # silt streaks run down the metal: the light is above, so what settles reads as vertical grime
    streak = value_noise(n, 2, rng_for(rune + "/streak"))
    streak = np.asarray(Image.fromarray((streak * 255).astype(np.uint8)).resize((n // 8, n), Image.BILINEAR)
                        .resize((n, n), Image.BILINEAR), dtype=np.float32) / 255
    metal *= (0.70 + 0.42 * streak)[..., None]

    face = np.array(TRENCH, dtype=np.float32) / 255
    face_field = face[None, None, :] * (0.55 + 0.85 * value_noise(n, 4, rng_for(rune + "/face")))[..., None]
    face_field *= np.clip(1.25 - r * 0.9, 0.25, 1.3)[..., None]                      # the face is lit from the centre out

    img = face_field * (1 - is_ring)[..., None] + metal * is_ring[..., None]
    img *= disc[..., None]

    # ---- the rune, carved into the face ----
    glyph = Image.new("L", (n, n), 0)
    gd = ImageDraw.Draw(glyph)
    font = pick_font(int(n * (0.40 if len(rune) > 1 else 0.52)))
    bb = gd.textbbox((0, 0), rune, font=font)
    gd.text(((n - (bb[2] - bb[0])) / 2 - bb[0], (n - (bb[3] - bb[1])) / 2 - bb[1]), rune, font=font, fill=255)
    gm = np.asarray(glyph, dtype=np.float32) / 255
    off = max(1, int(n * 0.008))
    up = np.roll(np.roll(gm, -off, axis=0), -off, axis=1)       # light catches the upper-left lip of the groove
    dn = np.roll(np.roll(gm, off, axis=0), off, axis=1)         # the lower-right wall stays in shadow
    carve_dark = np.clip(dn - gm, 0, 1)
    carve_lite = np.clip(up - gm, 0, 1)
    inner = np.asarray(Image.fromarray((gm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(n * 0.012)), dtype=np.float32) / 255
    img *= (1 - gm * 0.92)[..., None]                                                 # the cut goes nearly black
    img += (np.array([0.035, 0.055, 0.062], dtype=np.float32)[None, None, :] * (inner * gm)[..., None])
    img *= (1 - carve_dark * 0.75)[..., None]                                         # the far wall stays in shadow
    img += (hi * 0.95)[None, None, :] * carve_lite[..., None] * 1.15                  # only the near lip catches the light
    # the faintest pooled light at the very bottom of the groove
    img += tint[None, None, :] * (gm * inner * inner)[..., None] * 0.07

    # ---- rim light: one arc, upper-left, the colour of the depth ----
    rim = np.clip(1 - np.abs(r - ring_outer * 0.985) / 0.045, 0, 1)
    facing = np.clip(-(dx * 0.72 + dy * 0.78) / (r + 1e-5), 0, 1) ** 1.6
    img += tint[None, None, :] * (rim * (facing ** 2.2) * disc)[..., None] * 1.25     # a short arc, not a halo
    # and the faintest bounce on the inner lip
    inner_rim = np.clip(1 - np.abs(r - ring_inner) / 0.03, 0, 1)
    img += tint[None, None, :] * (inner_rim * (facing ** 2.0) * disc)[..., None] * 0.3

    # the whole medallion falls away from the key light, so it sits in water instead of on a page
    falloff = np.clip(0.52 + 0.48 * (-(dx * 0.6 + dy * 0.78) * 0.5 + 0.5), 0, 1.25)
    img *= falloff[..., None]
    # pitting: tiny dark craters, the sea has been at this for a while
    pits = rng.random((n, n)) < 0.00035
    pit_img = np.asarray(Image.fromarray((pits * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(n * 0.004)), dtype=np.float32) / 255
    img *= (1 - np.clip(pit_img * 3.5, 0, 1) * 0.75 * is_ring)[..., None]

    rgb = np.clip(img, 0, 1)
    alpha = np.clip(disc * 1.02, 0, 1)
    out = np.dstack([rgb * 255, alpha * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA").resize((size, size), Image.LANCZOS)


def sheet(images, path: Path, bg=(10, 18, 22)):
    cell = images[0][1].width
    img = Image.new("RGB", (cell * len(images), cell + 26), bg)
    d = ImageDraw.Draw(img)
    for i, (name, im) in enumerate(images):
        img.paste(im, (i * cell, 0), im)
        d.text((i * cell + 8, cell + 6), name, fill=(195, 209, 212))
    img.save(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=384, help="atlas cell size (the engine's cells are 384)")
    ap.add_argument("--level", type=int, default=0, help="depth level 0-5: sets the water's tint on the rim light")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    runes = a.only or RUNES
    made, manifest = [], {}
    for rune in runes:
        im = medallion(rune, a.size, a.level)
        key = "low_" + ("10" if rune == "10" else rune.lower())
        p = out / f"{key}.png"
        im.save(p)
        made.append((rune, im))
        manifest[key] = {"file": p.name, "rune": rune, "size": a.size, "level": a.level,
                         "source": "procedural (scripts/ai/assetgen/symbols.py)", "licence": "ours"}
        print(f"[sym] {key:<8} {a.size}px  {p.stat().st_size / 1024:6.1f} KB")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if a.sheet:
        sp = REPO / "artifacts" / "canvas" / "symbols_sheet.png"
        sheet(made, sp)
        print(f"[sym] sheet -> {sp.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
