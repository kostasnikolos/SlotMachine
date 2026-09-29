import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('http://127.0.0.1:8085/')
        await page.wait_for_timeout(2000)
        
        layout = await page.evaluate("""
            () => {
                const doc = document.documentElement;
                const body = document.body;
                const footer = document.querySelector('.control-bar');
                const spinBtn = document.getElementById('btn-spin');
                
                const footerRect = footer ? footer.getBoundingClientRect() : null;
                const btnRect = spinBtn ? spinBtn.getBoundingClientRect() : null;
                
                return {
                    docHeight: doc.clientHeight,
                    bodyHeight: body.clientHeight,
                    docScrollHeight: doc.scrollHeight,
                    footerRect,
                    btnRect
                };
            }
        """)
        print(f"Layout: {layout}")
        
        await browser.close()

asyncio.run(main())
