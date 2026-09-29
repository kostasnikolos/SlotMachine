import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1728, 'height': 1080})
        
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Error: {err.message}"))
        
        await page.goto('http://127.0.0.1:8085/')
        await page.wait_for_timeout(2000)
        
        print("Clicking spin...")
        btn = await page.locator('#btn-spin').bounding_box()
        if btn:
            x = btn['x'] + btn['width'] / 2
            y = btn['y'] + btn['height'] / 2
            await page.mouse.click(x, y)
        else:
            print("No btn-spin")
            
        await page.wait_for_timeout(2000)
        await browser.close()

asyncio.run(main())
