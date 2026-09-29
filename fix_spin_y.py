import re

with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

replacement = """
    startSpin() {
        this.currentState = 'SPIN';
        // State 2 (Spin/Descend)
        this.planes.forEach((plane, i) => {
            // Just a temporary scale pop instead of breaking the Y coordinate permanently
            plane.scale.set(0.9, 0.9, 1);
            setTimeout(() => {
                plane.scale.set(1, 1, 1);
            }, 200);
        });
    }
"""

code = re.sub(r'    startSpin\(\) \{.*?\}\n', replacement + "\n", code, flags=re.DOTALL)

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)

