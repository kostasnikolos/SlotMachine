import re

with open("slot_engine/static/index.html", "r") as f:
    code = f.read()

# Remove ambient ocean canvas
code = re.sub(r'<canvas id="ambient-ocean-canvas"></canvas>', '', code)
# Remove old ocean script
code = re.sub(r'<script src="/slot_engine/static/ocean_ambient.js\?v=[0-9]+"></script>', '', code)
code = re.sub(r'<script src="/static/ocean_ambient.js\?v=[0-9]+"></script>', '', code)

# Remove old slot grid
code = re.sub(r'<div id="slot-grid"[^>]*></div>', '', code)

# Change fx-canvas z-index back to 0, but ensure it's not hidden
# Actually let's put fx-canvas as the main background of game-wrapper
with open("slot_engine/static/index.html", "w") as f:
    f.write(code)

