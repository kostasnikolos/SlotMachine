import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        await page.goto("http://localhost:8085")
        await page.wait_for_timeout(1000)
        await browser.close()

asyncio.run(run())
