"""
synth.py - a tiny offline synthesiser (numpy only) behind the asset kit's sound effects.

The game's runtime audio is procedural Web Audio (`slot_engine/static/canvas/audio_dark.js`). This module is the same
toolbox offline: oscillators, noise, envelopes, biquad filters, sweeps and a convolution reverb built from decaying
noise. It exists so a sound can be rendered to a file, tuned on a waveform, shipped in a sprite sheet and logged with
its provenance, instead of only existing as code that runs in a browser.

Everything is mono float32 at SR Hz and clips nothing: the caller mixes and normalises.
"""

import numpy as np

SR = 48000


def t_of(dur: float) -> np.ndarray:
    return np.arange(int(max(1, round(dur * SR))), dtype=np.float32) / SR


def silence(dur: float) -> np.ndarray:
    return np.zeros(int(max(1, round(dur * SR))), dtype=np.float32)


def sweep(a: float, b: float, dur: float, curve: str = "exp") -> np.ndarray:
    """A frequency envelope from a to b over dur seconds."""
    t = t_of(dur)
    k = t / max(1e-6, dur)
    if curve == "exp":
        a = max(1e-3, a); b = max(1e-3, b)
        return (a * (b / a) ** k).astype(np.float32)
    return (a + (b - a) * k).astype(np.float32)


def osc(freq, dur: float, shape: str = "sine", phase: float = 0.0) -> np.ndarray:
    """freq is a scalar or a per-sample array (from sweep)."""
    n = int(max(1, round(dur * SR)))
    f = np.full(n, float(freq), dtype=np.float32) if np.isscalar(freq) else np.asarray(freq, dtype=np.float32)[:n]
    if len(f) < n:
        f = np.pad(f, (0, n - len(f)), mode="edge")
    ph = (np.cumsum(f) / SR * 2 * np.pi + phase).astype(np.float32)
    if shape == "sine":
        return np.sin(ph, dtype=np.float32)
    if shape == "tri":
        return (2 / np.pi * np.arcsin(np.sin(ph))).astype(np.float32)
    if shape == "saw":
        return (2 * (ph / (2 * np.pi) % 1.0) - 1).astype(np.float32)
    if shape == "square":
        return np.sign(np.sin(ph)).astype(np.float32)
    raise ValueError(shape)


def noise(dur: float, rng: np.random.Generator, colour: str = "white") -> np.ndarray:
    n = int(max(1, round(dur * SR)))
    w = rng.standard_normal(n).astype(np.float32)
    if colour == "white":
        return w
    if colour == "brown":                       # integrated noise, drifts low
        b = np.cumsum(w) / 50.0
        return (b - b.mean()).astype(np.float32)
    if colour == "pink":                        # one-pole cascade approximation
        out = np.zeros(n, dtype=np.float32); s = 0.0
        for i in range(n):
            s = 0.985 * s + 0.015 * w[i]
            out[i] = s * 8.0
        return out
    raise ValueError(colour)


def env(dur: float, attack: float, decay: float, peak: float = 1.0, curve: float = 2.0) -> np.ndarray:
    """One-shot attack/decay envelope; decay is a power curve so it reads like a real impact."""
    n = int(max(1, round(dur * SR)))
    a = max(1, int(attack * SR))
    out = np.zeros(n, dtype=np.float32)
    out[:min(a, n)] = np.linspace(0, peak, min(a, n), dtype=np.float32)
    if n > a:
        d = max(1, int(decay * SR))
        k = np.linspace(0, 1, min(d, n - a), dtype=np.float32)
        out[a:a + len(k)] = peak * (1 - k) ** curve
    return out


def biquad(x: np.ndarray, kind: str, freq, q: float = 0.707) -> np.ndarray:
    """A biquad with a per-sample cutoff (freq scalar or array), so filters can sweep like the Web Audio set."""
    n = len(x)
    f = np.full(n, float(freq), dtype=np.float32) if np.isscalar(freq) else np.asarray(freq, dtype=np.float32)[:n]
    if len(f) < n:
        f = np.pad(f, (0, n - len(f)), mode="edge")
    f = np.clip(f, 20.0, SR * 0.45)
    out = np.zeros(n, dtype=np.float32)
    x1 = x2 = y1 = y2 = 0.0
    for i in range(n):
        w0 = 2 * np.pi * f[i] / SR
        cw, sw = np.cos(w0), np.sin(w0)
        alpha = sw / (2 * q)
        if kind == "lowpass":
            b0 = (1 - cw) / 2; b1 = 1 - cw; b2 = b0
        elif kind == "highpass":
            b0 = (1 + cw) / 2; b1 = -(1 + cw); b2 = b0
        elif kind == "bandpass":
            b0 = alpha; b1 = 0.0; b2 = -alpha
        else:
            raise ValueError(kind)
        a0 = 1 + alpha; a1 = -2 * cw; a2 = 1 - alpha
        xi = float(x[i])
        yi = (b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2) / a0
        x2, x1 = x1, xi
        y2, y1 = y1, yi
        out[i] = yi
    return out.astype(np.float32)


def ring_mod(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    n = min(len(a), len(b))
    return (a[:n] * b[:n]).astype(np.float32)


def fm(carrier: float, mod: float, index, dur: float) -> np.ndarray:
    """Simple FM: the modulator's output drives the carrier's frequency. index may sweep."""
    n = int(max(1, round(dur * SR)))
    idx = np.full(n, float(index), dtype=np.float32) if np.isscalar(index) else np.asarray(index, dtype=np.float32)[:n]
    if len(idx) < n:
        idx = np.pad(idx, (0, n - len(idx)), mode="edge")
    m = osc(mod, dur, "sine")
    return osc(np.full(n, carrier, dtype=np.float32) + m * idx * mod, dur, "sine")


def reverb_ir(dur: float, rng: np.random.Generator, lp_from: float = 4000.0, lp_to: float = 800.0) -> np.ndarray:
    """The dark set's impulse response: decaying noise, progressively lowpassed, 20 ms fade-in."""
    n = int(dur * SR)
    ir = rng.standard_normal(n).astype(np.float32)
    ir *= (1 - np.linspace(0, 1, n, dtype=np.float32)) ** 2.6
    ir = biquad(ir, "lowpass", sweep(lp_from, lp_to, dur, "exp"), 0.7)
    fade = min(n, int(0.02 * SR))
    ir[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
    return ir / (np.max(np.abs(ir)) + 1e-9)


def convolve(x: np.ndarray, ir: np.ndarray, wet: float = 0.25) -> np.ndarray:
    if wet <= 0:
        return x
    n = len(x) + len(ir) - 1
    size = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[:n].astype(np.float32)
    y /= (np.max(np.abs(y)) + 1e-9)
    out = np.zeros(n, dtype=np.float32)
    out[:len(x)] = x * (1 - wet)
    return (out + y * wet).astype(np.float32)


def mix(*parts, length: int = None) -> np.ndarray:
    n = length or max((len(p) for p in parts if p is not None), default=1)
    out = np.zeros(n, dtype=np.float32)
    for p in parts:
        if p is None:
            continue
        m = min(n, len(p))
        out[:m] += p[:m]
    return out


def at(sig: np.ndarray, start: float, length: int) -> np.ndarray:
    """Place a signal at an offset inside a buffer of `length` samples."""
    out = np.zeros(length, dtype=np.float32)
    s = int(start * SR)
    if s >= length:
        return out
    m = min(length - s, len(sig))
    out[s:s + m] = sig[:m]
    return out


def normalise(x: np.ndarray, peak: float = 0.89) -> np.ndarray:
    m = float(np.max(np.abs(x)))
    return (x * (peak / m)).astype(np.float32) if m > 1e-6 else x.astype(np.float32)


def fade_edges(x: np.ndarray, ms: float = 4.0) -> np.ndarray:
    n = min(len(x) // 2, int(ms / 1000 * SR))
    if n <= 0:
        return x
    x = x.copy()
    x[:n] *= np.linspace(0, 1, n, dtype=np.float32)
    x[-n:] *= np.linspace(1, 0, n, dtype=np.float32)
    return x
