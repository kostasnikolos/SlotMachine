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


def cutout(img, lo=0.04, hi=0.16):
    """Soft luminance key: pixels darker than `lo` become transparent, brighter than `hi` opaque."""
    rgb = np.asarray(img.convert("RGB"), dtype=np.float32) / 255
    lum = rgb.max(axis=2)
    alpha = np.clip((lum - lo) / (hi - lo), 0, 1)
    # Un-premultiply against black so edges don't keep a dark fringe.
    safe = np.maximum(alpha, 1e-3)[..., None]
    rgb = np.clip(rgb / safe, 0, 1) * (alpha[..., None] > 0)
    out = np.dstack([rgb, alpha])
    return Image.fromarray((out * 255).astype(np.uint8), "RGBA")


def grade(img):
    arr = np.asarray(img.convert("RGBA"), dtype=np.float32) / 255
    rgb, a = arr[..., :3], arr[..., 3:]
    grey = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    rgb = grey[..., None] + (rgb - grey[..., None]) * SATURATION
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
        if not args.no_cutout:
            im = cutout(im)
        im = grade(im)
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
