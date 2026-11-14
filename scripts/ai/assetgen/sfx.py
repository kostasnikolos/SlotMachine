"""
sfx.py - render The Descent's sound effects to files, offline and deterministically.

Each recipe is the same design as the runtime set in `slot_engine/static/canvas/audio_dark.js` (docs/feel_design_plan.md
section B): no bubbles as hits, pressure and metal instead of sparkle, nothing tonal and major-key. Rendering them to
files means they can be tuned on a waveform, packed into a sprite sheet, A/B'd against the runtime set, and logged with
their provenance, which AI-generated audio needs anyway (docs/audio_sourcing_brief.md).

    python scripts/ai/assetgen/sfx.py                 # render every recipe -> generated/sfx/*.wav + manifest
    python scripts/ai/assetgen/sfx.py --only crush seam_jet --sheet

Every recipe is seeded from its own name, so the same command always produces the same file.
"""

import argparse
import hashlib
import json
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import synth as S  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "generated" / "sfx"


# ---------------------------------------------------------------- recipes ---------------------------------------------
# Each takes a seeded Generator and returns mono float32. Keep them short: these are hits, not beds.

def dissolve(rng):
    """A symbol leaves the board: a noise burst falling 900 -> 250 Hz under a sine dropping 110 -> 55. No ding."""
    n = S.noise(0.09, rng, "white")
    n = S.biquad(n, "bandpass", S.sweep(900, 250, 0.09), 3.0) * S.env(0.09, 0.002, 0.085, 1.0, 1.6)
    sub = S.osc(S.sweep(110, 55, 0.12), 0.12, "sine") * S.env(0.12, 0.004, 0.115, 0.55, 2.2)
    return S.mix(S.at(n, 0, int(0.14 * S.SR)), S.at(sub, 0.004, int(0.14 * S.SR)))


def crush(rng):
    """Crush depth: the hull takes a dust win. A long pressure groan with the air squeezed out of it."""
    L = int(0.9 * S.SR)
    groan = S.osc(S.sweep(90, 26, 0.85), 0.85, "tri") * S.env(0.85, 0.05, 0.78, 0.8, 1.4)
    metal = S.biquad(S.noise(0.5, rng, "pink"), "bandpass", S.sweep(420, 120, 0.5), 6.0) * S.env(0.5, 0.02, 0.46, 0.4, 2.0)
    air = S.biquad(S.noise(0.35, rng, "white"), "lowpass", S.sweep(1800, 180, 0.35)) * S.env(0.35, 0.006, 0.33, 0.3, 2.6)
    body = S.mix(S.at(groan, 0, L), S.at(metal, 0.03, L), S.at(air, 0.0, L))
    return S.convolve(body, S.reverb_ir(2.0, rng), 0.3)[:L]


def land(rng, step=0):
    """A cascade lands: sub thud + lowpassed noise + a short FM metal tap. Each later step is 2 semitones down."""
    k = 2 ** (-2 * step / 12)
    L = int(0.3 * S.SR)
    sub = S.osc(S.sweep(70 * k, 38 * k, 0.2), 0.2, "sine") * S.env(0.2, 0.003, 0.19, 0.9, 1.8)
    thud = S.biquad(S.noise(0.12, rng, "white"), "lowpass", 400 * k) * S.env(0.12, 0.002, 0.11, 0.5, 2.2)
    metal = S.fm(180 * k, 311 * k, S.sweep(4, 0.05, 0.15, "exp"), 0.15) * S.env(0.15, 0.001, 0.14, 0.28, 3.0)
    return S.mix(S.at(sub, 0, L), S.at(thud, 0, L), S.at(metal, 0.004, L))


def impact(rng):
    """Wild Maw: 40 ms of nothing, an 8 ms click, a 500 ms body, a sub drop and a rumble under it all."""
    L = int(1.9 * S.SR)
    click = S.biquad(S.noise(0.008, rng, "white"), "highpass", 2000.0) * S.env(0.008, 0.0005, 0.0075, 1.0, 1.0)
    body = S.biquad(S.noise(0.5, rng, "white"), "lowpass", S.sweep(3000, 150, 0.5)) * S.env(0.5, 0.002, 0.49, 0.85, 1.9)
    sub = S.osc(S.sweep(55, 28, 0.6), 0.6, "sine") * S.env(0.6, 0.004, 0.58, 1.0, 1.7)
    rumble = S.biquad(S.noise(1.5, rng, "brown"), "lowpass", 90.0) * S.env(1.5, 0.05, 1.4, 0.45, 1.2)
    dry = S.mix(S.at(click, 0.04, L), S.at(body, 0.048, L), S.at(sub, 0.048, L), S.at(rumble, 0.05, L))
    return S.convolve(dry, S.reverb_ir(2.6, rng), 0.26)[:L]


def riser(rng, dur=1.5):
    """Anticipation: pink noise through a bandpass climbing 200 -> 2500 Hz, Q6, going nowhere pleasant."""
    L = int((dur + 0.1) * S.SR)
    n = S.biquad(S.noise(dur, rng, "pink"), "bandpass", S.sweep(200, 2500, dur), 6.0)
    n *= np.linspace(0.12, 1.0, len(n), dtype=np.float32) ** 1.6
    det = S.osc(S.sweep(55, 150, dur), dur, "saw") * 0.12 * np.linspace(0, 1, int(dur * S.SR), dtype=np.float32) ** 3
    return S.mix(S.at(n, 0, L), S.at(det, 0, L))


def roar(rng):
    """The Leviathan strike: riser, 300 ms of total silence, then the impact with a ring-modulated growl."""
    rise = riser(rng, 1.5)
    hole = 0.3
    L = len(rise) + int((hole + 2.0) * S.SR)
    growl = S.ring_mod(S.osc(45, 0.9, "saw"), S.osc(31, 0.9, "sine"))
    growl = S.biquad(growl, "lowpass", 600.0) * S.env(0.9, 0.01, 0.88, 0.8, 1.5)
    hit = impact(rng) * 1.3
    start = (len(rise) / S.SR) + hole
    return S.mix(S.at(rise * 0.8, 0, L), S.at(hit, start, L), S.at(growl, start + 0.02, L))


def seam_jet(rng):
    """Seam Breach: the glass gives and a needle of water comes through under pressure."""
    L = int(0.55 * S.SR)
    crack = S.biquad(S.noise(0.02, rng, "white"), "highpass", 3200.0) * S.env(0.02, 0.0004, 0.019, 1.0, 1.2)
    jet = S.biquad(S.noise(0.42, rng, "white"), "bandpass", S.sweep(2600, 900, 0.42), 1.4) * S.env(0.42, 0.012, 0.4, 0.55, 1.5)
    press = S.osc(S.sweep(140, 60, 0.3), 0.3, "sine") * S.env(0.3, 0.005, 0.29, 0.35, 2.0)
    return S.mix(S.at(crack, 0, L), S.at(jet, 0.006, L), S.at(press, 0.01, L))


def hull_creak(rng):
    """The frame under depth: metal complaining, no impact. For the idle and the depth ladder."""
    L = int(1.4 * S.SR)
    base = S.osc(S.sweep(70, 96, 1.2, "lin"), 1.2, "saw") * 0.5
    bowed = S.biquad(base, "bandpass", S.sweep(240, 520, 1.2), 9.0)
    stick = np.ones(len(bowed), dtype=np.float32)
    rngv = rng.random(14)
    for i, v in enumerate(rngv):                       # stick-slip: the groan stutters as the metal lets go
        a = int((0.05 + i * 0.08) * S.SR)
        b = min(len(stick), a + int((0.004 + v * 0.01) * S.SR))
        stick[a:b] *= 0.25
    body = bowed * stick * S.env(1.2, 0.12, 1.05, 0.6, 1.1)
    return S.convolve(S.at(body, 0.02, L), S.reverb_ir(2.2, rng), 0.3)[:L]


def tick(rng):
    """Count-up tick: a noise click, 400 -> 1200 Hz with the count's progress. Never a coin."""
    L = int(0.07 * S.SR)
    c = S.biquad(S.noise(0.02, rng, "white"), "bandpass", S.sweep(400, 1200, 0.02), 4.0) * S.env(0.02, 0.0006, 0.019, 1.0, 1.6)
    return S.at(c, 0, L)


def shimmer(rng):
    """Wilds surfacing / pearls: a dark minor shimmer, no sparkle."""
    L = int(1.6 * S.SR)
    parts = [S.osc(f, 1.5, "sine") * S.env(1.5, 0.08 + i * 0.05, 1.4, 0.22 / (i + 1), 1.4)
             for i, f in enumerate((73.42, 110.0, 146.83, 220.0))]
    dry = S.mix(*[S.at(p, 0.02 * i, L) for i, p in enumerate(parts)], length=L)
    return S.convolve(dry, S.reverb_ir(2.8, rng), 0.38)[:L]


RECIPES = {
    "dissolve": dissolve,
    "land": lambda r: land(r, 0),
    "land_deep": lambda r: land(r, 4),
    "crush": crush,
    "impact": impact,
    "riser": lambda r: riser(r, 1.5),
    "roar": roar,
    "seam_jet": seam_jet,
    "hull_creak": hull_creak,
    "tick": tick,
    "shimmer": shimmer,
}


def render(name: str) -> np.ndarray:
    # a stable seed per name: Python's hash() is salted per process, which would make every run different
    seed = int(hashlib.sha256(("the-descent/" + name).encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    x = RECIPES[name](rng)
    return S.fade_edges(S.normalise(x, 0.89), 5.0)


def write_wav(path: Path, x: np.ndarray) -> int:
    pcm = np.clip(x, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(S.SR)
        w.writeframes(pcm.tobytes())
    return path.stat().st_size


def sheet(rendered, path: Path):
    """A waveform contact sheet: one row per effect, so the set can be judged at a glance."""
    from PIL import Image, ImageDraw
    W, RH = 1100, 86
    img = Image.new("RGB", (W, RH * len(rendered) + 10), (6, 12, 16))
    d = ImageDraw.Draw(img)
    for i, (name, x) in enumerate(rendered):
        y0 = 5 + i * RH
        d.rectangle([0, y0, W, y0 + RH - 6], fill=(10, 20, 24))
        n = len(x); step = max(1, n // (W - 150))
        env = np.abs(x[:step * (W - 150)].reshape(-1, step)).max(axis=1)
        mid = y0 + (RH - 6) // 2
        for px, v in enumerate(env):
            h = int(v * (RH - 18) / 2)
            d.line([(150 + px, mid - h), (150 + px, mid + h)], fill=(63, 224, 208))
        d.text((10, mid - 6), f"{name}  {n / S.SR:.2f}s", fill=(242, 230, 207))
    img.save(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="render just these recipes")
    ap.add_argument("--sheet", action="store_true", help="also write a waveform contact sheet")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    names = a.only or list(RECIPES)
    bad = [n for n in names if n not in RECIPES]
    if bad:
        sys.exit(f"unknown recipe(s): {bad}; have {list(RECIPES)}")
    manifest, rendered = {}, []
    for n in names:
        x = render(n)
        size = write_wav(out / f"{n}.wav", x)
        manifest[n] = {"file": f"{n}.wav", "seconds": round(len(x) / S.SR, 3), "bytes": size,
                       "source": "procedural (scripts/ai/assetgen/sfx.py)", "licence": "ours", "sample_rate": S.SR}
        rendered.append((n, x))
        print(f"[sfx] {n:<12} {len(x) / S.SR:5.2f}s  {size / 1024:6.1f} KB")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if a.sheet:
        sp = REPO / "artifacts" / "canvas" / "sfx_sheet.png"
        sheet(rendered, sp)
        print(f"[sfx] sheet -> {sp.relative_to(REPO)}")
    print(f"[sfx] manifest -> {(out / 'manifest.json').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
