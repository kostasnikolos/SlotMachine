from playwright.sync_api import sync_playwright
import time
import subprocess

server = subprocess.Popen(["python3", "-m", "http.server", "8000"], cwd="/Users/kosta/SlotMachine")
time.sleep(1)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
    page.on("console", lambda msg: print(f"CONSOLE {msg.type}: {msg.text}"))
    page.goto("http://localhost:8000/slot_engine/static/headless_render_4.html")
    page.wait_for_timeout(3000)
    browser.close()

server.terminate()
