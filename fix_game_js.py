import re

with open("slot_engine/static/game.js", "r") as f:
    code = f.read()

stubs = """
  updatePurgedRunes(purgedArr) {
    // DOM logic stripped for WebGL engine
  }

  clearVents() {
    // DOM logic stripped for WebGL engine
  }

  showVents(activeVents) {
    // DOM logic stripped for WebGL engine
  }
"""

code = code.replace("  updateStats() {", stubs + "\n  updateStats() {")

with open("slot_engine/static/game.js", "w") as f:
    f.write(code)

