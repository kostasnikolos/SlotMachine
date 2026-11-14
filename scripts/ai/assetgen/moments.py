"""
moments.py - the sound of The Descent's MOMENTS, rendered offline, deterministically, to the storyboard's beats.

sfx.py renders one-shots. This module renders the two sequences the game is built around, plus a voice per symbol:

  help    the Leviathan's "help" (CREATURE_LIFELINE_STRIKE, strikeSeq) as STEMS that sum to the mix:
          dread, targeting, vacuum, impact, transform, aftermath
          in two lengths: FULL (3.1 s, first time)  -> help_full_<stem>.wav  + help_full_mix.wav
                          SHORT (1.7 s, repeats)    -> help_short_<stem>.wav + help_short_mix.wav
  win     the seam breach (WIN_EVALUATION -> CASCADE_DROP): crack, jet, implosion + scar hum, with a cascade-step
          parameter 1..5 that makes it heavier, denser and longer  ->  win_s<step>_<stem>.wav
  sym     three round-robin lands (<= 250 ms) and a win stinger (<= 700 ms) per symbol, one family: stone (LOW),
          brass (MID), wet and living (HIGH viper / angler / squid), the Leviathan (APEX) and the Wild Maw

    python scripts/ai/assetgen/moments.py --sheet            # everything -> generated/sfx/moments/ + four sheets
    python scripts/ai/assetgen/moments.py --only help --depth 5

The help's beat times are the ones the engine is being re-timed to (docs/targets/sound_design_target.md); they are a
table (BEATS_FULL, BEATS_SHORT), so a re-time is a one-line change.

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
# Beat times in seconds from the first frame of the sequence. FULL is the first-time version, SHORT the repeat / xBet
# one. recede = where the creature starts to go down (under the transformation), drain = where the water leaves.

# Cell and recede offsets are the game's own (strikePace in the canvas front end): first cell 200 / 150 ms after the bite,
# cells 110 / 70 ms apart, the recede 60 ms after the first cell. last_ring = how long the weighted last cell rings.
BEATS_FULL = dict(name="full", dread=0.0, approach=0.90, vacuum=1.42, impact=1.50, transform=1.70, cell_gap=0.11,
                  recede=1.76, drain=2.30, end=3.10, cells=4, last_ring=1.7)
BEATS_SHORT = dict(name="short", dread=0.0, approach=0.35, vacuum=0.64, impact=0.70, transform=0.85, cell_gap=0.07,
                   recede=0.91, drain=1.25, end=1.70, cells=4, last_ring=0.75)
HELP_STEMS = ("dread", "targeting", "vacuum", "impact", "transform", "aftermath")
MINOR = (0, 2, 3, 5, 7, 8, 10, 12, 14, 15)
CELL_BASE = 1975.53            # B6: every struck cell is above 1.5 kHz


def turbulence(dur, rng, rate=18.0):
    """A slow random 0..1 curve: water moving, not a tremolo."""
    x = ffilt(fnoise(dur, rng), "lowpass", rate, 0.707, order=2)
    return (0.5 + 0.5 * x / (np.max(np.abs(x)) + 1e-9)).astype(F32)


def st_dread(rng, B, D, L):
    """H1: the eye opens. Underneath, a sub swell you feel on real speakers. On top, so a phone has something to follow,
    a slow bowed-metal tone: D4 against Eb4 with ringing partials up to 1.2 kHz, each breathing at its own rate.
    It holds under the targeting and is cut dead at the vacuum."""
    dur = B["vacuum"] - B["dread"]
    t = S.t_of(dur)
    ap = B["approach"] - B["dread"]
    rise = np.clip(t / ap, 0, 1) ** 1.8
    sub = (np.sin(2 * np.pi * 36 * D.pitch * t) + 0.6 * np.sin(2 * np.pi * 37.4 * D.pitch * t + 1.0)) * rise * 0.06 * D.sub
    f0 = 146.83 * D.pitch
    glide = 1 + 0.02 * np.clip(t / ap, 0, 1)
    ph = 2 * np.pi * np.cumsum(f0 * glide) / SR
    eye = np.sin(ph) + 0.8 * np.sin(ph * 1.0595 + 0.4) + 0.3 * np.sin(ph * 1.4983 + 1.1)
    open_env = np.where(t < ap, 0.15 + 0.85 * (t / ap) ** 1.3, 1.0 - 0.35 * (t - ap) / max(1e-6, dur - ap))
    eye = eye * open_env * (0.8 + 0.2 * np.sin(2 * np.pi * 0.9 * t)) * 0.09
    # the layer a small speaker can carry: bowed metal, 294 Hz - 1.2 kHz
    bow = np.zeros(len(t))
    for i, (r, a) in enumerate(((2.0, 1.0), (2.119, 0.8), (4.0, 0.55), (5.52, 0.4), (8.14, 0.22))):
        lfo = 0.65 + 0.35 * np.sin(2 * np.pi * (1.7 + 0.9 * i) * t + rng.random() * 6.283)
        bow += a * lfo * np.sin(ph * r + rng.random() * 6.283)
    bow = bow * open_env * 0.125
    lid = sfilt(fnoise(dur, rng, "pink"), "bandpass", S.sweep(300, 1300, dur), 0.9) * open_env * 0.15
    x = verb((sub + eye + bow + lid).astype(F32), 0.25 + D.wet)[:len(t)]
    return put(np.zeros(L, dtype=F32), x, B["dread"])


def st_targeting(rng, B, D, L):
    """H2: the pupil snaps onto the strike cell (one dry 'tok'), the water over that cell starts to churn, and the glass
    bows inward: a bowed, high, narrow strain whose stick-slip ticks crowd together into the vacuum."""
    dur = B["vacuum"] - B["approach"]
    n = N(dur)
    k = np.linspace(0, 1, n, dtype=F32)
    x = np.zeros(n, dtype=F32)
    # the lock: a click and a short damped knock, no pitch to speak of
    put(x, click(rng, 3, 1800) * 0.4, 0)
    put(x, modal(np.array([620, 930, 1480]) * D.pitch, [0.035, 0.025, 0.015], [1, 0.7, 0.4], 0.09, rng) * 0.28, 0.001)
    # churn: water moving over the cell, 350 Hz -> 1.4 kHz, turbulent, rising
    churn = sfilt(fnoise(dur, rng, "pink"), "bandpass", S.sweep(350, 1400, dur), 1.2)
    x += churn * (0.25 + 0.75 * turbulence(dur, rng)) * (0.2 + 0.8 * k ** 1.3) * 0.5
    # the glass bows: a narrow bowed strain climbing, letting go more and more often
    saw = S.osc(S.sweep(196 * D.pitch, 262 * D.pitch, dur), dur, "saw")
    bowed = sfilt(saw, "bandpass", S.sweep(700, 1500, dur), 12.0) * 2.4
    stick = np.ones(n, dtype=F32)
    ticks = np.zeros(n, dtype=F32)
    te = 0.05
    while te < dur - 0.02:
        kk = te / dur
        a = int(te * SR)
        b = min(n, a + N(0.004 + rng.random() * 0.008))
        stick[a:b] *= 0.2
        pf = (1800 + 1400 * rng.random()) * D.pitch
        pg = modal([pf, pf * 2.756], [0.014, 0.008], [1, 0.4], 0.05, rng) * (0.06 + 0.2 * kk)
        m = min(n - b, len(pg))
        if m > 0:
            ticks[b:b + m] += pg[:m]
        te += (0.12 - 0.09 * kk) * (0.7 + 0.6 * rng.random())
    x += (bowed * stick + ticks) * (0.15 + 0.85 * k ** 1.4) * 0.4
    x += S.osc(S.sweep(55 * D.pitch, 98 * D.pitch, dur), dur, "tri") * k ** 1.5 * 0.07
    x = verb(x.astype(F32), 0.22 + D.wet)[:n]
    return put(np.zeros(L, dtype=F32), x, B["approach"])


def st_vacuum(rng, B, D, L):
    """The breath in: air being pulled out of the room, cut to nothing for the dip before the impact.
    The stem is mostly silence on purpose: the dip is the sound."""
    dur = min(0.14, 0.5 * (B["vacuum"] - B["approach"]))
    k = ramp(dur)
    suck = sfilt(fnoise(dur, rng), "highpass", S.sweep(600, 7000, dur), 0.9) * k ** 3 * 0.2
    tone = S.osc(S.sweep(70 * D.pitch, 210 * D.pitch, dur), dur) * k ** 2 * 0.22
    return put(np.zeros(L, dtype=F32), (suck + tone).astype(F32), B["vacuum"] - dur)


def st_impact(rng, B, D, L):
    """H3: the sea comes in. Click, a sub thump that is the loudest low-end event of the cue, a 300-900 Hz slap and a
    wall of water (both survive a phone speaker), struck hull plates and the creature's ring-modulated throat. The water's
    top end closes in 350 ms so the transformation, 80 ms later, has the air above 1.5 kHz to itself."""
    p = D.pitch
    dur = 2.0 * D.tail
    x = np.zeros(N(dur), dtype=F32)
    put(x, click(rng, 8, 2500) * 0.7, 0)
    put(x, S.osc(S.sweep(64 * p, 30 * p, 0.5), 0.95) * S.env(0.95, 0.004, 0.9, 1.25 * D.sub, 1.8), 0.002)
    put(x, S.osc(S.sweep(125 * p, 46 * p, 0.09), 0.12) * S.env(0.12, 0.002, 0.115, 0.6, 1.6), 0.0)
    slap = ffilt(fnoise(0.2, rng), "bandpass", 520, 0.8) * S.env(0.2, 0.002, 0.19, 1.8, 2.0)
    put(x, slap, 0.001)
    body = sfilt(fnoise(0.5, rng), "lowpass", S.sweep(5200, 170, 0.35), 0.8) * S.env(0.5, 0.003, 0.48, 0.6, 1.9)
    put(x, body, 0.004)
    mass = ffilt(fnoise(1.4, rng, "brown"), "lowpass", 110, 0.7) * S.env(1.4, 0.03, 1.3, 0.16, 1.3)
    put(x, mass, 0.01)
    fr = np.array([187, 311, 523, 742, 1180]) * p
    put(x, modal(fr, np.array([0.5, 0.4, 0.3, 0.2, 0.12]) * D.tail, [1, 0.8, 0.6, 0.4, 0.25], 1.2, rng) * 0.16, 0.003)
    growl = ffilt(S.ring_mod(S.osc(45 * p, 0.9, "saw"), S.osc(31 * p, 0.9)), "lowpass", 600, 0.8)
    put(x, growl * S.env(0.9, 0.01, 0.88, 0.42, 1.5), 0.02)
    x = verb(x, 0.22 + D.wet, tail=1.0)
    return put(np.zeros(L, dtype=F32), x, B["impact"])


def cell_semis(n):
    """The struck cells climb the minor scale by step (relief becoming appetite) and the last one resolves upward onto
    the fifth or the octave: an open interval, neither major nor minor."""
    if n <= 1:
        return [7][:n]
    body = list(MINOR[:n - 1])
    return body + [next(v for v in (7, 12, 19, 24) if v > body[-1])]


def cell_voice(rng, D, semi=0, last=False, ring=1.7):
    """H4, one struck cell: cold glass, not a chime. Inharmonic bar partials (1 : 2.756 : 5.404) with a beating twin,
    a soft 6 ms onset so it never 'dings', and a breath of frost. The LAST cell carries the weight: it is doubled a
    fifth below (an open fifth), rings `ring` times as long (1.7 full, 0.75 short) and is 4 dB up."""
    f0 = CELL_BASE * 2 ** (semi / 12)
    k = ring if last else 1.0
    dur = 0.7 * D.tail * k
    fr = [f0, f0 * 1.004, f0 * 2.756, f0 * 5.404]
    dc = np.array([0.42, 0.38, 0.2, 0.09]) * D.tail * k
    am = [1, 0.7, 0.35, 0.12]
    if last:
        under = f0 * 2 ** (-7 / 12)
        fr += [under, under * 1.003, under * 2.756]
        dc = np.concatenate([dc, np.array([0.5, 0.46, 0.22]) * D.tail * k])
        am += [0.95, 0.6, 0.3]
    tone = modal(fr, dc, am, dur, rng, droop=0.0 if last else 0.003)
    on = N(0.006)
    tone[:on] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, on))).astype(F32)
    if D.d > 0:                                                   # deeper = rougher: a little ring modulation
        tone = tone * (1 + 0.07 * D.d * S.osc(61.0, dur))
    fd = 0.05 if last else 0.03
    frost = ffilt(fnoise(fd, rng) * S.env(fd, 0.004, fd - 0.004, 1.0, 1.5), "highpass", 5000 if last else 6000, 0.7)
    x = tone * (0.16 if last else 0.10)
    put(x, frost * (0.22 if last else 0.12), 0.0)
    return x.astype(F32)


def seat(D, amp=0.3):
    """What the last cell lands ON: a short, soft, low-mid thud (150 -> 95 Hz with a 300 Hz knock). It exists only in
    the help_cell_last one-shots the game fires; no stem carries it, so the mixes do not contain it."""
    p = D.pitch
    x = S.osc(S.sweep(150 * p, 95 * p, 0.1), 0.22) * S.env(0.22, 0.004, 0.21, amp, 2.0)
    put(x, modal(np.array([300, 452]) * p, [0.06, 0.04], [1, 0.6], 0.15) * amp * 0.6, 0.0)
    return x.astype(F32)


def st_transform(rng, B, D, L):
    x = np.zeros(L, dtype=F32)
    semis = cell_semis(B["cells"])
    for i, sm in enumerate(semis):
        put(x, cell_voice(rng, D, sm, last=(i == len(semis) - 1), ring=B["last_ring"]), B["transform"] + i * B["cell_gap"])
    x = verb(x, 0.3 + D.wet)[:L]
    return ffilt(x, "highpass", 1500, 0.707, order=2)             # it lives above the tail, by construction


def st_aftermath(rng, B, D, L):
    """Under H4 and through H5: the creature goes down (one low tone falling an octave, its throat faint behind it, and a
    250-500 Hz moan a phone can carry), then the water leaves (a falling wash, no bubbles) while
    the plates keep ringing."""
    p = D.pitch
    dur = B["end"] - B["recede"]
    n = N(dur)
    x = np.zeros(n, dtype=F32)
    t = S.t_of(dur)
    fall = S.sweep(84 * p, 33 * p, dur) * (1 + 0.015 * np.sin(2 * np.pi * 4.0 * t))
    x += S.osc(fall, dur) * S.env(dur, 0.08, dur * 0.9, 0.09, 1.3)
    moan = ffilt(S.osc(fall * 4, dur, "tri") + 0.6 * S.osc(fall * 6.02, dur, "tri"), "lowpass", 700, 0.7)
    x += moan * S.env(dur, 0.12, dur * 0.85, 0.07, 1.2)
    growl = ffilt(S.ring_mod(S.osc(fall * 0.55, dur, "saw"), S.osc(31 * p, dur)), "lowpass", 300, 0.8)
    x += growl * S.env(dur, 0.1, dur * 0.7, 0.07, 1.4)
    dd = B["end"] - B["drain"]
    off = B["drain"] - B["recede"]
    drain = sfilt(fnoise(dd, rng, "pink"), "bandpass", S.sweep(1500, 260, dd), 1.2) * S.env(dd, 0.1, dd - 0.11, 0.36, 1.4)
    drain = drain * (0.6 + 0.4 * turbulence(dd, rng, 12.0))
    put(x, drain, off)
    put(x, sfilt(fnoise(dd, rng), "lowpass", S.sweep(3000, 300, dd * 0.6), 0.8) * S.env(dd, 0.05, dd * 0.6, 0.06, 2.0), off)
    put(x, modal(np.array([311, 523, 742]) * p, np.array([1.0, 0.7, 0.4]) * D.tail, [1, 0.6, 0.35], dur, rng) * 0.05, 0)
    x = verb(x, 0.28 + D.wet)[:n]
    x[-N(0.25):] *= np.linspace(1, 0, N(0.25), dtype=F32) ** 1.5
    return put(np.zeros(L, dtype=F32), x, B["recede"])


def edges(x, ms=5.0, mask=None):
    """Fade both ends, then take out whatever DC is left WITHOUT lifting the ends off zero (the correction is shaped
    by the same fade window, and by mask where the sound must stay digitally silent)."""
    w = S.fade_edges(np.ones(len(x), dtype=F32), ms)
    x = x.astype(F32) * w
    if mask is not None:
        w = w * mask
    return (x - w * (float(np.sum(x)) / float(np.sum(w)))).astype(F32)


def finish(x, D, drive=True, hp=20.0, ref=1.0):
    """Common exit: no DC or subsonics (before and after the drive, which can add DC), and the depth colour."""
    x = D.fx(ffilt(x, "highpass", hp, 0.707), drive, ref)
    return ffilt(x, "highpass", hp, 0.707) if (drive and D.d > 0) else x


def help_cue(depth=2, B=BEATS_FULL):
    """Returns ({stem: array}, mix). Stems share one gain, so they sum to the mix exactly (before 16-bit rounding)."""
    D = Depth(depth)
    L = N(B["end"])
    fns = dict(dread=st_dread, targeting=st_targeting, vacuum=st_vacuum, impact=st_impact, transform=st_transform,
               aftermath=st_aftermath)
    stems = {}
    # nothing may sound inside the dip: the pre-impact stems are gated shut over the vacuum (3 ms ramp)
    gate = np.ones(L, dtype=F32)
    v0 = int(B["vacuum"] * SR)
    r = N(0.003)
    gate[v0 - r:v0] = np.linspace(1, 0, r, dtype=F32)
    gate[v0:] = 0
    live = np.zeros(L, dtype=F32)
    live[int(B["impact"] * SR):] = 1
    out_fade = np.ones(L, dtype=F32)                         # nothing is still ringing when the cue ends
    out_fade[-N(0.2):] = np.linspace(1, 0, N(0.2), dtype=F32) ** 1.5
    for name in HELP_STEMS:
        x = fns[name](rng_of("help/" + name), B, D, L)      # the seed ignores depth and length: only the design changes
        x = finish(x, D, drive=(name != "transform"), ref=(2.0 if name == "impact" else 1.0))
        if name == "transform":
            x = ffilt(x, "highpass", 1500, 0.707, order=1)
        if name in ("dread", "targeting", "vacuum"):
            x = x * gate
        elif name in ("impact", "transform", "aftermath"):
            x[:int(B["impact"] * SR)] = 0                    # the filters' pre-roll must not leak into the dip
        stems[name] = edges(x * out_fade, mask=(gate if name in ("dread", "targeting", "vacuum") else live))
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
    """Escalation by cascade step: lower (1.5 semitones a step), denser (more fractures, more jets, more water),
    longer (the run-off and the scar hum hang on). The weight is on W2, the breach: that is the strongest picture."""
    step = int(max(1, min(5, step)))
    D = Depth(depth)
    e = step - 1
    p = D.pitch * 2 ** (-1.5 * e / 12)
    f = chain_factor(step)
    hum_len = 0.7 + 0.2 * step
    tj = WIN_T["jet"]
    t_thud = WIN_T["implode"] + 0.07
    L = N(t_thud + 0.1 + hum_len + 0.35)
    out = {}

    # W1 crack: hairline fractures in glass, sparse then crowding toward the breach. Dry clicks and tiny damped pings at
    # fixed pitches: nothing sweeps, so nothing sounds electric.
    rng = rng_of("win/crack/%d" % step)
    x = np.zeros(L, dtype=F32)
    nclk = 5 + 3 * step
    times = np.sort(tj * rng.random(nclk) ** 0.6)
    for j, tc in enumerate(times):
        a = 0.18 + 0.3 * (j + 1) / nclk
        put(x, click(rng, 1.5 + 2.5 * rng.random(), 3000 * p ** 0.5, order=2) * a, float(tc))
        pf = (2200 + 2300 * rng.random()) * p ** 0.5
        put(x, modal([pf, pf * 2.756], [0.008, 0.004], [1, 0.4], 0.03, rng) * a * 0.35, float(tc) + 0.0005)
    put(x, S.osc(S.sweep(160 * p, 110 * p, 0.05), 0.05) * S.env(0.05, 0.002, 0.048, 0.10 + 0.03 * e, 2.0), 0.0)   # the glass ticks once, low
    out["crack"] = verb(x, 0.12 + D.wet, "short")[:L]

    # W2 breach: the seam tears and water under pressure comes THROUGH, toward us: a hard broadband slap with a short
    # low push behind it, a needle of spray per winning column, then the water running off the glass.
    rng = rng_of("win/jet/%d" % step)
    x = np.zeros(L, dtype=F32)
    put(x, click(rng, 6, 1800) * (0.7 + 0.06 * e), tj - 0.002)
    slap = sfilt(fnoise(0.14, rng), "lowpass", S.sweep(7000, 1400, 0.14), 0.7) * S.env(0.14, 0.002, 0.135, 0.5 * (1 + 0.10 * e), 1.6)
    put(x, slap, tj)
    put(x, ffilt(fnoise(0.16, rng), "bandpass", 420 * p, 0.8) * S.env(0.16, 0.003, 0.155, 0.9 * (1 + 0.10 * e), 1.8), tj)   # the body of the water
    put(x, S.osc(S.sweep(105 * p, 60 * p, 0.14), 0.22) * S.env(0.22, 0.005, 0.21, (0.95 + 0.12 * e) * D.sub, 1.8), tj + 0.002)
    njet = 2 + step
    for qn in range(njet):
        jd = 0.34
        hi = 2600 * 2 ** (-e / 12) * (0.9 + 0.2 * rng.random())
        j = sfilt(fnoise(jd, rng), "bandpass", S.sweep(hi, hi * 0.7, jd), 0.8)          # broad and barely moving: spray, not a laser
        put(x, j * S.env(jd, 0.012, jd - 0.014, 0.42 * (1 + 0.10 * e) / np.sqrt(njet), 1.5), tj + qn * 0.02)
    rd = (WIN_T["implode"] - tj) + 0.35 + 0.08 * e                                       # run-off: it keeps falling under the implosion
    run = sfilt(fnoise(rd, rng, "pink"), "lowpass", S.sweep(3600, 500, rd), 0.8) * (0.35 + 0.65 * turbulence(rd, rng, 14.0))
    put(x, run * S.env(rd, 0.09, rd - 0.1, 0.30 + 0.04 * e, 1.3), tj + 0.06)
    out["jet"] = verb(x, 0.18 + 0.02 * e + D.wet)[:L]

    # W3 implosion: lighter than the breach on purpose. 70 ms of suction, a short crush (no ding), and the scar's hum.
    rng = rng_of("win/implode/%d" % step)
    x = np.zeros(L, dtype=F32)
    t0 = WIN_T["implode"]
    sk = ramp(0.07)
    suck = sfilt(fnoise(0.07, rng), "lowpass", S.sweep(300, 2400, 0.07), 0.9) * sk ** 2.5 * 0.2
    suck[-N(0.003):] *= np.linspace(1, 0, N(0.003), dtype=F32)
    put(x, suck, t0)
    cl = (WIN_T["explode"] * f) - 0.07
    put(x, S.osc(S.sweep(110 * p, 46 * p, 0.14), cl) * S.env(cl, 0.003, cl - 0.004, (0.34 + 0.05 * e) * D.sub, 2.2), t_thud)
    cr = sfilt(fnoise(0.11, rng), "bandpass", S.sweep(900 * p, 250 * p, 0.11), 3.0) * S.env(0.11, 0.002, 0.105, 0.34 + 0.05 * e, 1.6)
    put(x, cr, t_thud)
    dust = modal(np.array([420, 660, 990]) * p, [0.05, 0.035, 0.02], [1, 0.6, 0.35], 0.12, rng) * (0.10 + 0.02 * e)
    put(x, dust, t_thud + 0.002)
    hd = hum_len
    th = S.t_of(hd)
    hf = 146.83 * p
    hum = (np.sin(2 * np.pi * hf * th) + 0.8 * np.sin(2 * np.pi * hf * 1.0595 * th + 0.7) + 0.3 * np.sin(2 * np.pi * hf * 1.4983 * th)
           + 0.5 * np.sin(2 * np.pi * hf * 0.5 * th + 0.2) + 0.35 * np.sin(2 * np.pi * hf * 2 * th + 0.9))
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
# The five stones are one family (a dead knock on the family thud) but not one sound: each has its own pitch, its own
# partial spacing, damping and grit, and one detail of its own. Worth more = lower, longer, heavier.
#            pitch   partial ratios            damp  grit Hz  thud  detail
LOW = {
    "low_10": (440.00, (1, 1.58, 2.21, 3.31), 0.75, 2600, 0.36, "dry"),        # smallest pebble: short, bright grit
    "low_j": (392.00, (1, 1.47, 2.09, 3.10), 0.90, 2100, 0.40, "double"),     # two-part knock, 14 ms apart
    "low_q": (349.23, (1, 1.62, 2.40, 3.50), 1.00, 1700, 0.45, "ring"),       # a second partial that rings on
    "low_k": (329.63, (1, 1.35, 2.21, 2.90), 1.20, 1350, 0.50, "grind"),      # lands with a 40 ms scrape
    "low_a": (293.66, (1, 1.50, 2.00, 2.76), 1.45, 1100, 0.58, "slab"),       # a slab: an octave-down partial under it
}
LOW_F = {k: v[0] for k, v in LOW.items()}


def stone_knock(rng, D, key, f, dur=0.15, gain=0.6):
    _, ratios, damp, grit, _, detail = LOW[key]
    dec = np.array([0.045, 0.03, 0.02, 0.012]) * damp
    amps = [1, 0.6, 0.4, 0.25]
    fr = [f * r for r in ratios]
    if detail == "ring":
        dec[1] *= 2.6; amps[1] = 0.85
    if detail == "slab":
        fr.append(f * 0.5); dec = np.append(dec, 0.07); amps.append(0.7)
    x = np.zeros(N(dur + 0.03), dtype=F32)
    put(x, modal(fr, dec, amps, dur, rng) * gain, 0.001)
    put(x, ffilt(fnoise(0.012, rng) * S.env(0.012, 0.0005, 0.0115, 1, 1.5), "bandpass", grit, 1.0) * gain * 0.85, 0)
    if detail == "double":
        put(x, modal(fr, dec * 0.7, amps, dur * 0.6, rng) * gain * 0.55, 0.014)
    if detail == "grind":
        g = sfilt(fnoise(0.04, rng, "pink"), "bandpass", S.sweep(700, 1100, 0.04), 2.5) * S.env(0.04, 0.004, 0.036, 1.0, 1.3)
        put(x, g * gain * 0.7, 0.006)
    return x


def v_low(key):
    def land(rng, D):
        f = LOW_F[key] * D.pitch
        x = np.zeros(N(0.2), dtype=F32)
        put(x, stone_knock(rng, D, key, f), 0)
        put(x, thud(D, LOW[key][4]), 0)
        return verb(x, 0.10 + D.wet, "short")

    def sting(rng, D):
        f = LOW_F[key] * D.pitch
        x = np.zeros(N(0.42), dtype=F32)
        put(x, stone_knock(rng, D, key, f, gain=0.5), 0)
        sc = sfilt(fnoise(0.17, rng, "pink"), "bandpass", S.sweep(520, 950, 0.17), 2.5)
        grains = np.repeat((rng.random(N(0.17) // 384 + 1) > 0.35).astype(F32), 384)[:len(sc)]   # stone dragging on stone
        put(x, sc * grains * ramp(0.17, 1.0, 0.3, 1.0) * 0.55, 0.03)
        f2 = f * 0.749
        put(x, stone_knock(rng, D, key, f2, dur=0.2, gain=0.7), 0.2)
        put(x, modal([f * 0.5], [0.16], [0.3], 0.2, rng, droop=0.03), 0.2)
        put(x, thud(D, LOW[key][4] + 0.15), 0.2)
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


def throat(D, dur, lo=500.0):
    """The Leviathan's voice in two bands: the sub growl, and the same growl an octave and more up (150-400 Hz) so it
    still exists when the speaker cannot move air."""
    p = D.pitch
    low = ffilt(S.ring_mod(S.osc(45 * p, dur, "saw"), S.osc(31 * p, dur)), "lowpass", lo, 0.8)
    mid = ffilt(S.ring_mod(S.osc(110 * p, dur, "saw"), S.osc(31 * p, dur)), "bandpass", 260, 0.9)
    return low, mid


def knock(rng, f=700.0, amp=0.6):
    """A hard, short, mid-band transient: the part of a heavy hit a phone speaker keeps."""
    x = ffilt(fnoise(0.016, rng) * S.env(0.016, 0.0005, 0.0155, 1, 1.6), "bandpass", f, 1.5) * amp
    put(x, click(rng, 4, 1500)[:len(x)] * amp * 0.7, 0)
    return x.astype(F32)


def lev_land(rng, D):
    p = D.pitch
    x = np.zeros(N(0.23), dtype=F32)
    put(x, knock(rng, 650, 0.75), 0)
    put(x, S.osc(S.sweep(62 * p, 32 * p, 0.2), 0.22) * S.env(0.22, 0.004, 0.21, 0.28 * D.sub, 1.8), 0)
    put(x, S.osc(S.sweep(240 * p, 150 * p, 0.08), 0.12) * S.env(0.12, 0.002, 0.115, 0.5, 1.8), 0)         # the body: 150-240 Hz
    low, mid = throat(D, 0.2)
    put(x, low * S.env(0.2, 0.008, 0.19, 0.4, 1.6) + mid * S.env(0.2, 0.006, 0.19, 1.7, 1.5), 0.004)
    put(x, ffilt(fnoise(0.08, rng), "lowpass", 400, 0.8) * S.env(0.08, 0.002, 0.078, 0.35, 2.0), 0)
    return verb(x, 0.12 + D.wet, "short")


def lev_sting(rng, D):
    p = D.pitch
    d = 0.62
    x = np.zeros(N(0.64), dtype=F32)
    put(x, knock(rng, 600, 0.7), 0)
    low, mid = throat(D, d, 600.0)
    put(x, low * S.env(d, 0.04, d - 0.05, 0.45, 1.4) + mid * S.env(d, 0.03, d - 0.04, 1.8, 1.3), 0)
    put(x, S.osc(S.sweep(55 * p, 30 * p, 0.5), d) * S.env(d, 0.006, d - 0.01, 0.25 * D.sub, 1.7), 0)
    put(x, S.osc(S.sweep(230 * p, 140 * p, 0.1), 0.14) * S.env(0.14, 0.002, 0.135, 0.45, 1.8), 0)
    cl = ffilt(S.osc(S.sweep(146.83 * p, 138.6 * p, d), d, "tri") + S.osc(S.sweep(155.56 * p, 146.83 * p, d), d, "tri")
               + 0.5 * S.osc(S.sweep(73.42 * p, 69.3 * p, d), d, "tri"), "lowpass", 700, 0.7)
    put(x, cl * S.env(d, 0.05, d - 0.06, 0.45, 1.3), 0)                            # D against Eb: the flat second is the creature
    put(x, ffilt(fnoise(d, rng, "brown"), "lowpass", 250, 0.7) * S.env(d, 0.06, d - 0.07, 0.10, 1.4), 0)
    return verb(x, 0.16 + D.wet, "short")


def maw_land(rng, D):
    p = D.pitch
    x = np.zeros(N(0.23), dtype=F32)
    sk = ramp(0.03)
    put(x, sfilt(fnoise(0.03, rng), "highpass", S.sweep(800, 5000, 0.03), 0.8) * sk ** 3 * 0.12, 0)     # 30 ms of nothing but a breath in
    put(x, click(rng, 6, 2000) * 0.9, 0.03)
    put(x, knock(rng, 800, 0.6), 0.03)
    put(x, sfilt(fnoise(0.15, rng), "lowpass", S.sweep(3000, 200, 0.14), 0.8) * S.env(0.15, 0.002, 0.145, 0.45, 1.9), 0.032)
    put(x, ffilt(fnoise(0.14, rng), "bandpass", 300, 0.9) * S.env(0.14, 0.002, 0.135, 1.2, 1.7), 0.032)   # jaw body, 150-400 Hz
    put(x, modal(np.array([187, 311, 523]) * p, [0.09, 0.07, 0.05], [1, 0.8, 0.6], 0.16, rng) * 0.45, 0.033)
    put(x, S.osc(S.sweep(70 * p, 36 * p, 0.16), 0.18) * S.env(0.18, 0.003, 0.175, 0.3 * D.sub, 1.8), 0.032)
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
    put(x, click(rng, 8, 2000) * 0.9, t0)
    put(x, knock(rng, 750, 0.6), t0)
    put(x, sfilt(fnoise(0.3, rng), "lowpass", S.sweep(3500, 160, 0.28), 0.8) * S.env(0.3, 0.002, 0.29, 0.45, 1.9), t0 + 0.002)
    put(x, ffilt(fnoise(0.25, rng), "bandpass", 300, 0.9) * S.env(0.25, 0.002, 0.245, 1.2, 1.7), t0 + 0.002)
    put(x, S.osc(S.sweep(64 * p, 30 * p, 0.36), 0.4) * S.env(0.4, 0.004, 0.39, 0.3 * D.sub, 1.7), t0 + 0.002)
    put(x, modal(np.array([187, 311, 523]) * p, [0.22, 0.16, 0.1], [1, 0.8, 0.6], 0.35, rng, droop=0.02) * 0.45, t0 + 0.003)
    return verb(x, 0.16 + D.wet, "short")


# name -> (tier, land fn, stinger fn, [old peak targets, unused: the level now comes from MID_TARGET])
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


VARIANTS = ((0.0, 0.0), (0.6, -0.5), (-0.7, -0.3))     # round-robin lands: (semitones, dB) on top of a new seed

# The loudness ladder is set where a phone can hear it: RMS in 200 Hz - 4 kHz, 2 dB a tier, (land, stinger) in dBFS.
# Worth more = louder in that band, whatever the sub is doing. Peaks follow from it and stay under -1.5 dBFS.
MID_TARGET = {"LOW stone": (-27.0, -25.0), "MID brass": (-25.0, -23.0), "HIGH living": (-23.0, -21.0),
              "APEX": (-21.0, -19.0), "WILD": (-19.0, -17.0)}
TIERS = tuple(MID_TARGET)
TILT = {}                                               # name -> how much mid-band was added to reach the target


def mid_rms_db(x):
    xd = x.astype(np.float64)
    P = np.abs(np.fft.rfft(xd)) ** 2
    f = np.fft.rfftfreq(len(xd), 1 / SR)
    return db(float(np.sqrt(P[(f >= 200) & (f <= 4000)].sum() * 2) / len(xd)))


def knee(y, cap=PEAK, t=0.7):
    """A soft knee: untouched below 70 % of the cap, folding smoothly into it above."""
    T = cap * t
    a = np.abs(y)
    return np.where(a <= T, y, np.sign(y) * (T + (cap - T) * np.tanh((a - T) / (cap - T)))).astype(F32)


def to_ladder(x, target_db, ms=4.5):
    """Gain the voice to its tier's 200 Hz - 4 kHz level. If that would push the peak over -1.5 dBFS, the voice is too
    bottom- or top-heavy for its rung: mix in more of its own mid band (same sound, re-weighted) until it fits. A voice
    that is mostly clicks cannot get there by weighting alone, so as a last resort its tallest peaks (up to 6 dB over)
    are folded on a soft knee. Returns (voice, mid-band added, dB of peak folded)."""
    mid = ffilt(ffilt(x, "highpass", 200, 0.707, order=2), "lowpass", 4000, 0.707, order=2)
    steps = (0, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8, 12)
    for allow in (0.0, 6.0):
        for g in steps:
            base = edges(x + g * mid, ms)
            y = (base * 10 ** ((target_db - mid_rms_db(base)) / 20)).astype(F32)
            over = db(float(np.max(np.abs(y))) / PEAK)
            if over <= 0:
                return y, g, 0.0
            if over <= allow:
                for _ in range(6):                       # fold, then re-trim to the target (folding costs a little level)
                    z = knee(y)
                    y = (y * 10 ** ((target_db - mid_rms_db(z)) / 20)).astype(F32)
                z = knee(y)
                if abs(mid_rms_db(z) - target_db) < 0.05:
                    return z, g, round(over, 1)
    raise RuntimeError("cannot reach %.1f dBFS in 200 Hz-4 kHz under the peak limit" % target_db)


def symbol_voice(key, kind, depth=2, var=0):
    """kind 'land' takes var 1..3 (the round-robin takes: own seed, slightly different pitch and level)."""
    tier, land, sting = SYMBOLS[key][:3]
    D = Depth(depth)
    fn, mx, target = (land, LAND_MAX, MID_TARGET[tier][0]) if kind == "land" else (sting, STING_MAX, MID_TARGET[tier][1])
    name = "sym/%s/%s" % (key, kind)
    if var:
        st, gdb = VARIANTS[var - 1]
        D.pitch *= 2 ** (st / 12)
        target += gdb
        name += "/v%d" % var
    x = np.concatenate([np.zeros(N(0.005), dtype=F32), finish(fn(rng_of(name), D), D, hp=30.0)])[:N(mx)]   # 5 ms lead-in: the fade never eats the transient
    tail = N(0.03)
    x[-tail:] *= np.linspace(1, 0, tail, dtype=F32) ** 1.5       # the room is cut off inside the length budget
    y, g, fold = to_ladder(x, target)
    TILT[name] = (g, fold)
    return y


def ladder_check(manifest):
    """Per tier, the lowest and highest 200 Hz - 4 kHz RMS among its lands and its stingers, and the gap up to the next tier."""
    out = {}
    for kind in ("land", "stinger"):
        rows = []
        for tier in TIERS:
            v = [e["rms_200_4k_dbfs"] for k, e in manifest.items() if e.get("tier") == tier and (("_land_" in k) if kind == "land" else k.endswith("_stinger"))]
            rows.append([tier, min(v), max(v)])
        for i, r in enumerate(rows):
            r.append(round(rows[i + 1][1] - r[2], 2) if i + 1 < len(rows) else None)
        out[kind] = [{"tier": t, "min_dbfs": a, "max_dbfs": b, "step_to_next_db": st} for t, a, b, st in rows]
    out["ok"] = all(r["step_to_next_db"] is None or r["step_to_next_db"] >= 1.5 for k in ("land", "stinger") for r in out[k])
    return out


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
        # what a small speaker keeps: 200 Hz - 4 kHz
        "share_200_4k": round(float(P[(f >= 200) & (f <= 4000)].sum() / tot), 4),
        "rms_200_4k_dbfs": round(db(float(np.sqrt(P[(f >= 200) & (f <= 4000)].sum() * 2) / len(xd))), 2),
        "dc": round(float(np.mean(xd)), 6),
        # a 4 ms fade exists if the first and last 4 ms never exceed a linear ramp to the file's own peak
        "edge_ok": bool(abs(xd[0]) < thr and abs(xd[-1]) < thr
                        and np.all(np.abs(xd[:N(0.004)]) <= np.linspace(0, 1, N(0.004)) * np.max(np.abs(xd)) + 1e-6)
                        and np.all(np.abs(xd[-N(0.004):]) <= np.linspace(1, 0, N(0.004)) * np.max(np.abs(xd)) + 1e-6)),
    }


def quant(x):
    """What is actually in the file: 16-bit."""
    return (np.clip(x, -1, 1) * 32767.0).astype("<i2")


SMALL_SPEAKER_LIMIT_DB = 12.0


def beat_windows(B):
    return [("H1 dread", B["dread"], B["approach"]), ("H2 targeting", B["approach"], B["vacuum"]),
            ("V dip", B["vacuum"], B["impact"]), ("H3 impact", B["impact"], B["transform"]),
            ("H4 transformation", B["transform"], B["drain"]), ("H5 aftermath", B["drain"], B["end"])]


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
    a, b = int(B["transform"] * SR), int(B["drain"] * SR)
    rest = (full - stems["transform"])[a:b]
    trw = stems["transform"][a:b]
    hi_tr = float(np.sqrt(np.mean(band(trw, 1500, 12000) ** 2)))
    hi_rest = float(np.sqrt(np.mean(band(rest, 1500, 12000) ** 2)))
    qsum = np.sum([quant(s).astype(np.int64) for s in stems.values()], axis=0)
    # small-speaker read: the cue through a 200 Hz - 4 kHz window, beat by beat, against the impact
    rows = {}
    for name, t0, t1 in beat_windows(B):
        seg = band(full[int(t0 * SR):int(t1 * SR)], 200, 4000)        # filtered per window: nothing leaks across a beat line
        rows[name] = db(float(np.sqrt(np.mean(seg ** 2))))
    ref = rows["H3 impact"]
    beats = {k: {"rms_200_4k_dbfs": round(v, 1), "vs_impact_db": round(v - ref, 1),
                 "flag": bool(k != "V dip" and k != "H3 impact" and ref - v > SMALL_SPEAKER_LIMIT_DB)} for k, v in rows.items()}
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
        "small_speaker_beats": beats,
        "small_speaker_flags": [k for k, v in beats.items() if v["flag"]],
        "impact_lead_200_4k_db": round(ref - max(v for k, v in rows.items() if k != "H3 impact"), 1),
    }


def win_checks(seams):
    """Where the win's weight sits: stem peaks, and RMS of the mix in the W2 and W3 windows."""
    out = {}
    for s, (st, full) in seams.items():
        w2 = full[int(WIN_T["jet"] * SR):int(WIN_T["implode"] * SR)].astype(np.float64)
        w3 = full[int(WIN_T["implode"] * SR):int((WIN_T["implode"] + WIN_T["explode"]) * SR)].astype(np.float64)
        pk = {k: round(db(float(np.max(np.abs(v)))), 2) for k, v in st.items()}
        out["step%d" % s] = {"stem_peak_dbfs": pk, "loudest_stem": max(pk, key=pk.get),
                             "w2_rms_dbfs": round(db(float(np.sqrt(np.mean(w2 ** 2)))), 1),
                             "w3_rms_dbfs": round(db(float(np.sqrt(np.mean(w3 ** 2)))), 1)}
    return out


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
    return [("H1", B["dread"], "DREAD"), ("H2", B["approach"], "TARGETING"), ("V", B["vacuum"], "DIP"),
            ("H3", B["impact"], "IMPACT"), ("H4", B["transform"], "TRANSFORM"), ("H5", B["drain"], "AFTERMATH")]


def help_sheet(path, stems, full, B, chk, depth):
    from PIL import Image
    W = 1800
    H = 34 + 60 + 78 * 6 + 117 + 250 + 30 + 18 * 7 + 30
    img = Image.new("RGB", (W, H), BG)
    sb = chk["small_speaker_beats"]
    lines = [
        "sub 30-80 Hz (50 ms RMS): peak %.1f dBFS at %.3f s (impact at %.2f s)  |  +%.1f dB over anything before it, +%.1f dB over every other stem, +%.1f dB over the cue from 0.9 s after" % (
            chk["sub_peak_dbfs_30_80"], chk["sub_peak_time_s"], B["impact"], chk["sub_margin_vs_before_db"], chk["sub_margin_vs_other_stems_db"], chk["sub_margin_vs_after_db"] or 0),
        "dip: %d ms at %s (the 100 ms before it: %.1f dBFS RMS)" % (chk["vacuum_ms"], "digital silence" if chk["vacuum_rms_dbfs"] < -120 else "%.1f dBFS RMS" % chk["vacuum_rms_dbfs"], chk["pre_vacuum_rms_dbfs"]),
        "transformation: %.1f%% of its energy above 1.5 kHz, centroid %.0f Hz, %+.1f dB against the rest of the mix above 1.5 kHz in its window" % (
            100 * chk["transform_energy_above_1k5"], chk["transform_centroid_hz"], chk["transform_vs_rest_above_1k5_db"]),
        "small speaker (200 Hz-4 kHz RMS per beat, dB against the impact):  " + "   ".join(
            "%s %.1f (%+.1f)%s" % (k.split()[0], v["rms_200_4k_dbfs"], v["vs_impact_db"], " FLAG" if v["flag"] else "") for k, v in sb.items() if k != "V dip"),
        "   limit: no beat more than %.0f dB under the impact in that band (the dip is exempt)   ->   %s   |   the impact leads the next loudest beat by %+.1f dB in that band" % (
            SMALL_SPEAKER_LIMIT_DB, ("FLAGGED: " + ", ".join(chk["small_speaker_flags"])) if chk["small_speaker_flags"] else "all beats inside", chk["impact_lead_200_4k_db"]),
        "mix peak %.2f dBFS  |  stems sum to the mix within %d LSB (16-bit)" % (chk["full_peak_dbfs"], chk["stems_sum_max_error_lsb"]),
        "MEASURED, NOT HEARD: a human listen is still required.",
    ]
    title = "THE HELP CUE  (CREATURE_LIFELINE_STRIKE)  -  %s version, %.1f s  -  depth %d  -  rows autoscaled, peak printed" % (B["name"].upper(), B["end"], depth)
    timeline_panel(img, (0, 10), W, title, [(n.upper(), stems[n]) for n in HELP_STEMS], full, help_beats(B), B["end"], lines)
    img.save(path)


def win_sheet(path, seams):
    from PIL import Image, ImageDraw
    steps = sorted(seams)
    dur = max(len(seams[s][1]) for s in steps) / SR
    W, pw = 1860, 620
    H = 34 + 60 + 78 * 3 + 117 + 250 + 30 + 18 * 5 + 40
    img = Image.new("RGB", (W, H), BG)
    for i, s in enumerate(steps):
        st, full = seams[s]
        pad = lambda v: np.pad(v, (0, N(dur) - len(v))) if len(v) < N(dur) else v
        f = chain_factor(s)
        beats = [("W1", WIN_T["crack"], "CRACK"), ("W2", WIN_T["jet"], "BREACH"), ("W3", WIN_T["implode"], "IMPLODE")]
        m = metrics(full)
        c = win_checks({s: seams[s]})["step%d" % s]
        lines = ["peak %.1f dBFS  RMS %.1f dBFS  %.2f s" % (m["peak_dbfs"], m["rms_dbfs"], m["seconds"]),
                 "centroid %.0f Hz  sub %.0f%%  200 Hz-4 kHz %.0f%%" % (m["centroid_hz"], 100 * m["sub_share_30_80"], 100 * m["share_200_4k"]),
                 "loudest stem: %s   W2 %.1f / W3 %.1f dBFS RMS" % (c["loudest_stem"].upper(), c["w2_rms_dbfs"], c["w3_rms_dbfs"]),
                 "explode budget %d ms (chainFactor %.2f)" % (round(WIN_T["explode"] * f * 1000), f)]
        timeline_panel(img, (i * pw, 10), pw, "WIN SEAM - cascade step %d" % s, [(n.upper(), pad(st[n])) for n in WIN_STEMS],
                       pad(full), beats, dur, lines, gutter=150)
    ImageDraw.Draw(img).text((8, H - 24), "Same time axis and one shared gain across the three steps: later steps are lower, denser, longer and louder. The weight is on W2. "
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
        for j, (nm, x, bx, bw, mx) in enumerate((("LAND v1", land, x0, lw, LAND_MAX), ("STINGER", sting, x0 + lw + 14, avail - lw, STING_MAX))):
            xx = np.pad(x, (0, max(0, N(mx) - len(x))))
            m = metrics(x)
            d.text((x0, oy + 24 + 16 * j), "%-7s %3d ms  peak %5.1f  rms %5.1f dBFS  cen %4.0f Hz  sub %2.0f%%  200-4k %2.0f%%" % (
                nm, round(m["seconds"] * 1000), m["peak_dbfs"], m["rms_dbfs"], m["centroid_hz"], 100 * m["sub_share_30_80"], 100 * m["share_200_4k"]), fill=DIM, font=fs)
            d.text((bx + 4, oy + 62), nm, fill=AMBER, font=fs)
            draw_wave(d, xx, (bx, oy + 60, bx + bw, oy + 130), scale=1.0)
            d.text((bx + 4, oy + 62), nm, fill=AMBER, font=fs)
            img.paste(spectro(xx, bw, 110, fmin=40.0, fmax=16000.0, win=2048), (bx, oy + 136))
        freq_ticks(d, (x0, oy + 136, x0, oy + 246), 40.0, 16000.0, fs, ticks=(100, 1000, 10000))
    d.text((10, rows * ch + 14), "Per symbol: land take v1 of 3 (<= 250 ms) and win stinger (<= 700 ms). Waveforms on a 0 dBFS scale (so tiers compare), "
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
        print("[moments] %-28s %5.2fs  pk %6.2f  rms %6.2f  cen %6.0f Hz  sub %5.1f%%  200-4k %5.1f%% (%6.1f dBFS)  dc %+.5f  edges %s" % (
            name, e["seconds"], e["peak_dbfs"], e["rms_dbfs"], e["centroid_hz"], 100 * e["sub_share_30_80"], 100 * e["share_200_4k"],
            e["rms_200_4k_dbfs"], e["dc"], "ok" if e["edge_ok"] else "FAIL"))

    if a.sheet:
        SHEETS.mkdir(parents=True, exist_ok=True)

    if "help" in groups:
        for B, tag in ((BEATS_FULL, "help_full"), (BEATS_SHORT, "help_short")):
            stems, full = help_cue(a.depth, B)
            starts = dict(dread=B["dread"], targeting=B["approach"], vacuum=B["vacuum"] - min(0.14, 0.5 * (B["vacuum"] - B["approach"])),
                          impact=B["impact"], transform=B["transform"], aftermath=B["recede"])
            for n in HELP_STEMS:
                emit("%s_%s" % (tag, n), stems[n], tag, depth=a.depth, profile=B["name"], beat_offset_s=round(starts[n], 3))
            emit(tag + "_mix", full, tag, depth=a.depth, profile=B["name"], beat_offset_s=0.0)
            report[tag] = help_checks(stems, full, B)
            print("[moments] checks %s: %s" % (tag, json.dumps(report[tag])))
            if a.sheet:
                sp = SHEETS / ("sound_help_sheet.png" if tag == "help_full" else "sound_help_short_sheet.png")
                help_sheet(sp, stems, full, B, report[tag], a.depth)
                print("[moments] sheet -> %s" % sp.relative_to(REPO))
        for dv in (0, 5):                                                     # the depth ladder's two ends, mix only
            stems, full = help_cue(dv, BEATS_FULL)
            emit("help_full_mix_d%d" % dv, full, "help_depth", depth=dv, profile="full", beat_offset_s=0.0)
            report["help_full_d%d" % dv] = help_checks(stems, full, BEATS_FULL)
        D = Depth(a.depth)                                                    # the one-shots the runtime fires per struck cell
        for nm, last, ring, cap in (("help_cell", False, 1.0, None), ("help_cell_last", True, 1.7, None), ("help_cell_last_short", True, 0.75, 0.70)):
            cv = verb(cell_voice(rng_of("help/" + ("help_cell_last" if last else nm)), D, 7 if last else 0, last, ring), 0.3 + D.wet, tail=0.25)
            cv = ffilt(finish(cv, D, drive=False), "highpass", 1500, 0.707, order=3)
            if last:
                put(cv, finish(seat(D), D), 0.0)                              # the one-shot carries its own seat
            if cap:
                cv = cv[:N(cap)]
            cv[-N(0.1):] *= np.linspace(1, 0, N(0.1), dtype=F32)
            cv = edges(cv)
            emit(nm, (cv * (10 ** ((-6 if last else -10) / 20) / float(np.max(np.abs(cv))))).astype(F32), "help", depth=a.depth, profile="any")

    if "win" in groups:
        seams = win_seams(a.depth, (1, 3, 5))
        for s, (st, full) in seams.items():
            for n in WIN_STEMS:
                emit("win_s%d_%s" % (s, n), st[n], "win", depth=a.depth, cascade_step=s, beat_offset_s=WIN_T[n])
            emit("win_s%d_full" % s, full, "win", depth=a.depth, cascade_step=s, beat_offset_s=0.0)
        report["win"] = win_checks(seams)
        print("[moments] checks win: %s" % json.dumps(report["win"]))
        if a.sheet:
            win_sheet(SHEETS / "sound_win_sheet.png", seams)
            print("[moments] sheet -> artifacts/targets/sound_win_sheet.png")

    if "symbols" in groups:
        voices = {}
        for k in SYMBOLS:
            lands = [symbol_voice(k, "land", a.depth, v) for v in (1, 2, 3)]
            sting = symbol_voice(k, "stinger", a.depth)
            voices[k] = (lands[0], sting)
            for v, land in enumerate(lands, 1):
                emit("sym_%s_land_v%d" % (k, v), land, "symbols", depth=a.depth, tier=SYMBOLS[k][0], variant=v, mid_tilt=TILT["sym/%s/land/v%d" % (k, v)][0], peak_fold_db=TILT["sym/%s/land/v%d" % (k, v)][1])
            emit("sym_%s_stinger" % k, sting, "symbols", depth=a.depth, tier=SYMBOLS[k][0], mid_tilt=TILT["sym/%s/stinger" % k][0], peak_fold_db=TILT["sym/%s/stinger" % k][1])
        report["symbol_ladder"] = ladder_check(manifest)
        print("[moments] ladder: %s" % json.dumps(report["symbol_ladder"]))
        if a.sheet:
            symbols_sheet(SHEETS / "sound_symbols_sheet.png", voices)
            print("[moments] sheet -> artifacts/targets/sound_symbols_sheet.png")

    if not a.only:                                                            # a full render owns the folder: no stale files
        for old in out.glob("*.wav"):
            if old.stem not in manifest:
                old.unlink()
    mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    bad = [k for k, e in manifest.items() if e["peak_dbfs"] > -1.0 or abs(e["dc"]) > 1e-3 or not e["edge_ok"]]
    print("[moments] %d files, manifest -> %s%s" % (len(manifest), mpath.relative_to(REPO) if mpath.is_relative_to(REPO) else mpath,
                                                    "" if not bad else "   TARGETS MISSED: %s" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
