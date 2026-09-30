import re

with open('slot_engine/static/index.html', 'r') as f:
    html = f.read()

# Move #webgl-grid-container INSIDE #slot-grid
html = html.replace('<!-- 3D WebGL Symbols Layer -->\n          <div id="webgl-grid-container" style="position:absolute; inset:0; z-index:2; pointer-events:none !important;"></div>', '')

new_grid = '''          <!-- Reels Grid -->
          <div class="grid-container" id="slot-grid" style="z-index:5; position:relative;">
            <!-- 3D WebGL Symbols Layer -->
            <div id="webgl-grid-container" style="position:absolute; inset:0; z-index:-1; pointer-events:none !important;"></div>
            <!-- Dynamically populated by game.js -->
          </div>'''

html = re.sub(r'<!-- Reels Grid -->\s*<div class="grid-container" id="slot-grid" style="z-index:5; position:relative;">\s*<!-- Dynamically populated by game\.js -->\s*</div>', new_grid, html)

with open('slot_engine/static/index.html', 'w') as f:
    f.write(html)
