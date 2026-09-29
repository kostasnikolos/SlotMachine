import re
with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

replacement = """        this.loadingManager.onLoad = () => {
                window.__RENDER_READY = true;
                const geometry = new THREE.PlaneGeometry(10, 10);"""

code = code.replace("        this.loadingManager.onLoad = () => {\n                const geometry = new THREE.PlaneGeometry(10, 10);", replacement)

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)
