import re

# Fix Leviathan Director
with open('slot_engine/static/js/leviathan_director.js', 'r') as f:
    code = f.read()

# Fix the intensity, distance, and position
code = code.replace('50000.0', '10.0')
code = code.replace('1000.0', '100.0')
code = code.replace('this.mesh.scale.set(40, 40, 40);', 'this.mesh.scale.set(100, 100, 100);')
code = code.replace('this.mesh.position.set(0, -15, 70);', 'this.mesh.position.set(0, -50, 0);')
code = code.replace('this.throatLight.position.set(0, 0, 5);', 'this.throatLight.position.set(0, 5, 20);')
# Try to actually open the jaws by finding the animation
code = code.replace('action.play();', 'action.play();\n                this.mixer.setTime(0.5);')

with open('slot_engine/static/js/leviathan_director.js', 'w') as f:
    f.write(code)

# Fix HTML cache
import time
with open('slot_engine/static/headless_render_4.html', 'r') as f:
    html = f.read()
ts = int(time.time())
html = re.sub(r'\?v=\d+', f'?v={ts}', html)
# Remove tonemapping to match Gate 3
html = re.sub(r'renderer\.toneMapping = THREE\.ACESFilmicToneMapping;\n', '', html)
html = re.sub(r'renderer\.toneMappingExposure = 1\.0;\n', '', html)

with open('slot_engine/static/headless_render_4.html', 'w') as f:
    f.write(html)
