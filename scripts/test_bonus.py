import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://localhost:8085")
        await page.wait_for_timeout(3000)
        
        # Click Bonus Buy
        await page.click('#btn-bonus-open')
        await page.wait_for_timeout(500)
        await page.click('.bonus-card[data-buy="STANDARD_BONUS_100X"]')
        
        # Wait for spin animation
        await page.wait_for_timeout(3000)
        
        await page.screenshot(path="verify_bonus_8085.png")
        await browser.close()
        print("Captured verify_bonus_8085.png")

asyncio.run(run())
