import re

with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

# Fix spacing so there are no massive black gaps
code = code.replace("this.symbolSpacing = 11.0;", "this.symbolSpacing = 10.0;")

# Make lighting much brighter
code = code.replace("const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);", "const ambientLight = new THREE.AmbientLight(0xffffff, 2.5);")
code = code.replace("const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);", "const directionalLight = new THREE.DirectionalLight(0xffffff, 3.0);")
code = code.replace("directionalLight.position.set(5, 10, 5);", "directionalLight.position.set(0, 0, 20);")

# Remove fog to ensure it doesn't darken the symbols too much
code = code.replace("this.scene.fog = new THREE.FogExp2(0x0a192f, 0.03);", "this.scene.fog = new THREE.FogExp2(0x0a192f, 0.005);")

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)

