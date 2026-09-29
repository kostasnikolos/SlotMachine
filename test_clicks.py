from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser error: {err}"))
        
        page.goto('http://localhost:8080/static/index.html')
        page.wait_for_timeout(3000)
        
        cells = page.locator('.symbol-cell').count()
        print(f"Number of cells found: {cells}")
        
        if cells > 0:
            try:
                page.click('.symbol-cell >> nth=0', timeout=2000)
                print("Cell is clickable!")
            except Exception as e:
                print("Failed to click cell:", e)
                
        # Click the spin button to see if it responds
        try:
            page.click('#btn-spin', timeout=2000)
            print("Spin button is clickable!")
        except Exception as e:
            print("Failed to click spin button:", e)

        browser.close()

if __name__ == '__main__':
    run()
