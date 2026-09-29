from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        page.goto("http://localhost:8085/")
        page.wait_for_timeout(2000)
        
        # Try to click the spin button
        try:
            btn = page.locator("#btn-spin")
            btn.wait_for(state="visible", timeout=2000)
            
            box = btn.bounding_box()
            print(f"Spin Button Bounding Box: {box}")
            
            # Click it
            page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
            print("Mouse clicked the button coordinates!")
            
            page.wait_for_timeout(1000)
            
            # Did it trigger a spin? Check console
            print("Check console for API fetch!")
            
        except Exception as e:
            print(f"Failed to click: {e}")
            
        browser.close()

main()
