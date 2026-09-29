with open("slot_engine/static/game.js", "r") as f:
    lines = f.readlines()

if lines[403].strip() == "}" and lines[404].strip() == "}":
    lines.pop(404)
    with open("slot_engine/static/game.js", "w") as f:
        f.writelines(lines)
        print("Fixed brace!")
