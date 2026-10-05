import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        
        await page.goto("http://localhost:8085/")
        
        print("Waiting 5 seconds for models to load...")
        await page.wait_for_timeout(5000)
        
        print("Clicking spin to verify animation...")
        await page.click('#btn-spin')
        
        print("Waiting 3 seconds for spin to resolve...")
        await page.wait_for_timeout(3000)
        
        print("Taking screenshot...")
        await page.screenshot(path="slot_engine/static/snapshots/final_verification.png")
        await browser.close()

asyncio.run(main())
