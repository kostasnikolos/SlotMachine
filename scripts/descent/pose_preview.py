#!/usr/bin/env python3
"""Offline twin of levUpdate(): poses the three parts along the swim spine and renders frames,
so the head/body joint and proportions can be tuned without a browser.
usage: pose_preview.py out.jpg  (params via env-free constants below)"""
import json, base64, sys, math, os
ASSETS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'slot_engine', 'static', 'assets', 'descent'))
import numpy as np
from PIL import Image, ImageDraw

CFG = dict(sections=4, front=0.55, front_len=7.0, body_s0=-1.6, head_off=(0.25, 0.75, 0.0), head_scale=0.78,
           taper_start=7.0, taper_rate=0.035, R0=66.0, times=(40.0, 46.0, 52.0, 58.0), zone=None)
W, H = 1920, 1080
D = 540 / math.tan(math.radians(15))


def load(n):
    g = json.load(open(os.path.join(ASSETS, f'lev_{n}.json'))); c = g['count']
    v = np.frombuffer(base64.b64decode(g['pos']), np.float32).reshape(c, 3).astype(np.float64)
    nr = np.frombuffer(base64.b64decode(g['nrm']), np.int8).reshape(c, 3) / 127
    uv = np.frombuffer(base64.b64decode(g['uv']), np.uint16).reshape(c, 2) / 65535
    f = np.frombuffer(base64.b64decode(g['idx']), np.uint32 if g['idx32'] else np.uint16).reshape(-1, 3).astype(int)
    base = np.asarray(Image.open(os.path.join(ASSETS, f'lev_{n}_base.jpg'))).astype(float)
    em = np.asarray(Image.open(os.path.join(ASSETS, f'lev_{n}_emissive.jpg'))).astype(float)
    return dict(v=v, n=nr, uv=uv, f=f, base=base, em=em, len=g['max'][0])


PARTS = {k: load(k) for k in ['head', 'body', 'tail']}


def levR(u, c):
    front = 1 + c['front'] * max(0, 1 - u / c['front_len']) ** 2
    taper = 1 if u < c['taper_start'] else max(0.5, 1 - (u - c['taper_start']) * c['taper_rate'])
    return front * taper


def path(u):
    return np.array([W * 0.27 + math.sin(u * 0.21) * W * 0.17 + math.sin(u * 0.53 + 1.3) * W * 0.045,
                     H * 0.02 - (math.sin(u * 0.34 + 0.7) * H * 0.25 + math.cos(u * 0.71) * H * 0.07),
                     math.sin(u * 0.27 + 0.5) * 170 - 80])


def pose(t, c):
    R0 = c['R0']; NS = 64
    s = c['body_s0'] * R0; secs = []
    for i in range(c['sections']):
        r = levR(max(s, 0) / R0, c) * R0; secs.append((s, r)); s += (PARTS['body']['len'] - 0.16) * r
    tailS = s; tailR = levR(s / R0, c) * R0; total = s + PARTS['tail']['len'] * tailR
    S0 = c['body_s0'] * R0  # spine starts ahead of the head anchor (negative s extends forward)
    M = 1000; dp = np.array([path(t - j * 0.03) for j in range(M)]); dc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(dp, axis=0), axis=1))])
    sk = S0 + np.arange(NS) / (NS - 1) * (total - S0)
    P = np.zeros((NS, 3))
    for i, x in enumerate(sk):
        if x < 0:
            t0 = dp[0] - dp[1]; t0 /= np.linalg.norm(t0); P[i] = dp[0] + t0 * (-x)
        else:
            j = min(np.searchsorted(dc, x) - 1, M - 2); j = max(j, 0)
            f = np.clip((x - dc[j]) / max(dc[j + 1] - dc[j], 1e-6), 0, 1); P[i] = dp[j] + (dp[j + 1] - dp[j]) * f
    def tuck(x):  # inside the skull the neck narrows so its open front end never shows
        if x >= 0: return 1.0
        u = np.clip((x - S0) / (-S0), 0, 1); return 0.12 + 0.88 * u * u * (3 - 2 * u)
    RR = np.array([tailR if x >= tailS else levR(max(x, 0) / R0, c) * R0 * tuck(x) for x in sk])

    def frames(P):
        T = np.zeros_like(P); N = np.zeros_like(P)
        for i in range(NS):
            a, b = max(0, i - 1), min(NS - 1, i + 1); tt = P[a] - P[b]; tt /= np.linalg.norm(tt); T[i] = tt
            n = np.array([0, 1, 0]) - tt * tt[1]; N[i] = n / (np.linalg.norm(n) + 1e-9)
        return T, N
    T, N = frames(P)
    for i in range(NS):
        env = 0.25 + 0.75 * max(sk[i], 0) / total
        w1 = math.sin(sk[i] * 0.0062 - t * 2.3) * 34 * env; w2 = math.sin(sk[i] * 0.0062 - t * 2.3 + 1.3) * 26 * env
        B = np.cross(N[i], T[i]); P[i] += N[i] * w1 + B * w2
    T, N = frames(P)
    return dict(P=P, T=T, N=N, R=RR, S0=S0, total=total, secs=secs, tailS=tailS, tailR=tailR, R0=R0)


def spine_at(sp, s):
    k = np.clip((s - sp['S0']) / (sp['total'] - sp['S0']), 0, 1) * 63; i = np.minimum(np.floor(k), 62).astype(int); f = (k - i)[:, None]
    P = sp['P'][i] * (1 - f) + sp['P'][i + 1] * f; R = sp['R'][i] * (1 - f[:, 0]) + sp['R'][i + 1] * f[:, 0]
    T = sp['T'][i] * (1 - f) + sp['T'][i + 1] * f; T /= np.linalg.norm(T, axis=1, keepdims=True)
    N = sp['N'][i] * (1 - f) + sp['N'][i + 1] * f; N -= T * (N * T).sum(1, keepdims=True); N /= np.linalg.norm(N, axis=1, keepdims=True)
    return P, T, N, R


def deform(part, sp, c, A0=None, Ls=None, fixR=None, head=False):
    v, n = part['v'], part['n']
    if head:
        # head frame: average of the first spine tangents so it turns with the neck
        Tm = sp['T'][:4].mean(0); Tm /= np.linalg.norm(Tm)
        Nm = sp['N'][:4].mean(0); Nm -= Tm * Nm.dot(Tm); Nm /= np.linalg.norm(Nm)
        B = np.cross(Nm, Tm); hr = sp['R0'] * c['head_scale']
        lv = (v - np.array(c['head_off'])) * 1.0
        wp = sp['P'][np.argmin(np.abs(np.linspace(sp['S0'], sp['total'], 64)))] + (-np.outer(lv[:, 0], Tm) + np.outer(lv[:, 1], Nm) + np.outer(lv[:, 2], B)) * hr
        wn = -np.outer(n[:, 0], Tm) + np.outer(n[:, 1], Nm) + np.outer(n[:, 2], B)
        return wp, wn
    s = A0 + v[:, 0] * Ls
    P, T, N, R = spine_at(sp, s)
    if fixR: R = np.full_like(R, fixR)
    B = np.cross(N, T)
    wp = P + (N * v[:, 1:2] + B * v[:, 2:3]) * R[:, None]
    wn = -T * n[:, 0:1] + N * n[:, 1:2] + B * n[:, 2:3]
    return wp, wn


def render(t, c, S=960):
    sp = pose(t, c)
    items = [(PARTS['head'], deform(PARTS['head'], sp, c, head=True))]
    for A0, r in sp['secs']:
        items.append((PARTS['body'], deform(PARTS['body'], sp, c, A0=A0, Ls=r)))
    items.append((PARTS['tail'], deform(PARTS['tail'], sp, c, A0=sp['tailS'], Ls=sp['tailR'], fixR=sp['tailR'])))
    tris = []
    L = np.array([-0.3, 0.8, 0.5]); L /= np.linalg.norm(L)
    for part, (wp, wn) in items:
        f = part['f']; sc = D / (D - wp[:, 2]); sx = W / 2 + wp[:, 0] * sc; sy = H / 2 - wp[:, 1] * sc
        base, em = part['base'], part['em']; Hb, Wb = base.shape[:2]
        cuv = part['uv'][f].mean(1); px = (cuv[:, 0] * (Wb - 1)).astype(int); py = (cuv[:, 1] * (Hb - 1)).astype(int)
        nrm = wn[f].mean(1); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
        shade = np.clip(nrm @ L, 0, 1) * 0.8 + 0.2
        col = base[py, px] * shade[:, None] + em[py * em.shape[0] // Hb, px * em.shape[1] // Wb] * 0.9
        z = wp[f][:, :, 2].mean(1)
        for i in range(len(f)):
            tris.append((z[i], np.stack([sx[f[i]], sy[f[i]]], 1), col[i]))
    k = S / W
    im = Image.new('RGB', (S, int(H * k)), (18, 30, 40)); dr = ImageDraw.Draw(im)
    for z, q, col in sorted(tris, key=lambda x: x[0]):
        dr.polygon([tuple(p * k) for p in q], fill=tuple(np.clip(col, 0, 255).astype(int)))
    # HUD footprint for reference
    for x0, y0, x1, y1 in [(48, 120, 378, 916), (554, 104, 1366, 916), (1542, 120, 1872, 916)]:
        dr.rectangle([x0 * k, y0 * k, x1 * k, y1 * k], outline=(63, 245, 255))
    return im


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'pose.jpg'
    ims = [render(t, CFG) for t in CFG['times']]
    w, h = ims[0].size
    sheet = Image.new('RGB', (w * 2, h * 2))
    for i, im in enumerate(ims): sheet.paste(im, ((i % 2) * w, (i // 2) * h))
    sheet.save(out, quality=85)
    print('ok', out)
