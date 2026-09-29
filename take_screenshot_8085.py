from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    page.goto("http://localhost:8085/")
    page.wait_for_timeout(3000) # wait for models to load
    page.screenshot(path="slot_engine/static/snapshots/final_hybrid_verification.png")
    browser.close()
