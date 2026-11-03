"""
interp_frames.py - interpolate N frames between two cut-out paintings (RGBA on transparent) with RIFE, locally on the GPU.

    python scripts/ai/interp_frames.py A.png B.png --n 12 --out generated/flipbook/lev_jaws_chomp

Needs the free RIFE package (Vulkan build, runs on the NVIDIA card):  python -m pip install rife-ncnn-vulkan-python
RGB is interpolated over black (the paintings are lit on black anyway); alpha is interpolated as a grey image with the
same model so the silhouette moves with the colour. Output: 000.png (= A) ... NNN.png (= B), same size as A.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--n", type=int, default=12, help="frames between A and B (output has n + 2 frames)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    try:
        from rife_ncnn_vulkan_python import Rife
    except ImportError:
        sys.exit("RIFE is not installed. Run:  python -m pip install rife-ncnn-vulkan-python")
    A = Image.open(args.a).convert("RGBA")
    B = Image.open(args.b).convert("RGBA").resize(A.size, Image.LANCZOS)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rife = Rife(gpuid=0, model="rife-v4.6")

    def rgb_on_black(im):
        arr = np.asarray(im, dtype=np.float32)
        rgb = arr[..., :3] * (arr[..., 3:] / 255)
        return Image.fromarray(rgb.astype(np.uint8), "RGB")

    def alpha_as_rgb(im):
        a = np.asarray(im.getchannel("A"))
        return Image.fromarray(np.stack([a, a, a], -1), "RGB")

    A_rgb, B_rgb, A_a, B_a = rgb_on_black(A), rgb_on_black(B), alpha_as_rgb(A), alpha_as_rgb(B)
    frames = [A]
    for i in range(1, args.n + 1):
        t = i / (args.n + 1)
        rgb = np.asarray(rife.process(A_rgb, B_rgb, timestep=t), dtype=np.float32)
        al = np.asarray(rife.process(A_a, B_a, timestep=t), dtype=np.float32)[..., 0]
        safe = np.maximum(al, 1)[..., None]
        un = np.clip(rgb / safe * 255, 0, 255)
        frames.append(Image.fromarray(np.dstack([un, al]).astype(np.uint8), "RGBA"))
    frames.append(B)
    for i, f in enumerate(frames):
        f.save(out / f"{i:03d}.png")
    print(f"[interp] {len(frames)} frames -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
