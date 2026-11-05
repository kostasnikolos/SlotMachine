"""
interp_frames.py - interpolate N frames between two cut-out paintings (RGBA on transparent) with RIFE 4.9, locally on the GPU.

Runs on the ComfyUI venv (torch + CUDA) and the RIFE implementation of the ComfyUI-Frame-Interpolation node
(C:/Users/kosta/AI/ComfyUI/custom_nodes/ComfyUI-Frame-Interpolation, MIT). The rife49.pth weights (~20 MB) are fetched
once from the node's GitHub release into its ckpts folder.

    "C:/Users/kosta/AI/ComfyUI/venv/Scripts/python.exe" scripts/ai/interp_frames.py A.png B.png --n 12 --out generated/flipbook/lev_jaws_chomp

RGB is interpolated over black (the paintings are lit on black anyway); alpha is interpolated as a grey image with the
same model so the silhouette moves with the colour. Output: 000.png (= A) ... NNN.png (= B), same size as A.
"""

import argparse
import os
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

COMFY = Path(os.environ.get("COMFY_ROOT", r"C:\Users\kosta\AI\ComfyUI"))
NODE = COMFY / "custom_nodes" / "ComfyUI-Frame-Interpolation"
CKPT = "rife49.pth"
CKPT_URLS = [
    "https://github.com/Fannovel16/ComfyUI-Frame-Interpolation/releases/download/models/" + CKPT,
    "https://github.com/styler00dollar/VSGAN-tensorrt-docker/releases/download/models/" + CKPT,
]


def get_model():
    import torch
    sys.path.insert(0, str(COMFY))
    sys.path.insert(0, str(NODE))
    from vfi_models.rife.rife_arch import IFNet  # noqa: E402
    ck_dir = NODE / "ckpts" / "rife"
    ck_dir.mkdir(parents=True, exist_ok=True)
    ck = ck_dir / CKPT
    if not ck.exists():
        for url in CKPT_URLS:
            try:
                print(f"[interp] downloading {url}")
                urllib.request.urlretrieve(url, ck)
                break
            except Exception as e:  # noqa: BLE001
                print(f"[interp] failed: {e}")
        if not ck.exists():
            sys.exit("could not download the RIFE weights")
    model = IFNet(arch_ver="4.7")
    model.load_state_dict(torch.load(ck, weights_only=False))
    model.eval().to("cuda")
    return model, torch


def to_tensor(im_rgb, torch):
    a = np.asarray(im_rgb, dtype=np.float32) / 255
    return torch.from_numpy(a).permute(2, 0, 1)[None].to("cuda")


def interp(model, torch, A_rgb, B_rgb, t):
    h, w = A_rgb.shape[2:]
    ph, pw = (64 - h % 64) % 64, (64 - w % 64) % 64
    import torch.nn.functional as F
    a = F.pad(A_rgb, (0, pw, 0, ph)); b = F.pad(B_rgb, (0, pw, 0, ph))
    ts = torch.tensor([t], dtype=torch.float32, device="cuda").view(-1, 1, 1, 1)
    with torch.inference_mode():
        out = model(a, b, ts, [8, 4, 2, 1], False, True)
    out = out[:, :, :h, :w].clamp(0, 1)[0].permute(1, 2, 0).cpu().numpy()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--n", type=int, default=12, help="frames between A and B (output has n + 2 frames)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    model, torch = get_model()
    A = Image.open(args.a).convert("RGBA")
    B = Image.open(args.b).convert("RGBA").resize(A.size, Image.LANCZOS)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    def rgb_on_black(im):
        arr = np.asarray(im, dtype=np.float32)
        return Image.fromarray((arr[..., :3] * (arr[..., 3:] / 255)).astype(np.uint8), "RGB")

    def alpha_rgb(im):
        a = np.asarray(im.getchannel("A"))
        return Image.fromarray(np.stack([a, a, a], -1), "RGB")

    Ar, Br, Aa, Ba = (to_tensor(x, torch) for x in (rgb_on_black(A), rgb_on_black(B), alpha_rgb(A), alpha_rgb(B)))
    frames = [A]
    for i in range(1, args.n + 1):
        t = i / (args.n + 1)
        rgb = interp(model, torch, Ar, Br, t) * 255
        al = interp(model, torch, Aa, Ba, t)[..., 0] * 255
        un = np.clip(rgb / np.maximum(al, 1)[..., None] * 255, 0, 255)
        frames.append(Image.fromarray(np.dstack([un, al]).astype(np.uint8), "RGBA"))
        print(f"[interp] frame {i}/{args.n} t={t:.2f}")
    frames.append(B)
    for i, f in enumerate(frames):
        f.save(out / f"{i:03d}.png")
    print(f"[interp] {len(frames)} frames -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
