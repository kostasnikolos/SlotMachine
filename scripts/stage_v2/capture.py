"""
capture.py - headless snapshots of the Stage v2 prototype (slot_engine/static/stage_v2/index.html).

Serves slot_engine/static with a throwaway http.server (no FastAPI / game API needed), loads the page
with a cache-busting ?v=<timestamp>, waits for window.__RENDER_READY, and writes:
    artifacts/stage_v2/desktop_1920x1080.png
    artifacts/stage_v2/mobile_390x844.png

Uses the system Chrome (or Edge) via Playwright channels, so no Playwright browser download is needed.
Extra query params are passed through, e.g.:  python scripts/stage_v2/capture.py --query "depth=6200&seals=4"
"""

import argparse
import functools
import http.server
import socket
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / "slot_engine" / "static"
OUT = ROOT / "artifacts" / "stage_v2"
VIEWPORTS = [("desktop_1920x1080", 1920, 1080, 1, False), ("mobile_390x844", 390, 844, 2, True)]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def serve():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    handler = functools.partial(QuietHandler, directory=str(STATIC))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port


def launch(p):
    args = ["--ignore-gpu-blocklist", "--enable-webgl", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
    for channel in ("chrome", "msedge", None):
        try:
            return p.chromium.launch(headless=True, channel=channel, args=args) if channel else p.chromium.launch(headless=True, args=args)
        except Exception as e:  # noqa: BLE001 - try the next available browser
            print(f"[capture] channel {channel!r} unavailable: {str(e).splitlines()[0]}")
    raise SystemExit("No Chromium-family browser available for Playwright.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="", help="extra query string, e.g. 'depth=6200&seals=4'")
    ap.add_argument("--settle", type=float, default=1.0, help="seconds to wait after __RENDER_READY")
    a = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    httpd, port = serve()
    url = f"http://127.0.0.1:{port}/stage_v2/index.html?v={int(time.time() * 1000)}"
    if a.query:
        url += "&" + a.query.lstrip("&?")
    print(f"[capture] {url}")
    failed = False
    with sync_playwright() as p:
        browser = launch(p)
        for name, w, h, dpr, mobile in VIEWPORTS:
            ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, is_mobile=mobile, has_touch=mobile)
            page = ctx.new_page()
            logs = []
            page.on("console", lambda m, logs=logs: logs.append(f"{m.type}: {m.text}"))
            page.on("pageerror", lambda e, logs=logs: logs.append(f"pageerror: {e}"))
            page.goto(url, wait_until="load")
            try:
                page.wait_for_function("window.__RENDER_READY === true || !!window.__RENDER_ERROR", timeout=60000)
            except Exception:  # noqa: BLE001
                logs.append("timeout waiting for __RENDER_READY")
            err = page.evaluate("window.__RENDER_ERROR || null")
            page.wait_for_timeout(int(a.settle * 1000))
            path = OUT / f"{name}.png"
            page.screenshot(path=str(path))
            errors = [l for l in logs if l.startswith(("error", "pageerror", "timeout")) and "404" not in l]
            print(f"[capture] {name}: {path}  ready={err is None}  issues={len(errors)}")
            for l in errors:
                print("   ", l)
            failed |= bool(err) or bool(errors)
            ctx.close()
        browser.close()
    httpd.shutdown()
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
