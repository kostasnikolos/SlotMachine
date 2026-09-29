import re
with open("slot_engine/static/index.html", "r") as f:
    code = f.read()

replacement = """  <!-- Three.js 3D WebGL Engine & 3D Leviathan Controller -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
  <script src="/static/js/monolithic_frame.js?v=9999"></script>
  <script src="/static/js/webgl_reel_engine.js?v=9999"></script>
  <script src="/static/js/leviathan_director.js?v=9999"></script>
  <script src="/static/js/WebGLGameEngine.js?v=1009"></script>
  <script>
    window.addEventListener('DOMContentLoaded', () => {
      window.engine = new WebGLGameEngine('fx-canvas');
      window.engine.init();
    });
  </script>
  <script src="/static/ocean_ambient.js"></script>
  <script src="/static/sound.js"></script>
  <script src="/static/game.js?v=1009"></script>
</body>"""

code = re.sub(r'  <!-- Three.js 3D WebGL Engine & 3D Leviathan Controller -->.*?</body>', replacement, code, flags=re.DOTALL)

with open("slot_engine/static/index.html", "w") as f:
    f.write(code)
