import re
with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

# Find the texture loading lines
code = code.replace("_albedo.png')", "_albedo.png?v=9999')")
code = code.replace("_normal.png')", "_normal.png?v=9999')")
code = code.replace("_orm.png')", "_orm.png?v=9999')")
code = code.replace("_emissive.png')", "_emissive.png?v=9999')")

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)
