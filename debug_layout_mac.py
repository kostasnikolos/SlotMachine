import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Set viewport to Mac 16-inch 1728x1080
        page = await browser.new_page(viewport={'width': 1728, 'height': 1080})
        await page.goto('http://127.0.0.1:8085/')
        await page.wait_for_timeout(2000)
        
        btn = await page.locator('#btn-spin').bounding_box()
        if btn:
            x = btn['x'] + btn['width'] / 2
            y = btn['y'] + btn['height'] / 2
            
            top_element = await page.evaluate(f"""
                () => {{
                    const el = document.elementFromPoint({x}, {y});
                    if (!el) return 'NULL';
                    return el.tagName + (el.id ? '#' + el.id : '') + (el.className ? '.' + el.className : '');
                }}
            """)
            print(f"Top element at {x},{y}: {top_element}")
        else:
            print("No btn-spin found.")
            
        await browser.close()

asyncio.run(main())
