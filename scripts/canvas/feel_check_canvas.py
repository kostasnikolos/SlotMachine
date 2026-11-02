"""
feel_check_canvas.py - game-feel gate on the CANVAS front end (slot_engine/static/canvas/index.html) with real server outcomes.

Needs the game server running:  python -m uvicorn slot_engine.api.app:app --port 8080

For each profile (mga, ukgc by default) it loads /static/canvas/index.html?profile=<p>, plays N real spins (a slam attempt
during the first grid drop), then one real STANDARD_BONUS_100X buy through the UI (button.ibtn.buy -> second .bcard .bbtn),
presses skip during the bonus count-up if one happens (and saves artifacts/canvas/feel_bigwin.png while the tier screen is up),
dumps window.__FEEL_LOG to artifacts/canvas/feel_<profile>.json and checks gate items 1, 2, 4, 5, 6 of docs/game_feel_teardown.md.

    python scripts/canvas/feel_check_canvas.py [--spins 4] [--profiles mga,ukgc] [--no-bonus] [--headed]
"""

import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "canvas"
PAGE = "http://127.0.0.1:8080/static/canvas/index.html"
TIERS = [("big", 15), ("mega", 40), ("epic", 100), ("abyssal", 500)]
FLOOR = {"mga": 0, "ukgc": 2500, "de": 5000}
GPU_ARGS = ["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"]


def launch(p, headed=False):
    for channel in ("chrome", "msedge", None):
        try:
            kw = dict(headless=not headed, args=GPU_ARGS)
            return p.chromium.launch(channel=channel, **kw) if channel else p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001 - try the next available browser
            print(f"[canvas] channel {channel!r} unavailable: {str(e).splitlines()[0]}")
    raise SystemExit("No Chromium-family browser available for Playwright.")


def money(v):
    return f"{v:,.2f}"


def wait_cycle(page, n, timeout=300000):
    page.wait_for_function(f"(window.__FEEL_CYCLE_DONE || 0) >= {n}", timeout=timeout)


def play(browser, profile, spins, bonus):
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    errs = []
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    # console errors other than the server's missing favicon (a pre-existing 404 on every page load)
    page.on("console", lambda m: errs.append(f"console.error: {m.text} ({m.location.get('url', '')})")
            if m.type == "error" and "favicon" not in (m.location.get("url", "") or "") else None)
    page.goto(PAGE + f"?profile={profile}&v={int(time.time())}", wait_until="load")
    page.wait_for_function("window.__FEEL_READY === true && !!window.__canvasGame", timeout=60000)
    page.wait_for_timeout(1500)
    done = 0
    for i in range(spins):
        page.click("button.spinbtn")
        if i == 0:
            page.wait_for_timeout(350)
            page.keyboard.press("Space")  # slam attempt during the grid drop
        done += 1
        wait_cycle(page, done)
        page.wait_for_timeout(200)
    if bonus:
        page.click("button.ibtn.buy")
        page.wait_for_selector(".bcard .bbtn")
        page.locator(".bcard .bbtn").nth(1).click()  # STANDARD_BONUS_100X
        try:
            page.wait_for_function(
                "window.__FEEL_LOG.some(e => e.type === 'countStart' && e.t > (window.__FEEL_LOG.filter(x => x.type === 'cycleEnd').slice(-1)[0] || {t: 0}).t)"
                f" || (window.__FEEL_CYCLE_DONE || 0) >= {done + 1}", timeout=300000)
            if page.evaluate(f"(window.__FEEL_CYCLE_DONE || 0) < {done + 1}"):
                page.wait_for_timeout(1300)
                page.screenshot(path=str(OUT / "feel_bigwin.png"))
                page.evaluate("window.__canvasGame.onBigWinTap()")  # skip the count-up (the overlay covers the spin button)
        except Exception as e:  # noqa: BLE001
            errs.append(f"bonus wait: {e}")
        done += 1
        wait_cycle(page, done)
    log = page.evaluate("window.__FEEL_LOG")
    page.close()
    return log, errs


def cycles(log):
    out, cur = [], None
    for e in log:
        if e["type"] == "press":
            cur = [e]
        elif cur is not None:
            cur.append(e)
            if e["type"] == "cycleEnd":
                out.append(cur)
                cur = None
    return out


def gate(log, profile):
    cs = cycles(log)
    res = {}
    of = lambda c, t: [e for e in c if e["type"] == t]  # noqa: E731
    if not cs:
        return {"G1 min cycle / no turbo-slam": (False, "no complete cycle logged")}

    # G1: cycle floor, no turbo / slam honoured outside mga, columns of the base drop stop left to right
    bad, notes = [], []
    for c in cs:
        end, press = of(c, "cycleEnd")[0], c[0]
        if end["cycleMs"] < FLOOR[profile]:
            bad.append(f"cycle {end['cycleMs']}ms")
        if profile != "mga" and (of(c, "slam") or press.get("turbo")):
            bad.append("slam/turbo honoured")
        stops = of(c, "reelStop")
        if not stops:
            bad.append("no column stops logged")
        cols = [e["col"] for e in stops]
        # the first grid drop of the cycle: all columns, in order
        first = cols[:5] if len(cols) >= 5 else cols
        if first != sorted(first) or len(set(first)) != len(first):
            bad.append(f"column order {first}")
    ms = [of(c, "cycleEnd")[0]["cycleMs"] for c in cs]
    pads = [of(c, "pad")[0]["ms"] for c in cs if of(c, "pad")]
    notes.append(f"{len(cs)} cycles, min {min(ms)}ms max {max(ms)}ms, padded {sum(1 for p in pads if p > 0)}x (max {max(pads) if pads else 0}ms), "
                 f"slam honoured {sum(len(of(c, 'slam')) for c in cs)}, ignored {sum(len(of(c, 'slamIgnored')) for c in cs)}")
    res["G1 min cycle / no turbo-slam"] = (not bad, "; ".join(notes + bad[:3]))

    # G2: no celebration on a return <= stake
    ldw = [c for c in cs if 0 < of(c, "cycleEnd")[0]["won"] <= c[0]["stake"]]
    if profile == "mga":
        res["G2 no LDW celebration"] = (None, f"n/a under mga ({len(ldw)} LDW cycles, celebration allowed)")
    elif ldw:
        n = sum(len(of(c, "celebrationSound")) + len(of(c, "countStart")) + len(of(c, "tier")) for c in ldw)
        res["G2 no LDW celebration"] = (n == 0, f"{len(ldw)} cycles with 0 < return <= stake, celebration events {n}")
    else:
        res["G2 no LDW celebration"] = (None, "n/a (no return <= stake this run)")

    # G4: cascade step 900-2300 ms (slowed twice per user 2026-11-02), long chains keep >= 70%, running total visible >= 300 ms
    ends = [e for e in log if e["type"] == "stepEnd"]
    if ends:
        durs = [e["ms"] for e in ends]
        ok = all(900 <= d <= 2300 for d in durs)
        chains, cur = [], []
        for e in ends:
            if e["step"] == 1 and cur:
                chains.append(cur)
                cur = []
            cur.append(e["ms"])
        chains.append(cur)
        long_ = [ch for ch in chains if len(ch) >= 6]
        ok &= all(ch[-1] >= 0.7 * ch[0] for ch in long_)
        vis = []
        for c in cs:
            ts = [e["t"] for e in of(c, "stepWin")] + [of(c, "cycleEnd")[0]["t"]]
            vis += [b - a for a, b in zip(ts, ts[1:])]
        ok &= min(vis) >= 300
        res["G4 cascade pacing"] = (ok, f"{len(durs)} steps {min(durs)}-{max(durs)}ms, chains>=6: {len(long_)} "
                                        f"{[round(ch[-1] / ch[0], 2) for ch in long_]}, min total visible {min(vis):.0f}ms")
    else:
        res["G4 cascade pacing"] = (None, "n/a (no cascades)")

    # G5: hit-stop 3-6 frames (50-100 ms planned), shake gone within 300 ms
    hs = [e for e in log if e["type"] == "hitStopStart"]
    he = [e for e in log if e["type"] == "hitStopEnd"]
    sh = [e for e in log if e["type"] == "shakeEnd"]
    if hs and he:
        ok = all(50 <= h["plannedMs"] <= 100 for h in hs) and all(s["ms"] <= 300 for s in sh)
        ok &= all(2 <= h["frames"] <= 7 for h in he)  # one frame of scheduling slack either side of the 3-6 target
        kinds = sorted({h["kind"] for h in hs})
        res["G5 hit-stop + shake"] = (ok, f"{len(hs)} heavy hits {kinds}; planned {sorted({h['plannedMs'] for h in hs})}ms, "
                                          f"frozen {min(h['frames'] for h in he)}-{max(h['frames'] for h in he)} frames, shake max {max(s['ms'] for s in sh) if sh else 0}ms")
    else:
        res["G5 hit-stop + shake"] = (None, "n/a (no heavy hit this run)")

    # G6: tiers at the configured multiples, skip lands on the exact final value within 2 frames
    counts = [c for c in cs if of(c, "countStart")]
    if counts:
        ok, notes = True, []
        for c in counts:
            st, ce = of(c, "countStart")[0], (of(c, "countEnd") or [None])[0]
            if ce is None:
                ok = False
                notes.append("count never ended")
                continue
            bet = c[0]["bet"]
            want = [t for t, m in TIERS if st["target"] / bet >= m]
            got = of(c, "tier")
            ids = [t["id"] for t in got]
            ok &= ids == want
            ok &= all(t["skipped"] or t["mult"] >= dict(TIERS)[t["id"]] for t in got)
            ok &= ce["shownText"] == money(st["target"])
            si, sl = of(c, "skipInput"), of(c, "skipLanded")
            lag = (sl[0]["f"] - si[0]["inputF"]) if si and sl else None
            if si and not sl:
                ok = False
            if lag is not None:
                ok &= lag <= 2
            notes.append(f"{st['target'] / bet:.1f}x -> {[(t['id'], t['mult']) for t in got] or 'no tier'}, final {ce['shownText']}"
                         + (f", skip {lag} frame(s)" if lag is not None else ""))
        res["G6 tiers + skip"] = (ok, "; ".join(notes))
    else:
        res["G6 tiers + skip"] = (None, "n/a (no count-up this run)")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spins", type=int, default=4)
    ap.add_argument("--profiles", default="mga,ukgc")
    ap.add_argument("--no-bonus", action="store_true")
    ap.add_argument("--headed", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    failed = False
    with sync_playwright() as p:
        browser = launch(p, a.headed)
        for prof in a.profiles.split(","):
            log, errs = play(browser, prof, a.spins, not a.no_bonus)
            (OUT / f"feel_{prof}.json").write_text(json.dumps(log, indent=1))
            print(f"\n== canvas ?profile={prof} ==")
            for k, (ok, note) in gate(log, prof).items():
                failed |= ok is False
                print(f"  {'N/A ' if ok is None else ('PASS' if ok else 'FAIL')}  {k}: {note}")
            if errs:
                failed = True
                print("  FAIL  page errors:", errs[:3])
            else:
                print("  PASS  no page errors")
        browser.close()
    print("\nOVERALL:", "FAIL" if failed else "PASS")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
