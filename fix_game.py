import re

with open('/Users/kosta/SlotMachine/slot_engine/static/game.js', 'r') as f:
    code = f.read()

# 1. Strip renderInitialGrid and createSymbolElement DOM logic
def replace_render_grid(match):
    return """  renderInitialGrid() {
    this.gridState = [];
    
    const defaultSymbols = [
      ['HIGH_ANGLER', 'MID_HELMET', 'LOW_10', 'MID_COMPASS', 'HIGH_VIPER'],
      ['MID_COMPASS', 'HIGH_SQUID', 'LOW_J', 'HIGH_LEVIATHAN', 'LOW_Q'],
      ['HIGH_VIPER', 'LOW_K', 'WILD_MAW', 'LOW_A', 'MID_HELMET'],
      ['LOW_10', 'HIGH_ANGLER', 'LOW_J', 'HIGH_SQUID', 'LOW_K'],
      ['MID_HELMET', 'LOW_Q', 'HIGH_VIPER', 'MID_COMPASS', 'HIGH_ANGLER'],
    ];

    if (window.engine) {
      window.engine.updateGrid(defaultSymbols);
    }
  }

  createSymbolElement(symType, hasPearl = false) {
    // Deprecated for WebGL Pipeline
    return null;
  }"""

code = re.sub(
    r'  renderInitialGrid\(\) \{.*?\n  attachEventListeners\(\)',
    replace_render_grid(None) + '\n\n  attachEventListeners()',
    code,
    flags=re.DOTALL
)

# 2. Hook up triggerSpin()
spin_hook = """  async triggerSpin() {
    if (this.isSpinning) return;
    
    // Trigger State 2 (Spin/Descend) in WebGL
    if (window.engine) window.engine.startSpin();"""

code = re.sub(r'  async triggerSpin\(\) \{\n    if \(this.isSpinning\) return;', spin_hook, code)

# 3. Hook up animateCascade()
cascade_hook = """  // Symbol Destruction Physics
  async animateCascade(cascadeData, speed) {
    // Trigger State 3 (Hit/Squash) in WebGL
    if (window.engine) window.engine.startCascade();"""

code = re.sub(r'  // Symbol Destruction Physics.*?\n  async animateCascade\(cascadeData, speed\) \{', cascade_hook, code, flags=re.DOTALL)

# 4. updateGridDrop logic
grid_drop = """  async animateGridDrop(gridData, speed) {
    if (window.engine) {
        window.engine.updateGrid(gridData.grid || gridData);
    }"""
code = re.sub(r'  async animateGridDrop\(gridData, speed\) \{\n    if \(window\.reelEngine\) \{\n        window\.reelEngine\.updateGridMatrix\(gridData\.grid\);\n    \}', grid_drop, code)

with open('/Users/kosta/SlotMachine/slot_engine/static/game.js', 'w') as f:
    f.write(code)
