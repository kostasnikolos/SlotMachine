"""
install_models.py - install the licence-cleared local model stack into ComfyUI, repeatably.

The list is the shortlist in docs/local_asset_tools.md: Apache 2.0 / MIT / BSD only, sized for the 8 GB card.
Every file is fetched from the Hugging Face Hub at the repo's current commit, placed in the ComfyUI models folder
it belongs in, and logged in artifacts/model_provenance.json with repo, commit, licence, size and SHA-256 - the
per-asset provenance record the brief asks for. Re-running skips files already present at the right size.

Run it on the ComfyUI venv (it has huggingface_hub):

    "C:/Users/kosta/AI/ComfyUI/venv/Scripts/python.exe" scripts/ai/install_models.py --list
    "C:/Users/kosta/AI/ComfyUI/venv/Scripts/python.exe" scripts/ai/install_models.py              # everything
    "C:/Users/kosta/AI/ComfyUI/venv/Scripts/python.exe" scripts/ai/install_models.py --only zimage chroma

No token is needed: none of these repos is gated. Nothing here is a non-commercial model; do not add one.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COMFY = Path(os.environ.get("COMFY_DIR", r"C:\Users\kosta\AI\ComfyUI"))
MODELS = COMFY / "models"
PROVENANCE = REPO / "artifacts" / "model_provenance.json"

# group -> (what it is, licence, [(hub repo, file in repo, models subfolder, file name on disk)])
STACK = {
    "zimage": ("Z-Image-Turbo: fast painted stills (8 steps)", "apache-2.0", [
        ("Comfy-Org/z_image_turbo", "split_files/diffusion_models/z_image_turbo_bf16.safetensors", "diffusion_models", None),
        ("Comfy-Org/z_image_turbo", "split_files/text_encoders/qwen_3_4b.safetensors", "text_encoders", None),
        ("Comfy-Org/z_image_turbo", "split_files/vae/ae.safetensors", "vae", None),
    ]),
    "chroma": ("Chroma1-HD: FLUX-grade painting on schnell's licence", "apache-2.0", [
        ("silveroxides/Chroma1-HD-GGUF", "Chroma1-HD-Q4_K_M.gguf", "diffusion_models", None),
        ("city96/t5-v1_1-xxl-encoder-gguf", "t5-v1_1-xxl-encoder-Q5_K_M.gguf", "text_encoders", None),
        ("Comfy-Org/z_image_turbo", "split_files/vae/ae.safetensors", "vae", None),          # the FLUX VAE, shared
    ]),
    "klein": ("FLUX.2 klein 4B: 4-step stills and edits (the 4B only; 9B and dev are non-commercial)", "apache-2.0", [
        ("Comfy-Org/flux2-klein-4B", "split_files/diffusion_models/flux-2-klein-4b.safetensors", "diffusion_models", None),
        ("Comfy-Org/z_image_turbo", "split_files/text_encoders/qwen_3_4b.safetensors", "text_encoders", None),  # shared
        ("Comfy-Org/flux2-klein-4B", "split_files/vae/flux2-vae.safetensors", "vae", None),
    ]),
    "qwenedit": ("Qwen-Image-Edit-2511: same creature, new pose", "apache-2.0", [
        ("unsloth/Qwen-Image-Edit-2511-GGUF", "qwen-image-edit-2511-Q4_K_M.gguf", "diffusion_models", None),
        ("Comfy-Org/Qwen-Image_ComfyUI", "split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors", "text_encoders", None),
        ("Comfy-Org/Qwen-Image_ComfyUI", "split_files/vae/qwen_image_vae.safetensors", "vae", None),
    ]),
    "wan": ("Wan 2.2 TI2V-5B: image-to-video", "apache-2.0", [
        ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged", "split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors", "diffusion_models", None),
        ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged", "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors", "text_encoders", None),
        ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged", "split_files/vae/wan2.2_vae.safetensors", "vae", None),
    ]),
    "birefnet": ("BiRefNet: cut-outs (ComfyUI's native background-removal node)", "mit", [
        ("ZhengPeng7/BiRefNet", "model.safetensors", "background_removal", "birefnet.safetensors"),
    ]),
    "esrgan": ("Real-ESRGAN x4plus: upscaling", "bsd-3-clause", [
        ("Comfy-Org/Real-ESRGAN_repackaged", "RealESRGAN_x4plus.safetensors", "upscale_models", None),
    ]),
}

# custom nodes the quantised models need: (folder, git url, licence, pip packages)
NODES = [
    ("ComfyUI-GGUF", "https://github.com/city96/ComfyUI-GGUF", "apache-2.0", ["gguf"]),
]


def load_log() -> dict:
    if PROVENANCE.exists():
        return json.loads(PROVENANCE.read_text(encoding="utf-8"))
    return {"note": "Per-file provenance of the local model stack. Written by scripts/ai/install_models.py.",
            "files": {}, "nodes": {}}


def save_log(log: dict) -> None:
    PROVENANCE.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE.write_text(json.dumps(log, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def install_nodes(log: dict) -> None:
    for folder, url, licence, pips in NODES:
        dest = COMFY / "custom_nodes" / folder
        if not dest.exists():
            print(f"[node] cloning {url}")
            subprocess.run(["git", "clone", "--depth", "1", url, str(dest)], check=True)
        if pips:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", *pips], check=True)
        head = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        log["nodes"][folder] = {"url": url, "commit": head, "licence": licence}
        print(f"[node] {folder} @ {head[:10]}  ({licence})")
        save_log(log)


def install_file(api, group: str, licence: str, repo: str, rfile: str, sub: str, name, log: dict) -> None:
    from huggingface_hub import hf_hub_download
    info = api.model_info(repo, files_metadata=True)
    meta = next((s for s in info.siblings if s.rfilename == rfile), None)
    if meta is None:
        raise SystemExit(f"{repo} has no file {rfile}")
    tagged = getattr(info.card_data, "license", None) if info.card_data else None
    if tagged != licence:
        raise SystemExit(f"{repo}: hub licence tag is {tagged!r}, expected {licence!r} - stop and re-read the licence")
    dest = MODELS / sub / (name or Path(rfile).name)
    key = f"{sub}/{dest.name}"
    sha = meta.lfs.sha256 if meta.lfs else None
    if dest.exists() and dest.stat().st_size == meta.size:
        print(f"[have] {key}  {meta.size / 1e9:6.2f} GB")
    else:
        print(f"[get ] {key}  {meta.size / 1e9:6.2f} GB  <- {repo}")
        t0 = time.time()
        stage = MODELS / ".staging"
        got = Path(hf_hub_download(repo, rfile, revision=info.sha, local_dir=str(stage / repo.replace("/", "__"))))
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(got), str(dest))
        print(f"[done] {key}  in {time.time() - t0:5.0f} s")
    entry = log["files"].setdefault(key, {"used_by": []})
    entry.update({"repo": repo, "file": rfile, "commit": info.sha, "licence": licence, "bytes": meta.size, "sha256": sha})
    if group not in entry["used_by"]:
        entry["used_by"] = sorted(entry["used_by"] + [group])
    save_log(log)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", choices=sorted(STACK), help="install only these groups")
    ap.add_argument("--list", action="store_true", help="show the stack and exit")
    ap.add_argument("--skip-nodes", action="store_true", help="do not clone or update custom nodes")
    a = ap.parse_args()
    groups = a.only or list(STACK)
    if a.list:
        for g in groups:
            what, lic, files = STACK[g]
            print(f"{g:<9} {lic:<13} {what}")
            for repo, rfile, sub, name in files:
                print(f"            {sub}/{name or Path(rfile).name}  <- {repo}")
        return 0
    if not MODELS.is_dir():
        sys.exit(f"ComfyUI models folder not found at {MODELS} (set COMFY_DIR)")
    from huggingface_hub import HfApi
    api = HfApi()
    log = load_log()
    if not a.skip_nodes:
        install_nodes(log)
    for g in groups:
        what, lic, files = STACK[g]
        print(f"== {g}: {what}")
        for repo, rfile, sub, name in files:
            install_file(api, g, lic, repo, rfile, sub, name, log)
    shutil.rmtree(MODELS / ".staging", ignore_errors=True)
    print(f"provenance -> {PROVENANCE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
