class WebGLGameEngine {
    constructor(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        if (container.tagName.toLowerCase() === 'canvas') {
            this.canvas = container;
        } else {
            this.canvas = document.createElement('canvas');
            this.canvas.style.width = '100%';
            this.canvas.style.height = '100%';
            container.appendChild(this.canvas);
        }

        this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true, alpha: true });
        this.renderer.setClearColor(0x000000, 0);

        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
        this.camera.position.set(0, 0, 72);
        
        // Volumetric fog
        this.scene.fog = new THREE.FogExp2(0x0a192f, 0.005);
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);
        
        const dirLight = new THREE.DirectionalLight(0x00f0ff, 1.5);
        dirLight.position.set(50, 50, 50);
        this.scene.add(dirLight);
        
        this.loadingManager = new THREE.LoadingManager();
        this.textureLoader = new THREE.TextureLoader(this.loadingManager);
        this.materials = {};
        this.planes = [];
        this.gridSize = 5;
        this.symbolSpacing = 11.0;
        
        this.isSpinning = false;
        this.spinVelocity = 0;
        this.lastTime = 0;
        
        this.onWindowResize();
        window.addEventListener('resize', this.onWindowResize.bind(this), false);
    }

    async init() {
        return new Promise((resolve) => {
            const syms = [
                'sym_high_leviathan', 'sym_high_angler', 'sym_high_viper', 'sym_high_squid',
                'sym_mid_helmet', 'sym_mid_compass', 'sym_wild_maw', 'sym_dead_sediment',
                'rune_10', 'rune_j', 'rune_q', 'rune_k', 'rune_a'
            ];
            
            syms.forEach(sym => {
                const albedo = this.textureLoader.load(`/static/assets/pbr/${sym}_albedo.png?v=9999`);
                const normal = this.textureLoader.load(`/static/assets/pbr/${sym}_normal.png?v=9999`);
                const orm = this.textureLoader.load(`/static/assets/pbr/${sym}_orm.png?v=9999`);
                const emissive = this.textureLoader.load(`/static/assets/pbr/${sym}_emissive.png?v=9999`);
                
                [albedo, normal, orm, emissive].forEach(tex => {
                    tex.wrapS = THREE.RepeatWrapping;
                    tex.wrapT = THREE.RepeatWrapping;
                    tex.colorSpace = THREE.SRGBColorSpace;
                });
                
                let symbolKey = sym;
                if (sym === 'sym_high_leviathan') symbolKey = 'HIGH_LEVIATHAN';
                else if (sym === 'sym_high_angler') symbolKey = 'HIGH_ANGLER';
                else if (sym === 'sym_high_viper') symbolKey = 'HIGH_VIPER';
                else if (sym === 'sym_high_squid') symbolKey = 'HIGH_SQUID';
                else if (sym === 'sym_mid_helmet') symbolKey = 'MID_HELMET';
                else if (sym === 'sym_mid_compass') symbolKey = 'MID_COMPASS';
                else if (sym === 'sym_wild_maw') symbolKey = 'WILD_MAW';
                else if (sym === 'sym_dead_sediment') symbolKey = 'DEAD_SEDIMENT';
                else if (sym === 'rune_10') symbolKey = 'LOW_10';
                else if (sym === 'rune_j') symbolKey = 'LOW_J';
                else if (sym === 'rune_q') symbolKey = 'LOW_Q';
                else if (sym === 'rune_k') symbolKey = 'LOW_K';
                else if (sym === 'rune_a') symbolKey = 'LOW_A';

                this.materials[symbolKey] = new THREE.MeshStandardMaterial({
                    map: albedo,
                    normalMap: normal,
                    roughnessMap: orm,
                    metalnessMap: orm,
                    aoMap: orm,
                    emissiveMap: emissive,
                    emissive: 0xffffff,
                    emissiveIntensity: 2.0,
                    roughness: 0.7,
                    metalness: 0.3,
                    transparent: false
                });
            });

            this.loadingManager.onLoad = () => {
                this.onWindowResize(); window.addEventListener("resize", () => this.onWindowResize()); console.log("[WebGLGameEngine] init loaded!"); window.__RENDER_READY = true;
                if (this.pendingGridData) {
                    this.updateGrid(this.pendingGridData);
                    this.pendingGridData = null;
                }
                this.render(0);
                resolve();
            };
        });
    }
    
    rebuildPlanes(rows, cols) {
        this.planes.forEach(plane => this.scene.remove(plane));
        this.planes = [];
        this.gridSize = Math.max(rows, cols);
        
        const geometry = new THREE.PlaneGeometry(10, 10);
        const offsetX = (cols - 1) * this.symbolSpacing / 2;
        const offsetY = (rows - 1) * this.symbolSpacing / 2;
        
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const defaultMat = new THREE.MeshBasicMaterial({color: 0x111111});
                const mesh = new THREE.Mesh(geometry, defaultMat);
                const x = (c * this.symbolSpacing) - offsetX;
                const y = -((r * this.symbolSpacing) - offsetY);
                mesh.position.set(x, y, 0);
                mesh.userData = { baseX: x, baseY: y };
                this.scene.add(mesh);
                this.planes.push(mesh);
            }
        }
    }

    updateGrid(gridData) {
        if (!window.__RENDER_READY) {
            this.pendingGridData = gridData;
            return;
        }
        console.log("updateGrid gridData:", gridData); if (!gridData || gridData.length === 0) return;
        
        this.isSpinning = false;
        this.spinVelocity = 0;

        const rows = gridData.length;
        const cols = gridData[0].length;
        this.rows = rows;
        this.cols = cols;
        
        if (this.planes.length === 0 || this.planes.length !== rows * cols) {
            this.rebuildPlanes(rows, cols);
        }
        
        // Map 2D array to 1D planes and restore positions
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const idx = r * cols + c;
                if (this.planes[idx]) {
                    const symbolKey = gridData[r][c];
                    if (this.materials[symbolKey]) {
                        this.planes[idx].material = this.materials[symbolKey];
                        this.planes[idx].material.emissiveIntensity = 2.0;
                    }
                    
                    // Critical Reset
                    this.planes[idx].position.x = this.planes[idx].userData.baseX;
                    this.planes[idx].position.y = this.planes[idx].userData.baseY;
                    this.planes[idx].scale.set(1, 1, 1);
                }
            }
        }
    }

    startSpin() {
        this.isSpinning = true;
        this.spinVelocity = 0;
        this.targetSpinVelocity = 250.0;
        this.baseCameraZ = this.camera.position.z;
        this.targetCameraZ = this.baseCameraZ + 25;
    }

    startCascade() {
        this.planes.forEach(plane => {
            plane.scale.set(1.2, 0.8, 1);
            setTimeout(() => {
                if (!this.isSpinning) plane.scale.set(1, 1, 1);
            }, 300);
        });
    }

    startDevour() {
        this.startCascade();
    }

    highlightCell(row, col) {
        if (!this.cols) return;
        const idx = row * this.cols + col;
        if (this.planes[idx]) {
            this.planes[idx].scale.set(1.2, 1.2, 1.2);
            setTimeout(() => {
                if (!this.isSpinning) this.planes[idx].scale.set(1, 1, 1);
            }, 650);
        }
    }

    onWindowResize() {
        if (!this.canvas || !this.canvas.parentElement) return;
        let width = this.canvas.parentElement.clientWidth || 390;
        let height = this.canvas.parentElement.clientHeight || 480;
        if (height < 200) height = 480;
        
        this.renderer.setSize(width, height);
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();

        const vFov = this.camera.fov * Math.PI / 180;
        const hFov = 2 * Math.atan(Math.tan(vFov / 2) * this.camera.aspect);
        const requiredZ = 55 / (2 * Math.tan(hFov / 2));
        const requiredZVert = 55 / (2 * Math.tan(vFov / 2));
        
        this.camera.position.z = Math.max(72, requiredZ, requiredZVert);
    }

    render(time) {
        requestAnimationFrame(this.render.bind(this));
        
        const timeSec = time * 0.001;
        const dt = Math.min(timeSec - (this.lastTime || timeSec), 0.1);
        this.lastTime = timeSec;

        if (this.isSpinning) {
            this.spinVelocity += (this.targetSpinVelocity - this.spinVelocity) * dt * 5.0;
            this.camera.position.z += (this.targetCameraZ - this.camera.position.z) * dt * 3.0;

            const rows = this.rows || this.gridSize;
            const wrapDistance = rows * this.symbolSpacing;
            const bottomLimit = -((rows - 1) * this.symbolSpacing / 2) - (this.symbolSpacing * 0.6);
            
            this.planes.forEach((plane) => {
                plane.position.y -= this.spinVelocity * dt;
                const stretch = 1.0 + (this.spinVelocity / 40.0);
                plane.scale.set(1, stretch, 1);
                
                if (plane.position.y < bottomLimit) {
                    plane.position.y += wrapDistance;
                }
            });
        } else {
            if (this.baseCameraZ !== undefined) {
                this.camera.position.z += (this.baseCameraZ - this.camera.position.z) * dt * 5.0;
            }
            this.planes.forEach((plane, index) => {
                plane.position.z = Math.sin(timeSec + index) * 0.1;
                if (plane.scale.y > 1.01) {
                    plane.scale.lerp(new THREE.Vector3(1, 1, 1), dt * 10);
                }
            });
        }

        this.renderer.render(this.scene, this.camera);
    }
}

if(typeof window !== 'undefined') {
    window.WebGLGameEngine = WebGLGameEngine;
}
