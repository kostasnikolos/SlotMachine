import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"ERROR: {exc}"))
        
        print("Navigating...")
        await page.goto("http://localhost:8085/")
        print("Waiting 5 seconds for WebGL models to load...")
        await page.wait_for_timeout(5000)
        
        print("Taking screenshot...")
        await page.screenshot(path="slot_engine/static/snapshots/debug_snapshot.png")
        await browser.close()
        print("Done!")

asyncio.run(main())
