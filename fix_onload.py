import re

with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

replacement = """
                        this.scene.add(mesh);
                        this.planes.push(mesh);
                    }
                }

                // If gridData was queued, update it now
                if (this.pendingGridData) {
                    this.updateGrid(this.pendingGridData);
                    this.pendingGridData = null;
                }

                // Start Render Loop
"""
code = code.replace("""
                        this.scene.add(mesh);
                        this.planes.push(mesh);
                    }
                }

                // Start Render Loop""", replacement)

update_replacement = """
    updateGrid(gridData) {
        if (this.planes.length === 0) {
            this.pendingGridData = gridData;
            return;
        }
        // Map 2D array symbols to 1D planes
"""
code = code.replace("""
    updateGrid(gridData) {
        // Map 2D array symbols to 1D planes""", update_replacement)

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)

