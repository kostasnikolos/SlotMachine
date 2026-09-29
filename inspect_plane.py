import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://localhost:8085")
        await page.wait_for_timeout(3000)
        
        # Check Row 0 Col 0, which was Dark Grey (HIGH_ANGLER)
        # Check Row 0 Col 1, which was Helmet
        res = await page.evaluate("""() => {
            if (!window.engine || !window.engine.planes) return "No planes";
            const p0 = window.engine.planes[0]; // Row 0 Col 0 (Dark Grey)
            const p1 = window.engine.planes[1]; // Row 0 Col 1 (Helmet)
            
            return {
                p0_mat: p0.material.uuid,
                p0_color: p0.material.color ? p0.material.color.getHexString() : null,
                p0_emissive: p0.material.emissiveIntensity,
                p1_mat: p1.material.uuid,
                p1_color: p1.material.color ? p1.material.color.getHexString() : null,
                high_angler_mat: window.engine.materials["HIGH_ANGLER"].uuid,
                helmet_mat: window.engine.materials["MID_HELMET"].uuid
            };
        }""")
        print(res)
        await browser.close()

asyncio.run(run())
