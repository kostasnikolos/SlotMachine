"""Designer pass: turn raw Gemini output into cohesive, game-ready layers, plus Reviewer test sheets.

Steps (see .agents/skills/studio-designer/SKILL.md):
  cutout  - key the pure-black background to alpha (art is generated on #000 for this)
  grade   - pull every image onto the art-bible palette: desaturate, cool shadows, cap highlights
  sheets  - contact sheet, 64px phone-size sheet (gate G1) and 8px blur sheet (gate G2)

Usage:
    python scripts/ai/designer_pass.py generated/p2_symbols/<run> --out generated/p2_symbols/<run>/clean
    python scripts/ai/designer_pass.py <dir> --out <dir>/clean --no-cutout   # backdrops keep their ground
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SHADOW_TINT = np.array([0x0B, 0x14, 0x18], dtype=np.float32) / 255  # Trench
SATURATION = 0.72
HIGHLIGHT_CAP = 0.94


def cutout(img, lo=0.025, hi=0.12):
    """Soft luminance key: pixels darker than `lo` become transparent, brighter than `hi` opaque.

    The key is measured on a blurred copy so compression noise in glows doesn't step, and the matte is
    closed (dilate then erode) so dark scales inside a silhouette don't punch speckled holes.
    """
    img = img.convert("RGB")
    rgb = np.asarray(img, dtype=np.float32) / 255
    lum = np.asarray(img.filter(ImageFilter.GaussianBlur(2)), dtype=np.float32).max(axis=2) / 255
    matte = Image.fromarray((np.clip((lum - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8), "L")
    matte = matte.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(1.5))
    alpha = np.asarray(matte, dtype=np.float32) / 255
    # Un-premultiply against black so edges don't keep a dark fringe.
    safe = np.maximum(alpha, 1e-3)[..., None]
    rgb = np.clip(rgb / safe, 0, 1) * (alpha[..., None] > 0)
    out = np.dstack([rgb, alpha])
    return Image.fromarray((out * 255).astype(np.uint8), "RGBA")


TIER_SATURATION = {"low": 0.72, "mid": 0.8, "high": 1.0, "special": 1.05}


def trim(img, pad=0.04):
    """Crop to the alpha bounding box, then pad back to a square so the subject fills the cell."""
    box = img.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    if not box:
        return img
    img = img.crop(box)
    side = int(max(img.size) * (1 + pad * 2))
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    return sq


def grade(img, saturation=SATURATION):
    arr = np.asarray(img.convert("RGBA"), dtype=np.float32) / 255
    rgb, a = arr[..., :3], arr[..., 3:]
    grey = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    rgb = grey[..., None] + (rgb - grey[..., None]) * saturation
    shadow = (1 - grey)[..., None] ** 2
    rgb = rgb * (1 - shadow * 0.35) + SHADOW_TINT * shadow * 0.35
    rgb = np.minimum(rgb, HIGHLIGHT_CAP)
    return Image.fromarray((np.dstack([rgb, a]) * 255).astype(np.uint8), "RGBA")


def sheet(images, cell, cols=5, blur=0, bg=(11, 20, 24)):
    rows = (len(images) + cols - 1) // cols
    pad = 6
    canvas = Image.new("RGB", (cols * (cell + pad) + pad, rows * (cell + pad) + pad), bg)
    for i, (name, im) in enumerate(images):
        t = im.copy()
        t.thumbnail((cell, cell), Image.LANCZOS)
        if blur:
            t = t.filter(ImageFilter.GaussianBlur(blur))
        x = pad + (i % cols) * (cell + pad) + (cell - t.width) // 2
        y = pad + (i // cols) * (cell + pad) + (cell - t.height) // 2
        canvas.paste(t, (x, y), t if t.mode == "RGBA" else None)
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-cutout", action="store_true")
    args = ap.parse_args()

    src, out = Path(args.src), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    done = []
    files = sorted(f for ext in ("png", "jpg", "jpeg", "webp") for f in src.glob(f"*.{ext}"))
    for f in files:
        im = Image.open(f)
        tier = f.stem.split("_")[0]
        if not args.no_cutout:
            im = trim(cutout(im))
        im = grade(im, TIER_SATURATION.get(tier, SATURATION))
        im.save(out / f"{f.stem}.png")
        done.append((f.stem, im))
        print(f"  {f.name}")

    if not done:
        print("No images found.")
        return
    sheet(done, 220).save(out / "_sheet_contact.png")
    sheet(done, 64).save(out / "_sheet_64px_G1.png")
    sheet(done, 220, blur=8).save(out / "_sheet_blur_G2.png")
    print(f"Done -> {out} (+ 3 review sheets)")


if __name__ == "__main__":
    main()
