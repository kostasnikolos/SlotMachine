import re

with open('slot_engine/static/descent/design/Main.dc.html', 'r') as f:
    html = f.read()

old_set_level = '''    A.setLevel = (l) => {
      A.level = l;
      if (!A.ctx) return;
      const t = now();
      A.drone[0].frequency.setTargetAtTime(45 - l * 3, t, 1.2);
      A.drone[1].frequency.setTargetAtTime((45 - l * 3) * 1.5 + 0.4, t, 1.2);'''
new_set_level = '''    A.setLevel = (l) => {
      A.level = l;
      if (!A.ctx) return;
      const t = now();
      if (A.drone && A.drone.length >= 2) {
        A.drone[0].frequency.setTargetAtTime(45 - l * 3, t, 1.2);
        A.drone[1].frequency.setTargetAtTime((45 - l * 3) * 1.5 + 0.4, t, 1.2);
      }'''

html = html.replace(old_set_level, new_set_level)

with open('slot_engine/static/descent/design/Main.dc.html', 'w') as f:
    f.write(html)
