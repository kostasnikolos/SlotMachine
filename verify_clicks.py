import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        await page.set_viewport_size({"width": 1280, "height": 720})
        await page.goto("http://localhost:8085/")
        await asyncio.sleep(2)
        
        # Click spin button
        print("Clicking spin button...")
        try:
            await page.click("#btn-spin")
            print("Successfully clicked the spin button!")
            await asyncio.sleep(1) # wait for animation
        except Exception as e:
            print(f"Failed to click spin button: {e}")
            
        print("Taking screenshot...")
        await page.screenshot(path="verify_click_fix.png", full_page=True)
        await browser.close()
        print("Screenshot saved to verify_click_fix.png")

if __name__ == "__main__":
    asyncio.run(main())
