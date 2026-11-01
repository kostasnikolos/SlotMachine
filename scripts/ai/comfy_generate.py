"""Local, free generation through ComfyUI (SDXL + ControlNet Union), driven over its HTTP API.

Outline-locked glyphs: each low symbol is rendered from a real font into a depth map (flat stone surface,
letter pressed in with a bevel). ControlNet Union in depth mode forces SDXL to paint carved basalt along
exactly that shape, so letterforms come out right and all five glyphs share one construction.

ComfyUI must be running (default http://127.0.0.1:8188) and COMFY_DIR must point at its folder, because
control images are written straight into its input/ directory.

Usage:
    python scripts/ai/comfy_generate.py scripts/ai/prompts/local_glyphs.json --only low_q --variants 4
"""
import argparse
import math
import json
import os
import random
import time
import urllib.request
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = Path(__file__).resolve().parents[2]
COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
COMFY_DIR = Path(os.environ.get("COMFY_DIR", r"C:\Users\kosta\AI\ComfyUI"))
SIZE = 1024


def glyph_depth(text, font_path, out_path):
    """Stone slab at mid depth, glyph recessed with a soft bevel, slab edges chipped."""
    font = ImageFont.truetype(font_path, int(SIZE * 0.62))
    mask = Image.new("L", (SIZE, SIZE), 0)
    d = ImageDraw.Draw(mask)
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    d.text(((SIZE - (r - l)) / 2 - l, (SIZE - (b - t)) / 2 - t), text, font=font, fill=255)

    rng = random.Random(text)
    slab = Image.new("L", (SIZE, SIZE), 0)
    pts = []
    for i in range(24):
        a = i / 24 * 6.2832
        rad = SIZE * 0.47 * (0.93 + rng.random() * 0.07)
        x = SIZE / 2 + rad * math.cos(a) * 0.98
        y = SIZE / 2 + rad * math.sin(a) * 0.98
        pts.append((min(max(x, SIZE * 0.04), SIZE * 0.96), min(max(y, SIZE * 0.04), SIZE * 0.96)))
    ImageDraw.Draw(slab).polygon(pts, fill=150)
    slab = slab.filter(ImageFilter.GaussianBlur(6))

    bevel = mask.filter(ImageFilter.GaussianBlur(10))
    depth = Image.composite(Image.new("L", (SIZE, SIZE), 60), slab, bevel.point(lambda v: int(v * 0.9)))
    depth.convert("RGB").save(out_path)
    # The slab silhouette doubles as an exact matte: SDXL paints stone everywhere, we keep only our shape.
    return slab.point(lambda v: 255 if v > 70 else 0).filter(ImageFilter.GaussianBlur(2))


def workflow(job, ctrl_name, seed, cfg):
    wf = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": cfg["checkpoint"]}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": f"{cfg['style']}, {job['prompt']}"}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": cfg["negative"]}},
        "4": {"class_type": "LoadImage", "inputs": {"image": ctrl_name}},
        "5": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": cfg["controlnet"]}},
        "6": {"class_type": "SetUnionControlNetType", "inputs": {"control_net": ["5", 0], "type": "depth"}},
        "7": {"class_type": "ControlNetApplyAdvanced", "inputs": {
            "positive": ["2", 0], "negative": ["3", 0], "control_net": ["6", 0], "image": ["4", 0],
            "strength": job.get("control_strength", cfg["control_strength"]),
            "start_percent": 0.0, "end_percent": cfg.get("control_end", 0.8), "vae": ["1", 2]}},
        "8": {"class_type": "EmptyLatentImage", "inputs": {"width": SIZE, "height": SIZE, "batch_size": 1}},
        "9": {"class_type": "KSampler", "inputs": {
            "model": ["1", 0], "positive": ["7", 0], "negative": ["7", 1], "latent_image": ["8", 0],
            "seed": seed, "steps": cfg["steps"], "cfg": cfg["cfg"], "sampler_name": "dpmpp_2m",
            "scheduler": "karras", "denoise": 1.0}},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["9", 0], "vae": ["1", 2]}},
        "11": {"class_type": "SaveImage", "inputs": {"images": ["10", 0], "filename_prefix": f"slot_{job['id']}"}},
    }
    if ctrl_name is None:  # prompt only: sample straight from the text conditioning
        for k in ("4", "5", "6", "7"):
            del wf[k]
        wf["9"]["inputs"]["positive"] = ["2", 0]
        wf["9"]["inputs"]["negative"] = ["3", 0]
    return wf


def call(path, payload=None):
    req = urllib.request.Request(f"{COMFY_URL}{path}", data=json.dumps(payload).encode() if payload else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def run_job(wf):
    pid = json.loads(call("/prompt", {"prompt": wf, "client_id": str(uuid.uuid4())}))["prompt_id"]
    while True:
        hist = json.loads(call(f"/history/{pid}"))
        if pid in hist:
            status = hist[pid].get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError(json.dumps(status.get("messages", []))[:300])
            imgs = [i for o in hist[pid]["outputs"].values() for i in o.get("images", [])]
            return [call(f"/view?filename={i['filename']}&subfolder={i['subfolder']}&type={i['type']}") for i in imgs]
        time.sleep(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--variants", type=int, default=4)
    ap.add_argument("--no-control", action="store_true", help="prompt only, no ControlNet shape lock")
    args = ap.parse_args()

    cfg = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    out_dir = REPO / "generated" / Path(args.manifest).stem / time.strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    log = {"manifest": args.manifest, "config": {k: v for k, v in cfg.items() if k != "jobs"}, "jobs": []}

    for job in cfg["jobs"]:
        if args.only and job["id"] not in args.only:
            continue
        ctrl = matte = None
        if not args.no_control:
            ctrl = f"slot_ctrl_{job['id']}.png"
            matte = glyph_depth(job["glyph"], cfg["font"], COMFY_DIR / "input" / ctrl)
            Image.open(COMFY_DIR / "input" / ctrl).save(out_dir / f"_control_{job['id']}.png")
        for v in range(args.variants):
            seed = random.randrange(2**32)
            t0 = time.time()
            for i, data in enumerate(run_job(workflow(job, ctrl, seed, cfg))):
                f = out_dir / f"{job['id']}_v{v}.png"
                f.write_bytes(data)
                if matte is not None:
                    cut = Image.open(f).convert("RGBA")
                    cut.putalpha(matte)
                    cut.save(out_dir / f"{job['id']}_v{v}_cut.png")
                log["jobs"].append({"id": job["id"], "variant": v, "seed": seed, "file": f.name})
                print(f"  {f.relative_to(REPO)}  seed={seed}  {time.time() - t0:.1f}s")

    (out_dir / "run.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"Done -> {out_dir.relative_to(REPO)}")


if __name__ == "__main__":
    main()
