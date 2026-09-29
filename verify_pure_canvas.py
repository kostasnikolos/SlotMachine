import asyncio
import os
import subprocess
from playwright.async_api import async_playwright
import time

async def main():
    # start a server if not up on 8085
    proc = subprocess.Popen(["python3", "-m", "http.server", "8085", "-d", "/Users/kosta/SlotMachine/slot_engine"])
    time.sleep(2) # wait for server
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto("http://localhost:8085/static/index_pure.html", wait_until="networkidle")
            await page.wait_for_timeout(3000)
            await page.screenshot(path="/Users/kosta/SlotMachine/slot_engine/static/snapshots/pure_canvas_m1.png")
            print("Screenshot taken.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()
            proc.kill()

asyncio.run(main())
