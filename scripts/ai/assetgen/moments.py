"""
moments.py - the sound of The Descent's MOMENTS, rendered offline, deterministically, to the storyboard's beats.

sfx.py renders one-shots. This module renders the two sequences the game is built around, plus a voice per symbol:

  help    the Leviathan's "help" (CREATURE_LIFELINE_STRIKE, strikeSeq) as STEMS that sum to the full cue:
          dread, approach, vacuum, impact, transform, aftermath  ->  help_<stem>.wav + help_full.wav
  win     the seam breach (WIN_EVALUATION -> CASCADE_DROP): crack, jet, implosion + scar hum, with a cascade-step
          parameter 1..5 that makes it heavier, denser and longer, never brighter  ->  win_s<step>_<stem>.wav
  sym     a land (<= 250 ms) and a win stinger (<= 700 ms) per symbol, one family: stone (LOW), brass (MID),
          wet and living (HIGH viper / angler / squid), the Leviathan (APEX) and the Wild Maw

    python scripts/ai/assetgen/moments.py --sheet            # everything -> generated/sfx/moments/ + three sheets
    python scripts/ai/assetgen/moments.py --only help --depth 5

Two timing profiles exist for the help cue. CODE is what strikeSeq really does today (bite at 1.70 s, wilds surface at
3.06 s); STORYBOARD is the 2.4 s beat sheet the frames are painted to. Files named help_* use CODE, help_sb_* use
STORYBOARD. Same recipes, same seeds: only the beat times differ.

Conventions as sfx.py: every sound seeds from its own name with SHA-256, 48 kHz 16-bit mono, a manifest.json with source
and licence. numpy + Pillow only. The slow per-sample filters in synth.py are not used here: filtering is done in the
frequency domain (static) or block-wise with overlap-add (sweeping), which is fast and still deterministic.
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
OUT = REPO / "generated" / "sfx" / "moments"
SHEETS = REPO / "artifacts" / "targets"
SR = S.SR
PEAK = 10 ** (-1.5 / 20)          # every file and the summed cue stay under -1 dBFS; we aim at -1.5
F32 = np.float32


# ====================================================================== fast DSP helpers =============================

def N(d):
    return int(max(1, round(d * SR)))


def seed_of(name):
    return int(hashlib.sha256(("the-descent/moments/" + name).encode()).hexdigest()[:8], 16)


def rng_of(name):
    return np.random.default_rng(seed_of(name))


def _H(kind, f0, q, nfft):
    """Complex response of the same RBJ biquad synth.biquad uses, on the rfft grid."""
    f0 = float(np.clip(f0, 20.0, SR * 0.45))
    w0 = 2 * np.pi * f0 / SR
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / (2 * q)
    if kind == "lowpass":
        b = ((1 - cw) / 2, 1 - cw, (1 - cw) / 2)
    elif kind == "highpass":
        b = ((1 + cw) / 2, -(1 + cw), (1 + cw) / 2)
    elif kind == "bandpass":
        b = (alpha, 0.0, -alpha)
    else:
        raise ValueError(kind)
    a = (1 + alpha, -2 * cw, 1 - alpha)
    z = np.exp(-2j * np.pi * np.fft.rfftfreq(nfft))
    return (b[0] + b[1] * z + b[2] * z * z) / (a[0] + a[1] * z + a[2] * z * z)


def ffilt(x, kind, f0, q=0.707, order=1):
    """Static biquad applied in the frequency domain (zero-padded, so no wrap-around). order = cascaded passes."""
    n = len(x)
    size = 1 << (n + SR // 2 - 1).bit_length()
    X = np.fft.rfft(x.astype(np.float64), size) * _H(kind, f0, q, size) ** order
    return np.fft.irfft(X, size)[:n].astype(F32)


def sfilt(x, kind, fcurve, q=0.707, win=1024):
    """A biquad whose cutoff follows fcurve: Hann blocks, each filtered at its centre frequency, overlap-added."""
    n = len(x)
    f = np.asarray(fcurve, dtype=np.float64)
    if len(f) < n:
        f = np.pad(f, (0, n - len(f)), mode="edge")
    hop, nfft = win // 2, 4 * win
    w = np.hanning(win + 1)[:-1]
    xp = np.concatenate([np.zeros(hop), x.astype(np.float64), np.zeros(win)])
    out = np.zeros(len(xp) + nfft)
    for s in range(0, len(xp) - win + 1, hop):
        blk = xp[s:s + win] * w
        if not blk.any():
            continue
        Hk = _H(kind, f[min(n - 1, s)], q, nfft)
        out[s:s + nfft] += np.fft.irfft(np.fft.rfft(blk, nfft) * Hk, nfft)
    return out[hop:hop + n].astype(F32)


def fnoise(dur, rng, colour="white"):
    """Unit-RMS noise; pink and brown are shaped in the frequency domain (no per-sample loop), nothing below 20 Hz."""
    n = N(dur)
    w = rng.standard_normal(n)
    if colour == "white":
        return w.astype(F32)
    X = np.fft.rfft(w)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1] if n > 1 else 1.0
    X *= (f / 1000.0) ** ({"pink": -0.5, "brown": -1.0}[colour])
    X[f < 20.0] = 0
    y = np.fft.irfft(X, n)
    return (y / (np.sqrt(np.mean(y * y)) + 1e-12)).astype(F32)


def modal(freqs, decays, amps, dur, rng=None, droop=0.0):
    """A struck body: decaying sine partials. droop bends every partial down by that fraction over the note: the
    family's 'sinking' signature."""
    t = S.t_of(dur).astype(np.float64)
    k = t / max(1e-6, dur)
    out = np.zeros(len(t))
    for i, (f, d, a) in enumerate(zip(freqs, decays, amps)):
        ph = 0.0 if rng is None else rng.random() * 0.6
        inst = f * (1 - droop * k)
        out += a * np.exp(-t / max(1e-4, d)) * np.sin(2 * np.pi * np.cumsum(inst) / SR + ph + i * 0.3)
    return out.astype(F32)


def ramp(dur, power=1.0, a=0.0, b=1.0):
    k = np.linspace(0, 1, N(dur), dtype=F32)
    return (a + (b - a) * k ** power).astype(F32)


def click(rng, ms, hp=2500.0, order=1):
    x = fnoise(ms / 1000, rng) * S.env(ms / 1000, 0.0004, ms / 1000 - 0.0004, 1.0, 1.4)
    return ffilt(np.pad(x, (0, N(0.004))), "highpass", hp, 0.707, order)


_IR = {}


def ir(kind):
    """Shared impulse responses (their own fixed seed) so every sound sits in the same flooded steel room."""
    if kind not in _IR:
        dur = {"short": 0.55, "long": 2.4}[kind]
        r = rng_of("ir/" + kind)
        n = N(dur)
        x = r.standard_normal(n) * (1 - np.linspace(0, 1, n)) ** 2.6
        x = sfilt(x.astype(F32), "lowpass", S.sweep(4000, 800, dur), 0.7)
        fade = N(0.02)
        x[:fade] *= np.linspace(0, 1, fade, dtype=F32)
        _IR[kind] = (x / np.sqrt(np.sum(x.astype(np.float64) ** 2))).astype(F32)   # unit energy: wet level is absolute
    return _IR[kind]


def verb(x, wet=0.25, kind="long", tail=0.0):
    """dry + wet * (x convolved with the unit-energy IR). Output length = len(x) + tail seconds."""
    if wet <= 0:
        return np.pad(x, (0, N(tail) if tail > 0 else 0))
    h = ir(kind)
    n = len(x) + len(h) - 1
    size = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(h, size), size)[:n]
    L = len(x) + (N(tail) if tail > 0 else 0)
    out = np.zeros(L, dtype=F32)
    out[:len(x)] = x
    m = min(L, n)
    out[:m] += (wet * y[:m]).astype(F32)
    return out


def put(buf, sig, start):
    """Add sig into buf at start seconds (clipped to the buffer)."""
    s = int(round(start * SR))
    if s >= len(buf) or s < 0:
        return buf
    m = min(len(buf) - s, len(sig))
    buf[s:s + m] += sig[:m]
    return buf


class Depth:
    """Depth level 0..5 as one argument: colder and cleaner at the top, heavier, darker and more driven at the bottom."""

    def __init__(self, d):
        self.d = d = int(max(0, min(5, d)))
        self.pitch = 2 ** (-0.5 * d / 12)      # body pitch sinks half a semitone per level
        self.drive = 1 + 0.2 * d                # tanh pre-gain (1 = clean)
        self.top = 16000.0 * 0.82 ** d          # the water closes over the top end: 16 k -> 5.9 k
        self.sub = 1 + 0.07 * d                 # more weight under the hits
        self.wet = 0.03 * d                     # a bigger, wetter room
        self.tail = 1 + 0.06 * d                # resonances ring longer

    def fx(self, x, drive=True, ref=1.0):
        """ref = the level the loudest layer was built at, so 'how driven' means the same for every sound."""
        if drive and self.d > 0:
            g = self.drive / ref
            x = (np.tanh(x * g) / g).astype(F32)                      # unity gain for quiet material, peaks fold over
        if self.top < 15900:
            x = ffilt(x, "lowpass", self.top, 0.707)
        return x


def thud(D, weight=0.5, f=80.0):
    """The family's body: every symbol lands on the same short pressure thud, scaled by its tier."""
    return S.osc(S.sweep(f * D.pitch, f * 0.55 * D.pitch, 0.09), 0.09) * S.env(0.09, 0.002, 0.086, weight * D.sub, 2.0)


# ====================================================================== the help cue =================================
# Beat times in seconds from the moment strikeSeq dims the board (levStrike). See docs/targets/sound_design_target.md.

BEATS_CODE = dict(name="code", dread=0.0, approach=0.80, vacuum=1.62, impact=1.70, transform=3.06, cell_gap=0.11,
                  recede=1.96, end=4.90, cells=4)
BEATS_STORYBOARD = dict(name="storyboard", dread=0.0, approach=0.60, vacuum=1.02, impact=1.10, transform=1.18,
                        cell_gap=0.10, recede=1.70, end=2.60, cells=4)
HELP_STEMS = ("dread", "approach", "vacuum", "impact", "transform", "aftermath")


def st_dread(rng, B, D, L):
    """H1: a sub swell you feel before you hear, and the eye opening: a low minor-second pair behind a slow lid of noise.
    It holds under the approach and is cut dead at the vacuum."""
    dur = B["vacuum"] - B["dread"]
    t = S.t_of(dur)
    ap = B["approach"] - B["dread"]
    rise = np.clip(t / ap, 0, 1) ** 1.8
    sub = (np.sin(2 * np.pi * 36 * D.pitch * t) + 0.6 * np.sin(2 * np.pi * 37.4 * D.pitch * t + 1.0)) * rise * 0.06 * D.sub
    f0 = 146.83 * D.pitch
    glide = 1 + 0.02 * np.clip(t / ap, 0, 1)
    ph = 2 * np.pi * np.cumsum(f0 * glide) / SR
    eye = np.sin(ph) + 0.8 * np.sin(ph * 1.0595 + 0.4) + 0.3 * np.sin(ph * 1.4983 + 1.1)
    open_env = np.where(t < ap, 0.15 + 0.85 * (t / ap) ** 1.3, 1.0 - 0.45 * (t - ap) / max(1e-6, dur - ap))
    eye = eye * open_env * (0.8 + 0.2 * np.sin(2 * np.pi * 0.9 * t)) * 0.09
    lid = sfilt(fnoise(dur, rng, "pink"), "lowpass", S.sweep(150, 750, dur), 0.9) * open_env * 0.05
    x = verb((sub + eye + lid).astype(F32), 0.25 + D.wet)[:len(t)]
    return put(np.zeros(L, dtype=F32), x, B["dread"])


def st_approach(rng, B, D, L):
    """H2: the frame strains. A bowed-metal creak whose pitch and stick-slip density both climb, pings as rivets let go,
    and a pressure noise that narrows upward. Everything accelerates into the vacuum."""
    dur = B["vacuum"] - B["approach"]
    n = N(dur)
    k = np.linspace(0, 1, n, dtype=F32)
    saw = S.osc(S.sweep(62 * D.pitch, 150 * D.pitch, dur), dur, "saw")
    creak = sfilt(saw, "bandpass", S.sweep(260, 1100, dur), 9.0) * 2.2
    stick = np.ones(n, dtype=F32)
    pings = np.zeros(n, dtype=F32)
    te = 0.03
    while te < dur - 0.02:
        kk = te / dur
        a = int(te * SR)
        b = min(n, a + N(0.004 + rng.random() * 0.010))
        stick[a:b] *= 0.2                                           # the groan stutters as the metal lets go
        pf = (420 + 1100 * kk) * (0.85 + 0.3 * rng.random()) * D.pitch
        pg = modal([pf, pf * 1.47, pf * 2.09], [0.03, 0.02, 0.012], [1, 0.5, 0.3], 0.08, rng) * (0.05 + 0.2 * kk)
        m = min(n - b, len(pg))
        if m > 0:
            pings[b:b + m] += pg[:m]
        te += (0.13 - 0.10 * kk) * (0.7 + 0.6 * rng.random())       # 130 ms apart at first, 30 ms at the end
    groan = S.osc(S.sweep(48 * D.pitch, 92 * D.pitch, dur), dur, "tri") * k ** 1.5 * 0.07
    press = sfilt(fnoise(dur, rng, "pink"), "bandpass", S.sweep(200, 2200, dur), 4.0) * k ** 1.6 * 0.5
    body = (creak * stick + pings + press) * (0.15 + 0.85 * k ** 1.4) * 0.75 + groan
    x = verb(body.astype(F32), 0.22 + D.wet)[:n]
    return put(np.zeros(L, dtype=F32), x, B["approach"])


def st_vacuum(rng, B, D, L):
    """The breath in: 140 ms of air being pulled out of the room, cut to nothing for the 80 ms before the impact.
    The stem is mostly silence on purpose: the dip is the sound."""
    dur = 0.14
    k = ramp(dur)
    suck = sfilt(fnoise(dur, rng), "highpass", S.sweep(600, 7000, dur), 0.9) * k ** 3 * 0.16
    tone = S.osc(S.sweep(70 * D.pitch, 210 * D.pitch, dur), dur) * k ** 2 * 0.22
    return put(np.zeros(L, dtype=F32), (suck + tone).astype(F32), B["vacuum"] - dur)


def st_impact(rng, B, D, L):
    """H3: the sea comes in. Click, a sub thump that is the loudest low-end event of the cue, a wall of water closing
    from 5 kHz to 170 Hz in half a second, struck hull plates and the creature's ring-modulated throat under it."""
    p = D.pitch
    dur = 2.0 * D.tail
    x = np.zeros(N(dur), dtype=F32)
    put(x, click(rng, 8, 2500) * 0.7, 0)
    put(x, S.osc(S.sweep(64 * p, 30 * p, 0.5), 0.95) * S.env(0.95, 0.004, 0.9, 1.25 * D.sub, 1.8), 0.002)
    put(x, S.osc(S.sweep(125 * p, 46 * p, 0.09), 0.12) * S.env(0.12, 0.002, 0.115, 0.6, 1.6), 0.0)
    body = sfilt(fnoise(0.6, rng), "lowpass", S.sweep(5200, 170, 0.5), 0.8) * S.env(0.6, 0.003, 0.58, 0.32, 1.9)
    put(x, body, 0.004)
    mass = ffilt(fnoise(1.4, rng, "brown"), "lowpass", 110, 0.7) * S.env(1.4, 0.03, 1.3, 0.16, 1.3)
    put(x, mass, 0.01)
    fr = np.array([187, 311, 523, 742, 1180]) * p
    put(x, modal(fr, np.array([0.5, 0.4, 0.3, 0.2, 0.12]) * D.tail, [1, 0.8, 0.6, 0.4, 0.25], 1.2, rng) * 0.13, 0.003)
    growl = ffilt(S.ring_mod(S.osc(45 * p, 0.9, "saw"), S.osc(31 * p, 0.9)), "lowpass", 600, 0.8)
    put(x, growl * S.env(0.9, 0.01, 0.88, 0.42, 1.5), 0.02)
    x = verb(x, 0.22 + D.wet, tail=1.0)
    return put(np.zeros(L, dtype=F32), x, B["impact"])


def cell_voice(rng, D, i=0):
    """H4, one struck cell: cold glass, not a chime. Inharmonic bar partials (1 : 2.756 : 5.404) with a beating twin,
    a soft 6 ms onset so it never 'dings', a breath of frost, and each next cell a semitone LOWER (never an arpeggio up)."""
    f0 = 2349.3 * 2 ** (-i / 12)
    dur = 0.7 * D.tail
    tone = modal([f0, f0 * 1.004, f0 * 2.756, f0 * 5.404], np.array([0.42, 0.38, 0.2, 0.09]) * D.tail,
                 [1, 0.7, 0.35, 0.12], dur, rng, droop=0.004)
    on = N(0.006)
    tone[:on] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, on))).astype(F32)
    if D.d > 0:                                                   # deeper = rougher: a little ring modulation
        tone = tone * (1 + 0.07 * D.d * S.osc(61.0, dur))
    frost = ffilt(fnoise(0.03, rng) * S.env(0.03, 0.004, 0.026, 1.0, 1.5), "highpass", 6000, 0.7) * 0.12
    x = tone * 0.13
    put(x, frost, 0.0)
    return x.astype(F32)


def st_transform(rng, B, D, L):
    x = np.zeros(L, dtype=F32)
    for i in range(B["cells"]):
        put(x, cell_voice(rng, D, i), B["transform"] + i * B["cell_gap"])
    x = verb(x, 0.3 + D.wet)[:L]
    return ffilt(x, "highpass", 1500, 0.707, order=3)             # it lives above the tail, by construction


def st_aftermath(rng, B, D, L):
    """H5: the water leaves (a falling wash, no bubbles), the plates keep ringing, and the creature goes down:
    one low tone falling an octave and more, with its throat faint behind it."""
    p = D.pitch
    dur = B["end"] - B["recede"]
    n = N(dur)
    drain = sfilt(fnoise(dur, rng, "pink"), "bandpass", S.sweep(1500, 220, dur), 1.2) * S.env(dur, 0.12, dur - 0.13, 0.42, 1.5)
    wash = sfilt(fnoise(dur, rng), "lowpass", S.sweep(3000, 300, dur * 0.6), 0.8) * S.env(dur, 0.05, dur * 0.6, 0.05, 2.0)
    ring = modal(np.array([311, 523, 742]) * p, np.array([1.0, 0.7, 0.4]) * D.tail, [1, 0.6, 0.35], dur, rng) * 0.035
    t = S.t_of(dur)
    fall = S.sweep(84 * p, 33 * p, dur) * (1 + 0.015 * np.sin(2 * np.pi * 4.0 * t))
    tone = S.osc(fall, dur) * S.env(dur, 0.08, dur * 0.9, 0.09, 1.3)
    growl = ffilt(S.ring_mod(S.osc(fall * 0.55, dur, "saw"), S.osc(31 * p, dur)), "lowpass", 300, 0.8)
    growl = growl * S.env(dur, 0.1, dur * 0.7, 0.07, 1.4)
    x = verb((drain + wash + ring + tone + growl)[:n].astype(F32), 0.28 + D.wet)[:n]
    x[-N(0.25):] *= np.linspace(1, 0, N(0.25), dtype=F32) ** 1.5
    return put(np.zeros(L, dtype=F32), x, B["recede"])


def edges(x, ms=5.0):
    """Fade both ends, then take out whatever DC is left WITHOUT lifting the ends off zero (the correction is shaped
    by the same fade window)."""
    w = S.fade_edges(np.ones(len(x), dtype=F32), ms)
    x = x.astype(F32) * w
    return (x - w * (float(np.sum(x)) / float(np.sum(w)))).astype(F32)


def finish(x, D, drive=True, hp=20.0, ref=1.0):
    """Common exit: no DC or subsonics (before and after the drive, which can add DC), and the depth colour."""
    x = D.fx(ffilt(x, "highpass", hp, 0.707), drive, ref)
    return ffilt(x, "highpass", hp, 0.707) if (drive and D.d > 0) else x


def help_cue(depth=2, B=BEATS_CODE, tag="help"):
    """Returns ({stem: array}, full). Stems share one gain, so they sum to the full mix exactly (before 16-bit rounding)."""
    D = Depth(depth)
    L = N(B["end"])
    fns = dict(dread=st_dread, approach=st_approach, vacuum=st_vacuum, impact=st_impact, transform=st_transform,
               aftermath=st_aftermath)
    stems = {}
    # nothing may sound inside the dip: the pre-impact stems are gated shut over the vacuum (3 ms ramp)
    gate = np.ones(L, dtype=F32)
    v0 = int(B["vacuum"] * SR)
    r = N(0.003)
    gate[v0 - r:v0] = np.linspace(1, 0, r, dtype=F32)
    gate[v0:] = 0
    for name in HELP_STEMS:
        x = fns[name](rng_of("help/" + name), B, D, L)      # the seed ignores depth and profile: only the design changes
        x = finish(x, D, drive=(name != "transform"), ref=(2.0 if name == "impact" else 1.0))
        if name == "transform":
            x = ffilt(x, "highpass", 1500, 0.707, order=2)
        if name in ("dread", "approach", "vacuum"):
            x = x * gate
        elif name == "impact":
            x[:int(B["impact"] * SR)] = 0                    # the filters' pre-roll must not leak into the dip
        stems[name] = edges(x)
    full = np.sum(list(stems.values()), axis=0).astype(F32)
    g = PEAK / max(float(np.max(np.abs(full))), max(float(np.max(np.abs(s))) for s in stems.values()))
    return {k: (v * g).astype(F32) for k, v in stems.items()}, (full * g).astype(F32)


# ====================================================================== the win seam cue =============================
# Real timings (index.html engSeam / WIN_EVALUATION / CASCADE_DROP, feel.js): the crack runs for 240 ms, the jets fire
# from 240 ms (one per winning column, 20 ms apart, 340 ms each), the highlight holds to 750 ms, then the symbols implode
# over explodeMs (480 ms x chainFactor) and the seam becomes a scar that glows for 2.6 s.

WIN_T = dict(crack=0.0, jet=0.24, implode=0.75, explode=0.48)
WIN_STEMS = ("crack", "jet", "implode")


def chain_factor(step):
    return 1.0 if step <= 3 else max(0.7, 1 - 0.08 * (step - 3))


def win_seam_raw(step, depth=2):
    """Escalation by cascade step: lower (1.5 semitones a step), denser (more fractures, more jets, more sub),
    longer (the scar hum hangs on). Nothing gets brighter and nothing resolves."""
    step = int(max(1, min(5, step)))
    D = Depth(depth)
    e = step - 1
    p = D.pitch * 2 ** (-1.5 * e / 12)
    f = chain_factor(step)
    hum_len = 0.7 + 0.2 * step
    t_thud = WIN_T["implode"] + 0.07
    L = N(t_thud + 0.1 + hum_len + 0.35)
    out = {}

    # W1 crack: hairline fractures, sparse then crowding toward the breach, over a thin glass-stress whine
    rng = rng_of("win/crack/%d" % step)
    x = np.zeros(L, dtype=F32)
    nclk = 5 + 3 * step
    times = np.sort(WIN_T["jet"] * rng.random(nclk) ** 0.6)
    for j, tc in enumerate(times):
        c = click(rng, 1.5 + 2.5 * rng.random(), 3500 * p ** 0.5, order=2)
        put(x, c * (0.18 + 0.3 * (j + 1) / nclk), float(tc))
    cd = WIN_T["jet"]
    whine = S.osc(S.sweep(3800 * p, 2900 * p, cd), cd) * ramp(cd, 2.0) * 0.035
    whine[-N(0.004):] *= np.linspace(1, 0, N(0.004), dtype=F32)
    put(x, whine, 0.0)
    put(x, S.osc(S.sweep(160 * p, 110 * p, 0.05), 0.05) * S.env(0.05, 0.002, 0.048, 0.10 + 0.03 * e, 2.0), 0.0)   # the glass ticks once, low
    out["crack"] = verb(x, 0.12 + D.wet, "short")[:L]

    # W2 breach: needles of pressurised water, one per winning column, and the pressure drop under them
    rng = rng_of("win/jet/%d" % step)
    x = np.zeros(L, dtype=F32)
    njet = 2 + step
    for qn in range(njet):
        jd = 0.34
        hi = 2600 * 2 ** (-e / 12) * (0.9 + 0.2 * rng.random())
        j = sfilt(fnoise(jd, rng), "bandpass", S.sweep(hi, hi * 0.35, jd), 1.4)
        put(x, j * S.env(jd, 0.012, jd - 0.014, 0.34 * (1 + 0.10 * e) / np.sqrt(njet), 1.5), WIN_T["jet"] + qn * 0.02)
    put(x, click(rng, 6, 2800, order=2) * (0.45 + 0.05 * e), WIN_T["jet"] - 0.002)
    put(x, S.osc(S.sweep(140 * p, 60 * p, 0.3), 0.3) * S.env(0.3, 0.005, 0.29, (0.30 + 0.07 * e) * D.sub, 2.0), WIN_T["jet"] + 0.004)
    hold = WIN_T["implode"] - WIN_T["jet"]
    hiss = ffilt(fnoise(hold, rng, "pink"), "bandpass", 1200 * p, 0.8) * S.env(hold, 0.08, hold - 0.09, 0.07 + 0.012 * e, 1.2)
    put(x, hiss, WIN_T["jet"])
    out["jet"] = verb(x, 0.18 + 0.02 * e + D.wet)[:L]

    # W3 implosion: 70 ms of suction, the crush (sub + a dull brass crunch, no ding), and the scar's hum
    rng = rng_of("win/implode/%d" % step)
    x = np.zeros(L, dtype=F32)
    t0 = WIN_T["implode"]
    sk = ramp(0.07)
    suck = sfilt(fnoise(0.07, rng), "lowpass", S.sweep(300, 2400, 0.07), 0.9) * sk ** 2.5 * 0.2
    suck[-N(0.003):] *= np.linspace(1, 0, N(0.003), dtype=F32)
    put(x, suck, t0)
    cl = (WIN_T["explode"] * f) - 0.07
    put(x, S.osc(S.sweep(110 * p, 46 * p, 0.14), cl) * S.env(cl, 0.003, cl - 0.004, (0.55 + 0.11 * e) * D.sub, 2.0), t_thud)
    cr = sfilt(fnoise(0.11, rng), "bandpass", S.sweep(900 * p, 250 * p, 0.11), 3.0) * S.env(0.11, 0.002, 0.105, 0.5 + 0.08 * e, 1.6)
    put(x, cr, t_thud)
    dust = modal(np.array([420, 660, 990]) * p, [0.05, 0.035, 0.02], [1, 0.6, 0.35], 0.12, rng) * (0.10 + 0.02 * e)
    put(x, dust, t_thud + 0.002)
    hd = hum_len
    th = S.t_of(hd)
    hf = 146.83 * p
    hum = (np.sin(2 * np.pi * hf * th) + 0.8 * np.sin(2 * np.pi * hf * 1.0595 * th + 0.7) + 0.3 * np.sin(2 * np.pi * hf * 1.4983 * th)
           + 0.5 * np.sin(2 * np.pi * hf * 0.5 * th + 0.2))
    put(x, (hum * S.env(hd, 0.08, hd - 0.09, 0.045 + 0.008 * e, 1.3)).astype(F32), t_thud + 0.03)
    out["implode"] = verb(x, 0.2 + 0.03 * e + D.wet)[:L]

    out = {k: edges(finish(v, D)) for k, v in out.items()}
    return out, np.sum(list(out.values()), axis=0).astype(F32)


def win_seams(depth=2, steps=(1, 3, 5)):
    """One gain for the whole ladder (set by step 5), so later steps really are louder, not just normalised the same."""
    raw = {s: win_seam_raw(s, depth) for s in sorted(set(steps) | {5})}
    top = max(float(np.max(np.abs(raw[5][1]))), max(float(np.max(np.abs(v))) for v in raw[5][0].values()))
    g = PEAK / top
    res = {}
    for s in steps:
        st, full = raw[s]
        m = max(float(np.max(np.abs(full))), max(float(np.max(np.abs(v))) for v in st.values())) * g
        gs = g if m <= PEAK else g * PEAK / m
        res[s] = ({k: (v * gs).astype(F32) for k, v in st.items()}, (full * gs).astype(F32))
    return res


# ====================================================================== symbol voices ================================
# One family: every land sits on the same pressure thud, every pitch comes from D minor (with the flat second for the
# creature), every stinger droops downward at the end, and everything is in the same short steel room.

LAND_MAX, STING_MAX = 0.25, 0.70
LOW_F = {"low_10": 440.0, "low_j": 392.0, "low_q": 349.23, "low_k": 329.63, "low_a": 293.66}   # A G F E D: worth more = lower


def v_low(key):
    def land(rng, D):
        f = LOW_F[key] * D.pitch
        x = np.zeros(N(0.2), dtype=F32)
        put(x, modal([f, f * 1.58, f * 2.21, f * 3.31], [0.045, 0.03, 0.02, 0.012], [1, 0.6, 0.4, 0.25], 0.15, rng) * 0.6, 0.001)
        put(x, ffilt(fnoise(0.012, rng) * S.env(0.012, 0.0005, 0.0115, 1, 1.5), "bandpass", 1800, 1.0) * 0.5, 0)
        put(x, thud(D, 0.45), 0)
        return verb(x, 0.10 + D.wet, "short")

    def sting(rng, D):
        f = LOW_F[key] * D.pitch
        x = np.zeros(N(0.42), dtype=F32)
        put(x, modal([f, f * 1.58, f * 2.21], [0.05, 0.03, 0.02], [1, 0.6, 0.4], 0.15, rng) * 0.5, 0)
        sc = sfilt(fnoise(0.17, rng, "pink"), "bandpass", S.sweep(520, 950, 0.17), 2.5)
        grains = np.repeat((rng.random(N(0.17) // 384 + 1) > 0.35).astype(F32), 384)[:len(sc)]   # stone dragging on stone
        put(x, sc * grains * ramp(0.17, 1.0, 0.3, 1.0) * 0.55, 0.03)
        f2 = f * 0.749
        put(x, modal([f2, f2 * 1.58, f2 * 2.21, f * 0.5], [0.07, 0.04, 0.025, 0.16], [1, 0.6, 0.4, 0.35], 0.22, rng, droop=0.03) * 0.75, 0.2)
        put(x, thud(D, 0.6), 0.2)
        return verb(x, 0.14 + D.wet, "short")
    return land, sting


BELL = [1, 2.0, 2.41, 3.02, 4.53, 5.9]


def helmet_land(rng, D):
    f = 196.0 * D.pitch
    b = modal([f * r for r in BELL], [0.12, 0.09, 0.07, 0.05, 0.03, 0.02], [1, 0.7, 0.5, 0.35, 0.2, 0.1], 0.2, rng)
    x = np.zeros(N(0.2), dtype=F32)
    put(x, (b * 0.3 + ffilt(b, "bandpass", 420, 2.0) * 0.5), 0.001)      # hollow: you hear the inside of it
    put(x, click(rng, 3, 1500) * 0.25, 0)
    put(x, thud(D, 0.55), 0)
    return verb(x, 0.12 + D.wet, "short")


def helmet_sting(rng, D):
    f = 196.0 * D.pitch
    b = modal([f * r for r in BELL], np.array([0.36, 0.27, 0.2, 0.14, 0.08, 0.05]) * D.tail, [1, 0.7, 0.5, 0.35, 0.2, 0.1], 0.6, rng, droop=0.03)
    x = np.zeros(N(0.62), dtype=F32)
    put(x, b * 0.3 + ffilt(b, "bandpass", 420, 2.0) * 0.5, 0.001)
    put(x, click(rng, 3, 1500) * 0.25, 0)
    put(x, thud(D, 0.65), 0)
    breath = ffilt(fnoise(0.55, rng, "pink"), "bandpass", 380, 5.0) * S.env(0.55, 0.09, 0.45, 0.5, 1.4)   # air moving inside the helmet
    put(x, breath, 0.04)
    return verb(x, 0.16 + D.wet, "short")


def compass_land(rng, D):
    f = 587.33 * D.pitch
    x = np.zeros(N(0.2), dtype=F32)
    bell = S.fm(f, f * 1.41, S.sweep(2.5, 0.05, 0.14), 0.14) * S.env(0.14, 0.001, 0.135, 0.45, 2.5)
    put(x, ffilt(bell, "lowpass", 3500, 0.7), 0.001)
    put(x, ffilt(fnoise(0.006, rng) * S.env(0.006, 0.0004, 0.0055, 1, 1.4), "bandpass", 2200, 6.0) * 1.2, 0)
    put(x, thud(D, 0.35), 0)
    return verb(x, 0.12 + D.wet, "short")


def compass_sting(rng, D):
    f = 293.66 * D.pitch
    x = np.zeros(N(0.62), dtype=F32)
    for tt, cf in ((0.0, 1800), (0.11, 1500), (0.26, 1250)):                # the needle swings, slows, settles
        put(x, ffilt(fnoise(0.01, rng) * S.env(0.01, 0.0004, 0.0095, 1, 1.4), "bandpass", cf, 8.0) * 1.6, tt)
    rd = 0.34
    ring = modal([f, f * 1.4983, f * 2.3784, f * 4.1], np.array([0.3, 0.24, 0.16, 0.06]) * D.tail, [1, 0.7, 0.4, 0.15], rd, rng, droop=0.03)
    trem = 0.75 + 0.25 * np.sin(2 * np.pi * np.cumsum(S.sweep(9, 4, rd, "lin")) / SR)
    put(x, ring * trem * 0.4, 0.26)
    put(x, thud(D, 0.5), 0.26)
    return verb(x, 0.16 + D.wet, "short")


def viper_land(rng, D):
    x = np.zeros(N(0.15), dtype=F32)
    snap = sfilt(fnoise(0.045, rng), "bandpass", S.sweep(2800, 1100, 0.045), 3.0) * S.env(0.045, 0.001, 0.044, 0.9, 2.0)
    put(x, click(rng, 2.5, 3000) * 0.6, 0)
    put(x, snap, 0.001)
    put(x, snap * 0.4, 0.012)                                               # the wet slap of the jaw closing
    put(x, thud(D, 0.22, 95), 0)
    return verb(x, 0.10 + D.wet, "short")


def viper_sting(rng, D):
    x = np.zeros(N(0.62), dtype=F32)
    tt = 0.0
    for j in range(7):                                                      # teeth: a chatter that accelerates
        c = ffilt(fnoise(0.005, rng) * S.env(0.005, 0.0004, 0.0045, 1, 1.4), "bandpass", 2400 * (1 - 0.04 * j), 5.0)
        put(x, c * (1.0 + 0.15 * j), tt)
        tt += 0.06 - 0.007 * j
    hd = 0.36
    hiss = sfilt(fnoise(hd, rng), "bandpass", S.sweep(5200, 1700, hd), 2.0) * S.env(hd, 0.03, hd - 0.04, 0.5, 1.6)
    put(x, hiss, 0.255)
    put(x, S.osc(S.sweep(196 * D.pitch, 146.83 * D.pitch, hd), hd) * S.env(hd, 0.03, hd - 0.04, 0.12, 1.5), 0.255)
    put(x, thud(D, 0.45, 95), 0.255)
    return verb(x, 0.14 + D.wet, "short")


def angler_land(rng, D):
    d = 0.2
    t = S.t_of(d)
    lure = S.osc(466.16 * D.pitch * (1 + 0.03 * np.sin(2 * np.pi * 14 * t)), d) * S.env(d, 0.004, d - 0.005, 0.4, 2.2)
    x = np.zeros(N(0.21), dtype=F32)
    put(x, ffilt(lure, "lowpass", 1800, 0.7), 0.002)
    put(x, click(rng, 2, 2000) * 0.2, 0)
    put(x, thud(D, 0.5), 0)
    return verb(x, 0.12 + D.wet, "short")


def angler_sting(rng, D):
    p = D.pitch
    x = np.zeros(N(0.64), dtype=F32)
    d = 0.5
    t = S.t_of(d)
    throb = (0.5 + 0.5 * np.sin(2 * np.pi * 5.5 * t - np.pi / 2)) ** 2          # the lure pulses
    hum = (np.sin(2 * np.pi * 220 * p * t) + 0.6 * np.sin(2 * np.pi * 349.23 * p * t + 0.5) + 0.25 * np.sin(2 * np.pi * 466.16 * p * t))
    env = np.minimum(1, t / 0.3) * np.minimum(1, (d - t) / 0.02)
    put(x, (hum * (0.35 + 0.65 * throb) * env * 0.22).astype(F32), 0)
    put(x, ffilt(fnoise(d, rng, "pink"), "bandpass", 700, 3.0) * env.astype(F32) * 0.3, 0)
    snap = sfilt(fnoise(0.06, rng), "bandpass", S.sweep(1500, 500, 0.06), 2.5) * S.env(0.06, 0.001, 0.058, 1.0, 1.8)
    put(x, click(rng, 3, 2500) * 0.6, 0.5)                                       # and the trap shuts
    put(x, snap, 0.501)
    put(x, thud(D, 0.75), 0.5)
    return verb(x, 0.16 + D.wet, "short")


def squid_land(rng, D):
    d = 0.2
    x = np.zeros(N(0.21), dtype=F32)
    put(x, ffilt(fnoise(d, rng, "pink"), "lowpass", 900, 0.8) * S.env(d, 0.05, 0.15, 0.45, 1.5), 0)       # the mantle pulses once
    put(x, S.osc(S.sweep(174.61 * D.pitch, 146.83 * D.pitch, d), d) * S.env(d, 0.04, 0.16, 0.2, 1.6), 0)
    put(x, thud(D, 0.3), 0.03)
    return verb(x, 0.14 + D.wet, "short")


def squid_sting(rng, D):
    p = D.pitch
    d = 0.6
    n = N(d)
    k = np.linspace(0, 1, n)
    fc = np.where(k < 0.35, 500 * (1900 / 500) ** (k / 0.35), 1900 * (420 / 1900) ** ((k - 0.35) / 0.65))
    ex = sfilt(fnoise(d, rng, "pink"), "bandpass", fc, 2.2) * S.env(d, 0.15, d - 0.16, 0.9, 1.5)        # one long breath out through the siphon
    mf = np.where(k < 0.3, 174.61 + (196 - 174.61) * (k / 0.3), 196 * (146.83 / 196) ** ((k - 0.3) / 0.7)) * p
    mf = mf * (1 + 0.012 * np.sin(2 * np.pi * 5 * k * d))
    moan = (S.osc(mf, d) + 0.3 * S.osc(mf * 1.5, d)) * (1 + 0.25 * S.osc(60.0, d)) * S.env(d, 0.12, d - 0.13, 0.22, 1.4)
    x = np.zeros(N(0.62), dtype=F32)
    put(x, ex, 0)
    put(x, moan.astype(F32), 0)
    return verb(x, 0.18 + D.wet, "short")


def lev_land(rng, D):
    p = D.pitch
    x = np.zeros(N(0.23), dtype=F32)
    put(x, S.osc(S.sweep(62 * p, 32 * p, 0.2), 0.22) * S.env(0.22, 0.004, 0.21, 1.0 * D.sub, 1.8), 0)
    g = ffilt(S.ring_mod(S.osc(45 * p, 0.2, "saw"), S.osc(31 * p, 0.2)), "lowpass", 500, 0.8) * S.env(0.2, 0.008, 0.19, 0.5, 1.6)
    put(x, g, 0.004)
    put(x, ffilt(fnoise(0.08, rng), "lowpass", 300, 0.8) * S.env(0.08, 0.002, 0.078, 0.35, 2.0), 0)
    return verb(x, 0.12 + D.wet, "short")


def lev_sting(rng, D):
    p = D.pitch
    d = 0.62
    x = np.zeros(N(0.64), dtype=F32)
    g = ffilt(S.ring_mod(S.osc(45 * p, d, "saw"), S.osc(31 * p, d)), "lowpass", 600, 0.8) * S.env(d, 0.04, d - 0.05, 0.55, 1.4)
    put(x, g, 0)
    put(x, S.osc(S.sweep(55 * p, 30 * p, 0.5), d) * S.env(d, 0.006, d - 0.01, 0.9 * D.sub, 1.7), 0)
    cl = ffilt(S.osc(S.sweep(73.42 * p, 69.3 * p, d), d, "tri") + S.osc(S.sweep(77.78 * p, 73.42 * p, d), d, "tri"), "lowpass", 400, 0.7)
    put(x, cl * S.env(d, 0.05, d - 0.06, 0.22, 1.3), 0)                           # D against Eb: the flat second is the creature
    put(x, ffilt(fnoise(d, rng, "brown"), "lowpass", 250, 0.7) * S.env(d, 0.06, d - 0.07, 0.12, 1.4), 0)
    return verb(x, 0.16 + D.wet, "short")


def maw_land(rng, D):
    p = D.pitch
    x = np.zeros(N(0.23), dtype=F32)
    sk = ramp(0.03)
    put(x, sfilt(fnoise(0.03, rng), "highpass", S.sweep(800, 5000, 0.03), 0.8) * sk ** 3 * 0.12, 0)     # 30 ms of nothing but a breath in
    put(x, click(rng, 6, 2000) * 0.7, 0.03)
    put(x, sfilt(fnoise(0.15, rng), "lowpass", S.sweep(3000, 200, 0.14), 0.8) * S.env(0.15, 0.002, 0.145, 0.4, 1.9), 0.032)
    put(x, S.osc(S.sweep(70 * p, 36 * p, 0.16), 0.18) * S.env(0.18, 0.003, 0.175, 0.95 * D.sub, 1.8), 0.032)
    return verb(x, 0.12 + D.wet, "short")


def maw_sting(rng, D):
    p = D.pitch
    x = np.zeros(N(0.64), dtype=F32)
    k = ramp(0.2)
    put(x, sfilt(fnoise(0.2, rng), "bandpass", S.sweep(400, 3200, 0.2), 2.0) * k ** 2.2 * 0.5, 0)       # the inhale
    put(x, S.osc(S.sweep(60 * p, 150 * p, 0.2), 0.2) * k ** 2 * 0.2, 0)
    x[N(0.2) - N(0.003):N(0.2)] *= np.linspace(1, 0, N(0.003), dtype=F32)
    x[N(0.2):] = 0                                                                 # 25 ms of nothing
    t0 = 0.225
    put(x, click(rng, 8, 2000) * 0.8, t0)
    put(x, sfilt(fnoise(0.3, rng), "lowpass", S.sweep(3500, 160, 0.28), 0.8) * S.env(0.3, 0.002, 0.29, 0.4, 1.9), t0 + 0.002)
    put(x, S.osc(S.sweep(64 * p, 30 * p, 0.36), 0.4) * S.env(0.4, 0.004, 0.39, 1.0 * D.sub, 1.7), t0 + 0.002)
    put(x, modal(np.array([187, 311, 523]) * p, [0.22, 0.16, 0.1], [1, 0.7, 0.5], 0.35, rng, droop=0.02) * 0.12, t0 + 0.003)
    return verb(x, 0.16 + D.wet, "short")


# name -> (tier, land fn, stinger fn, land peak dBFS, stinger peak dBFS). Worth more = louder, heavier.
SYMBOLS = {}
for _k in LOW_F:
    _l, _s = v_low(_k)
    SYMBOLS[_k] = ("LOW stone", _l, _s, -10.0, -8.0)
SYMBOLS.update({
    "mid_helmet": ("MID brass", helmet_land, helmet_sting, -8.5, -6.5),
    "mid_compass": ("MID brass", compass_land, compass_sting, -8.5, -6.5),
    "high_viper": ("HIGH living", viper_land, viper_sting, -7.0, -5.0),
    "high_angler": ("HIGH living", angler_land, angler_sting, -7.0, -5.0),
    "high_squid": ("HIGH living", squid_land, squid_sting, -7.0, -5.0),
    "apex_leviathan": ("APEX", lev_land, lev_sting, -4.0, -2.5),
    "wild_maw": ("WILD", maw_land, maw_sting, -3.0, -1.5),
})


def symbol_voice(key, kind, depth=2):
    tier, land, sting, pl, ps = SYMBOLS[key]
    D = Depth(depth)
    fn, mx, pk = (land, LAND_MAX, pl) if kind == "land" else (sting, STING_MAX, ps)
    x = finish(fn(rng_of("sym/%s/%s" % (key, kind)), D), D, hp=30.0)[:N(mx)]
    tail = N(0.03)
    x[-tail:] *= np.linspace(1, 0, tail, dtype=F32) ** 1.5       # the room is cut off inside the length budget
    x = edges(x, 4.5)
    return (x * (10 ** (pk / 20) / float(np.max(np.abs(x))))).astype(F32)


# ====================================================================== measurement ==================================

def db(v):
    return float(20 * np.log10(max(1e-10, v)))


def band(x, lo, hi):
    """Brick-wall band (analysis only)."""
    X = np.fft.rfft(x.astype(np.float64))
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def st_rms(x, win=0.05, hop=0.01):
    w, h = N(win), N(hop)
    c = np.concatenate([[0.0], np.cumsum(np.asarray(x, dtype=np.float64) ** 2)])
    idx = np.arange(0, max(1, len(x) - w), h)
    return idx / SR, np.sqrt((c[idx + w] - c[idx]) / w)


def metrics(x):
    xd = x.astype(np.float64)
    P = np.abs(np.fft.rfft(xd)) ** 2
    f = np.fft.rfftfreq(len(xd), 1 / SR)
    tot = float(P.sum()) + 1e-20
    thr = 10 ** (-60 / 20)
    return {
        "peak_dbfs": round(db(float(np.max(np.abs(xd)))), 2),
        "rms_dbfs": round(db(float(np.sqrt(np.mean(xd ** 2)))), 2),
        "seconds": round(len(x) / SR, 3),
        "centroid_hz": round(float((P * f).sum() / tot), 1),
        "sub_share_30_80": round(float(P[(f >= 30) & (f <= 80)].sum() / tot), 4),
        "dc": round(float(np.mean(xd)), 6),
        # a 4 ms fade exists if the first and last 4 ms never exceed a linear ramp to the file's own peak
        "edge_ok": bool(abs(xd[0]) < thr and abs(xd[-1]) < thr
                        and np.all(np.abs(xd[:N(0.004)]) <= np.linspace(0, 1, N(0.004)) * np.max(np.abs(xd)) + 1e-6)
                        and np.all(np.abs(xd[-N(0.004):]) <= np.linspace(1, 0, N(0.004)) * np.max(np.abs(xd)) + 1e-6)),
    }


def quant(x):
    """What is actually in the file: 16-bit."""
    return (np.clip(x, -1, 1) * 32767.0).astype("<i2")


def help_checks(stems, full, B):
    """The engineering targets for the help cue, as numbers."""
    imp, vac = B["impact"], B["vacuum"]
    t, e = st_rms(band(full, 30, 80))
    inwin = (t >= imp - 0.05) & (t <= imp + 0.6)
    pre = t + 0.05 <= vac
    post = t >= imp + 0.9
    sub_peak = float(e[inwin].max())
    dip = full[int((vac + 0.004) * SR):int((imp - 0.001) * SR)].astype(np.float64)
    before = full[int((vac - 0.1) * SR):int(vac * SR)].astype(np.float64)
    tr = stems["transform"].astype(np.float64)
    P = np.abs(np.fft.rfft(tr)) ** 2
    f = np.fft.rfftfreq(len(tr), 1 / SR)
    a = int(B["transform"] * SR)
    b = int(min(len(full) / SR, B["transform"] + B["cells"] * B["cell_gap"] + 0.35) * SR)
    rest = (full - stems["transform"])[a:b]
    trw = stems["transform"][a:b]
    hi_tr = float(np.sqrt(np.mean(band(trw, 1500, 12000) ** 2)))
    hi_rest = float(np.sqrt(np.mean(band(rest, 1500, 12000) ** 2)))
    qsum = np.sum([quant(s).astype(np.int64) for s in stems.values()], axis=0)
    return {
        "profile": B["name"],
        "full_peak_dbfs": round(db(float(np.max(np.abs(full)))), 2),
        "sub_peak_time_s": round(float(t[np.argmax(e)]) + 0.025, 3),
        "sub_peak_in_impact_window": bool(inwin[np.argmax(e)]),
        "sub_peak_dbfs_30_80": round(db(sub_peak), 2),
        "sub_margin_vs_before_db": round(db(sub_peak) - db(float(e[pre].max())), 2),
        "sub_margin_vs_after_db": round(db(sub_peak) - db(float(e[post].max())), 2) if post.any() else None,
        "sub_margin_vs_other_stems_db": round(db(sub_peak) - db(float(st_rms(band(full - stems["impact"], 30, 80))[1].max())), 2),
        "vacuum_ms": round((imp - vac) * 1000),
        "vacuum_rms_dbfs": round(db(float(np.sqrt(np.mean(dip ** 2)))), 1),
        "pre_vacuum_rms_dbfs": round(db(float(np.sqrt(np.mean(before ** 2)))), 1),
        "vacuum_peak_dbfs": round(db(float(np.max(np.abs(dip)))), 1),
        "transform_energy_above_1k5": round(float(P[f >= 1500].sum() / (P.sum() + 1e-20)), 4),
        "transform_centroid_hz": round(float((P * f).sum() / (P.sum() + 1e-20)), 1),
        "transform_vs_rest_above_1k5_db": round(db(hi_tr) - db(hi_rest), 2),
        "stems_sum_max_error_lsb": int(np.max(np.abs(qsum - quant(full).astype(np.int64)))),
    }


# ====================================================================== files and sheets =============================

def write_wav(path, x):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(quant(x).tobytes())
    return path.stat().st_size


BG, PANEL, CYAN, CREAM, DIM, AMBER = (6, 12, 16), (10, 20, 24), (63, 224, 208), (242, 230, 207), (110, 140, 146), (232, 176, 74)


def font(size, bold=False):
    from PIL import ImageFont
    for name in (("consolab.ttf", "arialbd.ttf", "DejaVuSansMono-Bold.ttf") if bold else ("consola.ttf", "arial.ttf", "DejaVuSansMono.ttf")):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_wave(d, x, box, colour=CYAN, scale=None):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=PANEL)
    w = x1 - x0
    mid = (y0 + y1) // 2
    sc = scale or (float(np.max(np.abs(x))) + 1e-9)
    edges = np.linspace(0, len(x), w + 1).astype(int)
    for px in range(w):
        seg = x[edges[px]:max(edges[px] + 1, edges[px + 1])]
        hi = int(float(seg.max()) / sc * (y1 - y0 - 6) / 2)
        lo = int(float(seg.min()) / sc * (y1 - y0 - 6) / 2)
        d.line([(x0 + px, mid - hi), (x0 + px, mid - lo)], fill=colour)
    d.line([(x0, mid), (x1, mid)], fill=(24, 60, 64))


def spectro(x, w, h, fmin=25.0, fmax=20000.0, win=4096, floor=-78.0):
    """Log-frequency spectrogram as an RGB array (h, w, 3): black -> teal -> cyan -> cream."""
    from PIL import Image
    xp = np.concatenate([np.zeros(win // 2), x.astype(np.float64), np.zeros(win)])
    cen = np.linspace(0, len(x) - 1, w).astype(int)
    hann = np.hanning(win)
    frames = np.stack([xp[c:c + win] * hann for c in cen])
    mag = np.abs(np.fft.rfft(frames, axis=1)) / (win / 4)
    fr = fmin * (fmax / fmin) ** np.linspace(1, 0, h)
    pos = fr / (SR / win)
    i0 = np.clip(np.floor(pos).astype(int), 0, mag.shape[1] - 2)
    fracs = (pos - i0)[None, :]
    m = mag[:, i0] * (1 - fracs) + mag[:, i0 + 1] * fracs
    v = np.clip((20 * np.log10(m + 1e-9) - floor) / (-6.0 - floor), 0, 1).T          # (h, w)
    stops = np.array([0, 0.45, 0.8, 1.0])
    cols = np.array([BG, (16, 96, 108), CYAN, (250, 246, 232)], dtype=np.float64)
    rgb = np.stack([np.interp(v, stops, cols[:, c]) for c in range(3)], axis=-1)
    return Image.fromarray(rgb.astype(np.uint8))


def freq_ticks(d, box, fmin, fmax, f_small, ticks=(50, 100, 200, 500, 1000, 2000, 5000, 10000)):
    x0, y0, x1, y1 = box
    for f in ticks:
        if not fmin < f < fmax:
            continue
        y = y0 + (y1 - y0) * (1 - np.log(f / fmin) / np.log(fmax / fmin))
        d.line([(x0 - 5, y), (x0, y)], fill=DIM)
        d.text((x0 - 8, y), ("%dk" % (f // 1000)) if f >= 1000 else str(f), fill=DIM, font=f_small, anchor="rm")


def timeline_panel(img, origin, width, title, rows, full, beats, dur, checks=None, row_h=78, spec_h=250, gutter=170):
    """Rows of stem waveforms, the full mix, its spectrogram; beats as labelled vertical lines through everything."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    fb, fs, fl = font(20, True), font(13), font(15, True)
    ox, oy = origin
    x0, x1 = ox + gutter, ox + width - 14
    tx = lambda t: x0 + (x1 - x0) * t / dur
    d.text((ox + 8, oy), title, fill=CREAM, font=fb)
    top = oy + 34 + 20 * 3
    y = top
    boxes = []
    for name, x in rows:
        box = (x0, y, x1, y + row_h - 8)
        draw_wave(d, x, box)
        d.text((ox + 8, y + 12), name, fill=CREAM, font=fl)
        d.text((ox + 8, y + 34), "peak %.1f dBFS" % db(float(np.max(np.abs(x)))), fill=DIM, font=fs)
        boxes.append(box)
        y += row_h
    box = (x0, y, x1, y + int(row_h * 1.5) - 8)
    draw_wave(d, full, box, colour=(160, 245, 235), scale=1.0)
    d.text((ox + 8, y + 12), "FULL MIX", fill=CREAM, font=fl)
    d.text((ox + 8, y + 34), "peak %.1f dBFS" % db(float(np.max(np.abs(full)))), fill=DIM, font=fs)
    d.text((ox + 8, y + 52), "scale = 0 dBFS", fill=DIM, font=fs)
    y += int(row_h * 1.5)
    sp = spectro(full, x1 - x0, spec_h)
    img.paste(sp, (x0, y))
    d.text((ox + 8, y + 12), "SPECTROGRAM", fill=CREAM, font=fl)
    d.text((ox + 8, y + 34), "log f 25 Hz-20k", fill=DIM, font=fs)
    freq_ticks(d, (x0, y, x1, y + spec_h), 25.0, 20000.0, fs)
    bottom = y + spec_h
    for i, (lab, t, desc) in enumerate(beats):
        xx = tx(t)
        d.line([(xx, top - 6), (xx, bottom)], fill=AMBER, width=1)
        ly = oy + 34 + 20 * (i % 3)
        d.line([(xx, ly + 8), (xx, top - 6)], fill=(120, 92, 40), width=1)
        d.text((xx + 4, ly), "%s %s  %d ms" % (lab, desc, round(t * 1000)), fill=AMBER, font=fs)
    step = 0.5 if dur > 3 else 0.25
    tt = 0.0
    while tt <= dur + 1e-6:
        d.line([(tx(tt), bottom), (tx(tt), bottom + 5)], fill=DIM)
        d.text((tx(tt), bottom + 8), "%.2fs" % tt, fill=DIM, font=fs, anchor="ma")
        tt += step
    yy = bottom + 30
    if checks:
        for line in checks:
            d.text((ox + 8, yy), line, fill=CREAM, font=fs)
            yy += 18
    return yy


def help_beats(B):
    c = B["name"] == "code"
    b = [("H0/H1", B["dread"], "DREAD"), ("H2", B["approach"], "APPROACH"), ("V", B["vacuum"], "VACUUM"),
         ("H3", B["impact"], "IMPACT"), ("H4", B["transform"], "TRANSFORM"), ("H5", B["recede"], "AFTERMATH" if not c else "RECEDE/DRAIN")]
    return sorted(b, key=lambda r: r[1])


def help_sheet(path, stems, full, B, chk, depth):
    from PIL import Image
    W = 1800
    H = 34 + 60 + 78 * 6 + 117 + 250 + 30 + 18 * 5 + 30
    img = Image.new("RGB", (W, H), BG)
    lines = [
        "sub 30-80 Hz (50 ms RMS): peak %.1f dBFS at %.3f s (impact at %.2f s)  |  +%.1f dB over anything before it, +%.1f dB over every other stem, +%.1f dB over the cue from 0.9 s after" % (
            chk["sub_peak_dbfs_30_80"], chk["sub_peak_time_s"], B["impact"], chk["sub_margin_vs_before_db"], chk["sub_margin_vs_other_stems_db"], chk["sub_margin_vs_after_db"] or 0),
        "vacuum: %d ms at %.1f dBFS RMS (the 100 ms before it: %.1f dBFS)" % (chk["vacuum_ms"], chk["vacuum_rms_dbfs"], chk["pre_vacuum_rms_dbfs"]),
        "transformation: %.1f%% of its energy above 1.5 kHz, centroid %.0f Hz, %+.1f dB against the rest of the mix above 1.5 kHz in its window" % (
            100 * chk["transform_energy_above_1k5"], chk["transform_centroid_hz"], chk["transform_vs_rest_above_1k5_db"]),
        "full mix peak %.2f dBFS  |  stems sum to the full mix within %d LSB (16-bit)" % (chk["full_peak_dbfs"], chk["stems_sum_max_error_lsb"]),
        "MEASURED, NOT HEARD: a human listen is still required.",
    ]
    title = "THE HELP CUE  (CREATURE_LIFELINE_STRIKE)  -  timing profile: %s  -  depth %d  -  rows autoscaled, peak printed" % (B["name"].upper(), depth)
    timeline_panel(img, (0, 10), W, title, [(n.upper(), stems[n]) for n in HELP_STEMS], full, help_beats(B), B["end"], lines)
    img.save(path)


def win_sheet(path, seams):
    from PIL import Image, ImageDraw
    steps = sorted(seams)
    dur = max(len(seams[s][1]) for s in steps) / SR
    W, pw = 1860, 620
    H = 34 + 60 + 78 * 3 + 117 + 250 + 30 + 18 * 4 + 40
    img = Image.new("RGB", (W, H), BG)
    for i, s in enumerate(steps):
        st, full = seams[s]
        pad = lambda v: np.pad(v, (0, N(dur) - len(v))) if len(v) < N(dur) else v
        f = chain_factor(s)
        beats = [("W1", WIN_T["crack"], "CRACK"), ("W2", WIN_T["jet"], "BREACH"), ("W3", WIN_T["implode"], "IMPLODE")]
        m = metrics(full)
        lines = ["peak %.1f dBFS  RMS %.1f dBFS  %.2f s" % (m["peak_dbfs"], m["rms_dbfs"], m["seconds"]),
                 "centroid %.0f Hz  sub share %.1f%%" % (m["centroid_hz"], 100 * m["sub_share_30_80"]),
                 "explode budget %d ms (chainFactor %.2f)" % (round(WIN_T["explode"] * f * 1000), f)]
        timeline_panel(img, (i * pw, 10), pw, "WIN SEAM - cascade step %d" % s, [(n.upper(), pad(st[n])) for n in WIN_STEMS],
                       pad(full), beats, dur, lines, gutter=150)
    ImageDraw.Draw(img).text((8, H - 24), "Same time axis and one shared gain across the three steps: later steps are lower, denser, longer and louder. "
                             "MEASURED, NOT HEARD.", fill=CREAM, font=font(13))
    img.save(path)


def symbols_sheet(path, voices):
    from PIL import Image, ImageDraw
    keys = list(SYMBOLS)
    cols, cw, ch = 3, 620, 268
    rows = (len(keys) + cols - 1) // cols
    img = Image.new("RGB", (cols * cw, rows * ch + 40), BG)
    d = ImageDraw.Draw(img)
    fb, fs = font(17, True), font(12)
    for i, k in enumerate(keys):
        ox, oy = (i % cols) * cw, (i // cols) * ch + 6
        land, sting = voices[k]
        d.text((ox + 10, oy), "%s   [%s]" % (k.upper(), SYMBOLS[k][0]), fill=CREAM, font=fb)
        x0 = ox + 44
        avail = cw - 44 - 30
        lw = int(avail * LAND_MAX / (LAND_MAX + STING_MAX))
        for j, (nm, x, bx, bw, mx) in enumerate((("LAND", land, x0, lw, LAND_MAX), ("STINGER", sting, x0 + lw + 14, avail - lw, STING_MAX))):
            xx = np.pad(x, (0, max(0, N(mx) - len(x))))
            m = metrics(x)
            d.text((x0, oy + 24 + 16 * j), "%-7s %3d ms   peak %5.1f dBFS   rms %5.1f   centroid %5.0f Hz   sub %2.0f%%" % (
                nm, round(m["seconds"] * 1000), m["peak_dbfs"], m["rms_dbfs"], m["centroid_hz"], 100 * m["sub_share_30_80"]), fill=DIM, font=fs)
            d.text((bx + 4, oy + 62), nm, fill=AMBER, font=fs)
            draw_wave(d, xx, (bx, oy + 60, bx + bw, oy + 130), scale=1.0)
            d.text((bx + 4, oy + 62), nm, fill=AMBER, font=fs)
            img.paste(spectro(xx, bw, 110, fmin=40.0, fmax=16000.0, win=2048), (bx, oy + 136))
        freq_ticks(d, (x0, oy + 136, x0, oy + 246), 40.0, 16000.0, fs, ticks=(100, 1000, 10000))
    d.text((10, rows * ch + 14), "Per symbol: land (<= 250 ms) and win stinger (<= 700 ms). Waveforms on a 0 dBFS scale (so tiers compare), "
           "spectrograms log f 40 Hz-16 kHz. MEASURED, NOT HEARD.", fill=CREAM, font=font(13))
    img.save(path)


# ====================================================================== main =========================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", choices=["help", "win", "symbols"], help="render just these groups")
    ap.add_argument("--sheet", action="store_true", help="also write the timeline / spectrogram sheets")
    ap.add_argument("--depth", type=int, default=2, help="depth level 0..5 for the main render (default 2)")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    groups = a.only or ["help", "win", "symbols"]
    manifest, report = {}, {}
    mpath = out / "manifest.json"
    if a.only and mpath.exists():
        manifest = json.loads(mpath.read_text(encoding="utf-8"))
    if a.only and (out / "report.json").exists():
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))

    def emit(name, x, group, **extra):
        size = write_wav(out / (name + ".wav"), x)
        q = quant(x).astype(np.float64) / 32767.0
        e = {"file": name + ".wav", "group": group, "bytes": size, "source": "procedural (scripts/ai/assetgen/moments.py)",
             "licence": "ours", "sample_rate": SR, "bit_depth": 16, "channels": 1,
             "sha256": hashlib.sha256((out / (name + ".wav")).read_bytes()).hexdigest()}
        e.update(metrics(q)); e.update(extra)
        manifest[name] = e
        print("[moments] %-26s %5.2fs  pk %6.2f  rms %6.2f  cen %7.0f Hz  sub %5.1f%%  dc %+.5f  edges %s" % (
            name, e["seconds"], e["peak_dbfs"], e["rms_dbfs"], e["centroid_hz"], 100 * e["sub_share_30_80"], e["dc"], "ok" if e["edge_ok"] else "FAIL"))

    if a.sheet:
        SHEETS.mkdir(parents=True, exist_ok=True)

    if "help" in groups:
        for B, tag in ((BEATS_CODE, "help"), (BEATS_STORYBOARD, "help_sb")):
            stems, full = help_cue(a.depth, B, tag)
            starts = dict(dread=B["dread"], approach=B["approach"], vacuum=B["vacuum"] - 0.14, impact=B["impact"],
                          transform=B["transform"], aftermath=B["recede"])
            for n in HELP_STEMS:
                emit("%s_%s" % (tag, n), stems[n], tag, depth=a.depth, profile=B["name"], beat_offset_s=round(starts[n], 3))
            emit(tag + "_full", full, tag, depth=a.depth, profile=B["name"], beat_offset_s=0.0)
            report[tag] = help_checks(stems, full, B)
            print("[moments] checks %s: %s" % (tag, json.dumps(report[tag])))
            if a.sheet:
                sp = SHEETS / ("sound_help_sheet.png" if tag == "help" else "sound_help_sheet_storyboard.png")
                help_sheet(sp, stems, full, B, report[tag], a.depth)
                print("[moments] sheet -> %s" % sp.relative_to(REPO))
        for dv in (0, 5):                                                     # the depth ladder's two ends, full mix only
            stems, full = help_cue(dv, BEATS_CODE, "help")
            emit("help_full_d%d" % dv, full, "help_depth", depth=dv, profile="code", beat_offset_s=0.0)
            report["help_d%d" % dv] = help_checks(stems, full, BEATS_CODE)
        D = Depth(a.depth)                                                    # the one-shot the runtime fires per struck cell
        cv = finish(verb(cell_voice(rng_of("help/transform_cell"), D, 0), 0.3 + D.wet, tail=0.25), D, drive=False)
        cv = ffilt(cv, "highpass", 1500, 0.707, order=3)
        cv[-N(0.1):] *= np.linspace(1, 0, N(0.1), dtype=F32)
        cv = edges(cv)
        emit("help_transform_cell", (cv * (10 ** (-9 / 20) / float(np.max(np.abs(cv))))).astype(F32), "help", depth=a.depth, profile="any")

    if "win" in groups:
        seams = win_seams(a.depth, (1, 3, 5))
        for s, (st, full) in seams.items():
            for n in WIN_STEMS:
                emit("win_s%d_%s" % (s, n), st[n], "win", depth=a.depth, cascade_step=s, beat_offset_s=WIN_T[n])
            emit("win_s%d_full" % s, full, "win", depth=a.depth, cascade_step=s, beat_offset_s=0.0)
        if a.sheet:
            win_sheet(SHEETS / "sound_win_sheet.png", seams)
            print("[moments] sheet -> artifacts/targets/sound_win_sheet.png")

    if "symbols" in groups:
        voices = {}
        for k in SYMBOLS:
            land, sting = symbol_voice(k, "land", a.depth), symbol_voice(k, "stinger", a.depth)
            voices[k] = (land, sting)
            emit("sym_%s_land" % k, land, "symbols", depth=a.depth, tier=SYMBOLS[k][0])
            emit("sym_%s_stinger" % k, sting, "symbols", depth=a.depth, tier=SYMBOLS[k][0])
        if a.sheet:
            symbols_sheet(SHEETS / "sound_symbols_sheet.png", voices)
            print("[moments] sheet -> artifacts/targets/sound_symbols_sheet.png")

    mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    bad = [k for k, e in manifest.items() if e["peak_dbfs"] > -1.0 or abs(e["dc"]) > 1e-3 or not e["edge_ok"]]
    print("[moments] %d files, manifest -> %s%s" % (len(manifest), mpath.relative_to(REPO) if mpath.is_relative_to(REPO) else mpath,
                                                    "" if not bad else "   TARGETS MISSED: %s" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
