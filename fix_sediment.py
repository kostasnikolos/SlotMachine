import re
with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

# Remove the red override for DEAD_SEDIMENT
code = re.sub(r"            if \(symKey === 'DEAD_SEDIMENT'\) \{.*?continue;\n            \}", "", code, flags=re.DOTALL)

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)
