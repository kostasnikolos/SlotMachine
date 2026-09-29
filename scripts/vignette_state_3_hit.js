import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import AudioController from './AudioController.js';

let audioController = new AudioController();
let userInteracted = false;

document.getElementById('overlay').addEventListener('click', async (e) => {
    e.target.style.display = 'none';
    await audioController.init();
    userInteracted = true;
});

const manager = new THREE.LoadingManager();
let renderReady = false;
manager.onLoad = () => {
    console.log('Loading complete!');
    renderReady = true;
    window.__RENDER_READY = true;
};

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x020813, 0.008);
scene.background = new THREE.Color(0x020813);

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 1000);
camera.position.z = 85;

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
document.body.appendChild(renderer.domElement);

const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);

const dirLight = new THREE.DirectionalLight(0x4488ff, 2.0);
dirLight.position.set(10, 20, 30);
scene.add(dirLight);

const pointLight = new THREE.PointLight(0x00ff88, 3.0, 100);
pointLight.position.set(0, 0, 10);
scene.add(pointLight);

const textureLoader = new THREE.TextureLoader(manager);
const symbols = [
    'sym_high_angler', 'sym_high_leviathan', 'sym_high_squid', 'sym_high_viper',
    'sym_mid_compass', 'sym_mid_helmet', 'sym_wild_maw',
    'rune_10', 'rune_a', 'rune_j', 'rune_k', 'rune_q'
];

const planeGeom = new THREE.PlaneGeometry(10, 10, 32, 32);
const cells = [];

for (let row = 0; row < 5; row++) {
    for (let col = 0; col < 5; col++) {
        // Force the middle row to be winning symbols (e.g., wild maw)
        const isWinningRow = row === 2;
        const sym = isWinningRow ? 'sym_wild_maw' : symbols[Math.floor(Math.random() * symbols.length)];
        const basePath = `../slot_engine/static/assets/pbr/${sym}`;
        
        const albedo = textureLoader.load(`${basePath}_albedo.png`).clone();
        albedo.colorSpace = THREE.SRGBColorSpace;
        albedo.needsUpdate = true;
        const normal = textureLoader.load(`${basePath}_normal.png`).clone();
        normal.needsUpdate = true;
        const orm = textureLoader.load(`${basePath}_orm.png`).clone();
        orm.needsUpdate = true;
        const emissive = textureLoader.load(`${basePath}_emissive.png`).clone();
        emissive.colorSpace = THREE.SRGBColorSpace;
        emissive.needsUpdate = true;

        const maps = [albedo, normal, orm, emissive];
        maps.forEach(tex => {
            tex.wrapS = THREE.RepeatWrapping;
            tex.wrapT = THREE.RepeatWrapping;
        });

        const mat = new THREE.MeshStandardMaterial({
            map: albedo,
            normalMap: normal,
            aoMap: orm,
            roughnessMap: orm,
            metalnessMap: orm,
            emissiveMap: emissive,
            emissive: new THREE.Color(0xffffff),
            emissiveIntensity: 1.5,
            transparent: true,
        });

        const mesh = new THREE.Mesh(planeGeom, mat);
        mesh.position.set((col - 2) * 11, -(row - 2) * 11, 0);
        scene.add(mesh);

        let pLight = null;
        if (isWinningRow) {
            pLight = new THREE.PointLight(0xffaa00, 0, 80);
            pLight.position.set((col - 2) * 11, -(row - 2) * 11, 5);
            scene.add(pLight);
        }

        cells.push({
            mesh,
            col,
            row,
            maps,
            isWinning: isWinningRow,
            pLight: pLight,
            baseEmissiveInt: 1.5,
            hasFlashed: false
        });
    }
}

let leviathan;
const gltfLoader = new GLTFLoader(manager);
gltfLoader.load('../slot_engine/static/assets/models/custom_leviathan.glb', (gltf) => {
    leviathan = gltf.scene;
    leviathan.position.set(0, -10, -180);
    leviathan.scale.set(10, 10, 10);
    leviathan.traverse((child) => {
        if (child.isMesh && child.material) {
            child.material.emissive = new THREE.Color(0x002244);
            child.material.emissiveIntensity = 0.5;
        }
    });
    scene.add(leviathan);
});

const clock = new THREE.Clock();
let animationStartTime = -1;

function animate() {
    requestAnimationFrame(animate);
    
    if (renderReady) {
        if (animationStartTime < 0) {
            animationStartTime = clock.getElapsedTime();
        }
        const t = clock.getElapsedTime() - animationStartTime;
        
        cells.forEach(cell => {
            const stopTime = 1.0 + cell.col * 0.3; // Staggered stops
            
            if (t < stopTime) {
                // Phase 1: Spinning
                const speed = 15.0;
                cell.maps.forEach(map => {
                    map.offset.y += speed * 0.016; // Approx delta time
                });
            } else {
                // Phase 2: Stopped & Bounce
                if (!cell.hasStopped) {
                    cell.hasStopped = true;
                    if (audioController && audioController.isInitialized && cell.row === 0) {
                        audioController.playSpank();
                    }
                }
                const tStop = t - stopTime;
                
                // Align to 0
                cell.maps.forEach(map => {
                    map.offset.y = 0;
                });
                
                // Harmonic squash and stretch bounce
                // Max stretch when tStop is small, settling to 1.0
                const bounce = Math.exp(-tStop * 8.0) * Math.cos(tStop * 30.0);
                cell.mesh.scale.y = 1.0 + bounce * 0.6;
                cell.mesh.scale.x = 1.0 - bounce * 0.2; // Converse squash
                
                // Phase 3: Dim & Flash
                const flashTime = 2.5;
                if (t > flashTime) {
                    const tFlash = t - flashTime;
                    
                    if (cell.isWinning) {
                        if (!cell.hasFlashed) {
                            cell.hasFlashed = true;
                        }
                        // Flash and glow
                        cell.mesh.material.emissiveIntensity = cell.baseEmissiveInt + Math.sin(tFlash * 10.0) * 3.0;
                        cell.mesh.material.color.setScalar(1.0); // full color
                        
                        // massive flash initially, then pulsing
                        if (cell.pLight) {
                            const flashSpike = Math.exp(-tFlash * 10.0) * 100.0;
                            const pulse = Math.sin(tFlash * 10.0) * 15.0 + 15.0;
                            cell.pLight.intensity = flashSpike + pulse;
                        }
                    } else {
                        // Dim
                        const dimFactor = Math.max(0.2, 1.0 - tFlash * 2.0); // smooth dim down to 0.2
                        cell.mesh.material.color.setScalar(dimFactor);
                        cell.mesh.material.emissiveIntensity = Math.max(0.0, cell.baseEmissiveInt - tFlash * 4.0);
                    }
                }
            }
        });

        if (leviathan) {
            leviathan.position.x = Math.sin(t * 0.3) * 40;
            leviathan.position.y = -10 + Math.cos(t * 0.2) * 15;
            leviathan.rotation.y = Math.sin(t * 0.2) * 0.3;
            leviathan.rotation.z = Math.cos(t * 0.2) * 0.1;
        }
    }

    renderer.render(scene, camera);
}

animate();

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
