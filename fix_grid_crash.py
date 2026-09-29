import re

with open("slot_engine/static/game.js", "r") as f:
    code = f.read()

# Fix 1: Add null check for GRID_EXPANSION_6X5
code = code.replace("this.gridEl.classList.add('grid-6x5');", "if (this.gridEl) this.gridEl.classList.add('grid-6x5');")

# Fix 2: Add null check for remove
code = code.replace("this.gridEl.classList.remove('grid-6x5');", "if (this.gridEl) this.gridEl.classList.remove('grid-6x5');")

with open("slot_engine/static/game.js", "w") as f:
    f.write(code)

print("Fixed game.js")
