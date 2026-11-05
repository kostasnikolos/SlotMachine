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


def compose_lunge(w=1344, h=768):
    """A collage with a matching depth map: our frontal jaws painting as the head (near), a procedural serpentine body
    coiling back and up into the dark (far), photophores along the spine, tendrils. SDXL repaints it as one painting."""
    import math
    import numpy as np
    img = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    dep = Image.new("L", (w, h), 0)
    d, dd = ImageDraw.Draw(img), ImageDraw.Draw(dep)
    # body path: from behind the head (centre-bottom) curving up to the top-right then back left, receding
    pts = []
    for i in range(0, 101):
        t = i / 100
        x = w * (0.50 + 0.33 * math.sin(t * 2.6) + 0.12 * t)
        y = h * (0.62 - 0.55 * t + 0.10 * math.sin(t * 5.2))
        pts.append((x, y, t))
    rng0 = random.Random(3)
    for x, y, t in reversed(pts):
        r = (1 - t) ** 1.3 * h * 0.19 + 6
        g = int(30 - 20 * t)
        d.ellipse([x - r, y - r * 0.82, x + r, y + r * 0.82], fill=(g, g + 10, g + 12, 255))
        dd.ellipse([x - r, y - r * 0.82, x + r, y + r * 0.82], fill=int(200 * (1 - t) ** 1.2 + 20))
    # plated texture and a ridge of spines so SDXL sees scales, not a tube
    for x, y, t in pts[::2]:
        r = (1 - t) ** 1.3 * h * 0.19 + 6
        for k in range(5):
            px = x + rng0.uniform(-r * 0.8, r * 0.8); py = y + rng0.uniform(-r * 0.6, r * 0.6)
            pr = r * rng0.uniform(0.12, 0.3)
            gg = int(18 + 28 * rng0.random() - 16 * t)
            d.ellipse([px - pr, py - pr * 0.6, px + pr, py + pr * 0.6], outline=(gg + 14, gg + 26, gg + 28, 255), fill=(gg, gg + 9, gg + 11, 255), width=2)
        if int(t * 100) % 6 == 0:
            sp = r * 0.55
            d.polygon([(x - sp * 0.25, y - r * 0.8), (x + sp * 0.25, y - r * 0.8), (x, y - r * 0.8 - sp)], fill=(22, 34, 38, 255))
            dd.polygon([(x - sp * 0.25, y - r * 0.8), (x + sp * 0.25, y - r * 0.8), (x, y - r * 0.8 - sp)], fill=int(200 * (1 - t) ** 1.2 + 20))
    # dorsal ridge + photophores
    for x, y, t in pts[::4]:
        r = (1 - t) ** 1.3 * h * 0.19 + 6
        d.ellipse([x - 4, y - r * 0.82 - 4, x + 4, y - r * 0.82 + 4], fill=(60, 220, 210, 255))
        d.ellipse([x - 14, y - r * 0.82 - 14, x + 14, y - r * 0.82 + 14], fill=(30, 110, 110, 120))
    # the head: our painted jaws, frontal, in the lower centre
    head = Image.open(REPO / "slot_engine" / "static" / "canvas" / "assets" / "hero" / "lev_jaws.png").convert("RGBA")
    hw = int(w * 0.46); hh = int(head.height * hw / head.width)
    head = head.resize((hw, hh), Image.LANCZOS)
    # harden the matte: the keyed painting keeps a faint dark box around the creature on pure black
    import numpy as np
    ha = np.asarray(head, dtype=np.float32)
    al = np.clip((ha[..., 3] - 70) / 90, 0, 1)
    ha[..., 3] = al * 255
    head = Image.fromarray(ha.astype(np.uint8), "RGBA")
    hx, hy = int(w * 0.5 - hw * 0.5), int(h * 0.62 - hh * 0.5)
    img.alpha_composite(head, (hx, hy))
    hm = head.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    dep.paste(Image.new("L", (hw, hh), 255), (hx, hy), hm)
    # tendrils from the jaw
    rng = random.Random(7)
    for k in range(9):
        x0 = hx + hw * (0.3 + 0.4 * rng.random()); y0 = hy + hh * 0.86
        pts2 = [(x0, y0)]
        for j in range(8):
            pts2.append((pts2[-1][0] + rng.uniform(-22, 22), pts2[-1][1] + rng.uniform(14, 34)))
        d.line(pts2, fill=(40, 70, 75, 230), width=3)
        dd.line(pts2, fill=120, width=3)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    dep = dep.filter(ImageFilter.GaussianBlur(3))
    return img.convert("RGB"), dep.convert("RGB")


def lunge_local(variants, denoise=0.55, strength=0.75):
    init, dep = compose_lunge()
    init_name, dep_name = "hero_lunge_init.png", "hero_lunge_depth.png"
    init.save(COMFY_DIR / "input" / init_name); dep.save(COMFY_DIR / "input" / dep_name)
    init.save(REPO / "artifacts" / "canvas" / "comfy_lunge_collage.png")
    pos = (STYLE + ", the whole colossal leviathan lunging straight at the viewer out of the black, head with open jaws of "
           "needle teeth in the centre foreground lit by its cyan lure, the long serpentine body coiling away behind it into "
           "the dark with rows of cyan photophores along the spine receding in perspective, tendrils trailing from the jaw, "
           "wet plated skin, the body dissolving into pure black at the edges, nothing else in the frame")
    outs = []
    for v in range(variants):
        seed = random.randint(1, 2**31)
        wf = base_graph(pos, NEG + ", sea surface, waves, sky, horizon, ship", seed, steps=32, cfg=6.5)
        wf["4"] = {"class_type": "LoadImage", "inputs": {"image": init_name}}
        wf["5"] = {"class_type": "LoadImage", "inputs": {"image": dep_name}}
        wf["12"] = {"class_type": "ControlNetLoader", "inputs": {"control_net_name": "controlnet_union_sdxl_promax.safetensors"}}
        wf["13"] = {"class_type": "SetUnionControlNetType", "inputs": {"control_net": ["12", 0], "type": "depth"}}
        wf["14"] = {"class_type": "ControlNetApplyAdvanced", "inputs": {"positive": ["2", 0], "negative": ["3", 0], "control_net": ["13", 0],
                                                                        "image": ["5", 0], "strength": strength, "start_percent": 0.0, "end_percent": 0.8, "vae": ["1", 2]}}
        wf["8"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["4", 0], "vae": ["1", 2]}}
        wf["9"]["inputs"]["positive"] = ["14", 0]; wf["9"]["inputs"]["negative"] = ["14", 1]; wf["9"]["inputs"]["denoise"] = denoise
        png = run(wf)[0]
        out = INBOX / f"lev_lunge_l{v + 1}.png"
        out.write_bytes(png)
        outs.append(out)
        print(f"[comfy] lunge (local collage) variant {v + 1} (seed {seed}, denoise {denoise}) -> {out.relative_to(REPO)}")
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
    ap.add_argument("what", choices=["closed", "closed-refine", "lunge", "lunge-local"])
    ap.add_argument("--strength", type=float, default=0.75)
    ap.add_argument("--denoise", type=float, default=0.5)
    ap.add_argument("--variants", type=int, default=4)
    a = ap.parse_args()
    INBOX.mkdir(parents=True, exist_ok=True)
    try:
        call("/system_stats")
    except Exception as e:  # noqa: BLE001
        sys.exit(f"ComfyUI is not reachable at {COMFY_URL}: {e}")
    outs = (closed(a.variants) if a.what == "closed" else closed_refine(a.variants, a.denoise) if a.what == "closed-refine"
            else lunge_local(a.variants, a.denoise, a.strength) if a.what == "lunge-local" else lunge(a.variants))
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
