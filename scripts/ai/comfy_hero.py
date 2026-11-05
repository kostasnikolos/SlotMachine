"""
comfy_hero.py - paint the Leviathan hero keyframes locally with SDXL in ComfyUI (free route, no Gemini needed).

    python scripts/ai/comfy_hero.py closed  [--variants 4]   # inpaint the mouth of lev_jaws_1.jpg shut -> generated/inbox/p3_leviathan_hero/lev_jaws_closed_<n>.png
    python scripts/ai/comfy_hero.py lunge   [--variants 4]   # whole-figure lunge, text-to-image 1344x768 -> lev_lunge_<n>.png

closed: the open-jaws painting is the init image; only an ellipse over the mouth interior is repainted (VAEEncodeForInpaint,
denoise 1 inside the mask, the rest of the painting untouched), so the head, angle, scale and lighting stay identical and
the interpolation test measures only the jaw. ComfyUI must be running on http://127.0.0.1:8188 with sd_xl_base_1.0.
"""

import argparse
import json
import random
import shutil
import sys
import time
import urllib.request
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parents[2]
COMFY_URL = "http://127.0.0.1:8188"
COMFY_DIR = Path(r"C:\Users\kosta\AI\ComfyUI")
INBOX = REPO / "generated" / "inbox" / "p3_leviathan_hero"
CKPT = "sd_xl_base_1.0.safetensors"

STYLE = ("dark painterly digital illustration, deep-sea horror, eldritch leviathan, heavily desaturated teal-grey palette, "
         "bioluminescent cyan light only, wet scaled skin, bony plates, visible brush texture, fine film grain, matte, pure black background")
NEG = ("text, watermark, logo, frame, border, cartoon, anime, bright colours, rainbow, blurry, deformed, extra heads, human, "
       "daylight, white background, fog outside the creature")


def call(path, payload=None):
    req = urllib.request.Request(COMFY_URL + path, data=json.dumps(payload).encode() if payload is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.read()


def run(wf):
    pid = json.loads(call("/prompt", {"prompt": wf, "client_id": str(uuid.uuid4())}))["prompt_id"]
    while True:
        hist = json.loads(call(f"/history/{pid}"))
        if pid in hist:
            outs = hist[pid]["outputs"]
            imgs = [i for o in outs.values() for i in o.get("images", [])]
            return [call(f"/view?filename={i['filename']}&subfolder={i['subfolder']}&type={i['type']}") for i in imgs]
        time.sleep(1.5)


def base_graph(pos, neg, seed, steps=30, cfg=6.5):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": pos}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": neg}},
        "9": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["8", 0],
                                                   "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0}},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["9", 0], "vae": ["1", 2]}},
        "11": {"class_type": "SaveImage", "inputs": {"images": ["10", 0], "filename_prefix": "hero"}},
    }


def closed(variants):
    src = INBOX / "lev_jaws_1.jpg"
    im = Image.open(src).convert("RGB")
    w, h = im.size
    # the mouth interior of lev_jaws_1 (measured): an ellipse between the upper and lower teeth rows
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([w * 0.30, h * 0.26, w * 0.72, h * 0.86], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(14))
    init_name, mask_name = "hero_jaws_init.png", "hero_jaws_mask.png"
    im.save(COMFY_DIR / "input" / init_name)
    mask.save(COMFY_DIR / "input" / mask_name)
    pos = (STYLE + ", the same creature with its jaws SHUT, mouth closed, lips pressed together, long needle teeth interlocking "
           "and overlapping outside the closed lips, dim cyan glow between the teeth, bony plated snout, no open throat")
    outs = []
    for v in range(variants):
        seed = random.randint(1, 2**31)
        wf = base_graph(pos, NEG + ", open mouth, gaping jaws, visible throat, tongue", seed, steps=32, cfg=7)
        wf["4"] = {"class_type": "LoadImage", "inputs": {"image": init_name}}
        wf["5"] = {"class_type": "LoadImage", "inputs": {"image": mask_name}}
        wf["6"] = {"class_type": "ImageToMask", "inputs": {"image": ["5", 0], "channel": "red"}}
        wf["8"] = {"class_type": "VAEEncodeForInpaint", "inputs": {"pixels": ["4", 0], "vae": ["1", 2], "mask": ["6", 0], "grow_mask_by": 24}}
        png = run(wf)[0]
        out = INBOX / f"lev_jaws_closed_{v + 1}.png"
        out.write_bytes(png)
        outs.append(out)
        print(f"[comfy] closed jaws variant {v + 1} (seed {seed}) -> {out.relative_to(REPO)}")
    return outs


def closed_refine(variants, denoise=0.5):
    """Structure first: the synthetic closed pose (lower jaw slid up 16%) is the init image; SDXL only repaints the band
    where the two jaws meet (SetLatentNoiseMask, partial denoise), so the head stays identical and the seam becomes a painted bite."""
    sys.path.insert(0, str(REPO / "scripts" / "ai"))
    from flipbook_pack import synthetic
    fr = synthetic("lev_jaws", 2)[1]
    w, h = fr.size
    bg = Image.new("RGBA", (w, h), (0, 0, 0, 255)); bg.alpha_composite(fr)
    init = bg.convert("RGB")
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([w * 0.26, h * 0.40, w * 0.76, h * 0.80], fill=255)        # the meeting line of the jaws, inside the mouth ellipse
    mask = mask.filter(ImageFilter.GaussianBlur(18))
    init_name, mask_name = "hero_jaws_closed_init.png", "hero_jaws_closed_mask.png"
    init.save(COMFY_DIR / "input" / init_name); mask.save(COMFY_DIR / "input" / mask_name)
    pos = (STYLE + ", the creature's jaws are shut, upper and lower needle teeth interlocking and overlapping, lips pressed together, "
           "wet gums, dim cyan glow leaking between the teeth, no open throat")
    outs = []
    for v in range(variants):
        seed = random.randint(1, 2**31)
        wf = base_graph(pos, NEG + ", open mouth, gaping jaws, visible throat", seed, steps=30, cfg=6.5)
        wf["4"] = {"class_type": "LoadImage", "inputs": {"image": init_name}}
        wf["5"] = {"class_type": "LoadImage", "inputs": {"image": mask_name}}
        wf["6"] = {"class_type": "ImageToMask", "inputs": {"image": ["5", 0], "channel": "red"}}
        wf["7"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["4", 0], "vae": ["1", 2]}}
        wf["8"] = {"class_type": "SetLatentNoiseMask", "inputs": {"samples": ["7", 0], "mask": ["6", 0]}}
        wf["9"]["inputs"]["denoise"] = denoise
        png = run(wf)[0]
        out = INBOX / f"lev_jaws_closed_r{v + 1}.png"
        out.write_bytes(png)
        outs.append(out)
        print(f"[comfy] closed (refined seam) variant {v + 1} (seed {seed}, denoise {denoise}) -> {out.relative_to(REPO)}")
    return outs


def lunge(variants):
    pos = (STYLE + ", the WHOLE colossal leviathan rushing straight at the viewer out of the black, seen from the front and "
           "slightly above, head with open jaws of needle teeth in the centre foreground, long serpentine body coiling away "
           "behind it into the dark with perspective, rows of cyan photophores along the spine receding, fins and tendrils trailing, "
           "the body fading into pure black at the edges")
    outs = []
    for v in range(variants):
        seed = random.randint(1, 2**31)
        wf = base_graph(pos, NEG, seed, steps=34, cfg=6.5)
        wf["8"] = {"class_type": "EmptyLatentImage", "inputs": {"width": 1344, "height": 768, "batch_size": 1}}
        png = run(wf)[0]
        out = INBOX / f"lev_lunge_{v + 1}.png"
        out.write_bytes(png)
        outs.append(out)
        print(f"[comfy] lunge variant {v + 1} (seed {seed}) -> {out.relative_to(REPO)}")
    return outs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["closed", "closed-refine", "lunge"])
    ap.add_argument("--denoise", type=float, default=0.5)
    ap.add_argument("--variants", type=int, default=4)
    a = ap.parse_args()
    INBOX.mkdir(parents=True, exist_ok=True)
    try:
        call("/system_stats")
    except Exception as e:  # noqa: BLE001
        sys.exit(f"ComfyUI is not reachable at {COMFY_URL}: {e}")
    outs = closed(a.variants) if a.what == "closed" else closed_refine(a.variants, a.denoise) if a.what == "closed-refine" else lunge(a.variants)
    # contact sheet for review
    ims = [Image.open(p).convert("RGB") for p in outs]
    W, H = 688, 384
    sheet = Image.new("RGB", (W * 2, H * ((len(ims) + 1) // 2)), (20, 20, 20))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((W, H)), ((i % 2) * W, (i // 2) * H))
    sp = REPO / "artifacts" / "canvas" / f"comfy_{a.what.replace('-', '_')}_sheet.png"
    sheet.save(sp)
    print(f"[comfy] sheet -> {sp.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
