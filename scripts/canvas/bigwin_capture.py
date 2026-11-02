"""
bigwin_capture.py - the escalating big-win screens (docs/feel_design_plan.md, section C) on the CANVAS front end.

Needs the game server running:  python -m uvicorn slot_engine.api.app:app --port 8080

Loads /static/canvas/index.html at 1920x1080 on the real GPU, then drives window.__canvasGame.celebrate() directly
with one win per tier and captures to artifacts/canvas/:
  bigwin_t1_disturbance.png   20x   (T1: vignette, fog, a few far silhouettes)
  bigwin_t2_eyes.png          60x   (T2: eye pairs open around the number, cooler grade, 2x creatures)
  bigwin_t3_breach(_b).png    400x  (T3: 40% darker, push-in, creatures at the glass, chips, count stutters, number 1.25x)
  bigwin_t4_blackout.png      700x  (T4: the 500 ms blackout)
  bigwin_t4_leviathan.png     700x  (T4: the face behind the number, cracks propagating)
  bigwin_t4_slam.png          700x  (T4: the final 1.5x slam)
and prints per-tier escalation state, the frame-time p95 during T4, and any page errors.

    python scripts/canvas/bigwin_capture.py [--headed] [--portrait]
"""

import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "canvas"
PAGE = "http://127.0.0.1:8080/static/canvas/index.html"
GPU_ARGS = ["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"]

STATE_JS = """
() => { const g = window.__canvasGame, B = g && g.bwFx; if (!B) return null; const E = B.esc;
  return { t: +B.t.toFixed(2), tier: B.tier, dim: +E.dim.toFixed(2), dens: E.dens, cool: +E.cool.toFixed(2), push: +E.push.toFixed(3),
    eyesOpen: E.eyes.filter(e => e.open > 0.5).length, breachers: E.breachers.filter(b => b.on).length, breachN: E.breachN,
    blackout: +E.blackout.toFixed(2), face: +E.face.toFixed(2), faceEye: +E.faceEye.toFixed(2), crackA: +B.crackA.toFixed(2), chips: E.chips.length,
    amtScale: +E.amtScale.toFixed(2), fov: +B.fov.toFixed(1), critters: B.critters.filter(c => c.on).length, fogX: E.fogX,
    text: (document.querySelector('.bwamt') || {}).textContent, kicker: (document.querySelector('.bwkicker') || {}).textContent,
    cls: (document.querySelector('.bwfront') || {}).className }; }
"""

FPS_JS = """
() => new Promise((res) => { const ts = []; let last = performance.now(); const n = 90;
  const f = () => { const now = performance.now(); ts.push(now - last); last = now; if (ts.length < n) requestAnimationFrame(f); else { ts.sort((a, b) => a - b); res({ p50: +ts[Math.floor(n * 0.5)].toFixed(1), p95: +ts[Math.floor(n * 0.95)].toFixed(1) }); } };
  requestAnimationFrame(f); })
"""


def launch(p, headed=False):
    for channel in ("chrome", "msedge", None):
        try:
            kw = dict(headless=not headed, args=GPU_ARGS)
            return p.chromium.launch(channel=channel, **kw) if channel else p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001
            print(f"[bigwin] channel {channel!r} unavailable: {str(e).splitlines()[0]}")
    raise SystemExit("No Chromium-family browser available for Playwright.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--portrait", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    errs = []
    with sync_playwright() as p:
        browser = launch(p, a.headed)
        vp = {"width": 390, "height": 844} if a.portrait else {"width": 1920, "height": 1080}
        page = browser.new_page(viewport=vp, device_scale_factor=2 if a.portrait else 1)
        page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
        page.on("console", lambda m: errs.append(f"console.error: {m.text} ({m.location.get('url', '')})")
                if m.type == "error" and "favicon" not in (m.location.get("url", "") or "") else None)
        page.goto(PAGE + f"?engine=local&v={int(time.time())}", wait_until="load")
        page.wait_for_function("window.__FEEL_READY === true && !!window.__canvasGame", timeout=60000)
        page.wait_for_timeout(1500)
        sfx = "_por" if a.portrait else ""

        def start(mult):
            # bet 1, stake 1, win = mult; detached so we can sample while it runs
            page.evaluate(f"() => {{ window.__canvasGame.celebrate({mult}, 1, 1, false).catch(e => console.error('celebrate', e)); }}")

        def shot(name, ms):
            page.wait_for_timeout(ms)
            st = page.evaluate(STATE_JS)
            page.screenshot(path=str(OUT / f"bigwin_{name}{sfx}.png"))
            report[name] = st
            print(f"[bigwin] {name}: {json.dumps(st)}")

        def finish():
            page.wait_for_timeout(1200)
            page.evaluate("window.__canvasGame.onBigWinTap()")  # skip to the end
            page.wait_for_timeout(1600)
            page.evaluate("window.__canvasGame.onBigWinTap()")  # close
            page.wait_for_function("!window.__canvasGame.bwFx", timeout=30000)
            page.wait_for_timeout(600)

        start(20); shot("t1_disturbance", 3200); finish()
        start(60); shot("t2_eyes", 6200); finish()
        # 400x: the count reaches 100x at 8 s and 400x at 11 s; the first breacher hits the glass at ~9.2 s
        start(400); shot("t3_breach", 9300); shot("t3_breach_b", 900); finish()
        # 700x: 500x at 12 s -> 500 ms blackout -> the face from 12.5 s; the count ends at ~14.1 s and slams
        start(700)
        page.wait_for_function("(() => { const B = window.__canvasGame.bwFx; return B && B.esc.blackout >= 0; })()", timeout=40000)
        shot("t4_blackout", 200)
        shot("t4_leviathan", 1400)
        report["fps_t4"] = page.evaluate(FPS_JS)
        print(f"[bigwin] T4 frame time: {report['fps_t4']}")
        shot("t4_slam", 1400)
        page.wait_for_timeout(1200)
        page.evaluate("window.__canvasGame.onBigWinTap()")
        page.wait_for_function("!window.__canvasGame.bwFx", timeout=30000)
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / f"bigwin_after{sfx}.png"))
        browser.close()
    report["errors"] = errs
    (OUT / f"bigwin_report{sfx}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("[bigwin] errors:", errs or "none")


if __name__ == "__main__":
    main()
