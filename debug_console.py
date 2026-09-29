import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Error: {err.message}"))
        
        await page.goto('http://127.0.0.1:8085/')
        await page.wait_for_timeout(3000)
        
        await browser.close()

asyncio.run(main())
