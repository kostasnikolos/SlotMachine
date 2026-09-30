import re

with open('slot_engine/static/index.html', 'r') as f:
    html = f.read()

# Replace the current grid-container block
old_block = '''          <!-- Reels Grid -->
          <div class="grid-container" id="slot-grid" style="z-index:5; position:relative;">
            <!-- 3D WebGL Symbols Layer -->
            <div id="webgl-grid-container" style="position:absolute; top:0; left:0; width:100%; height:100%; z-index:0; pointer-events:none !important;"></div>
            <!-- Dynamically populated by game.js -->
          </div>'''

new_block = '''          <!-- Reels Grid Wrapper -->
          <div class="grid-wrapper" style="position:relative; z-index:5;">
            <!-- 3D WebGL Symbols Layer -->
            <div id="webgl-grid-container" style="position:absolute; top:0; left:0; width:100%; height:100%; z-index:0; pointer-events:none !important;"></div>
            <!-- Reels Grid -->
            <div class="grid-container" id="slot-grid" style="position:relative; z-index:1; background:transparent !important; border:none; box-shadow:none;">
              <!-- Dynamically populated by game.js -->
            </div>
          </div>'''

html = html.replace(old_block, new_block)

with open('slot_engine/static/index.html', 'w') as f:
    f.write(html)
