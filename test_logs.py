import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.on("response", lambda response: print(f"RESPONSE {response.status}: {response.url}") if response.status == 404 else None)
        page.on("console", lambda msg: print(f"BROWSER LOG: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"BROWSER ERROR: {exc}"))
        await page.goto("http://localhost:8085/")
        await asyncio.sleep(3)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
