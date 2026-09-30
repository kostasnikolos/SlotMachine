import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        errors = []
        page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(f"[pageerror] {exc}"))

        await page.goto("http://localhost:8085/")
        
        # Check if #btn-spin is clickable
        spin_btn = page.locator("#btn-spin")
        await spin_btn.wait_for(state="visible")
        is_enabled = await spin_btn.is_enabled()
        print(f"Spin button enabled: {is_enabled}")
        
        # Check #webgl-grid-container and #slot-grid
        webgl_container = page.locator("#webgl-grid-container")
        slot_grid = page.locator("#slot-grid")
        print(f"WebGL container visible: {await webgl_container.is_visible()}")
        print(f"Slot grid visible: {await slot_grid.is_visible()}")
        
        # Click spin
        await spin_btn.click()
        await page.wait_for_timeout(2000) # wait for spin to finish/process
        
        print("Console errors during run:")
        for e in errors:
            print(e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
