class PureCanvasEngine {
    constructor() {
        this.symbols = [
            'sym_high_leviathan', 'sym_high_angler', 'sym_high_viper', 'sym_high_squid',
            'sym_mid_helmet', 'sym_mid_compass', 'sym_wild_maw', 'sym_dead_sediment',
            'rune_10', 'rune_j', 'rune_q', 'rune_k', 'rune_a'
        ];
        this.materials = {};
        this.grid = [];
        this.uiElements = [];
        this.init();
    }

    init() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000510);
        this.scene.fog = new THREE.FogExp2(0x000510, 0.02);

        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.camera.position.z = 10;
        this.camera.position.y = 0;

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        document.body.appendChild(this.renderer.domElement);

        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xaabbff, 1.0);
        dirLight.position.set(5, 10, 5);
        this.scene.add(dirLight);

        const pointLight = new THREE.PointLight(0x00ffff, 1.5, 20);
        pointLight.position.set(0, 0, 5);
        this.scene.add(pointLight);

        this.loadMaterials();
        this.createGrid();
        this.createUI();

        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();

        window.addEventListener('resize', this.onWindowResize.bind(this));
        window.addEventListener('pointerdown', this.onPointerDown.bind(this));

        this.animate();
    }

    loadMaterials() {
        const loader = new THREE.TextureLoader();
        const cb = '?v=9999';
        this.symbols.forEach(sym => {
            const mat = new THREE.MeshStandardMaterial({
                map: loader.load(`/static/assets/pbr/${sym}_albedo.png${cb}`),
                normalMap: loader.load(`/static/assets/pbr/${sym}_normal.png${cb}`),
                roughnessMap: loader.load(`/static/assets/pbr/${sym}_orm.png${cb}`),
                metalnessMap: loader.load(`/static/assets/pbr/${sym}_orm.png${cb}`),
                emissiveMap: loader.load(`/static/assets/pbr/${sym}_emissive.png${cb}`),
                emissive: new THREE.Color(0xffffff),
                emissiveIntensity: 0.5,
                transparent: true
            });
            this.materials[sym] = mat;
            this.materials[sym.replace('sym_', '').replace('rune_', 'LOW_').toUpperCase()] = mat;
        });
        
        const fallbackMat = new THREE.MeshStandardMaterial({ color: 0x444444, wireframe: true });
        this.fallbackMaterial = fallbackMat;
    }

    createGrid() {
        this.gridGroup = new THREE.Group();
        this.scene.add(this.gridGroup);

        const spacingX = 1.5;
        const spacingY = 1.5;
        const offsetX = - (4 * spacingX) / 2;
        const offsetY = - (4 * spacingY) / 2;

        for (let row = 0; row < 5; row++) {
            this.grid[row] = [];
            for (let col = 0; col < 5; col++) {
                const geometry = new THREE.PlaneGeometry(1.4, 1.4);
                const mesh = new THREE.Mesh(geometry, this.fallbackMaterial);
                mesh.position.set(offsetX + col * spacingX, -offsetY - row * spacingY, 0);
                this.gridGroup.add(mesh);
                this.grid[row][col] = mesh;
            }
        }
    }

    createCanvasTexture(text, width=256, height=128, bgColor='#111', textColor='#0f0') {
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = bgColor;
        ctx.fillRect(0, 0, width, height);
        ctx.font = 'bold 30px sans-serif';
        ctx.fillStyle = textColor;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(text, width/2, height/2);
        return new THREE.CanvasTexture(canvas);
    }

    createUI() {
        this.uiGroup = new THREE.Group();
        this.scene.add(this.uiGroup);
        this.uiGroup.position.z = 2;

        const spinTex = this.createCanvasTexture('SPIN', 128, 128, '#800', '#fff');
        const spinGeo = new THREE.CircleGeometry(0.8, 32);
        const spinMat = new THREE.MeshBasicMaterial({ map: spinTex });
        this.spinBtn = new THREE.Mesh(spinGeo, spinMat);
        this.spinBtn.position.set(4, -4, 0);
        this.spinBtn.userData = { action: 'spin' };
        this.uiGroup.add(this.spinBtn);
        this.uiElements.push(this.spinBtn);

        const balTex = this.createCanvasTexture('Balance: $1000.00', 256, 64, '#000', '#fff');
        const balGeo = new THREE.PlaneGeometry(3, 0.75);
        this.balMesh = new THREE.Mesh(balGeo, new THREE.MeshBasicMaterial({ map: balTex }));
        this.balMesh.position.set(-4, -4, 0);
        this.uiGroup.add(this.balMesh);

        const betTex = this.createCanvasTexture('Bet: $1.00', 128, 64, '#000', '#fff');
        const betGeo = new THREE.PlaneGeometry(1.5, 0.75);
        this.betMesh = new THREE.Mesh(betGeo, new THREE.MeshBasicMaterial({ map: betTex }));
        this.betMesh.position.set(-1.5, -4, 0);
        this.uiGroup.add(this.betMesh);

        const betPlusTex = this.createCanvasTexture('+', 64, 64, '#222', '#fff');
        this.betPlusBtn = new THREE.Mesh(new THREE.PlaneGeometry(0.75, 0.75), new THREE.MeshBasicMaterial({map: betPlusTex}));
        this.betPlusBtn.position.set(-0.25, -4, 0);
        this.betPlusBtn.userData = { action: 'bet_up' };
        this.uiGroup.add(this.betPlusBtn);
        this.uiElements.push(this.betPlusBtn);

        const betMinTex = this.createCanvasTexture('-', 64, 64, '#222', '#fff');
        this.betMinBtn = new THREE.Mesh(new THREE.PlaneGeometry(0.75, 0.75), new THREE.MeshBasicMaterial({map: betMinTex}));
        this.betMinBtn.position.set(-2.6, -4, 0);
        this.betMinBtn.userData = { action: 'bet_down' };
        this.uiGroup.add(this.betMinBtn);
        this.uiElements.push(this.betMinBtn);

        const winTex = this.createCanvasTexture('Win: $0.00', 256, 64, '#000', '#ff0');
        this.winMesh = new THREE.Mesh(new THREE.PlaneGeometry(3, 0.75), new THREE.MeshBasicMaterial({ map: winTex }));
        this.winMesh.position.set(0, 4, 0);
        this.uiGroup.add(this.winMesh);
    }

    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    onPointerDown(event) {
        this.mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
        this.mouse.y = - (event.clientY / window.innerHeight) * 2 + 1;
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.uiElements);
        if (intersects.length > 0) {
            const action = intersects[0].object.userData.action;
            if (action === 'spin' && this.onSpin) {
                this.startSpin();
                this.onSpin();
            } else if (action === 'bet_up' && this.onBetUp) {
                this.onBetUp();
            } else if (action === 'bet_down' && this.onBetDown) {
                this.onBetDown();
            }
        }
    }

    startSpin() {
        this.isSpinning = true;
        this.spinVelocity = 0;
    }

    updateText(mesh, text, width=256, height=128, bgColor='#111', textColor='#0f0') {
        const tex = this.createCanvasTexture(text, width, height, bgColor, textColor);
        if (mesh.material.map) {
            mesh.material.map.dispose();
        }
        mesh.material.map = tex;
        mesh.material.needsUpdate = true;
    }

    updateGrid(gridData) {
        this.isSpinning = false;
        this.spinVelocity = 0;
        this.gridGroup.position.set(0, 0, 0);
        
        const symbolMap = {
            'HIGH_LEVIATHAN': 'sym_high_leviathan',
            'HIGH_ANGLER': 'sym_high_angler',
            'HIGH_VIPER': 'sym_high_viper',
            'HIGH_SQUID': 'sym_high_squid',
            'MID_HELMET': 'sym_mid_helmet',
            'MID_COMPASS': 'sym_mid_compass',
            'WILD_MAW': 'sym_wild_maw',
            'DEAD_SEDIMENT': 'sym_dead_sediment',
            'LOW_10': 'rune_10',
            'LOW_J': 'rune_j',
            'LOW_Q': 'rune_q',
            'LOW_K': 'rune_k',
            'LOW_A': 'rune_a'
        };

        const spacingX = 1.5;
        const spacingY = 1.5;
        const offsetX = - (4 * spacingX) / 2;
        const offsetY = - (4 * spacingY) / 2;

        for (let row = 0; row < 5; row++) {
            for (let col = 0; col < 5; col++) {
                const plane = this.grid[row][col];
                plane.position.set(offsetX + col * spacingX, -offsetY - row * spacingY, 0);
                plane.scale.set(1, 1, 1);

                if (gridData && gridData[row] && gridData[row][col]) {
                    const symbol = gridData[row][col];
                    const key = symbolMap[symbol] || symbol;
                    plane.material = this.materials[key] || this.materials[symbol] || this.fallbackMaterial;
                }
            }
        }
    }

    animate() {
        requestAnimationFrame(this.animate.bind(this));
        
        if (this.isSpinning) {
            this.spinVelocity = Math.min(this.spinVelocity + 0.02, 0.8);
            for (let row = 0; row < 5; row++) {
                for (let col = 0; col < 5; col++) {
                    const plane = this.grid[row][col];
                    plane.position.y -= this.spinVelocity;
                    if (plane.position.y < -6) {
                        plane.position.y += 12;
                    }
                    plane.scale.y = 1 + Math.min(this.spinVelocity * 0.5, 2.0);
                }
            }
        }

        this.renderer.render(this.scene, this.camera);
    }
}
window.PureCanvasEngine = PureCanvasEngine;
