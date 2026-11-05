"""
chomp_test.py - the riskiest-assumption test for the Leviathan bite: painted open jaws + painted closed jaws -> RIFE frames
-> flipbook at the chomp -> captures.

    python scripts/ai/chomp_test.py [--closed generated/inbox/p3_leviathan_hero/lev_jaws_closed_1.png] [--n 12] [--fps 24]

Steps: cut out the closed painting with the same key as lev_jaws; align it to the open cut-out by the brow plates (the top
40% of each matte: scale to the same width, translate so the brow centres match, so the only motion left is the jaw);
interpolate with scripts/ai/interp_frames.py on the ComfyUI venv; pack with flipbook_pack.py; run hero_capture.py; write
artifacts/canvas/chomp_test_sheet.png (the frames over grey) next to hero_jaws_seq.png. The judge is the eye: do the
teeth travel without smearing, do the lips meet.
"""

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
HERO = REPO / "slot_engine" / "static" / "canvas" / "assets" / "hero"
VENV_PY = Path(r"C:\Users\kosta\AI\ComfyUI\venv\Scripts\python.exe")
sys.path.insert(0, str(REPO / "scripts" / "ai"))
from designer_pass import cutout  # noqa: E402


def brow_bbox(im: Image.Image, top=0.4):
    a = np.asarray(im.getchannel("A"), dtype=np.float32) / 255
    h = a.shape[0]
    a = a[: int(h * top)]
    ys, xs = np.where(a > 0.3)
    return (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None


def align(B: Image.Image, A: Image.Image) -> Image.Image:
    """Scale/translate B so its brow bbox matches A's; canvas size = A's."""
    ba, bb = brow_bbox(A), brow_bbox(B)
    if not ba or not bb:
        return B.resize(A.size, Image.LANCZOS)
    sa = (ba[2] - ba[0]) / max(1, bb[2] - bb[0])
    nw, nh = int(B.width * sa), int(B.height * sa)
    Bs = B.resize((nw, nh), Image.LANCZOS)
    cxa, cya = (ba[0] + ba[2]) / 2, (ba[1] + ba[3]) / 2
    cxb, cyb = (bb[0] + bb[2]) / 2 * sa, (bb[1] + bb[3]) / 2 * sa
    out = Image.new("RGBA", A.size, (0, 0, 0, 0))
    out.paste(Bs, (int(round(cxa - cxb)), int(round(cya - cyb))), Bs)
    print(f"[chomp] aligned closed painting: scale {sa:.3f}, shift ({cxa - cxb:+.0f}, {cya - cyb:+.0f}) px")
    return out


def sheet(frames, path, cols=4):
    W, H = 688, 384
    rows = (len(frames) + cols - 1) // cols
    s = Image.new("RGB", (W * cols, H * rows), (60, 60, 60))
    for i, f in enumerate(frames):
        im = Image.open(f).convert("RGBA").resize((W, H))
        bg = Image.new("RGBA", (W, H), (60, 60, 60, 255)); bg.alpha_composite(im)
        s.paste(bg.convert("RGB"), ((i % cols) * W, (i // cols) * H))
    s.save(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--closed", default=str(REPO / "generated" / "inbox" / "p3_leviathan_hero" / "lev_jaws_closed_1.png"))
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--no-capture", action="store_true")
    a = ap.parse_args()
    closed = Path(a.closed)
    if not closed.exists():
        cands = sorted(closed.parent.glob("lev_jaws_closed*"))
        if not cands:
            sys.exit(f"[chomp] no closed-jaws painting at {closed}")
        closed = cands[0]
    A = Image.open(HERO / "lev_jaws.png").convert("RGBA")
    B = cutout(Image.open(closed))
    if B.width > 1536:
        B = B.resize((1536, round(B.height * 1536 / B.width)), Image.LANCZOS)
    B = align(B, A)
    work = REPO / "generated" / "flipbook" / "lev_jaws_chomp"
    work.mkdir(parents=True, exist_ok=True)
    A.save(work / "A_open.png"); B.save(work / "B_closed.png")
    frames_dir = work / "frames"
    subprocess.run([str(VENV_PY), str(REPO / "scripts" / "ai" / "interp_frames.py"), str(work / "A_open.png"), str(work / "B_closed.png"),
                    "--n", str(a.n), "--out", str(frames_dir)], check=True)
    subprocess.run([sys.executable, str(REPO / "scripts" / "ai" / "flipbook_pack.py"), "--id", "lev_jaws", "--frames", str(frames_dir), "--fps", str(a.fps)], check=True)
    sheet(sorted(frames_dir.glob("*.png")), REPO / "artifacts" / "canvas" / "chomp_test_sheet.png")
    print("[chomp] frames sheet -> artifacts/canvas/chomp_test_sheet.png")
    if not a.no_capture:
        subprocess.run([sys.executable, str(REPO / "scripts" / "canvas" / "hero_capture.py")], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
