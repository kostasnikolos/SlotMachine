import re

with open('slot_engine/static/descent/design/Main.dc.html', 'r') as f:
    html = f.read()

# Mute the ping
old_ping = '''    A.ping = () => {
      if (!A.ctx) return;
      const t = now(), o = osc('sine', 880), g = gain(0.0001, A.sfx);
      env(g, t, 0.005, 0.07, 1.4);
      o.connect(g); wet(g, 0.9); o.start(t); o.stop(t + 1.5);
    };'''
new_ping = '''    A.ping = () => {
      // User disabled the sonar ping, felt too noisy.
      return; 
    };'''
html = html.replace(old_ping, new_ping)

with open('slot_engine/static/descent/design/Main.dc.html', 'w') as f:
    f.write(html)
