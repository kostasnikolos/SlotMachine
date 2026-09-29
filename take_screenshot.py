import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.on("console", lambda msg: print(msg.text))
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.goto("http://localhost:8085/")
        await asyncio.sleep(2)
        
        # Click the Ultra Bonus buy button
        print("Triggering Ultra Bonus...")
        await page.evaluate("if(window.slotGame) { window.slotGame.triggerBonusBuy('ULTRA_BONUS_350X'); }")
        
        # Wait for the animation (grid expansion and drop)
        await asyncio.sleep(8)
        
        print("Taking screenshot...")
        await page.screenshot(path="verify_mobile.png", full_page=True)
        await browser.close()
        print("Screenshot saved to verify_mobile.png")

if __name__ == "__main__":
    asyncio.run(main())
