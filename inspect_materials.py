from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("http://localhost:8085")
    page.wait_for_timeout(2000)
    
    res = page.evaluate("""() => {
        if (!window.engine || !window.engine.materials) return "No engine";
        const m = window.engine.materials["LOW_10"];
        if (!m) return "No material";
        return {
            uuid: m.uuid,
            type: m.type,
            transparent: m.transparent,
            visible: m.visible,
            opacity: m.opacity,
            map: m.map ? m.map.image ? "Loaded" : "No image" : "No map"
        };
    }""")
    print("LOW_10:", res)
    
    res2 = page.evaluate("""() => {
        const m = window.engine.materials["MID_HELMET"];
        return {
            map: m.map ? m.map.image ? "Loaded" : "No image" : "No map"
        };
    }""")
    print("MID_HELMET:", res2)
    
    browser.close()
