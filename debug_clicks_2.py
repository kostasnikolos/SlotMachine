import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('http://127.0.0.1:8085/')
        await page.wait_for_timeout(2000)
        
        spin_btn = await page.locator('#btn-spin').bounding_box()
        if spin_btn:
            x = spin_btn['x'] + spin_btn['width'] / 2
            y = spin_btn['y'] + spin_btn['height'] / 2
            
            top_element = await page.evaluate(f"""
                () => {{
                    const el = document.elementFromPoint({x}, {y});
                    if (!el) return 'NULL';
                    return el.tagName + '#' + el.id + '.' + el.className;
                }}
            """)
            print(f"Top element at {x},{y}: {top_element}")
            
            # Check z-index and pointer-events of the spin button itself
            btn_styles = await page.evaluate(f"""
                () => {{
                    const btn = document.getElementById('btn-spin');
                    const style = window.getComputedStyle(btn);
                    const parent = window.getComputedStyle(btn.parentElement);
                    const footer = window.getComputedStyle(document.querySelector('.footer-panel'));
                    return {{
                        btn_pointer: style.pointerEvents,
                        btn_zindex: style.zIndex,
                        parent_pointer: parent.pointerEvents,
                        footer_pointer: footer.pointerEvents,
                        footer_zindex: footer.zIndex
                    }};
                }}
            """)
            print(f"Styles: {btn_styles}")
        
        await browser.close()

asyncio.run(main())
