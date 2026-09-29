import re
with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

code = code.replace("updateGrid(gridData) {", "updateGrid(gridData) {\n        console.log('updateGrid called! rows: ' + (gridData?gridData.length:0) + ' cols: ' + (gridData&&gridData[0]?gridData[0].length:0));")

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)
