import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Record video
        context = await browser.new_context(
            record_video_dir="slot_engine/static/snapshots/",
            record_video_size={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        
        await page.goto("http://localhost:8085")
        await page.wait_for_timeout(2000)
        
        # Click spin
        await page.click('#btn-spin')
        
        # Wait for spin animation and results
        await page.wait_for_timeout(3000)
        
        # Close to save video
        await context.close()
        await browser.close()
        
        import os, glob, shutil
        # Find the video and rename it
        video_files = glob.glob("slot_engine/static/snapshots/*.webm")
        if video_files:
            video_file = max(video_files, key=os.path.getmtime)
            shutil.copy(video_file, "slot_engine/static/snapshots/vignette_state_2_video_live.webm")
            print("Captured vignette_state_2_video_live.webm")

asyncio.run(run())
