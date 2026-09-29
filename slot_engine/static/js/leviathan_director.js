// leviathan_director.js
// Stage continuous 3D Leviathan and Devour Execution

class LeviathanDirector {
    constructor(scene, loadingManager) {
        this.scene = scene;
        this.manager = loadingManager;
        
        this.leviathanGroup = new THREE.Group();
        this.scene.add(this.leviathanGroup);
        
        this.mixer = null;
        this.mesh = null;
        this.throatLight = null;
        
        this.state = 0; // 0: Idle (Z=-180), 2: Devour Surge (Z=+70)
        
        this.loadModel();
    }
    
    loadModel() {
        // Assume GLTFLoader is globally available via script tag
        const loader = new THREE.GLTFLoader(this.manager);
        
        loader.load('/static/assets/models/custom_leviathan.glb', (gltf) => {
            this.mesh = gltf.scene;
            
            // The model might need significant scaling to match our Z=480 camera and Frame scale
            this.mesh.scale.set(100, 100, 100); 
            
            // Set Idle State
            this.mesh.position.set(0, 0, -180);
            
            this.leviathanGroup.add(this.mesh);
            
            if (gltf.animations && gltf.animations.length > 0) {
                this.mixer = new THREE.AnimationMixer(this.mesh);
                // Try to find devour or open jaw animation, or just play first
                let action = this.mixer.clipAction(gltf.animations[0]);
                gltf.animations.forEach(anim => {
                    if (anim.name.toLowerCase().includes('bite') || anim.name.toLowerCase().includes('devour')) {
                        action = this.mixer.clipAction(anim);
                    }
                });
                action.play();
                this.mixer.setTime(0.5);
            }
            
            // Add dynamic Throat Light
            this.throatLight = new THREE.PointLight(0xff2a4b, 1.5, 450);
            
            let jawBoneFound = false;
            this.mesh.traverse((child) => {
                if (child.isBone && (child.name.toLowerCase().includes('jaw') || child.name.toLowerCase().includes('mouth'))) {
                    child.add(this.throatLight);
                    // Light position offset relative to jaw
                    this.throatLight.position.set(0, 5, 20); 
                    jawBoneFound = true;
                }
                if (child.isMesh) {
                    child.castShadow = true;
                }
            });
            
            if (!jawBoneFound) {
                // Fallback if no specific jaw bone
                this.mesh.add(this.throatLight);
                this.throatLight.position.set(0, 5, 20); // rough throat area
            }
        });
    }
    
    setSnapshotState() {
        if (this.mesh) {
            // Peak Lunge Devour Surge
            this.state = 2;
            this.mesh.position.set(0, -50, 0); // Z=+70, Jaws over center reels
            // Maybe rotate slightly so it's striking the grid
            this.mesh.rotation.x = Math.PI * 0.15; 
            
            if (this.throatLight) {
                // Devour Surge brightly illuminates adjacent symbols
                this.throatLight.intensity = 10.0; // Scaled up massively because of distances
                this.throatLight.distance = 100.0;
                this.throatLight.color.setHex(0xff2a4b); // Magma crimson under-glow
            }
        }
    }
    
    update(deltaTime) {
        if (this.mixer) {
            this.mixer.update(deltaTime);
        }
    }
}

if(typeof window !== 'undefined') {
    window.LeviathanDirector = LeviathanDirector;
}
