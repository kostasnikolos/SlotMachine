import os
import shutil
import time
import subprocess
from playwright.sync_api import sync_playwright

def main():
    port = 59875
    print(f"[capture] Starting HTTP server on port {port} in /Users/kosta/SlotMachine")
    server = subprocess.Popen(["python3", "-m", "http.server", str(port)], cwd="/Users/kosta/SlotMachine")
    time.sleep(1)

    html_src = "scripts/vignette_state_4_tension.html"
    html_busted = "scripts/_vignette_state_4_tension_busted.html"
    with open(html_src, "r") as f:
        html = f.read()
    html = html.replace("vignette_state_4_tension.js", f"vignette_state_4_tension.js?v={int(time.time())}")
    with open(html_busted, "w") as f:
        f.write(html)

    video_dir = os.path.abspath("scripts/_video_tmp_state4")
    out_video = os.path.abspath("slot_engine/static/snapshots/vignette_state_4_video.webm")
    if os.path.exists(video_dir): shutil.rmtree(video_dir)
    os.makedirs(video_dir, exist_ok=True)
    
    url = f"http://localhost:{port}/{html_busted}"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                record_video_dir=video_dir,
                record_video_size={"width": 1920, "height": 1080}
            )
            page = context.new_page()
            page.set_viewport_size({"width": 1920, "height": 1080})
            
            page.on("console", lambda msg: print(f"BROWSER: {msg.text}"))
            page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
            
            print(f"[capture] Navigating to {url}")
            page.goto(url)
            
            print("[capture] Waiting for __RENDER_READY...")
            try:
                page.wait_for_function("window.__RENDER_READY === true", timeout=20000)
            except Exception as e:
                print(f"[capture] Timed out waiting for __RENDER_READY: {e}")
                
            print("[capture] Recording animation for 5500ms...")
            page.wait_for_timeout(5500)
            
            context.close()
            browser.close()
            
            videos = os.listdir(video_dir)
            if videos:
                raw_vid = os.path.join(video_dir, videos[0])
                print(f"[capture] Raw video at: {raw_vid}")
                shutil.copy(raw_vid, out_video)
                size_kb = os.path.getsize(out_video) / 1024
                print(f"[capture] ✓ Video saved to {out_video}")
                print(f"[capture]   Size: {size_kb:.1f} KB")
            else:
                print("[capture] ✗ Failed to record video.")
    finally:
        server.terminate()
        server.wait()
        if os.path.exists(html_busted): os.remove(html_busted)
        if os.path.exists(video_dir): shutil.rmtree(video_dir)
        print("[capture] Server terminated, cleanup done.")

if __name__ == "__main__":
    main()
