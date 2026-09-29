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
camera.position.z = 75;

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
        // Massive 5-of-a-kind with Wild Maw across the center line
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
            pLight = new THREE.PointLight(0xff6600, 0, 150);
            pLight.position.set((col - 2) * 11, -(row - 2) * 11, 15);
            scene.add(pLight);
        }

        cells.push({
            mesh,
            col,
            row,
            maps,
            isWinning: isWinningRow,
            pLight: pLight
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
        
        if (t > 1.0) {
            const tWin = t - 1.0;
            
            // Dramatic camera pullback to accommodate massive symbols
            camera.position.z = THREE.MathUtils.lerp(camera.position.z, 85, 0.05);

            cells.forEach(cell => {
                if (cell.isWinning) {
                    // Eruption kinematics: aggressive thrust forward + massive bounce
                    const progress = Math.min(tWin * 5.0, 1.0); // fast deploy
                    const bounce = Math.exp(-tWin * 4.0) * Math.sin(tWin * 25.0);
                    
                    cell.mesh.position.z = progress * 18.0 + bounce * 6.0;
                    cell.mesh.scale.setScalar(1.0 + progress * 0.5 + bounce * 0.2); // 1.5x scale
                    
                    // Violent warm strobe on emissive
                    cell.mesh.material.emissiveIntensity = 8.0 + Math.sin(tWin * 40.0) * 5.0;
                    cell.mesh.material.emissive.lerp(new THREE.Color(0xff8800), 0.2);
                    
                    // PointLight strobe
                    if (cell.pLight) {
                        cell.pLight.intensity = 8000.0 + Math.sin(tWin * 40.0) * 4000.0;
                    }
                } else {
                    // Shove non-winning symbols backwards and dim to black
                    cell.mesh.position.z = THREE.MathUtils.lerp(cell.mesh.position.z, -15.0, 0.1);
                    cell.mesh.material.color.lerp(new THREE.Color(0x111111), 0.1);
                    cell.mesh.material.emissiveIntensity = THREE.MathUtils.lerp(cell.mesh.material.emissiveIntensity, 0.0, 0.2);
                }
            });
            
            // Deepen background to emphasize the glowing symbols
            scene.fog.color.lerp(new THREE.Color(0x010204), 0.05);
            scene.background.lerp(new THREE.Color(0x010204), 0.05);
            ambientLight.intensity = THREE.MathUtils.lerp(ambientLight.intensity, 0.1, 0.1);
            dirLight.intensity = THREE.MathUtils.lerp(dirLight.intensity, 0.1, 0.1);
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
