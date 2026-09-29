from playwright.sync_api import sync_playwright

html = """
<!DOCTYPE html>
<html>
<body>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
    const manager = new THREE.LoadingManager();
    manager.onLoad = () => console.log('LOADED');
    manager.onError = (url) => console.log('ERROR: ' + url);
    const loader = new THREE.TextureLoader(manager);
    loader.load('http://localhost:9999/fake.png');
</script>
</body>
</html>
"""

with open("test_loader.html", "w") as f:
    f.write(html)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        page.goto("file:///Users/kosta/SlotMachine/test_loader.html")
        page.wait_for_timeout(2000)
        browser.close()

run()
