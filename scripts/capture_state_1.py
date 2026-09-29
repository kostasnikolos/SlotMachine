"""
capture_state_1.py – Playwright VIDEO capture for State 1: Abyssal Idle.

Records the idle animation loop: breathing shader pulsing on symbols,
Leviathan swimming in volumetric fog behind the grid, ambient particles.

We record for 4.5s to capture at least one full breathing cycle.

Output: slot_engine/static/snapshots/vignette_state_1_video.webm
"""

import os
import re
import time
import shutil
import socket
import subprocess
from playwright.sync_api import sync_playwright


def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


if __name__ == "__main__":
    port = get_free_port()
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # ── Cache-bust: inject timestamp into the HTML so Playwright doesn't
    #    serve stale JS from its cache (SKILL.md pitfall #1) ──
    html_path = os.path.join(base_dir, 'scripts', 'vignette_state_1_idle.html')
    with open(html_path, 'r') as f:
        html = f.read()

    cache_bust = int(time.time())
    # Add or update cache-bust query string on the JS import
    html = re.sub(
        r'vignette_state_1_idle\.js(\?v=\d+)?',
        f'vignette_state_1_idle.js?v={cache_bust}',
        html,
    )

    busted_path = os.path.join(base_dir, 'scripts', '_vignette_state_1_idle_busted.html')
    with open(busted_path, 'w') as f:
        f.write(html)

    print(f"[capture] Starting HTTP server on port {port} in {base_dir}")
    server_process = subprocess.Popen(
        ['python3', '-m', 'http.server', str(port)],
        cwd=base_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(2)  # let server spin up

    # ── Video recording temp dir ──
    video_tmp_dir = os.path.join(base_dir, 'scripts', '_video_tmp_state1')
    os.makedirs(video_tmp_dir, exist_ok=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # ── Create context with native video recording ──
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir=video_tmp_dir,
                record_video_size={"width": 1920, "height": 1080},
            )
            page = context.new_page()

            url = f"http://localhost:{port}/scripts/_vignette_state_1_idle_busted.html"
            print(f"[capture] Navigating to {url}")
            page.goto(url)

            # ── Wait for __RENDER_READY or fallback timeout ──
            print("[capture] Waiting for __RENDER_READY...")
            try:
                page.wait_for_function("window.__RENDER_READY === true", timeout=10000)
            except Exception:
                print("[capture] __RENDER_READY not found, using time-based fallback")
                page.wait_for_timeout(3000)

            # ── Let the idle animation loop play for video capture ──
            # Record for 4.5s to capture breathing shader pulse + Leviathan fog swim.
            record_duration_ms = 4500
            print(f"[capture] Recording animation for {record_duration_ms}ms...")
            page.wait_for_timeout(record_duration_ms)

            # ── Close context to finalize the video file ──
            # Playwright writes the video on context.close()
            video_path = page.video.path()
            print(f"[capture] Raw video at: {video_path}")
            context.close()

            # ── Copy finalized video to snapshots directory ──
            output_dir = os.path.join(base_dir, 'slot_engine', 'static', 'snapshots')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, 'vignette_state_1_video.webm')

            shutil.copy2(video_path, output_path)
            file_size = os.path.getsize(output_path)
            print(f"[capture] ✓ Video saved to {output_path}")
            print(f"[capture]   Size: {file_size / 1024:.1f} KB")

            browser.close()
    finally:
        server_process.terminate()
        server_process.wait()
        # Clean up busted HTML and temp video dir
        if os.path.exists(busted_path):
            os.remove(busted_path)
        if os.path.exists(video_tmp_dir):
            shutil.rmtree(video_tmp_dir, ignore_errors=True)
        print("[capture] Server terminated, cleanup done.")
