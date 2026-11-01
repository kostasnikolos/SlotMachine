"""
feel_check_live.py - game-feel gate on the LIVE game (slot_engine/static/index.html) with real server outcomes.

Needs the game server running:  python -m uvicorn slot_engine.api.app:app --port 8080

1. Baseline: loads the game WITHOUT ?feel=1, asserts no feel code is loaded, saves
   artifacts/stage_v2/live_noflag_desktop.png and a side-by-side with artifacts/current_game_desktop.png,
   and reports pixel difference on the static UI regions (fish/bubbles animate, so the full frame never matches).
2. Feel: for each profile, loads /?feel=1&profile=<p>, plays N real spins (one slam attempt on the first),
   then one real 100x bonus buy (skip pressed during its count-up), dumps window.__FEEL_LOG to
   artifacts/stage_v2/live_feel_<profile>.json and checks gate items 1, 2, 4, 5, 6.

    python scripts/stage_v2/feel_check_live.py [--spins 6] [--profiles mga,ukgc] [--no-bonus]
"""

import argparse
import json
import sys
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture import OUT, launch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = "http://127.0.0.1:8080/"
TIERS = [("big", 15), ("mega", 40), ("epic", 100), ("abyssal", 500)]
FLOOR = {"mga": 0, "ukgc": 2500, "de": 5000}
# static UI regions on the 1920x1080 baseline (header, grid frame, side panels, footer HUD)
REGIONS = {"header": (160, 90, 1760, 160), "grid": (700, 300, 1220, 860), "left panel": (500, 290, 680, 770),
           "right panel": (1240, 290, 1420, 770), "footer HUD": (160, 900, 1760, 990)}


def baseline(browser):
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto(BASE + f"?v={int(time.time())}", wait_until="load")
    page.wait_for_function("window.slotGame && window.__RENDER_READY", timeout=60000)
    page.wait_for_timeout(2500)
    feel_loaded = page.evaluate("typeof window.FEEL !== 'undefined' || typeof window.FEEL_DIRECTOR !== 'undefined'")
    scripts = page.evaluate("[...document.scripts].map(s => s.src).filter(s => s.includes('feel'))")
    shot = OUT / "live_noflag_desktop.png"
    page.screenshot(path=str(shot))
    page.close()
    ref = Image.open(ROOT / "artifacts" / "current_game_desktop.png").convert("RGB")
    cur = Image.open(shot).convert("RGB")
    side = Image.new("RGB", (1920, 540))
    side.paste(ref.resize((960, 540)), (0, 0))
    side.paste(cur.resize((960, 540)), (960, 0))
    side.save(OUT / "live_noflag_vs_baseline.png")
    diffs = {}
    for name, box in REGIONS.items():
        d = ImageChops.difference(ref.crop(box), cur.crop(box)).convert("L")
        diffs[name] = round(ImageStat.Stat(d).mean[0], 2)
    full = round(ImageStat.Stat(ImageChops.difference(ref, cur).convert("L")).mean[0], 2)
    ok = not feel_loaded and not scripts and max(diffs.values()) < 12
    return ok, f"feel code loaded={feel_loaded}, mean abs diff per region {diffs}, full frame {full} (0-255)"


def wait_cycle(page, n, timeout=240000):
    page.wait_for_function(f"(window.__FEEL_CYCLE_DONE || 0) >= {n}", timeout=timeout)


def play(browser, profile, spins, bonus):
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(BASE + f"?feel=1&profile={profile}&v={int(time.time())}", wait_until="load")
    page.wait_for_function("window.__FEEL_READY === true", timeout=60000)
    page.wait_for_timeout(800)
    done = 0
    for i in range(spins):
        page.click("#btn-spin")
        if i == 0:
            page.wait_for_timeout(300)
            page.keyboard.press("Space")  # slam attempt during the reels
        done += 1
        wait_cycle(page, done)
        page.wait_for_timeout(150)
    if bonus:
        page.evaluate("void slotGame.triggerBonusBuy('STANDARD_BONUS_100X')")  # fire-and-forget (evaluate would await the whole cycle)
        try:
            page.wait_for_function(f"window.__FEEL_LOG.some(e => e.type === 'countStart' && e.t > (window.__FEEL_LOG.filter(x => x.type === 'cycleEnd').slice(-1)[0] || {{t: 0}}).t) || (window.__FEEL_CYCLE_DONE || 0) >= {done + 1}", timeout=240000)
            if page.evaluate(f"(window.__FEEL_CYCLE_DONE || 0) < {done + 1}"):
                page.wait_for_timeout(1200)
                page.evaluate("document.getElementById('btn-spin').click()")  # skip the count-up (button pulses, so no actionability wait)
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

    # G1
    bad, notes = [], []
    for c in cs:
        end, press = of(c, "cycleEnd")[0], c[0]
        if end["cycleMs"] < FLOOR[profile]:
            bad.append(f"cycle {end['cycleMs']}ms")
        if profile != "mga" and (of(c, "slam") or press.get("turbo")):
            bad.append("slam/turbo honoured")
        st = [e["plannedMs"] for e in of(c, "reelStop")]
        for k in range(0, len(st), 5):
            grp = st[k:k + 5]
            if not press.get("turbo") and not of(c, "slam") and (grp[0] < 900 or any(b - a != 160 for a, b in zip(grp, grp[1:]))):
                bad.append(f"reel schedule {grp}")
    ms = [of(c, "cycleEnd")[0]["cycleMs"] for c in cs]
    pads = [of(c, "pad")[0]["ms"] for c in cs if of(c, "pad")]
    notes.append(f"{len(cs)} cycles, min {min(ms)}ms, padded {sum(1 for p in pads if p > 0)}x (max {max(pads) if pads else 0}ms), "
                 f"slam attempts honoured {sum(len(of(c, 'slam')) for c in cs)}, ignored {sum(len(of(c, 'slamIgnored')) for c in cs)}")
    res["G1 min cycle / no turbo-slam"] = (not bad, "; ".join(notes + bad[:3]))

    # G2
    ldw = [c for c in cs if 0 < of(c, "cycleEnd")[0]["won"] <= c[0]["stake"]]
    if profile == "mga":
        res["G2 no LDW celebration"] = (None, f"n/a under mga ({len(ldw)} LDW cycles, celebration allowed)")
    elif ldw:
        n = sum(len(of(c, "celebrationSound")) + len(of(c, "countStart")) + len(of(c, "tier")) for c in ldw)
        res["G2 no LDW celebration"] = (n == 0, f"{len(ldw)} cycles with 0 < return <= stake, celebration events {n}")
    else:
        res["G2 no LDW celebration"] = (None, "n/a (no return <= stake this run)")

    # G4
    ends = [e for e in log if e["type"] == "stepEnd"]
    if ends:
        durs = [e["ms"] for e in ends]
        ok = all(900 <= d <= 1300 for d in durs)
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

    # G5
    hs = [e for e in log if e["type"] == "hitStopStart"]
    he = [e for e in log if e["type"] == "hitStopEnd"]
    sh = [e for e in log if e["type"] == "shakeEnd"]
    if hs:
        ok = all(50 <= h["plannedMs"] <= 100 for h in hs) and all(s["ms"] <= 300 for s in sh)
        kinds = sorted({h["kind"] for h in hs})
        res["G5 hit-stop + shake"] = (ok, f"{len(hs)} heavy hits {kinds}; planned {sorted({h['plannedMs'] for h in hs})}ms, "
                                          f"frozen {min(h['frames'] for h in he)}-{max(h['frames'] for h in he)} frames, shake max {max(s['ms'] for s in sh)}ms")
    else:
        res["G5 hit-stop + shake"] = (None, "n/a (no heavy hit this run)")

    # G6
    counts = [c for c in cs if of(c, "countStart")]
    if counts:
        ok, notes = True, []
        for c in counts:
            st, ce = of(c, "countStart")[0], of(c, "countEnd")[0]
            bet = c[0]["bet"]
            want = [t for t, m in TIERS if st["target"] / bet >= m]
            got = of(c, "tier")
            ids = [t["id"] for t in got]
            ok &= (ids == want) or (bool(got) and got[-1]["skipped"] and ids[-1] == want[-1] and all(i in want for i in ids))
            ok &= all(t["skipped"] or t["mult"] >= dict(TIERS)[t["id"]] for t in got)
            ok &= ce["shownText"] == f"${st['target']:.2f}"
            si, sl = of(c, "skipInput"), of(c, "skipLanded")
            lag = (sl[0]["f"] - si[0]["inputF"]) if si else None
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
    ap.add_argument("--spins", type=int, default=6)
    ap.add_argument("--profiles", default="mga,ukgc")
    ap.add_argument("--no-bonus", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    failed = False
    with sync_playwright() as p:
        browser = launch(p, gpu=True)
        ok, note = baseline(browser)
        failed |= not ok
        print(f"\n== baseline (no flag) ==\n  {'PASS' if ok else 'FAIL'}  visual parity: {note}")
        for prof in a.profiles.split(","):
            log, errs = play(browser, prof, a.spins, not a.no_bonus)
            (OUT / f"live_feel_{prof}.json").write_text(json.dumps(log, indent=1))
            print(f"\n== ?feel=1&profile={prof} ==")
            for k, (ok, note) in gate(log, prof).items():
                failed |= ok is False
                print(f"  {'N/A ' if ok is None else ('PASS' if ok else 'FAIL')}  {k}: {note}")
            if errs:
                failed = True
                print("  FAIL  page errors:", errs[:3])
        browser.close()
    print("\nOVERALL:", "FAIL" if failed else "PASS")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
