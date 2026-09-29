import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1728, 'height': 1080})
        await page.goto('http://127.0.0.1:8085/')
        await page.wait_for_timeout(2000)
        
        await page.evaluate("""
            window.clickedElements = [];
            document.addEventListener('click', e => {
                const el = e.target;
                window.clickedElements.push(el.tagName + (el.id ? '#'+el.id : '') + (el.className ? '.'+el.className : ''));
            }, true);
        """)
        
        btn = await page.locator('#btn-spin').bounding_box()
        if btn:
            x = btn['x'] + btn['width'] / 2
            y = btn['y'] + btn['height'] / 2
            print(f"Clicking at {x}, {y}")
            await page.mouse.click(x, y)
        else:
            print("no btn")
            
        await page.wait_for_timeout(1000)
        
        clicks = await page.evaluate("window.clickedElements")
        print(f"Clicked: {clicks}")
        
        await browser.close()

asyncio.run(main())
