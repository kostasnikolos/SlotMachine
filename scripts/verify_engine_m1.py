import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://localhost:8085")
        
        # Wait for textures to load
        await page.wait_for_timeout(3000)
        
        await page.screenshot(path="verify_playwright_8085.png")
        await browser.close()
        print("Captured verify_playwright_8085.png")

asyncio.run(run())
