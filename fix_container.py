import re

with open('slot_engine/static/index.html', 'r') as f:
    html = f.read()

html = html.replace(
    '<div id="webgl-grid-container" style="position:absolute; inset:0; z-index:0; pointer-events:none !important;"></div>',
    '<div id="webgl-grid-container" style="position:absolute; top:0; left:0; width:100%; height:100%; z-index:0; pointer-events:none !important;"></div>'
)

with open('slot_engine/static/index.html', 'w') as f:
    f.write(html)
