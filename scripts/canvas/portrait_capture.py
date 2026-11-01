"""
portrait_capture.py - orientation check for the CANVAS front end (slot_engine/static/canvas/index.html).

Needs the game server running:  python -m uvicorn slot_engine.api.app:app --port 8080

Captures the page at phone / tablet portrait sizes and at the two landscape sizes -> artifacts/canvas/portrait_<w>x<h>.png,
then (unless --no-play) plays real spins and one STANDARD_BONUS_100X buy in portrait at 390x844, checking for page errors
and that the symbol canvas / overlays are laid out inside the stage. Extra captures: portrait_390x844_spin.png (mid-spin),
portrait_390x844_buy.png (buy modal), portrait_390x844_bonus.png (feature overlay), portrait_rotate_*.png (live rotation).

    python scripts/canvas/portrait_capture.py [--spins 2] [--no-play] [--headed] [--sizes 390x844,430x932,768x1024,1920x1080,1280x720]
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
SIZES = [(390, 844), (430, 932), (768, 1024), (1920, 1080), (1280, 720)]

LAYOUT_JS = """
() => {
  const q = (s) => document.querySelector(s);
  const r = (el) => { if (!el) return null; const b = el.getBoundingClientRect(); return [Math.round(b.left), Math.round(b.top), Math.round(b.width), Math.round(b.height)]; };
  const hud = q('.hud');
  const cells = [...document.querySelectorAll('.cell')].map(r);
  const sym = q('canvas[data-sym]');
  return {
    orient: document.documentElement.getAttribute('data-orient'),
    hudCls: hud && hud.className, hud: r(hud), win: [innerWidth, innerHeight],
    frame: r(q('.frame')), sym: r(sym), symPx: sym && [sym.width, sym.height], cells: cells.length, cell0: cells[0], cellLast: cells[cells.length - 1],
    spin: r(q('button.spinbtn')), buy: r(q('button.ibtn.buy')), strip: r(q('.panel.ps')), pl: r(q('.panel.pl')), pr: r(q('.panel.pr')),
    lev3d: (() => { const c = q('canvas[data-lev3d]'); return c && [c.width, c.height]; })(),
    hudfx: (() => { const c = q('canvas[data-hudfx]'); return c && [c.width, c.height]; })(),
    abyss: (() => { const c = q('canvas[data-abyss]'); return c && [c.width, c.height, c.getAttribute('data-horiz')]; })(),
    gl: !!(window.__canvasGame && window.__canvasGame.E && window.__canvasGame.E.gl),
    cellsWithSymbols: window.__canvasGame && window.__canvasGame.E ? window.__canvasGame.E.cells.filter(Boolean).length : -1,
  };
}
"""


def launch(p, headed=False):
    for channel in ("chrome", "msedge", None):
        try:
            kw = dict(headless=not headed, args=GPU_ARGS)
            return p.chromium.launch(channel=channel, **kw) if channel else p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001
            print(f"[portrait] channel {channel!r} unavailable: {str(e).splitlines()[0]}")
    raise SystemExit("No Chromium-family browser available for Playwright.")


def hook_errors(page, errs):
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.on("console", lambda m: errs.append(f"console.error: {m.text} ({m.location.get('url', '')})")
            if m.type == "error" and "favicon" not in (m.location.get("url", "") or "") else None)


def open_page(browser, w, h, extra=""):
    page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
    errs = []
    hook_errors(page, errs)
    page.goto(PAGE + f"?profile=mga&v={int(time.time())}{extra}", wait_until="load")
    page.wait_for_function("window.__FEEL_READY === true && !!window.__canvasGame", timeout=60000)
    page.wait_for_timeout(2500)
    return page, errs


def check(name, info, errs):
    bad = []
    w, h = info["win"]
    por = h > w
    if (info["orient"] == "portrait") != por:
        bad.append(f"orient {info['orient']} for window {w}x{h}")
    if por and info["pl"]:
        bad.append("left landscape panel visible in portrait")
    if por and not info["strip"]:
        bad.append("no instrument strip in portrait")
    if not por and info["strip"]:
        bad.append("instrument strip visible in landscape")
    hx, hy, hw, hh = info["hud"]
    for key in ("frame", "spin", "buy", "strip", "pl", "pr"):
        rc = info[key]
        if not rc:
            continue
        x, y, rw, rh = rc
        if x < hx - 1 or y < hy - 1 or x + rw > hx + hw + 1 or y + rh > hy + hh + 1:
            bad.append(f"{key} {rc} outside the stage {info['hud']}")
    if info["cells"] not in (25, 30):
        bad.append(f"{info['cells']} cells")
    if info["cell0"] and por:
        cw = info["cell0"][2]
        scale = hw / 1080
        if cw / scale < 177:
            bad.append(f"cell {cw / scale:.0f} stage px < 177")
    if not info["gl"]:
        bad.append("symbol renderer has no GL context")
    exp = [1080, 1920] if por else [1920, 1080]
    if info["lev3d"] != exp or info["hudfx"] != exp:
        bad.append(f"full-screen canvases {info['lev3d']} / {info['hudfx']} != {exp}")
    if errs:
        bad.extend(errs)
    print(f"[{name}] {'OK' if not bad else 'FAIL'} orient={info['orient']} hud={info['hud']} frame={info['frame']} cell0={info['cell0']} spin={info['spin']} abyss={info['abyss']}")
    for b in bad:
        print("    -", b)
    return not bad


def wait_cycle(page, n, timeout=300000):
    page.wait_for_function(f"(window.__FEEL_CYCLE_DONE || 0) >= {n}", timeout=timeout)


def play(browser, spins, headed):
    page, errs = open_page(browser, 390, 844)
    ok = True
    done = 0
    for i in range(spins):
        page.click("button.spinbtn")
        if i == 0:
            page.wait_for_timeout(450)
            page.screenshot(path=str(OUT / "portrait_390x844_spin.png"))
        done += 1
        wait_cycle(page, done)
        page.wait_for_timeout(300)
    info = page.evaluate(LAYOUT_JS)
    if info["cellsWithSymbols"] not in (25, 30):
        ok = False
        print("    - symbols after spins:", info["cellsWithSymbols"])
    page.screenshot(path=str(OUT / "portrait_390x844_afterspins.png"))
    # bonus buy through the UI
    page.click("button.ibtn.buy")
    page.wait_for_selector(".bcard .bbtn")
    page.wait_for_timeout(400)
    page.screenshot(path=str(OUT / "portrait_390x844_buy.png"))
    cards = page.evaluate("() => [...document.querySelectorAll('.bcard')].map(c => { const b = c.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; })")
    for c in cards:
        if c[0] < 0 or c[1] < 0 or c[2] > 390 or c[3] > 844:
            ok = False
            print("    - buy card outside the viewport:", c)
    page.locator(".bcard .bbtn").nth(1).click()  # STANDARD_BONUS_100X
    try:
        page.wait_for_function("!!document.querySelector('.ov.feat, .ov.lu')", timeout=20000)
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT / "portrait_390x844_bonus.png"))
        ov = page.evaluate("() => { const o = document.querySelector('.ov.feat .card, .ov.lu .card'); if (!o) return null; const b = o.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; }")
        if ov and (ov[0] < 0 or ov[2] > 390):
            ok = False
            print("    - feature card overflows:", ov)
    except Exception as e:  # noqa: BLE001
        print("    - no feature overlay seen:", str(e).splitlines()[0])
    # the bonus runs to its end (a big-win count-up may need a tap)
    t0 = time.time()
    while time.time() - t0 < 240:
        if page.evaluate(f"(window.__FEEL_CYCLE_DONE || 0) >= {done + 1}"):
            break
        if page.evaluate("!!document.querySelector('.bwfront')"):
            page.wait_for_timeout(1200)
            page.screenshot(path=str(OUT / "portrait_390x844_bigwin.png"))
            page.evaluate("window.__canvasGame.onBigWinTap()")
        page.wait_for_timeout(500)
    done += 1
    wait_cycle(page, done)
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "portrait_390x844_afterbonus.png"))
    info = page.evaluate(LAYOUT_JS)
    if info["cellsWithSymbols"] not in (25, 30):
        ok = False
        print("    - symbols after bonus:", info["cellsWithSymbols"])
    # live rotation: portrait -> landscape -> portrait on the same page
    page.set_viewport_size({"width": 844, "height": 390})
    page.wait_for_timeout(1500)
    info_l = page.evaluate(LAYOUT_JS)
    page.screenshot(path=str(OUT / "portrait_rotate_landscape.png"))
    ok = check("rotate->landscape", info_l, []) and ok
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(1500)
    info_p = page.evaluate(LAYOUT_JS)
    page.screenshot(path=str(OUT / "portrait_rotate_portrait.png"))
    ok = check("rotate->portrait", info_p, []) and ok
    if errs:
        ok = False
        for e in errs:
            print("    -", e)
    print(f"[play] {'OK' if ok else 'FAIL'} spins={spins} errors={len(errs)}")
    page.close()
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spins", type=int, default=2)
    ap.add_argument("--no-play", action="store_true")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--sizes", default=",".join(f"{w}x{h}" for w, h in SIZES))
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sizes = [tuple(int(v) for v in sz.split("x")) for sz in a.sizes.split(",") if sz]
    ok = True
    with sync_playwright() as p:
        browser = launch(p, a.headed)
        for w, h in sizes:
            page, errs = open_page(browser, w, h)
            info = page.evaluate(LAYOUT_JS)
            page.screenshot(path=str(OUT / f"portrait_{w}x{h}.png"))
            ok = check(f"{w}x{h}", info, errs) and ok
            page.close()
        if not a.no_play:
            ok = play(browser, a.spins, a.headed) and ok
        browser.close()
    print("PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
