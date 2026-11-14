"""
hero_capture.py - the 2.5D Leviathan hero shots (hero.js) on the CANVAS front end.

Needs the game server running:  python -m uvicorn slot_engine.api.app:app --port 8080

Loads /static/canvas/index.html at 1920x1080 on the real GPU and captures to artifacts/canvas/:
  hero_idle.png       base game 8 s in: the body must be a silhouette only (reveal printed)
  hero_eye.png        window.__levReact('loss') -> the painted eye at the glass
  hero_jaws.png       Director STRIKE -> the jaws close-up over the strike zone at the bite
  hero_rise.png       Director LEVEL UP -> the head rising under the level card
  hero_*_seq.png      6-frame contact sheets: idle (1 s apart, pointer beside reel 5); the others step the frozen hero clock
                      (H.freezeAt): eye through its first blink (60 ms apart from arrival+280), jaws through the chomp
                      (+70/150/240/340/480/640 ms), rise through the head's blink (60 ms apart from 2660), maw 250 ms apart from
                      1 s after the T4 blackout
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
        page.goto(PAGE + f"?engine=local&director=1&v={int(time.time())}", wait_until="load")
        page.wait_for_function("window.__FEEL_READY === true && !!window.__canvasGame", timeout=60000)
        page.wait_for_function("(() => { const H = window.__canvasGame.hero; return H && (H.loaded || H.failed); })()", timeout=30000)

        def shot(name, ms, burst=0, every=220, steps=None, rel="chomp"):
            page.wait_for_timeout(ms)
            st = page.evaluate(STATE_JS)
            page.screenshot(path=str(OUT / f"hero_{name}{sfx}.png"))
            report[name] = st
            print(f"[hero] {name}: {json.dumps(st)}")
            if burst:
                # motion evidence for the reviewer: a contact sheet of `burst` frames `every` ms apart (3 per row, half size)
                from PIL import Image
                import io as _io
                frames = []
                for i in range(burst):
                    if steps:
                        # stepped: freeze the hero clock at this offset (into the jaws' chomp, or into the shot) before the frame
                        base = "H.cur.chompT + " if rel == "chomp" else ""
                        page.evaluate(f"() => {{ const H = window.__canvasGame.hero; if (H.cur) H.freezeAt({base}{steps[i]}); }}")
                        page.wait_for_timeout(60)
                    frames.append(Image.open(_io.BytesIO(page.screenshot())).convert("RGB"))
                    if every: page.wait_for_timeout(every)
                w, h = frames[0].size
                cw, ch = w // 2, h // 2
                cols = 3
                rows = (len(frames) + cols - 1) // cols
                sheet = Image.new("RGB", (cw * cols, ch * rows), (0, 0, 0))
                for i, f in enumerate(frames):
                    sheet.paste(f.resize((cw, ch)), ((i % cols) * cw, (i // cols) * ch))
                sheet.save(OUT / f"hero_{name}_seq{sfx}.png")
                print(f"[hero] {name}: {len(frames)} frames {'at ' + ('chomp+' if rel == 'chomp' else 'shot+') + ','.join(map(str, steps)) + ' ms' if steps else str(every) + ' ms apart'} -> hero_{name}_seq{sfx}.png")

        # the pointer parked beside reel 5 so the look-at engages; 6 frames 1 s apart for breath / look-at
        page.mouse.move(1430 if not a.portrait else 300, 500 if not a.portrait else 600)
        shot("idle", 8000, burst=6, every=1000)
        page.evaluate("window.__levReact('loss')")
        # the still mid-entry; the sheet steps the frozen hero clock through the first blink (arrival 1100 + 280 ms, 60 ms apart)
        shot("eye", 300, burst=6, steps=[1380, 1440, 1500, 1560, 1620, 1680], rel="el")
        page.evaluate("() => { window.__canvasGame.hero.freezeAt(null); }")
        page.wait_for_timeout(2500)
        page.evaluate("() => { window.__canvasGame.dirStrike(); }")
        page.wait_for_function("(() => { const H = window.__canvasGame.hero; return H && H.cur && H.cur.id === 'lev_jaws'; })()", timeout=20000)
        # the still is the bite itself (the chomp lands ~900 ms after the shot starts). A full-page screenshot takes longer than the
        # 70 ms slam, so the sheet steps the hero clock (H.freezeAt) through the choreography: slam done (70), hit-stop hold (150),
        # overshoot (240), then the drop (340 / 480 / 640 ms after the chomp)
        page.wait_for_function("(() => { const H = window.__canvasGame.hero; return H && H.cur && H.cur.id === 'lev_jaws' && H.cur.chompT != null; })()", timeout=20000)
        page.evaluate("() => { const H = window.__canvasGame.hero; H.freezeAt(H.cur.chompT + 70); }")
        page.wait_for_timeout(60)
        shot("jaws", 0, burst=6, every=0, steps=[70, 150, 240, 340, 480, 640])
        page.evaluate("() => { window.__canvasGame.hero.freezeAt(null); }")
        page.wait_for_function("(() => !window.__canvasGame.isStriking)()", timeout=30000)
        page.wait_for_timeout(800)
        page.evaluate("() => { window.__canvasGame.dirLevelUp(); }")
        page.wait_for_function("(() => { const H = window.__canvasGame.hero; return H && H.cur && H.cur.id === 'lev_rise'; })()", timeout=20000)
        # the sheet steps the frozen clock through the head's blink (arrival 1400 + 1260 ms, 60 ms apart)
        shot("rise", 200, burst=6, steps=[2660, 2720, 2780, 2840, 2900, 2960], rel="el")
        page.evaluate("() => { window.__canvasGame.hero.freezeAt(null); }")
        page.wait_for_timeout(4000)
        # the maw (500x tier): 6 frames 500 ms apart from the T4 blackout
        page.evaluate("() => { window.__canvasGame.celebrate(700, 1, 1, false).catch(e => console.error('celebrate', e)); }")
        page.wait_for_function("(() => { const B = window.__canvasGame.bwFx; return B && B.esc.blackout >= 0; })()", timeout=40000)
        # the maw starts 500 ms into the blackout; the sheet runs 250 ms apart from 1 s after the blackout (frozen clock, shot+500..1750)
        page.wait_for_function("(() => { const H = window.__canvasGame.hero; return H && H.cur && H.cur.id === 'lev_maw'; })()", timeout=20000)
        page.evaluate("() => { window.__canvasGame.hero.freezeAt(500); }")
        shot("maw", 60, burst=6, steps=[500, 750, 1000, 1250, 1500, 1750], rel="el")
        page.evaluate("() => { window.__canvasGame.hero.freezeAt(null); }")
        page.wait_for_timeout(1500)
        page.evaluate("window.__canvasGame.onBigWinTap()")
        page.wait_for_timeout(1600)
        page.evaluate("window.__canvasGame.onBigWinTap()")
        page.wait_for_function("!window.__canvasGame.bwFx", timeout=30000)
        page.wait_for_timeout(500)
        log = page.evaluate("(window.__FEEL_LOG || []).filter(e => /^hero/.test(e.type))")
        report["hero_log"] = log
        print("[hero] log:", json.dumps(log))
        browser.close()
    report["errors"] = errs
    (OUT / f"hero_report{sfx}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("[hero] errors:", errs or "none")


if __name__ == "__main__":
    main()
