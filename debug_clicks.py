import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('http://127.0.0.1:8085/')
        
        # Wait for load
        await page.wait_for_timeout(2000)
        
        # Inject click tracker
        await page.evaluate("""
            window.lastClickedElement = null;
            document.addEventListener('click', function(e) {
                window.lastClickedElement = e.target;
                console.log('Clicked element:', e.target.tagName, e.target.id, e.target.className);
            }, true);
        """)
        
        # Get spin button bounding box
        spin_btn = await page.locator('#btn-spin').bounding_box()
        if spin_btn:
            # Click exactly in the center of where the spin button is
            x = spin_btn['x'] + spin_btn['width'] / 2
            y = spin_btn['y'] + spin_btn['height'] / 2
            print(f"Spin button coords: {x}, {y}")
            
            # Perform a raw mouse click at those coordinates
            await page.mouse.click(x, y)
            
            # Retrieve what actually got clicked
            clicked_info = await page.evaluate("""
                window.lastClickedElement ? 
                { id: window.lastClickedElement.id, class: window.lastClickedElement.className, tag: window.lastClickedElement.tagName } : null
            """)
            print(f"Element that intercepted the click: {clicked_info}")
        else:
            print("Could not find #btn-spin")
            
        await browser.close()

asyncio.run(main())
