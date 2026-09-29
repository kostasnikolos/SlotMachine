import re

with open('/Users/kosta/SlotMachine/slot_engine/static/js/WebGLGameEngine.js', 'r') as f:
    content = f.read()

# Replace startSpin
new_startSpin = """    startSpin() {
        this.currentState = 'SPIN';
        this.isSpinning = true;
        this.spinVelocity = 0;
        this.targetSpinVelocity = 250.0; // Units per second
        this.baseCameraZ = this.camera.position.z;
        this.targetCameraZ = this.baseCameraZ + 25; // Pull back for extreme velocity
    }"""
content = re.sub(r'    startSpin\(\) \{[\s\S]*?\}\n', new_startSpin + '\n', content)

# Replace render
new_render = """    render(time) {
        requestAnimationFrame(this.render.bind(this));
        
        const timeSec = time * 0.001;
        const dt = Math.min(timeSec - (this.lastTime || timeSec), 0.1);
        this.lastTime = timeSec;

        if (this.isSpinning) {
            // Accelerate spin
            this.spinVelocity += (this.targetSpinVelocity - this.spinVelocity) * dt * 5.0;
            
            // Camera pull back
            this.camera.position.z += (this.targetCameraZ - this.camera.position.z) * dt * 3.0;

            const rows = this.rows || this.gridSize;
            const wrapDistance = rows * this.symbolSpacing;
            const bottomLimit = -((rows - 1) * this.symbolSpacing / 2) - (this.symbolSpacing * 0.6);
            
            this.planes.forEach((plane, index) => {
                plane.position.y -= this.spinVelocity * dt;
                
                // Vertical motion blur via stretch
                const stretch = 1.0 + (this.spinVelocity / 40.0);
                plane.scale.set(1, stretch, 1);
                
                // Wrap around
                if (plane.position.y < bottomLimit) {
                    plane.position.y += wrapDistance;
                }
            });
        } else {
            // Return to normal
            if (this.baseCameraZ !== undefined) {
                this.camera.position.z += (this.baseCameraZ - this.camera.position.z) * dt * 5.0;
            }
            
            // Gentle rotation or animation for planes
            this.planes.forEach((plane, index) => {
                plane.position.z = Math.sin(timeSec + index) * 0.1;
                if (plane.scale.y > 1.01) {
                    plane.scale.lerp(new THREE.Vector3(1, 1, 1), dt * 10);
                }
            });
        }

        this.renderer.render(this.scene, this.camera);
    }"""
content = re.sub(r'    render\(time\) \{[\s\S]*?\}\n\}', new_render + '\n}', content)

# Inject rows/cols saving and isSpinning = false in updateGrid
# Find: const rows = gridData.length;\n        const cols = gridData[0].length;
old_update_grid_vars = """        const rows = gridData.length;
        const cols = gridData[0].length;"""
new_update_grid_vars = """        this.isSpinning = false;
        if (this.spinVelocity !== undefined) this.spinVelocity = 0;

        const rows = gridData.length;
        const cols = gridData[0].length;
        this.rows = rows;
        this.cols = cols;"""
content = content.replace(old_update_grid_vars, new_update_grid_vars)

# Find where it maps symbols to planes and snap them
old_map = """        // Map 2D array symbols to 1D planes
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const idx = r * cols + c;
                if (this.planes[idx]) {
                    const symbolKey = gridData[r][c];"""

new_map = """        // Map 2D array symbols to 1D planes
        const offsetX = (cols - 1) * this.symbolSpacing / 2;
        const offsetY = (rows - 1) * this.symbolSpacing / 2;
        
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const idx = r * cols + c;
                if (this.planes[idx]) {
                    const symbolKey = gridData[r][c];
                    
                    // Snap positions and scale back
                    const x = (c * this.symbolSpacing) - offsetX;
                    const y = -((r * this.symbolSpacing) - offsetY);
                    this.planes[idx].position.set(x, y, 0);
                    this.planes[idx].scale.set(1, 1, 1);"""
content = content.replace(old_map, new_map)

with open('/Users/kosta/SlotMachine/slot_engine/static/js/WebGLGameEngine.js', 'w') as f:
    f.write(content)
