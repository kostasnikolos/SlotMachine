import os
import time
from playwright.sync_api import sync_playwright

def capture_snapshot():
    html_path = os.path.abspath("/Users/kosta/SlotMachine/scripts/verify_wild_maw_m2.html")
    # Append timestamp to bypass caching (The "Identical Snapshot" Loop)
    url = f"file://{html_path}?v={int(time.time())}"
    
    output_path = os.path.abspath("/Users/kosta/SlotMachine/slot_engine/static/snapshots/gate_maw_m2_verified.png")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--allow-file-access-from-files'])
        page = browser.new_page(viewport={"width": 800, "height": 600})
        
        # Log console messages
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        
        print(f"Loading {url}")
        page.goto(url)
        
        # Wait for the Three.js scene to finish loading and signal __RENDER_READY
        print("Waiting for render ready signal...")
        try:
            page.wait_for_function("window.__RENDER_READY === true", timeout=10000)
            page.wait_for_timeout(500)
            page.screenshot(path=output_path)
            print(f"Snapshot captured and saved to {output_path}")
        except Exception as e:
            print(f"Error waiting for render: {e}")
            page.screenshot(path=output_path)
            print("Captured error snapshot anyway.")
            
        browser.close()

if __name__ == "__main__":
    capture_snapshot()
