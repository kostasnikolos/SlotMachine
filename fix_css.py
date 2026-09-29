import re

with open("slot_engine/static/style.css", "r") as f:
    code = f.read()

# Make fx-canvas behind everything
code = code.replace("z-index: 22;", "z-index: 0;")
code = code.replace("pointer-events: none;", "/*pointer-events: none;*/")

# Remove background from game-wrapper so the canvas shows through
code = re.sub(r"background: url\('/static/assets/abyssal_trench_bg\.jpg'\).*?;", "background: transparent;", code)

with open("slot_engine/static/style.css", "w") as f:
    f.write(code)

