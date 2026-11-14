"""
lev_capture.py - Leviathan presence check for the CANVAS front end (docs/feel_design_plan.md, section A).

Needs the game server running:  python -m uvicorn slot_engine.api.app:app --port 8080

Loads /static/canvas/index.html at 1920x1080 on the real GPU and captures to artifacts/canvas/:
  lev_idle.png            10 s in, base game (should be a silhouette only)
  lev_reveal.png          Director level 2 forces the reveal
  lev_nearmiss.png        window.__levAttention({x, y, hold: true}) - the head snaps to the cell and holds
  lev_prestrike.png       the hush before a Director STRIKE (dark, still, ambience -12 dB)
  lev_strike.png          the bite
  lev_reaction_loss.png   window.__levReact('loss') - an eye at the glass
  lev_reaction_win.png    window.__levReact('win') - recoil then lunge at the cells
  lev_breath_0/1/2.png    three frames 1 s apart (vertex displacement proof: pixel diff printed)
and prints the frame-time p95 (window.__levFps) sampled over 10 s of idle, plus any page errors.

    python scripts/canvas/lev_capture.py [--headed]
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

LEV_JS = """
() => { const g = window.__canvasGame, L = g && g.L3; return L ? { reveal: +L.reveal.toFixed(3), agit: +g.lv.agit.toFixed(2), hush: g.lv.hush, react: g.lv.react,
  att: g.lv.att && [Math.round(g.lv.att.x), Math.round(g.lv.att.y), g.lv.att.hold], breath: +g.L3.shared.uBreath.value.toFixed(4), pulse: +g.L3.shared.uPulse.value.toFixed(2),
  lb: +L.lb.toFixed(2), push: +L.push.toFixed(2), yawDeg: +(L.camYaw * 57.3).toFixed(2), strike: g.strikeAnim && g.strikeAnim.kind, dirLevel: g.state.dirLevel } : null; }
"""


def launch(p, headed=False):
    for channel in ("chrome", "msedge", None):
        try:
            kw = dict(headless=not headed, args=GPU_ARGS)
            return p.chromium.launch(channel=channel, **kw) if channel else p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001
            print(f"[lev] channel {channel!r} unavailable: {str(e).splitlines()[0]}")
    raise SystemExit("No Chromium-family browser available for Playwright.")


def pixel_diff(a, b):
    """mean absolute difference (0-255) over the PNGs a/b, decoded with Pillow if present."""
    try:
        from PIL import Image, ImageChops, ImageStat
    except Exception:  # noqa: BLE001
        return None
    ia, ib = Image.open(a).convert("L"), Image.open(b).convert("L")
    d = ImageChops.difference(ia, ib)
    st = ImageStat.Stat(d)
    bbox = d.point(lambda v: 255 if v > 12 else 0).getbbox()
    return {"mean": round(st.mean[0], 3), "changedBox": bbox}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    with sync_playwright() as p:
        browser = launch(p, a.headed)
        page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        errs = []
        page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
        page.on("console", lambda m: errs.append(f"console.error: {m.text}") if m.type == "error" and "favicon" not in (m.location.get("url", "") or "") else None)
        page.goto(PAGE + f"?profile=mga&director=1&v={int(time.time())}", wait_until="load")
        page.wait_for_function("window.__FEEL_READY === true && !!window.__canvasGame && !!window.__canvasGame.L3", timeout=60000)
        # start the audio context (bioluminescence reads the analyser) with a click on the stage
        page.mouse.click(60, 60)
        snap = lambda name: page.screenshot(path=str(OUT / name))  # noqa: E731

        # 1. idle: 10 s in, then sample the fps over the next 10 s
        page.wait_for_timeout(10000)
        snap("lev_idle.png")
        report["idle"] = page.evaluate(LEV_JS)
        page.evaluate("() => { window.__canvasGame.lv.ft.length = 0; }")
        # reveal share over 20 s of idle (sampled every 100 ms)
        rv = []
        for _ in range(100):
            page.wait_for_timeout(100)
            rv.append(page.evaluate("() => window.__canvasGame.L3.reveal"))
        report["fps_idle"] = page.evaluate("() => window.__levFps()")
        report["idle_reveal"] = {"mean": round(sum(rv) / len(rv), 3), "max": round(max(rv), 3), "shareAbove0.6": round(sum(1 for v in rv if v > 0.6) / len(rv), 3)}

        # 2. breathing: three frames 1 s apart with the swim clock and camera frozen (lv.freeze) and the creature revealed, so the diff is the displacement
        page.evaluate("() => window.__canvasGame.dirGoLevel(2)")
        page.wait_for_timeout(5000)
        page.evaluate("() => { const g = window.__canvasGame; g.lv.freeze = true; g.levAgitate(1, 6000); }")
        page.wait_for_timeout(600)
        for i in range(3):
            snap(f"lev_breath_{i}.png")
            report[f"breath_{i}"] = page.evaluate(LEV_JS)
            if i < 2:
                page.wait_for_timeout(1000)
        page.evaluate("() => { window.__canvasGame.lv.freeze = false; window.__canvasGame.dirGoLevel(0); }")
        report["breath_diff_01"] = pixel_diff(OUT / "lev_breath_0.png", OUT / "lev_breath_1.png")
        report["breath_diff_02"] = pixel_diff(OUT / "lev_breath_0.png", OUT / "lev_breath_2.png")
        page.wait_for_timeout(3000)

        # 3. near-miss stare: the missing cell on the last reel (middle row)
        page.evaluate("""() => { const g = window.__canvasGame, G = g.geo(); const [x, y] = g.cellXY(G.cols - 1, 2, G);
          window.__levAttention({ x: x + G.cell / 2, y: y + G.cell / 2, hold: true, ms: 4000 }); g.levAgitate(1, 4000); }""")
        page.wait_for_timeout(900)
        snap("lev_nearmiss.png")
        report["nearmiss"] = page.evaluate(LEV_JS)
        page.wait_for_timeout(3500)

        # 4. Director level 2 forces the reveal
        page.evaluate("() => window.__canvasGame.dirGoLevel(2)")
        page.wait_for_timeout(4500)
        snap("lev_reveal.png")
        report["reveal"] = page.evaluate(LEV_JS)

        # 5. reaction shots
        page.evaluate("() => window.__levReact('loss')")
        page.wait_for_timeout(1600)
        snap("lev_reaction_loss.png")
        report["react_loss"] = page.evaluate(LEV_JS)
        page.wait_for_timeout(3200)
        page.evaluate("() => window.__levReact('win')")
        page.wait_for_timeout(1100)
        snap("lev_reaction_win.png")
        report["react_win"] = page.evaluate(LEV_JS)
        page.wait_for_timeout(3000)

        # 6. Director STRIKE: the hush, then the bite
        page.evaluate("() => { window.__canvasGame.dirStrike(); }")
        page.wait_for_function("() => window.__canvasGame.lv.hush === true", timeout=5000)
        page.wait_for_timeout(900)
        snap("lev_prestrike.png")
        report["prestrike"] = page.evaluate(LEV_JS)
        page.wait_for_function("() => window.__canvasGame.lv.hush === false", timeout=6000)
        page.wait_for_function("() => { const g = window.__canvasGame, S = g.strikeAnim; return !!S && !S.kind && (g.levT - S.u0) / S.dur >= 0.335; }", timeout=8000)
        snap("lev_strike.png")
        report["strike"] = page.evaluate(LEV_JS)
        page.wait_for_function("() => !window.__canvasGame.busy", timeout=20000)
        page.evaluate("() => { window.__canvasGame.lv.ft.length = 0; }")
        page.wait_for_timeout(5000)
        report["fps_after"] = page.evaluate("() => window.__levFps()")
        report["errors"] = errs
        browser.close()
    print(json.dumps(report, indent=1))
    (OUT / "lev_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
