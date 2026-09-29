// monolithic_frame.js
// 3D Monolithic Basalt & Steel Frame Integration - Tier-1 High Fidelity

class MonolithicFrame {
    constructor(scene, camera, renderer) {
        this.scene = scene;
        this.camera = camera;
        this.renderer = renderer;
        
        // PBR rendering setup
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.0;
        
        this.frameGroup = new THREE.Group();
        this.frameGroup.scale.set(20, 20, 20);
        this.frameGroup.position.set(0, 0, 20); // Z=+20
        this.scene.add(this.frameGroup);
        
        this.uniforms = {
            time: { value: 0 },
            depthLevel: { value: 3.0 }, // 5000m (Level 3)
            ritualProgress: { value: 0.5 }, // 50%
            radarSweep: { value: Math.PI * 0.75 } // 135 degrees
        };
        
        this.setupLighting();
        this.loadMaterials();
    }

    setupLighting() {
        // 1. Oceanic Abyssal Ambient Light
        const ambientLight = new THREE.AmbientLight(0x020b14, 1.2);
        this.scene.add(ambientLight);
        
        // 2. Submersible High-Intensity Key Light
        const keyLight = new THREE.DirectionalLight(0x00f0ff, 3.2);
        keyLight.position.set(14.0, 22.0, 26.0);
        this.scene.add(keyLight);
        
        // 3. Volcanic Fissure Rim Light
        const rimLight = new THREE.DirectionalLight(0xff2a4b, 2.4);
        rimLight.position.set(-18.0, -22.0, -8.0);
        this.scene.add(rimLight);
        
        // 4. Leviathan Throat Point Light (Center)
        const throatLight = new THREE.PointLight(0x00ffff, 1.5, 200.0);
        throatLight.position.set(0, 0, 5);
        this.scene.add(throatLight);
        
        // 5. Dynamic Feature Spot Light
        const featureLight = new THREE.SpotLight(0xffd700, 2.0, 250.0);
        featureLight.position.set(0, 10, 15);
        featureLight.angle = Math.PI / 4;
        featureLight.penumbra = 0.5;
        this.scene.add(featureLight);
        
        // Atmospheric Fog
        this.scene.fog = new THREE.FogExp2(0x021626, 0.002);
    }
    
    loadMaterials() {
        const manager = new THREE.LoadingManager();
        manager.onLoad = () => {
            console.log("All textures loaded");
            if (typeof window !== 'undefined') {
                window.__RENDER_READY = true;
            }
        };

        const texLoader = new THREE.TextureLoader(manager);
        
        const basaltAlbedo = texLoader.load('/static/assets/pbr/sym_dead_sediment_albedo.png');
        const basaltNormal = texLoader.load('/static/assets/pbr/sym_dead_sediment_normal.png');
        const basaltORM = texLoader.load('/static/assets/pbr/sym_dead_sediment_orm.png');
        
        [basaltAlbedo, basaltNormal, basaltORM].forEach(tex => {
            if(tex) {
                tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
                tex.repeat.set(0.05, 0.05);
                tex.colorSpace = THREE.SRGBColorSpace || THREE.sRGBEncoding;
            }
        });
        if(basaltNormal) basaltNormal.colorSpace = THREE.LinearSRGBColorSpace || THREE.LinearEncoding;
        if(basaltORM) basaltORM.colorSpace = THREE.LinearSRGBColorSpace || THREE.LinearEncoding;
        
        this.basaltMaterial = new THREE.MeshStandardMaterial({
            map: basaltAlbedo,
            normalMap: basaltNormal,
            normalScale: new THREE.Vector2(0.3, 0.3),
            roughnessMap: basaltORM, // G
            metalnessMap: basaltORM, // B
            aoMap: basaltORM,        // R
            roughness: 0.88,
            metalness: 0.0,
            color: 0x888888
        });
        
        const steelAlbedo = texLoader.load('/static/assets/pbr/sym_mid_helmet_albedo.png');
        const steelNormal = texLoader.load('/static/assets/pbr/sym_mid_helmet_normal.png');
        const steelORM = texLoader.load('/static/assets/pbr/sym_mid_helmet_orm.png');
        
        [steelAlbedo, steelNormal, steelORM].forEach(tex => {
            if(tex) {
                tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
                tex.repeat.set(0.1, 0.1);
                tex.colorSpace = THREE.SRGBColorSpace || THREE.sRGBEncoding;
            }
        });
        if(steelNormal) steelNormal.colorSpace = THREE.LinearSRGBColorSpace || THREE.LinearEncoding;
        if(steelORM) steelORM.colorSpace = THREE.LinearSRGBColorSpace || THREE.LinearEncoding;
        
        this.steelMaterial = new THREE.MeshStandardMaterial({
            map: steelAlbedo,
            normalMap: steelNormal,
            normalScale: new THREE.Vector2(0.5, 0.5),
            roughnessMap: steelORM,
            metalnessMap: steelORM,
            aoMap: steelORM,
            roughness: 0.55,
            metalness: 0.88,
            color: 0xbbbbbb
        });
        
        // True GLSL Plasma shader (Milestone 2 Attempt 5 spec)
        this.plasmaMaterial = new THREE.ShaderMaterial({
            uniforms: this.uniforms,
            vertexShader: `
                varying vec2 vUv;
                void main() {
                    vUv = uv;
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform float depthLevel;
                varying vec2 vUv;
                void main() {
                    float fill = step(vUv.y, depthLevel / 5.0);
                    vec3 color = vec3(0.5, 0.1, 0.9) * fill;
                    
                    float meniscus = smoothstep(0.0, 0.02, abs(vUv.y - (depthLevel / 5.0)));
                    color += vec3(0.9, 0.5, 1.0) * (1.0 - meniscus) * fill * 2.0;
                    
                    if (fill == 0.0) discard;
                    gl_FragColor = vec4(color, 1.0);
                }
            `,
            transparent: false,
            side: THREE.DoubleSide
        });

        this.buildBasaltFrame();
        this.buildLeftPillarBarometer();
        this.buildRightSonarDial();
        this.buildBottomRitualBar();
    }
    
    buildBasaltFrame() {
        const shape = new THREE.Shape();
        shape.moveTo(-14, -8);
        shape.lineTo(14, -8);
        shape.lineTo(14, 8);
        shape.lineTo(-14, 8);
        shape.lineTo(-14, -8);
        
        const hole = new THREE.Path();
        hole.moveTo(-8.5, -6);
        hole.lineTo(8.5, -6);
        hole.lineTo(8.5, 6);
        hole.lineTo(-8.5, 6);
        hole.lineTo(-8.5, -6);
        shape.holes.push(hole);

        const extrudeSettings = { depth: 1.5, bevelEnabled: true, bevelSegments: 4, steps: 2, bevelSize: 0.3, bevelThickness: 0.3 };
        const geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);
        
        const frameMesh = new THREE.Mesh(geometry, this.basaltMaterial);
        frameMesh.position.set(0, 0, -1);
        
        this.frameGroup.add(frameMesh);
    }
    
    buildLeftPillarBarometer() {
        const barometerGroup = new THREE.Group();
        barometerGroup.position.set(-11, 0, 0.5);
        
        // Brackets
        const bracketGeo = new THREE.CylinderGeometry(0.8, 0.8, 1.2, 16);
        const topBracket = new THREE.Mesh(bracketGeo, this.steelMaterial);
        topBracket.position.y = 4.5;
        const botBracket = new THREE.Mesh(bracketGeo, this.steelMaterial);
        botBracket.position.y = -4.5;
        barometerGroup.add(topBracket);
        barometerGroup.add(botBracket);
        
        // Quartz Glass Tube
        const tubeGeo = new THREE.CylinderGeometry(0.6, 0.6, 8, 32);
        const glassMat = new THREE.MeshPhysicalMaterial({
            color: 0xffffff,
            transmission: 0.9,
            opacity: 1,
            metalness: 0.1,
            roughness: 0.05,
            ior: 1.5,
            thickness: 0.5,
            clearcoat: 1.0,
            clearcoatRoughness: 0.1
        });
        const glassTube = new THREE.Mesh(tubeGeo, glassMat);
        barometerGroup.add(glassTube);
        
        // Solid Plasma fluid column representing Level 3 (5000m) ~60% full
        // The tube is 8 units high. 60% of 8 is 4.8. 
        // Position it so it rests at the bottom (-4.0).
        const fillHeight = 4.8;
        
        const fluidGeo = new THREE.CylinderGeometry(0.5, 0.5, fillHeight, 32);
        this.plasmaMaterial = new THREE.MeshStandardMaterial({
            color: 0x8800ff,
            emissive: 0xaa00ff,
            emissiveIntensity: 3.0
        });

        const fluid = new THREE.Mesh(fluidGeo, this.plasmaMaterial);
        fluid.position.y = -4.0 + (fillHeight / 2);
        barometerGroup.add(fluid);
        
        // Notches
        for(let i=1; i<=5; i++) {
            const notchGeo = new THREE.BoxGeometry(1.4, 0.1, 0.2);
            const notch = new THREE.Mesh(notchGeo, this.steelMaterial);
            notch.position.set(0, -4 + (i * (8/5)), 0.6);
            barometerGroup.add(notch);
        }
        
        this.frameGroup.add(barometerGroup);
    }
    
    buildRightSonarDial() {
        const sonarGroup = new THREE.Group();
        sonarGroup.position.set(11, 5.5, 0.5);
        
        // Brass housing / bezel
        const bezelGeo = new THREE.TorusGeometry(2.0, 0.4, 32, 64);
        const bezel = new THREE.Mesh(bezelGeo, this.steelMaterial);
        sonarGroup.add(bezel);
        
        const backplateGeo = new THREE.CylinderGeometry(2.0, 2.0, 0.2, 32);
        const backplate = new THREE.Mesh(backplateGeo, this.steelMaterial);
        backplate.rotation.x = Math.PI / 2;
        backplate.position.z = -0.2;
        sonarGroup.add(backplate);
        
        // Radar Sweep Shader Screen
        const screenGeo = new THREE.CircleGeometry(1.9, 32);
        const screenMat = new THREE.ShaderMaterial({
            uniforms: this.uniforms,
            vertexShader: `
                varying vec2 vUv;
                void main() {
                    vUv = uv;
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform float radarSweep;
                varying vec2 vUv;
                
                void main() {
                    vec2 uv = vUv - 0.5;
                    float dist = length(uv);
                    if(dist > 0.5) discard;
                    
                    float angle = atan(uv.y, uv.x);
                    
                    float sweep = mod(angle - radarSweep + 3.14159, 6.28318) / 6.28318;
                    float phosphor = pow(sweep, 4.0);
                    
                    vec3 color = vec3(0.0, 1.0, 0.2) * phosphor * 2.5;
                    
                    float rings = step(0.9, fract(dist * 10.0));
                    color += vec3(0.0, 0.4, 0.1) * rings;
                    
                    float cross = step(abs(uv.x), 0.01) + step(abs(uv.y), 0.01);
                    color += vec3(0.0, 0.5, 0.2) * cross;
                    
                    // Dark background for dial
                    color += vec3(0.01, 0.05, 0.02);
                    
                    gl_FragColor = vec4(color, 1.0);
                }
            `,
            transparent: false
        });
        const screen = new THREE.Mesh(screenGeo, screenMat);
        screen.position.z = 0.0;
        sonarGroup.add(screen);
        
        // Inner Glass covering the screen
        const glassGeo = new THREE.CircleGeometry(1.95, 32);
        const glassMat = new THREE.MeshPhysicalMaterial({
            color: 0x113322,
            transmission: 0.8,
            roughness: 0.1,
            metalness: 0.3
        });
        const glass = new THREE.Mesh(glassGeo, glassMat);
        glass.position.z = 0.1;
        sonarGroup.add(glass);
        
        this.frameGroup.add(sonarGroup);
    }
    
    buildBottomRitualBar() {
        const ritualGroup = new THREE.Group();
        // Recess it into the frame
        ritualGroup.position.set(0, -6.5, 0.0);
        
        // Deep canal recess cutout (simulated by placing black basalt behind)
        const troughGeo = new THREE.BoxGeometry(16, 1.8, 1);
        const trough = new THREE.Mesh(troughGeo, this.basaltMaterial);
        trough.position.z = -0.5;
        ritualGroup.add(trough);
        
        // Molten stone canal
        const canalGeo = new THREE.PlaneGeometry(15, 1.2);
        const canalMat = new THREE.ShaderMaterial({
            uniforms: this.uniforms,
            vertexShader: `
                varying vec2 vUv;
                void main() {
                    vUv = uv;
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform float ritualProgress;
                varying vec2 vUv;
                
                void main() {
                    float fill = step(vUv.x, ritualProgress);
                    vec3 magma = vec3(1.0, 0.3, 0.0) + vec3(1.0, 0.8, 0.0) * pow(sin(vUv.x * 20.0), 2.0) * 0.8;
                    vec3 deadRock = vec3(0.05, 0.05, 0.05);
                    vec3 color = mix(deadRock, magma, fill);
                    
                    gl_FragColor = vec4(color, 1.0);
                }
            `
        });
        const canal = new THREE.Mesh(canalGeo, canalMat);
        canal.position.z = 0.05;
        ritualGroup.add(canal);
        
        // 5 Carved Runic Purge Cartouches recessed into the canal
        for(let i=0; i<5; i++) {
            const cartGeo = new THREE.BoxGeometry(1.6, 1.6, 0.3);
            const cart = new THREE.Mesh(cartGeo, this.steelMaterial);
            // Placed along the canal
            cart.position.set(-6.0 + (i * 3.0), 0, 0.1);
            ritualGroup.add(cart);
            
            // Add a glowing rune center
            const runeGeo = new THREE.PlaneGeometry(1.0, 1.0);
            const runeMat = new THREE.MeshStandardMaterial({
                color: 0x000000,
                emissive: (i < 2.5) ? 0xff3300 : 0x333333, // Left half lit (ritualProgress 50%)
                emissiveIntensity: 2.0
            });
            const rune = new THREE.Mesh(runeGeo, runeMat);
            rune.position.z = 0.16;
            cart.add(rune);
        }
        
        this.frameGroup.add(ritualGroup);
    }
    
    update(deltaTime) {
        this.uniforms.time.value += deltaTime;
    }
}

if(typeof window !== 'undefined') {
    window.MonolithicFrame = MonolithicFrame;
}
