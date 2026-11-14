"""
sfx_pack.py - cut the rendered moment sounds into the event-sized clips the game plays.

moments.py renders the help cue as full-length stems that sum to the mix, which is right for measuring and wrong for
a game: the bite is gated by the animation clock, so each stem has to start on its own event. This trims every clip to
its first audible sample, sums the three pre-impact stems into one lead, and writes a manifest with each clip's
length and its offset from the impact, into the folder the front end serves.

    python scripts/ai/assetgen/moments.py          # render (generated/sfx/moments/)
    python scripts/ai/assetgen/sfx_pack.py         # pack   (slot_engine/static/canvas/assets/sfx/)

Deterministic: pure slicing and summing of deterministic inputs.
"""

import json
import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "generated" / "sfx" / "moments"
OUT = REPO / "slot_engine" / "static" / "canvas" / "assets" / "sfx"
IMPACT_AT = {"full": 1.500, "short": 0.700}     # the beat sheet's impact time inside each render
FLOOR = 10 ** (-66 / 20)                        # below this a sample counts as silence


def read(name: str):
    with wave.open(str(SRC / f"{name}.wav"), "rb") as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return x, sr


def write(name: str, x: np.ndarray, sr: int) -> int:
    x = np.clip(x, -1, 1)
    n = min(len(x) // 2, int(0.004 * sr))
    if n:
        x = x.copy()
        x[:n] *= np.linspace(0, 1, n, dtype=np.float32)
        x[-n:] *= np.linspace(1, 0, n, dtype=np.float32)
    p = OUT / f"{name}.wav"
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    return p.stat().st_size


def bounds(x: np.ndarray, sr: int):
    """First and last audible sample, with 3 ms of lead-in kept so a transient is never clipped."""
    idx = np.flatnonzero(np.abs(x) > FLOOR)
    if not len(idx):
        return 0, len(x)
    return max(0, int(idx[0]) - int(0.003 * sr)), min(len(x), int(idx[-1]) + int(0.02 * sr))


def main() -> int:
    if not SRC.is_dir():
        sys.exit(f"render first: python scripts/ai/assetgen/moments.py ({SRC} is missing)")
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.wav"):
        old.unlink()
    man, total = {}, 0

    def put(name, x, sr, **extra):
        nonlocal total
        size = write(name, x, sr)
        total += size
        man[name] = dict({"ms": round(len(x) / sr * 1000), "peak_db": round(float(20 * np.log10(np.max(np.abs(x)) + 1e-9)), 1)}, **extra)

    # ---- the help: lead (everything before the bite), impact, recede; the cells are their own one-shots ----
    for v, t_imp in IMPACT_AT.items():
        parts = [read(f"help_{v}_{s}") for s in ("dread", "targeting", "vacuum")]
        sr = parts[0][1]
        n = int(t_imp * sr)
        lead = sum(p[0][:n] for p in parts)
        put(f"help_{v}_lead", lead, sr, impact_at_ms=round(t_imp * 1000))
        x, sr = read(f"help_{v}_impact")
        a, b = bounds(x, sr)
        put(f"help_{v}_impact", x[a:b], sr, from_impact_ms=round((a / sr - t_imp) * 1000))
        x, sr = read(f"help_{v}_aftermath")
        a, b = bounds(x, sr)
        put(f"help_{v}_recede", x[a:b], sr, from_impact_ms=round((a / sr - t_imp) * 1000))
    for name in ("help_cell", "help_cell_last", "help_cell_last_short"):
        x, sr = read(name)
        a, b = bounds(x, sr)
        put(name, x[a:b], sr)

    # ---- the win seam: crack + jet fire together on the win, the implosion on the cascade ----
    for step in (1, 3, 5):
        c, sr = read(f"win_s{step}_crack")
        j, _ = read(f"win_s{step}_jet")
        n = max(len(c), len(j))
        mix = np.zeros(n, dtype=np.float32); mix[:len(c)] += c; mix[:len(j)] += j
        a, b = bounds(mix, sr)
        put(f"seam_s{step}", mix[a:b], sr)
        x, sr = read(f"win_s{step}_implode")
        a, b = bounds(x, sr)
        put(f"seam_implode_s{step}", x[a:b], sr)

    # ---- symbol voices: three land takes and one stinger each ----
    for f in sorted(SRC.glob("sym_*.wav")):
        x, sr = read(f.stem)
        a, b = bounds(x, sr)
        put(f.stem, x[a:b], sr)

    (OUT / "moments.json").write_text(json.dumps({"note": "Written by scripts/ai/assetgen/sfx_pack.py. Source: procedural, licence: ours.",
                                                    "clips": man}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[pack] {len(man)} clips, {total / 1e6:.2f} MB -> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
