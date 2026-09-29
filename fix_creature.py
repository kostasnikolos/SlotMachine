import re

with open('/Users/kosta/SlotMachine/slot_engine/static/game.js', 'r') as f:
    code = f.read()

creature_strike = """  // PHYSICAL ON-GRID LEVIATHAN STRIKE
  async animateCreatureStrike(data, speed) {
    if (window.oceanAmbient) window.oceanAmbient.scatterFish();
    if (window.engine && window.engine.startDevour) {
      window.engine.startDevour();
    }
    
    // Simulate strike delay
    await new Promise(r => setTimeout(r, 600 * speed));
    
    if (data.grid) {
      this.animateGridDrop(data.grid, speed);
    }
  }"""
code = re.sub(r'  // PHYSICAL ON-GRID LEVIATHAN STRIKE.*?  \}\n\n  //', creature_strike + '\n\n  //', code, flags=re.DOTALL)

with open('/Users/kosta/SlotMachine/slot_engine/static/game.js', 'w') as f:
    f.write(code)
