import re

with open('slot_engine/static/descent/design/Main.dc.html', 'r') as f:
    html = f.read()

# Make the ambient noise (A.amb) much lower or turn off the drone completely.
old_drone = "A.drone = [osc('sine', 45), osc('sine', 45 * 1.5 + 0.4)];"
# Mute the main drone frequencies by setting their gain super low, or just not connecting them to A.amb
new_drone = "A.drone = []; // Drone removed per user request"

old_droneF = "A.droneF = filt('lowpass', 120);"
new_droneF = "A.droneF = filt('lowpass', 0); // muted"

old_bed = "A.bedF = filt('bandpass', 420, 0.4);"
new_bed = "A.bedF = filt('bandpass', 0, 0.4); // muted"

html = html.replace(old_drone, new_drone)
html = html.replace(old_droneF, new_droneF)
html = html.replace(old_bed, new_bed)

with open('slot_engine/static/descent/design/Main.dc.html', 'w') as f:
    f.write(html)
