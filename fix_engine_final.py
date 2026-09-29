import re

with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

# Fix 1: Camera far clipping plane
code = code.replace("new THREE.PerspectiveCamera(45, 1, 0.1, 100);", "new THREE.PerspectiveCamera(45, 1, 0.1, 500);")

# Fix 2: Rebuild grid dynamically to handle 6x5 Ultra Bonus
update_grid_replacement = """
    updateGrid(gridData) {
        if (!gridData || gridData.length === 0) return;
        
        const rows = gridData.length;
        const cols = gridData[0].length;
        
        if (this.planes.length === 0 || this.gridSize !== Math.max(rows, cols)) {
            // Rebuild planes for new size (e.g. 5x5 to 6x5 Ultra Bonus)
            this.planes.forEach(plane => this.scene.remove(plane));
            this.planes = [];
            this.gridSize = Math.max(rows, cols);
            
            const geometry = new THREE.PlaneGeometry(10, 10);
            const offsetX = (cols - 1) * this.symbolSpacing / 2;
            const offsetY = (rows - 1) * this.symbolSpacing / 2;
            
            for (let r = 0; r < rows; r++) {
                for (let c = 0; c < cols; c++) {
                    const defaultMat = this.materials['DEAD_SEDIMENT'] || new THREE.MeshBasicMaterial({color: 0x333333});
                    const mesh = new THREE.Mesh(geometry, defaultMat);
                    const x = (c * this.symbolSpacing) - offsetX;
                    const y = -((r * this.symbolSpacing) - offsetY);
                    mesh.position.set(x, y, 0);
                    this.scene.add(mesh);
                    this.planes.push(mesh);
                }
            }
        }
        
        // Map 2D array symbols to 1D planes
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const idx = r * cols + c;
                if (this.planes[idx]) {
                    const symbolKey = gridData[r][c];
                    if (this.materials[symbolKey]) {
                        this.planes[idx].material = this.materials[symbolKey];
                        this.planes[idx].material.emissiveIntensity = 2.0;
                        setTimeout(() => {
                            if (this.planes[idx] && this.planes[idx].material) {
                                this.planes[idx].material.emissiveIntensity = 1.0;
                            }
                        }, 500);
                    }
                }
            }
        }
    }
"""

# Replace the entire updateGrid method
code = re.sub(r'    updateGrid\(gridData\) \{.*?(?=\n    startSpin\(\) \{)', update_grid_replacement, code, flags=re.DOTALL)

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)

