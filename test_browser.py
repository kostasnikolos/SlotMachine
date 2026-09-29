import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.on("console", lambda msg: print(f"Browser console: {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser error: {err}"))
        
        await page.goto("http://localhost:8000/")
        await page.wait_for_timeout(1000)
        
        print("Clicking spin button...")
        try:
            await page.click("#btn-spin")
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Error clicking: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
