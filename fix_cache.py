import re

with open('slot_engine/static/index.html', 'r') as f:
    html = f.read()

import random
v = str(random.randint(10000, 99999))

html = re.sub(r'(\.css|\.js)"', r'\1?v=' + v + '"', html)
html = re.sub(r'(\.css|\.js)\?v=\d+"', r'\1?v=' + v + '"', html)

with open('slot_engine/static/index.html', 'w') as f:
    f.write(html)
