import re

with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

# Make default material pure unlit GREEN
code = code.replace("const defaultMat = this.materials['DEAD_SEDIMENT'] || new THREE.MeshBasicMaterial({color: 0x333333});", "const defaultMat = new THREE.MeshBasicMaterial({color: 0x00ff00});")

# Make DEAD_SEDIMENT pure unlit RED
dead_sediment_replacement = """
            if (symKey === 'DEAD_SEDIMENT') {
                this.materials[symKey] = new THREE.MeshBasicMaterial({color: 0xff0000});
                continue;
            }
            this.materials[symKey] = new THREE.MeshStandardMaterial({
"""
code = code.replace("this.materials[symKey] = new THREE.MeshStandardMaterial({", dead_sediment_replacement)

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)

