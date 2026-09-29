import re

with open('slot_engine/static/leviathan_3d_engine.js', 'r') as f:
    code = f.read()

# Make the Leviathan visible on the right side
code = re.sub(r'this\.dormantY = -360;', 'this.dormantY = -20;\n    this.dormantX = 160;', code)
code = re.sub(r'this\.dormantZ = -200;', 'this.dormantZ = -80;', code)
code = re.sub(r'this\.creatureRoot\.position\.set\(0, this\.dormantY, this\.dormantZ\);', 'this.creatureRoot.position.set(this.dormantX, this.dormantY, this.dormantZ);\n    this.creatureRoot.rotation.y = -0.3; // Angle slightly towards center', code)

# Fix the surge animation X position
code = re.sub(r'this\.creatureRoot\.position\.x = Math\.sin\(time \* 12\) \* 4;', 'this.creatureRoot.position.x = this.dormantX + (Math.sin(time * 12) * 4);', code)

# Make him float slowly when idle
code = re.sub(r'// No animation logic in idle', 'this.creatureRoot.position.y = this.dormantY + Math.sin(time * 2) * 10;\n      this.creatureRoot.rotation.x = Math.sin(time * 1.5) * 0.05;', code)

with open('slot_engine/static/leviathan_3d_engine.js', 'w') as f:
    f.write(code)
