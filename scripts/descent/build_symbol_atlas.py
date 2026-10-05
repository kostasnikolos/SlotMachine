#!/usr/bin/env python3
"""Build the WebGL symbol atlases for The Descent from the repo's painted symbols.

Outputs four 4x4 atlases (TILE px per symbol) into OUT:
  sym_albedo.jpg   graded base colour (darker, tan/bronze)
  sym_normal.jpg   tangent-space normals (+Y up)
  sym_emissive.jpg bioluminescent emission
  sym_aux.jpg      R = alpha mask, G = specular, B = height
Painted symbols reuse assets/pbr/*_normal|_emissive|_orm maps; the five low
runes (A K Q J 10) are generated procedurally as engraved bronze coins.
Re-run any time:  python3 scripts/descent/build_symbol_atlas.py  (needs numpy, pillow, scipy)
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

REPO = '/Users/kosta/SlotMachine/slot_engine/static/assets'
OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'slot_engine', 'static', 'assets', 'descent'))
TILE = 384
COLS = 4

# name, source stem, crop centre x/y and radius (fractions of the 1024 source), mask shape
PAINTED = [
    ('leviathan', 'sym_high_leviathan', 0.50, 0.50, 0.50, 'square'),
    ('angler',    'sym_high_angler',    0.512, 0.468, 0.438, 'circle'),
    ('viper',     'sym_high_viper',     0.53, 0.52, 0.452, 'circle'),
    ('squid',     'sym_high_squid',     0.51, 0.495, 0.462, 'circle'),
    ('helmet',    'sym_mid_helmet',     0.505, 0.495, 0.472, 'circle'),
    ('compass',   'sym_mid_compass',    0.51, 0.52, 0.462, 'circle'),
    ('maw',       'sym_wild_maw',       0.50, 0.50, 0.50, 'square'),
    ('pearl',     'token_abyssal_pearl', 0.50, 0.50, 0.485, 'circle'),
    ('sediment',  'sym_dead_sediment',  0.50, 0.50, 0.40, 'square'),
]
LOW = [('A', '#c9a46a', '#3ff5ff'), ('K', '#b07a4a', '#3ff5ff'), ('Q', '#8fa58a', '#7cffd9'),
       ('J', '#8c8478', '#3ff5ff'), ('10', '#a8865a', '#ffb070')]


def load(path, mode='RGB'):
    return Image.open(path).convert(mode)


def crop(img, cx, cy, r):
    w, h = img.size
    box = (int((cx - r) * w), int((cy - r) * h), int((cx + r) * w), int((cy + r) * h))
    return img.crop(box).resize((TILE, TILE), Image.LANCZOS)


def mask_for(shape):
    yy, xx = np.mgrid[0:TILE, 0:TILE] / (TILE - 1) * 2 - 1
    if shape == 'circle':
        d = np.sqrt(xx ** 2 + yy ** 2)
        return np.clip((0.985 - d) / 0.03, 0, 1)
    k = 0.16  # rounded square, feathered
    qx, qy = np.maximum(np.abs(xx) - (0.97 - k), 0), np.maximum(np.abs(yy) - (0.97 - k), 0)
    d = np.sqrt(qx ** 2 + qy ** 2) - k
    return np.clip(-d / 0.025, 0, 1)


def grade(rgb):
    """Darker, warmer: crush blacks, pull mids toward bronze-tan, keep cyan highlights."""
    a = rgb.astype(np.float32) / 255
    lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    a = a ** 1.18 * 0.86
    tan = np.array([0.62, 0.48, 0.32], np.float32)
    mid = np.clip(1 - np.abs(lum - 0.42) / 0.42, 0, 1)[..., None] * 0.18
    a = a * (1 - mid) + (lum[..., None] * tan * 1.4) * mid
    return np.clip(a * 255, 0, 255).astype(np.uint8)


def painted(stem, cx, cy, r, shape):
    alb = grade(np.array(crop(load(f'{REPO}/{stem}.jpg'), cx, cy, r)))
    pbr = f'{REPO}/pbr/{stem}'
    lum = alb.astype(np.float32).mean(-1) / 255
    height = ndimage.gaussian_filter(lum, 1.5)
    m = mask_for(shape)
    if os.path.exists(f'{pbr}_normal.png'):
        nrm = np.array(crop(load(f'{pbr}_normal.png'), cx, cy, r))
        emi = np.array(crop(load(f'{pbr}_emissive.png'), cx, cy, r)).astype(np.float32)
        orm = np.array(crop(load(f'{pbr}_orm.png'), cx, cy, r)).astype(np.float32) / 255
        spec = np.clip((1 - orm[..., 1]) * 0.7 + orm[..., 2] * 0.5, 0, 1)
    else:  # no PBR set: derive from the painting
        nrm = normal_from_height(ndimage.gaussian_filter(lum, 1.2), 30)
        src = np.array(crop(load(f'{REPO}/{stem}.jpg'), cx, cy, r)).astype(np.float32)
        sat = src.max(-1) - src.min(-1)
        emi = src * (np.clip((sat - 90) / 120, 0, 1) * np.clip((src.max(-1) - 120) / 100, 0, 1))[..., None]
        spec = np.clip(lum * 1.2, 0, 1)
    aux = np.stack([m, spec, height], -1)
    emi = np.clip(emi * 1.1, 0, 255)
    return alb, nrm, emi.astype(np.uint8), (aux * 255).astype(np.uint8)


def normal_from_height(h, strength):
    gy, gx = np.gradient(h)
    n = np.stack([-gx * strength, gy * strength, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)


def rune(letter, metal, glow, seed):
    rng = np.random.default_rng(seed)
    S = TILE
    yy, xx = np.mgrid[0:S, 0:S] / (S - 1) * 2 - 1
    d = np.sqrt(xx ** 2 + yy ** 2)
    ang = np.arctan2(yy, xx)
    m = np.clip((0.93 - d) / 0.03, 0, 1)
    ring = np.clip((d - 0.74) / 0.02, 0, 1) * np.clip((0.92 - d) / 0.02, 0, 1)
    inner_lip = np.clip(1 - np.abs(d - 0.70) / 0.018, 0, 1)
    notch = (np.cos(ang * 48) > 0.55) * np.clip(1 - np.abs(d - 0.83) / 0.05, 0, 1)
    rivets = np.zeros_like(d)
    for k in range(8):
        a0 = k * np.pi / 4 + np.pi / 8
        rx, ry = np.cos(a0) * 0.83, np.sin(a0) * 0.83
        rd = np.sqrt((xx - rx) ** 2 + (yy - ry) ** 2)
        rivets = np.maximum(rivets, np.clip(1 - rd / 0.045, 0, 1) ** 0.6)
    # letter mask (Copperplate), raised with bevel
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Copperplate.ttc', int(S * (0.40 if len(letter) > 1 else 0.50)), index=1)
    L = Image.new('L', (S, S), 0)
    dr = ImageDraw.Draw(L)
    bb = dr.textbbox((0, 0), letter, font=font)
    dr.text(((S - (bb[2] - bb[0])) / 2 - bb[0], (S - (bb[3] - bb[1])) / 2 - bb[1]), letter, fill=255, font=font)
    lm = np.array(L).astype(np.float32) / 255
    bevel = ndimage.distance_transform_edt(lm > 0.5)
    lh = np.clip(bevel / (S * 0.02), 0, 1) ** 0.7
    groove = np.clip(1 - np.abs(ndimage.distance_transform_edt(lm < 0.5) - S * 0.018) / (S * 0.006), 0, 1)
    noise = ndimage.gaussian_filter(rng.standard_normal((S, S)), 1.2) * 0.04 + ndimage.gaussian_filter(rng.standard_normal((S, S)), 6) * 0.18
    pits = (ndimage.gaussian_filter(rng.random((S, S)), 0.8) > 0.62) * 0.05
    dome = np.clip(1 - d / 0.74, 0, 1) * 0.15
    h = ring * 0.55 + inner_lip * 0.25 + notch * -0.08 + rivets * 0.35 + lh * 0.6 - groove * 0.18 + dome + noise * 0.25 - pits
    h = ndimage.gaussian_filter(h, 0.9)
    nrm = normal_from_height(h, 26)
    # albedo: basalt face, metal ring + letter
    met = np.array(Image.new('RGB', (1, 1), metal))[0, 0].astype(np.float32) / 255
    basalt = np.array([0.055, 0.06, 0.07]) + noise[..., None] * 0.08
    face_grad = np.clip(1 - d / 0.74, 0, 1)[..., None] * np.array([0.03, 0.05, 0.06])
    metal_mask = np.clip(ring + rivets + lh + inner_lip * 0.6, 0, 1)[..., None]
    tarnish = np.clip(0.75 + noise[..., None] * 1.6, 0.35, 1.15)
    # engraved rune ticks in the recessed band between lip and ring
    band = np.clip(1 - np.abs(d - 0.715) / 0.02, 0, 1)
    ticks = band * ((np.cos(ang * 72) > 0.7) | ((np.cos(ang * 9) > 0.96) & (d < 0.73)))
    lmask = lh[..., None]
    rmask = np.clip(ring + rivets + inner_lip * 0.6, 0, 1)[..., None]
    alb = basalt + face_grad
    alb = alb * (1 - rmask) + met * tarnish * rmask * 0.62
    alb = alb * (1 - lmask) + np.clip(met * 1.25 * tarnish + 0.06, 0, 1) * lmask
    alb = alb * (1 - ticks[..., None] * 0.5) + met * ticks[..., None] * 0.35
    patina = np.clip(ndimage.gaussian_filter(rng.random((S, S)), 3) - 0.52, 0, 1)[..., None] * 5 * metal_mask
    alb = alb * (1 - patina * 0.5) + np.array([0.18, 0.32, 0.30]) * patina * 0.5
    # baked light from top-left + cavity occlusion so the coin reads even unlit
    nf = nrm.astype(np.float32) / 127.5 - 1
    shade = np.clip(nf @ np.array([-0.45, 0.55, 0.70]), 0, 1)
    ao = 1 - np.clip(ndimage.gaussian_filter(h, 5) - h, 0, 0.2) * 3.5
    alb = alb * (0.35 + 0.85 * shade)[..., None] * ao[..., None]
    alb = np.clip(alb * (0.85 + 0.15 * (1 - d))[..., None], 0, 1)
    g = np.array(Image.new('RGB', (1, 1), glow))[0, 0].astype(np.float32) / 255
    em = (groove * 0.9 + np.clip(1 - np.abs(d - 0.70) / 0.008, 0, 1) * 0.35)[..., None] * g
    spec = np.clip(metal_mask[..., 0] * 0.85 + 0.12, 0, 1)
    aux = np.stack([m, spec, np.clip(h, 0, 1)], -1)
    return ((alb * 255).astype(np.uint8), nrm, (np.clip(em, 0, 1) * 255).astype(np.uint8), (aux * 255).astype(np.uint8))


def main():
    tiles = [painted(*p[1:]) for p in PAINTED]
    tiles += [rune(l, mc, gc, i + 7) for i, (l, mc, gc) in enumerate(LOW)]
    rows = (len(tiles) + COLS - 1) // COLS
    names = ['sym_albedo', 'sym_normal', 'sym_emissive', 'sym_aux']
    for ch, name in enumerate(names):
        flat = [128, 128, 255] if name == 'sym_normal' else [0, 0, 0]
        atlas = np.zeros((COLS * TILE, COLS * TILE, 3), np.uint8) + np.array(flat, np.uint8)
        for i, t in enumerate(tiles):
            r, c = divmod(i, COLS)
            atlas[r * TILE:(r + 1) * TILE, c * TILE:(c + 1) * TILE] = t[ch]
        Image.fromarray(atlas).save(f'{OUT}/{name}.jpg', quality=90 if name != 'sym_aux' else 95, subsampling=0)
    order = [p[0] for p in PAINTED] + [l[0] for l in LOW]
    print('tiles', rows, 'rows; order:', order)


if __name__ == '__main__':
    main()
