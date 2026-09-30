import re

with open('slot_engine/static/js/WebGLGameEngine.js', 'r') as f:
    code = f.read()

code = code.replace(
    'console.log("[WebGLGameEngine] init loaded!"); window.__RENDER_READY = true;',
    'this.onWindowResize(); window.addEventListener("resize", () => this.onWindowResize()); console.log("[WebGLGameEngine] init loaded!"); window.__RENDER_READY = true;'
)

with open('slot_engine/static/js/WebGLGameEngine.js', 'w') as f:
    f.write(code)
