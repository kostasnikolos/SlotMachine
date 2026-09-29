import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

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
camera.position.z = 72;

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
        const sym = symbols[Math.floor(Math.random() * symbols.length)];
        const basePath = `../slot_engine/static/assets/pbr/${sym}`;
        
        const albedo = textureLoader.load(`${basePath}_albedo.png`).clone();
        albedo.colorSpace = THREE.SRGBColorSpace;
        const normal = textureLoader.load(`${basePath}_normal.png`).clone();
        const orm = textureLoader.load(`${basePath}_orm.png`).clone();
        const emissive = textureLoader.load(`${basePath}_emissive.png`).clone();
        emissive.colorSpace = THREE.SRGBColorSpace;

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
            side: THREE.DoubleSide
        });

        const mesh = new THREE.Mesh(planeGeom, mat);
        const startX = (col - 2) * 11;
        const startY = -(row - 2) * 11;
        mesh.position.set(startX, startY, 0);
        scene.add(mesh);
        
        cells.push({
            mesh,
            col,
            row,
            startX,
            startY,
            spinX: (Math.random() - 0.5) * 20.0,
            spinY: (Math.random() - 0.5) * 20.0,
            spinZ: (Math.random() - 0.5) * 20.0
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
            child.material = child.material.clone();
            child.material.emissive = new THREE.Color(0x002244);
            child.material.emissiveIntensity = 0.5;
        }
    });
    
    scene.add(leviathan);
});

// A central singularity light
const breachLight = new THREE.PointLight(0xff00ff, 0, 1000);
breachLight.position.set(0, 0, 15);
scene.add(breachLight);

const clock = new THREE.Clock();
let animationStartTime = -1;

function animate() {
    requestAnimationFrame(animate);
    
    if (renderReady) {
        if (animationStartTime < 0) {
            animationStartTime = clock.getElapsedTime();
        }
        const t = clock.getElapsedTime() - animationStartTime;
        
        if (t > 1.0) {
            const breachTime = t - 1.0;
            const breachProgress = Math.min(breachTime / 3.0, 1.0); // 3 seconds to total collapse
            
            const ease = Math.pow(breachProgress, 2.5);

            // Camera Shake and Zoom
            const shake = ease * 3.0; // intense shake
            const baseCameraZ = THREE.MathUtils.lerp(72, 35, breachProgress);
            camera.position.x = (Math.random() * 2.0 - 1.0) * shake;
            camera.position.y = (Math.random() * 2.0 - 1.0) * shake;
            camera.position.z = baseCameraZ + (Math.random() * 2.0 - 1.0) * shake;
            
            // Pulse singularity light (violent PBR impact)
            breachLight.intensity = ease * 150000.0 * (1.0 + Math.random() * 0.5);
            
            // Warp environment color to magenta/black
            scene.fog.color.lerp(new THREE.Color(0x110011), 0.1);
            scene.background.lerp(new THREE.Color(0x110011), 0.1);
            
            // Animate Symbols (Physical 3D Kinematics)
            cells.forEach(cell => {
                // Suck into singularity at (0,0,0)
                cell.mesh.position.x = THREE.MathUtils.lerp(cell.startX, 0, ease);
                cell.mesh.position.y = THREE.MathUtils.lerp(cell.startY, 0, ease);
                cell.mesh.position.z = THREE.MathUtils.lerp(0, -10, ease); // suck slightly back
                
                // Violent rapid rotation
                cell.mesh.rotation.x += cell.spinX * ease * 0.1;
                cell.mesh.rotation.y += cell.spinY * ease * 0.1;
                cell.mesh.rotation.z += cell.spinZ * ease * 0.1;
                
                // Scale down into nothingness
                cell.mesh.scale.setScalar(Math.max(1.0 - ease, 0.01));
                
                // Lerp PBR emissive to magenta to catch the light correctly
                cell.mesh.material.emissive.lerp(new THREE.Color(0xff00ff), 0.1);
                cell.mesh.material.emissiveIntensity = 1.5 + ease * 15.0;
            });

            // Suck Leviathan into singularity
            if (leviathan) {
                const levStartX = Math.sin(t * 0.3) * 40;
                const levStartY = -10 + Math.cos(t * 0.2) * 15;
                const levStartZ = -180;
                
                leviathan.position.x = THREE.MathUtils.lerp(levStartX, 0, ease);
                leviathan.position.y = THREE.MathUtils.lerp(levStartY, 0, ease);
                leviathan.position.z = THREE.MathUtils.lerp(levStartZ, 0, ease);
                
                leviathan.rotation.x += ease * 0.2;
                leviathan.rotation.y += ease * 0.5;
                leviathan.rotation.z += ease * 0.3;
                
                leviathan.scale.setScalar(Math.max(10.0 * (1.0 - ease), 0.01));
                
                leviathan.traverse((child) => {
                    if (child.isMesh && child.material) {
                        child.material.emissive.lerp(new THREE.Color(0xff00ff), 0.1);
                        child.material.emissiveIntensity = 0.5 + ease * 5.0;
                    }
                });
            }
        } else {
            if (leviathan) {
                // Normal Leviathan idle before breach
                leviathan.position.x = Math.sin(t * 0.3) * 40;
                leviathan.position.y = -10 + Math.cos(t * 0.2) * 15;
                leviathan.rotation.y = Math.sin(t * 0.2) * 0.3;
                leviathan.rotation.z = Math.cos(t * 0.2) * 0.1;
            }
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
