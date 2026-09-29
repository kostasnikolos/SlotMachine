import re
with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

replacement = """        this.loadingManager.onError = (url) => {
            let debugBox = document.getElementById("debug-box-123");
            if (debugBox) {
                debugBox.innerHTML += `<br>Err: ${url.split('/').pop()}`;
            }
        };
        this.loadingManager.onLoad = () => {"""

code = code.replace("this.loadingManager.onLoad = () => {", replacement)

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)
