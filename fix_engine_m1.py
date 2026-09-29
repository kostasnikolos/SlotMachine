import re

with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

# Fix camera Z
code = code.replace("this.camera.position.set(0, 0, 10);", "this.camera.position.set(0, 0, 72);")

# Fix geometry and spacing
code = code.replace("new THREE.PlaneGeometry(1, 1);", "new THREE.PlaneGeometry(10, 10);")
code = code.replace("this.symbolSpacing = 1.2;", "this.symbolSpacing = 11.0;")

# Fix renderer clear color to hide old CSS background
code = code.replace("alpha: true", "alpha: false")
if "setClearColor" not in code:
    code = code.replace("this.renderer.setSize", "this.renderer.setClearColor(0x050c18, 1);\n        this.renderer.setSize")

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)

