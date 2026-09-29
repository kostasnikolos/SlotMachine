import re

with open("slot_engine/static/game.js", "r") as f:
    code = f.read()

# We need to completely remove the second THREE.Scene creation block from game.js
# Let's find the try-catch block for "Initialize Unified WebGL Engine (Milestone 5)"
start_idx = code.find("// Initialize Unified WebGL Engine (Milestone 5)")
if start_idx != -1:
    end_idx = code.find("} catch (e) {", start_idx)
    end_catch_idx = code.find("}", end_idx + 13)
    # Remove the whole block
    code = code[:start_idx] + code[end_catch_idx + 1:]

with open("slot_engine/static/game.js", "w") as f:
    f.write(code)

