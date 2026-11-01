"""
feel_check.py - automated game-feel gate (docs/game_feel_teardown.md, items 1, 4, 5, 6; plus 2 as a bonus)
for the Stage v2 prototype. Runs every scripted demo under the default (mga) and ukgc profiles, presses SPIN,
presses again mid-reel (slam attempt), presses again during big-win count-up (skip), dumps window.__FEEL_LOG to
artifacts/stage_v2/feel_<demo>_<profile>.json and prints PASS/FAIL per gate item.

    python scripts/stage_v2/feel_check.py [--demos cascade,bigwin,loss] [--profiles mga,ukgc]
"""

import argparse
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture import OUT, launch, serve  # noqa: E402

TIERS = [("big", 15), ("mega", 40), ("epic", 100), ("abyssal", 500)]
MIN_CYCLE = {"mga": 0, "ukgc": 2500, "de": 5000}  # regulatory floors (profile pads to 2600 / 5100)


def fmt(v):
    return f"{v:,.2f}"


def ev(log, kind):
    return [e for e in log if e["type"] == kind]


def run(page, url, demo):
    page.goto(url, wait_until="load")
    page.wait_for_function("window.__FEEL_READY === true", timeout=60000)
    page.click("#spin")
    page.wait_for_timeout(300)
    page.click("#spin")  # slam attempt while reels spin (must be ignored where slam stop is banned)
    if demo == "bigwin":
        page.wait_for_function("window.__FEEL_LOG.some(e => e.type === 'countStart')", timeout=60000)
        page.wait_for_timeout(1200)
        page.click("#spin")  # skip the count-up
    page.wait_for_function("(window.__FEEL_CYCLE_DONE || 0) >= 1", timeout=90000)
    return page.evaluate("window.__FEEL_LOG")


def check(log, demo, profile):
    res = {}
    end = ev(log, "cycleEnd")[0]
    press = ev(log, "press")[0]
    # G1: minimum cycle (press -> start re-enabled), no slam stop where banned, padding only at the end
    notes = [f"cycle {end['cycleMs']}ms, pad {ev(log, 'pad')[0]['ms']}ms"]
    ok = end["cycleMs"] >= MIN_CYCLE[profile]
    if profile != "mga" and ev(log, "slam"):
        ok = False
        notes.append("slam honoured under " + profile)
    planned = [e["plannedMs"] for e in ev(log, "reelStop")]
    if profile != "mga" and planned != [900 + 160 * c for c in range(5)]:
        ok = False
        notes.append(f"reel schedule changed {planned}")  # minimums must be met by end padding, never slower reels
    res["G1 min cycle"] = (ok, "; ".join(notes))

    # G2 (bonus): no celebration for return <= stake where banned
    won, bet = end["won"], press["bet"]
    if 0 < won <= bet and profile != "mga":
        bad = ev(log, "countStart") + ev(log, "tier")
        res["G2 no LDW celebration"] = (not bad, f"won {won} <= bet {bet}, celebration events: {len(bad)}")
    else:
        res["G2 no LDW celebration"] = (None, "n/a")

    # G4: cascade pacing
    steps = ev(log, "stepEnd")
    if steps:
        durs = [s["ms"] for s in steps]
        ok = all(900 <= d <= 1300 for d in durs)
        if len(durs) >= 6:
            ok &= durs[-1] >= 0.7 * durs[0]
        wins = [e["t"] for e in ev(log, "stepWin")] + [end["t"]]
        vis = [b - a for a, b in zip(wins, wins[1:])]
        ok &= min(vis) >= 300
        res["G4 cascade pacing"] = (ok, f"steps {durs} ms, last/first {durs[-1] / durs[0]:.2f}, min win visible {min(vis):.0f}ms")
    else:
        res["G4 cascade pacing"] = (None, "n/a")

    # G5: heavy impacts -> 3-6 frame hit-stop (50-100 ms planned), shake to zero within 300 ms
    hs, he, sh = ev(log, "hitStopStart"), ev(log, "hitStopEnd"), ev(log, "shakeEnd")
    if hs:
        ok = all(50 <= h["plannedMs"] <= 100 for h in hs) and all(s["ms"] <= 300 for s in sh) and len(sh) >= 1
        res["G5 hit-stop + shake"] = (ok, f"{len(hs)} impacts {[h['kind'] for h in hs]}, planned {[h['plannedMs'] for h in hs]}ms, "
                                          f"actual {[h['actualMs'] for h in he]}ms, shake {[s['ms'] for s in sh]}ms")
    else:
        res["G5 hit-stop + shake"] = (None, "n/a (no heavy impact in this demo)")

    # G6: tiers at configured bet multiples, skip within 2 frames onto the exact final value
    cs = ev(log, "countStart")
    if cs:
        mult = cs[0]["mult"]
        want = [t for t, m in TIERS if mult >= m]
        got = ev(log, "tier")
        ok = [t["id"] for t in got] == want or (got and got[-1]["id"] == want[-1] and all(t["id"] in want for t in got))
        ok = bool(ok) and all(t["skipped"] or t["mult"] >= dict(TIERS)[t["id"]] for t in got)
        ce = ev(log, "countEnd")[0]
        ok &= ce["shownText"] == fmt(cs[0]["target"])
        note = f"mult {mult:.1f}x tiers {[(t['id'], t['mult']) for t in got]}, final '{ce['shownText']}'"
        si, sl = ev(log, "skipInput"), ev(log, "skipLanded")
        if si:
            lag = sl[0]["f"] - si[0]["inputF"]
            ok &= lag <= 2
            note += f", skip landed in {lag} frame(s)"
        res["G6 tiers + skip"] = (ok, note)
    else:
        res["G6 tiers + skip"] = (None, "n/a (no count-up)")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demos", default="cascade,bigwin,loss")
    ap.add_argument("--profiles", default="mga,ukgc")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    httpd, port = serve()
    allres, stops = {}, {}
    with sync_playwright() as p:
        browser = launch(p, gpu=True)  # timing gates need real 60 fps frames
        for demo in a.demos.split(","):
            for prof in a.profiles.split(","):
                ctx = browser.new_context(viewport={"width": 960, "height": 540})
                page = ctx.new_page()
                errs = []
                page.on("pageerror", lambda e, errs=errs: errs.append(str(e)))
                url = f"http://127.0.0.1:{port}/stage_v2/index.html?v={int(time.time() * 1000)}&demo={demo}&profile={prof}"
                log = run(page, url, demo)
                (OUT / f"feel_{demo}_{prof}.json").write_text(json.dumps(log, indent=1))
                stops[(demo, prof)] = [e["plannedMs"] for e in ev(log, "reelStop")]
                allres[(demo, prof)] = check(log, demo, prof)
                if errs:
                    allres[(demo, prof)]["page errors"] = (False, "; ".join(errs))
                ctx.close()
        browser.close()
    httpd.shutdown()

    failed = False
    for (demo, prof), res in allres.items():
        print(f"\n== {demo} / {prof} ==")
        for k, (ok, note) in res.items():
            tag = "N/A " if ok is None else ("PASS" if ok else "FAIL")
            failed |= ok is False
            print(f"  {tag}  {k}: {note}")
    for demo in a.demos.split(","):
        profs = a.profiles.split(",")
        if len(profs) > 1:
            print(f"\nreel stops {demo}: " + ", ".join(f"{pr}={stops[(demo, pr)]}" for pr in profs) + "  (planned stop ms; mga differs only because the slam press is honoured there)")
    print("\nOVERALL:", "FAIL" if failed else "PASS")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
