"""Batch image generation through Gemini, driven by a JSON prompt manifest.

The API key is read from the GEMINI_API_KEY environment variable and is never printed.
Every run writes images plus a run.json (prompts, model, seeds-as-variant-index, timestamps)
to generated/<manifest-name>/<timestamp>/ so the Reviewer can trace each file back to its prompt.

Usage:
    python scripts/ai/gemini_generate.py --list-models
    python scripts/ai/gemini_generate.py scripts/ai/prompts/p1_backdrop_frame.json
    python scripts/ai/gemini_generate.py scripts/ai/prompts/p2_symbols.json --only angler --variants 2
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-nano-banana-2.1")


def client():
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY is not set. Run: setx GEMINI_API_KEY \"<key>\" and restart the terminal.")
    try:
        from google import genai
    except ImportError:
        sys.exit("Missing SDK. Run: pip install google-genai pillow")
    return genai.Client()


def list_models(c):
    for m in c.models.list():
        name = m.name.replace("models/", "")
        if any(k in name for k in ("image", "imagen", "veo", "banana", "omni")):
            print(name)


def build_prompt(manifest, job):
    parts = [manifest.get("style", ""), job["prompt"], manifest.get("negative", "")]
    return "\n\n".join(p for p in parts if p)


def load_refs(manifest, job):
    from PIL import Image
    refs = manifest.get("style_refs", []) + job.get("refs", [])
    return [Image.open(REPO / r) for r in refs]


def gen_gemini(c, model, prompt, refs):
    resp = c.models.generate_content(model=model, contents=[prompt, *refs])
    out = []
    for cand in resp.candidates or []:
        for part in cand.content.parts:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                out.append(part.inline_data.data)
    return out


def gen_imagen(c, model, prompt, aspect):
    from google.genai import types
    resp = c.models.generate_images(
        model=model,
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio=aspect),
    )
    return [g.image.image_bytes for g in resp.generated_images]


def run(c, manifest_path, model, only, variants):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    out_dir = REPO / "generated" / Path(manifest_path).stem / time.strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    log = {"manifest": str(manifest_path), "model": model, "jobs": []}

    for job in manifest["jobs"]:
        if only and job["id"] not in only:
            continue
        prompt = build_prompt(manifest, job)
        n = variants or job.get("variants", manifest.get("variants", 4))
        for v in range(n):
            try:
                if model.startswith("imagen"):
                    images = gen_imagen(c, model, prompt, job.get("aspect", "1:1"))
                else:
                    images = gen_gemini(c, model, prompt, load_refs(manifest, job))
            except Exception as e:  # keep the batch going; the log records the failure
                print(f"  {job['id']} v{v}: FAILED {type(e).__name__}: {str(e)[:160]}")
                log["jobs"].append({"id": job["id"], "variant": v, "error": str(e)})
                continue
            for i, data in enumerate(images):
                f = out_dir / f"{job['id']}_v{v}_{i}.png"
                f.write_bytes(data)
                log["jobs"].append({"id": job["id"], "variant": v, "file": f.name, "prompt": prompt})
                print(f"  {f.relative_to(REPO)}")

    (out_dir / "run.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"Done -> {out_dir.relative_to(REPO)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", nargs="?")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--only", nargs="*", help="job ids to run")
    ap.add_argument("--variants", type=int)
    ap.add_argument("--list-models", action="store_true")
    args = ap.parse_args()

    c = client()
    if args.list_models:
        list_models(c)
    elif args.manifest:
        run(c, args.manifest, args.model, args.only, args.variants)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
