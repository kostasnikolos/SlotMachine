// webgl_reel_engine.js
// Integrated WebGL Reel Engine with Continuous Loop

class WebGLReelEngine {
    constructor(scene, textureLoader) {
        this.scene = scene;
        this.texLoader = textureLoader;
        
        this.reelGroup = new THREE.Group();
        this.reelGroup.scale.set(20, 20, 20);
        this.reelGroup.position.set(0, 0, 19.5);
        this.scene.add(this.reelGroup);
        
        this.symbolNames = [
            'sym_high_leviathan',
            'sym_high_angler',
            'sym_high_viper',
            'sym_high_squid',
            'sym_mid_helmet',
            'sym_mid_compass',
            'sym_wild_maw',
            'sym_dead_sediment',
            'rune_10',
            'rune_j',
            'rune_q',
            'rune_k',
            'rune_a'
        ];
        
        this.baseMaterials = {};
        this.quads = []; // 2D array [row][col]
        this.geo = new THREE.PlaneGeometry(2.8, 2.8, 32, 32);
        
        this.loadSymbolMaterials();
        this.buildInitialGrid();
    }
    
    getTextureNameFromSymbol(sym) {
        switch(sym) {
            case 'HIGH_LEVIATHAN': return 'sym_high_leviathan';
            case 'HIGH_SQUID': return 'sym_high_squid';
            case 'HIGH_ANGLER': return 'sym_high_angler';
            case 'HIGH_VIPER': return 'sym_high_viper';
            case 'MID_HELMET': return 'sym_mid_helmet';
            case 'MID_COMPASS': return 'sym_mid_compass';
            case 'WILD_MAW': return 'sym_wild_maw';
            case 'DEAD_SEDIMENT': return 'sym_dead_sediment';
            case 'LOW_10': return 'rune_10';
            case 'LOW_J': return 'rune_j';
            case 'LOW_Q': return 'rune_q';
            case 'LOW_K': return 'rune_k';
            case 'LOW_A': return 'rune_a';
            default: return 'sym_dead_sediment';
        }
    }
    
    loadSymbolMaterials() {
        this.symbolNames.forEach(sym => {
            const albedo = this.texLoader.load(`/static/assets/pbr/${sym}_albedo.png?v=9999`);
            const normal = this.texLoader.load(`/static/assets/pbr/${sym}_normal.png?v=9999`);
            const orm = this.texLoader.load(`/static/assets/pbr/${sym}_orm.png?v=9999`);
            const emissive = this.texLoader.load(`/static/assets/pbr/${sym}_emissive.png?v=9999`);
            
            if (albedo) albedo.colorSpace = THREE.SRGBColorSpace || THREE.sRGBEncoding;
            if (normal) normal.colorSpace = THREE.LinearSRGBColorSpace || THREE.LinearEncoding;
            if (orm) orm.colorSpace = THREE.LinearSRGBColorSpace || THREE.LinearEncoding;
            if (emissive) emissive.colorSpace = THREE.SRGBColorSpace || THREE.sRGBEncoding;
            
            const mat = new THREE.MeshStandardMaterial({
                map: albedo,
                normalMap: normal,
                roughnessMap: orm,
                metalnessMap: orm,
                aoMap: orm,
                emissiveMap: emissive,
                emissive: 0xffffff,
                emissiveIntensity: 1.5,
                roughness: 0.8,
                metalness: 0.2
            });
            
            this.baseMaterials[sym] = mat;
        });
    }
    
    buildInitialGrid() {
        const step = 2.9;
        for (let row = 0; row < 5; row++) {
            this.quads[row] = [];
            for (let col = 0; col < 5; col++) {
                const sym = 'sym_dead_sediment';
                const mat = this.baseMaterials[sym];
                
                const quad = new THREE.Mesh(this.geo, mat);
                const xPos = (col - 2) * step;
                const yPos = (2 - row) * step; 
                quad.position.set(xPos, yPos, 0);
                
                this.quads[row][col] = {
                    mesh: quad,
                    baseX: xPos,
                    baseY: yPos,
                    targetY: yPos,
                    velocity: 0,
                    state: 'idle', // idle, fall, impact
                    timer: 0
                };
                
                this.reelGroup.add(quad);
            }
        }
    }
    
    updateGridMatrix(matrix) {
        // matrix is array of strings e.g. [['HIGH_LEVIATHAN', ...], ...]
        // Rebuild or update materials
        const rows = matrix.length;
        const cols = matrix[0].length;
        
        for (let row = 0; row < rows; row++) {
            for (let col = 0; col < cols; col++) {
                if(row < 5 && col < 5) { // 5x5 baseline support
                    const symName = this.getTextureNameFromSymbol(matrix[row][col]);
                    const newMat = this.baseMaterials[symName] || this.baseMaterials['sym_dead_sediment'];
                    
                    const qData = this.quads[row][col];
                    qData.mesh.material = newMat.clone();
                    
                    // Trigger drop physics
                    qData.mesh.position.y = qData.baseY + 10.0; // Start high up
                    qData.targetY = qData.baseY;
                    qData.velocity = 0;
                    qData.state = 'fall';
                    qData.mesh.scale.set(0.9, 1.22, 1.0); // Pre-squash to stretch
                }
            }
        }
    }
    
    setSnapshotWinningState(matrix) {
        // Instantly places grid matrix and applies kinematics explicitly for snapshot
        const rows = matrix.length;
        const cols = matrix[0].length;
        
        for (let row = 0; row < rows; row++) {
            for (let col = 0; col < cols; col++) {
                if(row < 5 && col < 5) {
                    const symName = this.getTextureNameFromSymbol(matrix[row][col]);
                    const newMat = this.baseMaterials[symName] || this.baseMaterials['sym_dead_sediment'];
                    
                    const qData = this.quads[row][col];
                    qData.mesh.material = newMat.clone();
                    qData.mesh.position.y = qData.baseY;
                    qData.mesh.scale.set(1, 1, 1);
                    
                    // Force snapshot kinematics
                    if (col === 1 && row === 1) { // Falling symbol
                        qData.mesh.position.y += 1.5;
                        qData.mesh.scale.set(0.9, 1.22, 1.0);
                    }
                    if (col === 2 && row === 4) { // Impact symbol
                        qData.mesh.position.y -= 0.5;
                        qData.mesh.scale.set(1.12, 0.76, 1.0);
                    }
                }
            }
        }
    }

    update(deltaTime) {
        const fallSpeed = 30.0;
        const impactDuration = 0.15; // 150ms bounce recovery

        for (let row = 0; row < 5; row++) {
            for (let col = 0; col < 5; col++) {
                const qData = this.quads[row][col];
                
                if (qData.state === 'fall') {
                    qData.velocity -= fallSpeed * deltaTime;
                    qData.mesh.position.y += qData.velocity * deltaTime;
                    
                    if (qData.mesh.position.y <= qData.targetY) {
                        qData.mesh.position.y = qData.targetY;
                        qData.state = 'impact';
                        qData.timer = impactDuration;
                        qData.mesh.scale.set(1.12, 0.76, 1.0); // Impact Squash
                        qData.velocity = 0;
                    }
                } else if (qData.state === 'impact') {
                    qData.timer -= deltaTime;
                    // Interpolate back to normal
                    const t = 1.0 - Math.max(0, qData.timer / impactDuration);
                    const sx = 1.12 - (0.12 * t);
                    const sy = 0.76 + (0.24 * t);
                    qData.mesh.scale.set(sx, sy, 1.0);
                    
                    if (qData.timer <= 0) {
                        qData.state = 'idle';
                        qData.mesh.scale.set(1, 1, 1);
                    }
                }
            }
        }
    }
}

if(typeof window !== 'undefined') {
    window.WebGLReelEngine = WebGLReelEngine;
}
