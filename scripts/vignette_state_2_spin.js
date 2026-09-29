import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import AudioController from './AudioController.js';

let audioController = new AudioController();
let userInteracted = false;

document.getElementById('overlay').addEventListener('click', async (e) => {
    e.target.style.display = 'none';
    await audioController.init();
    audioController.playChain();
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
camera.position.z = 72; // Start Z

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

const customUniforms = [];
const planeGeom = new THREE.PlaneGeometry(10, 10, 32, 32);

for (let row = 0; row < 5; row++) {
    for (let col = 0; col < 5; col++) {
        const sym = symbols[Math.floor(Math.random() * symbols.length)];
        const basePath = `../slot_engine/static/assets/pbr/${sym}`;
        
        const albedo = textureLoader.load(`${basePath}_albedo.png`);
        albedo.colorSpace = THREE.SRGBColorSpace;
        const normal = textureLoader.load(`${basePath}_normal.png`);
        const orm = textureLoader.load(`${basePath}_orm.png`);
        const emissive = textureLoader.load(`${basePath}_emissive.png`);
        emissive.colorSpace = THREE.SRGBColorSpace;

        [albedo, normal, orm, emissive].forEach(tex => {
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

        const uniforms = { uTime: { value: 0 } };
        customUniforms.push(uniforms);

        mat.onBeforeCompile = (shader) => {
            shader.uniforms.uTime = uniforms.uTime;
            shader.vertexShader = `
                uniform float uTime;
                ${shader.vertexShader}
            `.replace(
                `#include <uv_vertex>`,
                `
                #include <uv_vertex>
                
                // Speed increases over time, simulating intense velocity
                float speed = min(uTime * 3.0, 10.0);
                float offset = uTime * speed;

                #ifdef USE_MAP
                    vMapUv.y += offset;
                #endif
                #ifdef USE_NORMALMAP
                    vNormalMapUv.y += offset;
                #endif
                #ifdef USE_EMISSIVEMAP
                    vEmissiveMapUv.y += offset;
                #endif
                #ifdef USE_AOMAP
                    vAoMapUv.y += offset;
                #endif
                #ifdef USE_ROUGHNESSMAP
                    vRoughnessMapUv.y += offset;
                #endif
                #ifdef USE_METALNESSMAP
                    vMetalnessMapUv.y += offset;
                #endif
                `
            );
        };

        const mesh = new THREE.Mesh(planeGeom, mat);
        mesh.position.set((col - 2) * 11, -(row - 2) * 11, 0);
        scene.add(mesh);
    }
}

// Leviathan
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
        
        // Smooth camera pullback
        camera.position.z = THREE.MathUtils.lerp(72, 90, Math.min(t / 2.0, 1.0));

        customUniforms.forEach(u => {
            u.uTime.value = t;
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
