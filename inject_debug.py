with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

debug_code = """
        let debugBox = document.getElementById("debug-box-123");
        if (!debugBox) {
            debugBox = document.createElement("div");
            debugBox.id = "debug-box-123";
            debugBox.style.position = "absolute";
            debugBox.style.top = "10px";
            debugBox.style.left = "10px";
            debugBox.style.backgroundColor = "red";
            debugBox.style.color = "white";
            debugBox.style.zIndex = "999999";
            debugBox.style.fontSize = "16px";
            document.body.appendChild(debugBox);
        }
        debugBox.innerHTML = `W: ${width}, H: ${height}, Z: ${this.camera.position.z}, Aspect: ${this.camera.aspect.toFixed(3)}, grid: ${this.gridSize}`;
"""

code = code.replace("this.renderer.setSize(width, height);", "this.renderer.setSize(width, height);\n" + debug_code)

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)

