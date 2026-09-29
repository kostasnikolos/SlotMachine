with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

debug_missing = """
                        if (!this.materials[symbolKey]) {
                            let debugBox = document.getElementById("debug-box-123");
                            if (debugBox) {
                                debugBox.innerHTML += `<br>Missing: '${symbolKey}'`;
                            }
                        }
"""

code = code.replace("if (this.materials[symbolKey]) {", debug_missing + "\n                        if (this.materials[symbolKey]) {")

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)

