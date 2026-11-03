"""
hero_capture.py - the 2.5D Leviathan hero shots (hero.js) on the CANVAS front end.

Needs the game server running:  python -m uvicorn slot_engine.api.app:app --port 8080

Loads /static/canvas/index.html at 1920x1080 on the real GPU and captures to artifacts/canvas/:
  hero_idle.png       base game 8 s in: the body must be a silhouette only (reveal printed)
  hero_eye.png        window.__levReact('loss') -> the painted eye at the glass
  hero_jaws.png       Director STRIKE -> the jaws close-up over the strike zone at the bite
  hero_rise.png       Director LEVEL UP -> the head rising under the level card
and prints the hero log entries (heroPlay/heroEnd/heroSkip), the texture sources (placeholder or painting) and page errors.

    python scripts/canvas/hero_capture.py [--headed] [--portrait]
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
() => { const g = window.__canvasGame, H = g && g.hero; return { reveal: g && g.L3 ? +g.L3.reveal.toFixed(3) : null, hero: H ? { ready: H.ready, failed: H.failed,
  loaded: H.loaded, cur: H.cur && H.cur.id, sources: Object.fromEntries(Object.entries(H.tex || {}).map(([k, v]) => [k, v.source])) } : null,
  heroZ: g && g.state.heroZ, level: g && g.state.level }; }
"""


def launch(p, headed=False):
    for channel in ("chrome", "msedge", None):
        try:
            kw = dict(headless=not headed, args=GPU_ARGS)
            return p.chromium.launch(channel=channel, **kw) if channel else p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001
            print(f"[hero] channel {channel!r} unavailable: {str(e).splitlines()[0]}")
    raise SystemExit("No Chromium-family browser available for Playwright.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--portrait", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    errs, report = [], {}
    sfx = "_por" if a.portrait else ""
    with sync_playwright() as p:
        browser = launch(p, a.headed)
        vp = {"width": 390, "height": 844} if a.portrait else {"width": 1920, "height": 1080}
        page = browser.new_page(viewport=vp, device_scale_factor=2 if a.portrait else 1)
        page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
        page.on("console", lambda m: errs.append(f"console.error: {m.text} ({m.location.get('url', '')})")
                if m.type == "error" and "favicon" not in (m.location.get("url", "") or "") else None)
        page.goto(PAGE + f"?engine=local&v={int(time.time())}", wait_until="load")
        page.wait_for_function("window.__FEEL_READY === true && !!window.__canvasGame", timeout=60000)
        page.wait_for_function("(() => { const H = window.__canvasGame.hero; return H && (H.loaded || H.failed); })()", timeout=30000)

        def shot(name, ms):
            page.wait_for_timeout(ms)
            st = page.evaluate(STATE_JS)
            page.screenshot(path=str(OUT / f"hero_{name}{sfx}.png"))
            report[name] = st
            print(f"[hero] {name}: {json.dumps(st)}")

        shot("idle", 8000)
        page.evaluate("window.__levReact('loss')")
        shot("eye", 1500)
        page.wait_for_timeout(2500)
        page.evaluate("() => { window.__canvasGame.dirStrike(); }")
        page.wait_for_function("(() => { const H = window.__canvasGame.hero; return H && H.cur && H.cur.id === 'lev_jaws'; })()", timeout=20000)
        shot("jaws", 900)
        page.wait_for_function("(() => !window.__canvasGame.isStriking)()", timeout=30000)
        page.wait_for_timeout(800)
        page.evaluate("() => { window.__canvasGame.dirLevelUp(); }")
        page.wait_for_function("(() => { const H = window.__canvasGame.hero; return H && H.cur && H.cur.id === 'lev_rise'; })()", timeout=20000)
        shot("rise", 1300)
        page.wait_for_timeout(4000)
        log = page.evaluate("(window.__FEEL_LOG || []).filter(e => /^hero/.test(e.type))")
        report["hero_log"] = log
        print("[hero] log:", json.dumps(log))
        browser.close()
    report["errors"] = errs
    (OUT / f"hero_report{sfx}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("[hero] errors:", errs or "none")


if __name__ == "__main__":
    main()
