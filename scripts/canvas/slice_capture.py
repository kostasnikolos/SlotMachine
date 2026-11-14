"""
slice_capture.py - capture the game the way the storyboards are drawn, so a reviewer can lay them side by side.

Needs the game server running:  python -m uvicorn slot_engine.api.app:app --port 8080

Records the page through the DevTools screencast (real frames with timestamps, no screenshot stalls), triggers the
help from the Director bar, and picks the frame nearest each storyboard beat using the game's own feel log
(strikePace / strikeBite / strikeEnd). Writes:

    artifacts/canvas/slice_idle_1920.png, slice_idle_390.png     the idle screen, landscape and phone
    artifacts/canvas/slice_help_full.png, slice_help_short.png   six beats H0-H5 as one sheet each
    artifacts/canvas/slice_report.json                           measured timings and page errors

    python scripts/canvas/slice_capture.py [--headed]
"""

import argparse
import base64
import io
import json
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "canvas"
PAGE = "http://127.0.0.1:8080/static/canvas/index.html"
GPU_ARGS = ["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"]
# beat -> (anchor event, offset ms): where in the real sequence each storyboard frame is taken
BEATS = [("H0 dead spin", "pace", -120), ("H1 dread", "pace", 0.6), ("H2 targeting", "bite", -200), ("H3 impact", "bite", 45),
         ("H4 transformation", "bite", 520), ("H5 aftermath", "end", -80)]


def font(px):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", px)
    except OSError:
        return ImageFont.load_default()


def launch(p, headed=False):
    """Installed Chrome or Edge first (they have the GPU path), then Playwright's own Chromium."""
    kw = {"headless": not headed, "args": GPU_ARGS}
    for channel in ("chrome", "msedge", None):
        try:
            return p.chromium.launch(channel=channel, **kw) if channel else p.chromium.launch(**kw)
        except Exception:
            continue
    raise SystemExit("no Chromium-family browser could be launched")


def record_strike(page, cdp, frames):
    """Click STRIKE, wait for strikeEnd, return the feel-log events of that strike (page clock, ms)."""
    n0 = page.evaluate("(window.__FEEL_LOG || []).length")
    page.get_by_role("button", name="STRIKE").click()
    page.wait_for_function("(n) => (window.__FEEL_LOG || []).slice(n).some((e) => e.type === 'strikeEnd')", arg=n0, timeout=15000)
    page.wait_for_timeout(700)
    ev = page.evaluate("(n) => (window.__FEEL_LOG || []).slice(n).filter((e) => /^strike/.test(e.type))", n0)
    return {e["type"]: e for e in ev}


def sheet(frames, origin_ms, ev, title, path):
    pace, bite, end = ev["strikePace"]["t"], ev["strikeBite"]["t"], ev["strikeEnd"]["t"]
    hush = bite - pace - ev["strikeBite"]["lungeMs"]
    anchors = {"pace": pace, "bite": bite, "end": end}
    cells = []
    for name, anchor, off in BEATS:
        t = anchors[anchor] + (off * hush if isinstance(off, float) else off)
        ts, jpg = min(frames, key=lambda f: abs((f[0] * 1000 - origin_ms) - t))
        cells.append((name, round((ts * 1000 - origin_ms) - pace), Image.open(io.BytesIO(jpg)).convert("RGB")))
    w, h = cells[0][2].size
    pad, cap = 16, 44
    out = Image.new("RGB", (3 * w + 4 * pad, 2 * (h + cap) + 3 * pad + 40), (4, 9, 12))
    d = ImageDraw.Draw(out)
    d.text((pad, 10), title, fill=(230, 236, 238), font=font(22))
    for i, (name, ms, im) in enumerate(cells):
        x, y = pad + (i % 3) * (w + pad), 40 + pad + (i // 3) * (h + cap + pad)
        out.paste(im, (x, y))
        d.text((x, y + h + 8), name.upper(), fill=(63, 224, 208), font=font(20))
        d.text((x + w - 110, y + h + 8), f"{ms:+d} ms", fill=(232, 176, 74), font=font(20))
    out.save(path)
    # a filmstrip of the transformation: every ~100 ms from the bite to the end, to see what the player sees between the beats
    strip = [min(frames, key=lambda f: abs((f[0] * 1000 - origin_ms) - (bite + k * 100))) for k in range(0, 16)]
    tw, th = w // 2, h // 2
    film = Image.new("RGB", (4 * tw, 4 * th), (0, 0, 0))
    for k, (ts, jpg) in enumerate(strip):
        im = Image.open(io.BytesIO(jpg)).convert("RGB").resize((tw, th), Image.LANCZOS)
        ImageDraw.Draw(im).text((8, 6), f"bite {round((ts * 1000 - origin_ms) - bite):+d} ms", fill=(232, 176, 74), font=font(16))
        film.paste(im, ((k % 4) * tw, (k // 4) * th))
    film.save(str(path).replace(".png", "_film.png"))
    return {"hushMs": round(hush), "lungeMs": ev["strikeBite"]["lungeMs"], "totalMs": ev["strikeEnd"]["totalMs"], "v": ev["strikePace"]["v"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    report, errors = {}, []
    with sync_playwright() as pw:
        br = launch(pw, a.headed)
        # ---- idle screens ----
        for w, h, name in ((1920, 1080, "slice_idle_1920"), (390, 844, "slice_idle_390")):
            ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=1 if w > 1000 else 2)
            page = ctx.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(PAGE)
            page.wait_for_function("window.__FEEL_READY === true || !!window.__canvasGame", timeout=30000)
            page.wait_for_timeout(3500)
            page.screenshot(path=str(OUT / f"{name}.png"))
            ctx.close()
        # ---- the help, full then short, through the screencast ----
        ctx = br.new_context(viewport={"width": 1280, "height": 720})
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(PAGE)
        page.wait_for_function("window.__FEEL_READY === true || !!window.__canvasGame", timeout=30000)
        page.wait_for_timeout(3000)
        page.mouse.click(640, 360)                      # a gesture, so the audio context starts and the clips load
        page.wait_for_timeout(2500)
        origin_ms = page.evaluate("performance.timeOrigin")
        cdp = ctx.new_cdp_session(page)
        frames = []

        def on_frame(p):
            frames.append((p["metadata"]["timestamp"], base64.b64decode(p["data"])))
            cdp.send("Page.screencastFrameAck", {"sessionId": p["sessionId"]})

        cdp.on("Page.screencastFrame", on_frame)
        for label in ("full", "short"):
            frames.clear()
            cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 88, "everyNthFrame": 1})
            page.wait_for_timeout(400)
            ev = record_strike(page, cdp, frames)
            cdp.send("Page.stopScreencast")
            page.wait_for_timeout(300)
            report[label] = sheet(list(frames), origin_ms, ev, f"THE HELP in the game / {ev['strikePace']['v']} version / {len(frames)} frames recorded",
                                  OUT / f"slice_help_{label}.png")
            report[label]["frames"] = len(frames)
            page.wait_for_timeout(1200)
        report["clips"] = page.evaluate("(() => { const M = window.__aud && window.__aud.moments; return M ? { state: M.state, loaded: Object.keys(M.buf).length, played: M.played } : null; })()")
        ctx.close()
        br.close()
    report["pageErrors"] = errors
    (OUT / "slice_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
