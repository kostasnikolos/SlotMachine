"""
comfy_tools.py - the everyday jobs on the licence-cleared local stack, over ComfyUI's HTTP API.

    python scripts/ai/comfy_tools.py cutout  IN.png OUT.png              # BiRefNet (MIT): subject on transparency
    python scripts/ai/comfy_tools.py upscale IN.png OUT.png              # Real-ESRGAN x4plus (BSD-3)
    python scripts/ai/comfy_tools.py paint   "prompt" OUT.png --seed 7   # Z-Image-Turbo (Apache 2.0), 8 steps

ComfyUI must be running on http://127.0.0.1:8188 and the models installed with scripts/ai/install_models.py.
Standard library only, so it runs on any Python. Every output gets a sidecar .json naming the model and licence
that made it: the provenance record docs/local_asset_tools.md asks for.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import uuid
from pathlib import Path

COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
COMFY_DIR = Path(os.environ.get("COMFY_DIR", r"C:\Users\kosta\AI\ComfyUI"))


def call(path, payload=None):
    req = urllib.request.Request(f"{COMFY_URL}{path}", data=json.dumps(payload).encode() if payload else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def run(wf):
    pid = json.loads(call("/prompt", {"prompt": wf, "client_id": str(uuid.uuid4())}))["prompt_id"]
    while True:
        hist = json.loads(call(f"/history/{pid}"))
        if pid in hist:
            status = hist[pid].get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError(json.dumps(status.get("messages", []))[-900:])
            i = [i for o in hist[pid]["outputs"].values() for i in o.get("images", [])][0]
            return call(f"/view?filename={i['filename']}&subfolder={i['subfolder']}&type={i['type']}")
        time.sleep(0.5)


def stage(src: Path) -> str:
    """ComfyUI's LoadImage reads from its own input folder: copy the file there under a unique name."""
    name = f"tools_{uuid.uuid4().hex[:8]}{src.suffix}"
    (COMFY_DIR / "input" / name).write_bytes(src.read_bytes())
    return name


def finish(data: bytes, out: Path, record: dict, staged=None):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    out.with_suffix(".json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if staged:
        (COMFY_DIR / "input" / staged).unlink(missing_ok=True)
    print(f"-> {out}  ({len(data) / 1024:.0f} KB)")


def cutout(a):
    name = stage(Path(a.src))
    wf = {
        "1": {"class_type": "LoadImage", "inputs": {"image": name}},
        "2": {"class_type": "LoadBackgroundRemovalModel", "inputs": {"bg_removal_name": "birefnet.safetensors"}},
        "3": {"class_type": "RemoveBackground", "inputs": {"bg_removal_model": ["2", 0], "image": ["1", 0]}},
        "6": {"class_type": "InvertMask", "inputs": {"mask": ["3", 0]}},   # JoinImageWithAlpha keeps where the mask is 0
        "4": {"class_type": "JoinImageWithAlpha", "inputs": {"image": ["1", 0], "alpha": ["6", 0]}},
        "5": {"class_type": "SaveImage", "inputs": {"images": ["4", 0], "filename_prefix": "tools/cutout"}},
    }
    finish(run(wf), Path(a.out), {"tool": "cutout", "source": a.src, "model": "ZhengPeng7/BiRefNet", "licence": "MIT"}, name)


def upscale(a):
    name = stage(Path(a.src))
    wf = {
        "1": {"class_type": "LoadImage", "inputs": {"image": name}},
        "2": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "RealESRGAN_x4plus.safetensors"}},
        "3": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["2", 0], "image": ["1", 0]}},
        "4": {"class_type": "SaveImage", "inputs": {"images": ["3", 0], "filename_prefix": "tools/upscale"}},
    }
    finish(run(wf), Path(a.out), {"tool": "upscale", "source": a.src, "model": "Real-ESRGAN x4plus",
                                  "licence": "BSD-3-Clause"}, name)


def paint(a):
    wf = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": a.prompt}},
        "6": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["5", 0]}},
        "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": a.width, "height": a.height, "batch_size": 1}},
        "8": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["5", 0], "negative": ["6", 0],
                                                   "latent_image": ["7", 0], "seed": a.seed, "steps": a.steps, "cfg": 1.0,
                                                   "sampler_name": "res_multistep", "scheduler": "simple", "denoise": 1.0}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "tools/paint"}},
    }
    t0 = time.time()
    data = run(wf)
    print(f"painted in {time.time() - t0:.0f} s")
    finish(data, Path(a.out), {"tool": "paint", "prompt": a.prompt, "seed": a.seed, "steps": a.steps,
                               "size": [a.width, a.height], "model": "Tongyi-MAI/Z-Image-Turbo (Comfy-Org repackage, bf16)",
                               "licence": "Apache-2.0"})


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("cutout", cutout), ("upscale", upscale)):
        p = sub.add_parser(name); p.add_argument("src"); p.add_argument("out"); p.set_defaults(fn=fn)
    p = sub.add_parser("paint"); p.add_argument("prompt"); p.add_argument("out")
    p.add_argument("--seed", type=int, default=1); p.add_argument("--steps", type=int, default=8)
    p.add_argument("--width", type=int, default=1024); p.add_argument("--height", type=int, default=1024)
    p.set_defaults(fn=paint)
    a = ap.parse_args()
    try:
        call("/system_stats")
    except Exception as e:
        sys.exit(f"ComfyUI is not reachable at {COMFY_URL}: {e}")
    a.fn(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
