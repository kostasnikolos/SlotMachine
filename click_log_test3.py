import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1728, 'height': 1080})
        
        await page.goto('http://127.0.0.1:8085/')
        await page.wait_for_timeout(2000)
        
        state = await page.evaluate("""
            () => {
                return {
                    isSpinning: window.slotGame.isSpinning,
                    btnDisabled: document.getElementById('btn-spin').disabled
                };
            }
        """)
        print(f"State: {state}")
        
        await browser.close()

asyncio.run(main())
