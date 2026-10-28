import re

with open('slot_engine/static/descent/design/Main.dc.html', 'r') as f:
    html = f.read()

# 1. Darker A.bubble
# Original: o.frequency.exponentialRampToValueAtTime(f * 2.2, t + 0.07);
html = html.replace(
    'o.frequency.exponentialRampToValueAtTime(f * 2.2, t + 0.07);',
    'o.frequency.exponentialRampToValueAtTime(f * 1.1, t + 0.07); // Darker, less upward glide'
)
# Make UI/win bubble calls use lower base frequencies by replacing random calls? No, let's just make the glide darker. Actually, let's modify the gain envelope to be softer/muffled too? Or we can just lower the multiplier.
# Wait, let's replace A.bubble entirely.
old_bubble = '''    A.bubble = (t, f, v, to) => {
      const o = osc('sine', f), g = gain(0.0001, to || A.sfx);
      o.frequency.setValueAtTime(f, t); o.frequency.exponentialRampToValueAtTime(f * 2.2, t + 0.07);
      env(g, t, 0.004, v, 0.07);
      o.connect(g); o.start(t); o.stop(t + 0.1);
    };'''
new_bubble = '''    A.bubble = (t, f, v, to) => {
      // Darker bubble: lower frequency, subtle downward or flat glide, muffled via a quick lowpass
      const o = osc('sine', f * 0.6), f1 = filt('lowpass', f), g = gain(0.0001, to || A.sfx);
      o.frequency.setValueAtTime(f * 0.6, t); o.frequency.exponentialRampToValueAtTime(f * 0.4, t + 0.08);
      env(g, t, 0.01, v * 1.5, 0.09);
      o.connect(f1); f1.connect(g); o.start(t); o.stop(t + 0.15);
    };'''
html = html.replace(old_bubble, new_bubble)


# 2. Darker A.sink (symbols moving)
old_sink = '''    A.sink = () => {
      if (!A.ctx) return;
      const t = now(), n = noise(), f = filt('lowpass', 1400), g = gain(0.0001, A.sfx);
      f.frequency.setValueAtTime(1400, t); f.frequency.exponentialRampToValueAtTime(140, t + 0.7);
      env(g, t, 0.05, 0.12, 0.65);
      n.connect(f); f.connect(g); wet(g, 0.4); n.start(t, Math.random()); n.stop(t + 0.8);
      const o = osc('sine', 90), og = gain(0.0001, A.sfx);
      o.frequency.exponentialRampToValueAtTime(32, t + 0.6);
      env(og, t, 0.02, 0.16, 0.6);
      o.connect(og); o.start(t); o.stop(t + 0.7);
    };'''
new_sink = '''    A.sink = () => {
      if (!A.ctx) return;
      // Darker, heavier sink for symbols
      const t = now(), n = noise(), f = filt('lowpass', 400), g = gain(0.0001, A.sfx);
      f.frequency.setValueAtTime(400, t); f.frequency.exponentialRampToValueAtTime(40, t + 0.8);
      env(g, t, 0.08, 0.18, 0.75);
      n.connect(f); f.connect(g); wet(g, 0.6); n.start(t, Math.random()); n.stop(t + 0.9);
      const o = osc('sine', 55), og = gain(0.0001, A.sfx);
      o.frequency.exponentialRampToValueAtTime(18, t + 0.7);
      env(og, t, 0.04, 0.25, 0.8);
      o.connect(og); o.start(t); o.stop(t + 0.9);
    };'''
html = html.replace(old_sink, new_sink)


# 3. Darker A.plunge / A.geyser / A.roar (Leviathan help)
old_plunge = '''    A.plunge = () => {
      if (!A.ctx) return;
      const t = now(), o = osc('sine', 180), g = gain(0.0001, A.sfx);
      o.frequency.exponentialRampToValueAtTime(42, t + 0.4);
      env(g, t, 0.005, 0.35, 0.4);
      o.connect(g); o.start(t); o.stop(t + 0.5);
      const n = noise(), f = filt('lowpass', 2400), ng = gain(0.0001, A.sfx);
      f.frequency.exponentialRampToValueAtTime(200, t + 0.5);
      env(ng, t, 0.005, 0.25, 0.5);
      n.connect(f); f.connect(ng); wet(ng, 0.6); n.start(t, Math.random()); n.stop(t + 0.6);
      for (let i = 0; i < 12; i++) A.bubble(t + 0.15 + Math.random() * 0.8, 200 + Math.random() * 500, 0.05);
    };'''
new_plunge = '''    A.plunge = () => {
      if (!A.ctx) return;
      // Dark, terrifying plunge (no fake bubbles, heavy low-end sweep)
      const t = now(), o = osc('sine', 60), g = gain(0.0001, A.sfx);
      o.frequency.exponentialRampToValueAtTime(10, t + 0.8);
      env(g, t, 0.02, 0.5, 0.8);
      o.connect(g); o.start(t); o.stop(t + 0.9);
      const n = noise(), f = filt('lowpass', 600), ng = gain(0.0001, A.sfx);
      f.frequency.exponentialRampToValueAtTime(60, t + 0.8);
      env(ng, t, 0.05, 0.35, 0.9);
      n.connect(f); f.connect(ng); wet(ng, 0.8); n.start(t, Math.random()); n.stop(t + 1.0);
    };'''
html = html.replace(old_plunge, new_plunge)

with open('slot_engine/static/descent/design/Main.dc.html', 'w') as f:
    f.write(html)
