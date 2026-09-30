import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        
        await page.goto("http://localhost:8085/")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="slot_engine/static/snapshots/debug_snapshot.png")
        await browser.close()

asyncio.run(main())
