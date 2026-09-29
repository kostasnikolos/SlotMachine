import re

with open('/Users/kosta/SlotMachine/slot_engine/static/game.js', 'r') as f:
    code = f.read()

animate_cascade = """  // Symbol Destruction Physics
  async animateCascade(cascadeData, speed) {
    // Trigger State 3 (Hit/Squash) in WebGL
    if (window.engine) window.engine.startCascade();
    
    audio.playWaterPlunge();
    await new Promise(r => setTimeout(r, 220 * speed));
    
    audio.playSteamHiss();
    await new Promise(r => setTimeout(r, 280 * speed));

    // Scatter ambient fish due to explosion shockwave
    if (window.oceanAmbient) window.oceanAmbient.scatterFish();

    // Phase 3: Grid Drop with Cascade Tiles
    if (cascadeData.grid) {
      await this.animateGridDrop(cascadeData.grid, speed);
    }
  }"""
code = re.sub(r'  // Symbol Destruction Physics.*?  async animateCascade\(cascadeData, speed\) \{.*?\n  \}\n\n  // PHYSICAL', animate_cascade + '\n\n  // PHYSICAL', code, flags=re.DOTALL)

with open('/Users/kosta/SlotMachine/slot_engine/static/game.js', 'w') as f:
    f.write(code)
