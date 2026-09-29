import os
import time
import json
import subprocess
from playwright.sync_api import sync_playwright

def run():
    print("Starting uvicorn server...")
    server = subprocess.Popen(["uvicorn", "slot_engine.api.app:app", "--port", "8000"], cwd="/Users/kosta/SlotMachine")
    time.sleep(3) 
    
    output_path = os.path.abspath('/Users/kosta/SlotMachine/slot_engine/static/snapshots/gate_5_integration_verified.png')

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.on("console", lambda msg: print(f"BROWSER: {msg.text}"))
            
            def handle_route(route):
                if "/api/slot/spin" in route.request.url:
                    print("Mocking /api/slot/spin response for verified win state!")
                    route.fulfill(
                        status=200,
                        content_type="application/json",
                        body=json.dumps({
                            "events": [
                                {
                                    "event_type": "SPIN_STARTED",
                                    "data": { "depth_level": 5, "depth_meters": 11000, "accumulated_points": 260, "purged_symbols": [] }
                                },
                                {
                                    "event_type": "GRID_DROP",
                                    "data": {
                                        "rows": 5,
                                        "cols": 5,
                                        "grid": [
                                            ["HIGH_LEVIATHAN", "HIGH_ANGLER", "HIGH_VIPER", "MID_HELMET", "LOW_10"],
                                            ["HIGH_LEVIATHAN", "HIGH_ANGLER", "HIGH_VIPER", "MID_HELMET", "LOW_10"],
                                            ["HIGH_LEVIATHAN", "HIGH_ANGLER", "HIGH_VIPER", "MID_HELMET", "LOW_10"],
                                            ["HIGH_LEVIATHAN", "HIGH_ANGLER", "HIGH_VIPER", "MID_HELMET", "LOW_10"],
                                            ["HIGH_LEVIATHAN", "HIGH_ANGLER", "HIGH_VIPER", "MID_HELMET", "LOW_10"]
                                        ]
                                    }
                                },
                                {
                                    "event_type": "WIN_EVALUATION",
                                    "data": {
                                        "wins": [
                                            {"coords": [[0,0],[1,0],[2,0],[3,0],[4,0]], "payout": 5000.0}
                                        ],
                                        "cumulative_payout": 5000.0
                                    }
                                },
                                {
                                    "event_type": "SPIN_COMPLETE",
                                    "data": {}
                                }
                            ],
                            "total_payout": 5000.0,
                            "payout_multiplier": 500.0,
                            "feature_type": "NONE"
                        })
                    )
                else:
                    route.continue_()
            
            page.route("**/*", handle_route)
            
            html_url = f"http://localhost:8000/?t={time.time()}"
            print(f"Loading {html_url}...")
            page.goto(html_url)
            
            page.wait_for_timeout(2000)
            
            print("Clicking SPIN button...")
            page.click("#btn-spin", force=True)
            
            print("Waiting for animations to complete...")
            page.wait_for_timeout(3500)
            
            print(f"Taking screenshot to {output_path}...")
            page.screenshot(path=output_path)
            
            browser.close()
            print("Success! Integrated snapshot captured via HTTP.")
    finally:
        server.terminate()
        server.wait()

if __name__ == '__main__':
    run()
