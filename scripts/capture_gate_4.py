import os
import time
import subprocess
from playwright.sync_api import sync_playwright

def run():
    print("Starting local HTTP server...")
    server = subprocess.Popen(["python3", "-m", "http.server", "8000"], cwd="/Users/kosta/SlotMachine")
    time.sleep(2) 
    
    html_url = f"http://localhost:8000/slot_engine/static/headless_render_4.html?t={time.time()}"
    output_path = os.path.abspath('/Users/kosta/SlotMachine/slot_engine/static/snapshots/gate_4_leviathan_devour_verified.png')

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.on("console", lambda msg: print(f"BROWSER: {msg.text}"))
            
            print(f"Loading {html_url}...")
            page.goto(html_url)
            
            page.wait_for_function("window.__RENDER_READY === true", timeout=25000)
            
            page.wait_for_timeout(1500) # give webgl time to render the complex scene
            
            print(f"Taking screenshot to {output_path}...")
            page.screenshot(path=output_path)
            
            browser.close()
            print("Success! Leviathan Devour Surge snapshot captured via HTTP.")
    finally:
        server.terminate()
        server.wait()

if __name__ == '__main__':
    run()
