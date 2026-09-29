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
camera.position.x = 0;

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

// Reel 5 spotlight/glow
const reel5Light = new THREE.PointLight(0xff2200, 0, 150);
reel5Light.position.set(22, 0, 10);
scene.add(reel5Light);

const textureLoader = new THREE.TextureLoader(manager);
const symbols = [
    'sym_high_angler', 'sym_high_leviathan', 'sym_high_squid', 'sym_high_viper',
    'sym_mid_helmet', 'sym_wild_maw',
    'rune_10', 'rune_a', 'rune_j', 'rune_k', 'rune_q'
];

const planeGeom = new THREE.PlaneGeometry(10, 10, 32, 32);
const cells = [];

for (let row = 0; row < 5; row++) {
    for (let col = 0; col < 5; col++) {
        const isScatter = (col === 0 && row === 2) || (col === 2 && row === 2);
        const sym = isScatter ? 'sym_mid_compass' : symbols[Math.floor(Math.random() * symbols.length)];
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

        cells.push({
            mesh,
            col,
            row,
            maps,
            isScatter,
            baseEmissiveInt: 1.5,
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

const currentLookAt = new THREE.Vector3(0, 0, 0);
const targetLookAt = new THREE.Vector3(0, 0, 0);

function animate() {
    requestAnimationFrame(animate);
    
    if (renderReady) {
        if (animationStartTime < 0) {
            animationStartTime = clock.getElapsedTime();
        }
        const t = clock.getElapsedTime() - animationStartTime;
        
        // Always spin reel 5
        cells.forEach(cell => {
            if (cell.col === 4) {
                cell.maps.forEach(map => {
                    map.offset.y += 18.0 * 0.016; // Fast spin
                });
            }
        });

        if (t > 1.0) {
            // Absolute Blackout
            ambientLight.intensity = 0;
            dirLight.intensity = 0;
            pointLight.intensity = 0;
            scene.background.setHex(0x000000);
            scene.fog.color.setHex(0x000000);
            
            // Camera Zoom & Pan (Look exactly at reel 5)
            targetLookAt.set(22, 0, 0);
            currentLookAt.lerp(targetLookAt, 0.05);
            camera.lookAt(currentLookAt);
            
            camera.position.z = THREE.MathUtils.lerp(camera.position.z, 40, 0.05);
            camera.position.x = THREE.MathUtils.lerp(camera.position.x, 22, 0.05);

            // Teaser Glow on Reel 5 (massive intensity for physical lighting)
            reel5Light.intensity = 5000.0 + Math.sin(t * 30.0) * 3000.0;
            
            cells.forEach(cell => {
                if (cell.col === 4) {
                    // Reel 5 glows red/gold aggressively
                    cell.mesh.material.emissiveIntensity = 5.0 + Math.sin(t * 30.0) * 3.0;
                    cell.mesh.material.emissive.lerp(new THREE.Color(0xff4400), 0.2);
                } else if (cell.isScatter) {
                    // Scatters keep a gentle glow
                    cell.mesh.material.color.lerp(new THREE.Color(0x888888), 0.1);
                    cell.mesh.material.emissiveIntensity = 1.0 + Math.sin(t * 5.0) * 0.5;
                } else {
                    // Force complete pitch black, avoiding specular reflections
                    cell.mesh.material.color.setHex(0x000000);
                    cell.mesh.material.emissive.setHex(0x000000);
                    cell.mesh.material.emissiveIntensity = 0.0;
                    cell.mesh.material.roughness = 1.0;
                    cell.mesh.material.metalness = 0.0;
                }
            });
        }

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
