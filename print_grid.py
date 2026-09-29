import re
with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

replacement = """    updateGrid(gridData) {
        if (!window.__RENDER_READY) {
            this.pendingGridData = gridData;
            return;
        }
        
        if (!gridData || gridData.length === 0) return;
        
        let debugStr = "GRID: ";
        for(let r=0; r<gridData.length; r++) {
            for(let c=0; c<gridData[r].length; c++) {
                if(!this.materials[gridData[r][c]]) {
                    debugStr += `MISSING(${r},${c})='${gridData[r][c]}' `;
                }
            }
        }
        
        let dbg = document.getElementById("debug-box-123");
        if(dbg && debugStr !== "GRID: ") {
            dbg.innerHTML += "<br>" + debugStr;
        }
"""
code = re.sub(r'    updateGrid\(gridData\) \{.*?if \(\!gridData \|\| gridData\.length === 0\) return;', replacement, code, flags=re.DOTALL)

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)
