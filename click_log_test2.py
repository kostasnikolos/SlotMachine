import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1728, 'height': 1080})
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        
        await page.goto('http://127.0.0.1:8085/')
        await page.wait_for_timeout(2000)
        
        await page.evaluate("""
            console.log("Calling triggerSpin...");
            window.slotGame.triggerSpin().catch(e => console.error(e));
        """)
        
        await page.wait_for_timeout(2000)
        await browser.close()

asyncio.run(main())
