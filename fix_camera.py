with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

start_idx = code.find("    onWindowResize() {")
if start_idx == -1:
    print("Could not find onWindowResize")
    exit(1)

# Find the next method by looking for "    start" or "    update" or just the next "\n    [a-z]"
import re
match = re.search(r'\n    [a-z]', code[start_idx+20:])
if match:
    end_idx = start_idx + 20 + match.start()
else:
    end_idx = len(code)

replacement = """    onWindowResize() {
        if (!this.canvas || !this.canvas.parentElement) return;
        
        let width = this.canvas.parentElement.clientWidth || 390;
        let height = this.canvas.parentElement.clientHeight || 480;
        if (height < 200) height = 480;
        
        this.renderer.setSize(width, height);
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();

        const vFov = this.camera.fov * Math.PI / 180;
        const hFov = 2 * Math.atan(Math.tan(vFov / 2) * this.camera.aspect);
        const requiredZ = 55 / (2 * Math.tan(hFov / 2));
        const requiredZVert = 55 / (2 * Math.tan(vFov / 2));
        
        this.camera.position.z = Math.max(70, requiredZ, requiredZVert);

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
        debugBox.innerHTML = `W: ${width}, H: ${height}, Z: ${this.camera.position.z.toFixed(1)}, Aspect: ${this.camera.aspect.toFixed(3)}`;
    }"""

code = code[:start_idx] + replacement + code[end_idx:]

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)

print("Replaced!")
