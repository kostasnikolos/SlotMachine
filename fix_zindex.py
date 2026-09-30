import re

with open('slot_engine/static/index.html', 'r') as f:
    html = f.read()

# Change z-index to 0
html = html.replace(
    '<div id="webgl-grid-container" style="position:absolute; inset:0; z-index:-1; pointer-events:none !important;"></div>',
    '<div id="webgl-grid-container" style="position:absolute; inset:0; z-index:0; pointer-events:none !important;"></div>'
)

with open('slot_engine/static/index.html', 'w') as f:
    f.write(html)
