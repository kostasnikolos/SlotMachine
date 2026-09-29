import re

with open('/Users/kosta/SlotMachine/slot_engine/static/js/WebGLGameEngine.js', 'r') as f:
    code = f.read()

methods = """
    updateGrid(gridData) {
        // Map 2D array symbols to 1D planes
        for (let r = 0; r < gridData.length; r++) {
            for (let c = 0; c < gridData[r].length; c++) {
                const idx = r * this.gridSize + c;
                if (this.planes[idx]) {
                    // Quick color shift or material update for demonstration
                    // In a real engine, we'd lookup the loaded PBR material for the symbol
                    this.planes[idx].material.emissiveIntensity = 2.0;
                    setTimeout(() => {
                        this.planes[idx].material.emissiveIntensity = 1.0;
                    }, 500);
                }
            }
        }
    }

    startSpin() {
        this.currentState = 'SPIN';
        // State 2 (Spin/Descend)
        this.planes.forEach((plane, i) => {
            plane.position.y += 10; // Simple visual pop
        });
    }

    startCascade() {
        this.currentState = 'CASCADE';
        // State 3 (Hit/Squash)
        this.planes.forEach(plane => {
            plane.scale.set(1.2, 0.8, 1);
            setTimeout(() => {
                plane.scale.set(1, 1, 1);
            }, 300);
        });
    }
"""

if "updateGrid(gridData)" not in code:
    code = code.replace('onWindowResize() {', methods + '\n    onWindowResize() {')
    with open('/Users/kosta/SlotMachine/slot_engine/static/js/WebGLGameEngine.js', 'w') as f:
        f.write(code)

