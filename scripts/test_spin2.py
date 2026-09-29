import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        await page.goto("http://localhost:8085")
        await page.wait_for_timeout(1000)
        
        print("Clicking spin button...")
        await page.click('#btn-spin')
        
        await page.wait_for_timeout(2000)
        await browser.close()

asyncio.run(run())
