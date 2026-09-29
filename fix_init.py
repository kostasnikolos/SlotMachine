import re
with open("slot_engine/static/game.js", "r") as f:
    code = f.read()

replacement = """  renderInitialGrid() {
    this.gridState = [];
    
    const defaultSymbols = [
      ['HIGH_ANGLER', 'MID_HELMET', 'LOW_10', 'MID_COMPASS', 'HIGH_VIPER'],
      ['MID_COMPASS', 'HIGH_SQUID', 'LOW_J', 'HIGH_LEVIATHAN', 'LOW_Q'],
      ['HIGH_VIPER', 'LOW_K', 'WILD_MAW', 'LOW_A', 'MID_HELMET'],
      ['LOW_10', 'HIGH_ANGLER', 'LOW_J', 'HIGH_SQUID', 'LOW_K'],
      ['MID_HELMET', 'LOW_Q', 'HIGH_VIPER', 'MID_COMPASS', 'HIGH_ANGLER'],
    ];

    const tryUpdate = () => {
      if (window.engine && window.__RENDER_READY) {
        window.engine.updateGrid(defaultSymbols);
      } else {
        setTimeout(tryUpdate, 100);
      }
    };
    tryUpdate();
"""
code = re.sub(r'  renderInitialGrid\(\) \{.*?(?=  })', replacement, code, flags=re.DOTALL)

with open("slot_engine/static/game.js", "w") as f:
    f.write(code)
