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
scene.fog = new THREE.FogExp2(0x011a2b, 0.012);
scene.background = new THREE.Color(0x011a2b);

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 1000);
camera.position.z = 70;

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
document.body.appendChild(renderer.domElement);

const ambientLight = new THREE.AmbientLight(0x4466aa, 1.2);
scene.add(ambientLight);

const dirLight = new THREE.DirectionalLight(0x224488, 3.0);
dirLight.position.set(10, 20, 30);
scene.add(dirLight);

const textureLoader = new THREE.TextureLoader(manager);
const symbols = [
    'sym_high_angler', 'sym_high_leviathan', 'sym_high_squid', 'sym_high_viper',
    'sym_wild_maw',
    'rune_10', 'rune_a', 'rune_j', 'rune_k', 'rune_q'
];

const planeGeom = new THREE.PlaneGeometry(10, 10, 32, 32);
const cells = [];

for (let row = 0; row < 5; row++) {
    for (let col = 0; col < 5; col++) {
        const isCollection = (col === 1 && row === 1) || (col === 3 && row === 3);
        const sym = isCollection ? 'sym_mid_compass' : symbols[Math.floor(Math.random() * symbols.length)];
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
            emissiveIntensity: 1.0,
            transparent: true,
            alphaTest: 0.01,
            side: THREE.DoubleSide
        });

        mat.userData.uniforms = {
            uSinkProgress: { value: 0.0 },
            uTime: { value: 0.0 }
        };

        mat.onBeforeCompile = (shader) => {
            shader.uniforms.uSinkProgress = mat.userData.uniforms.uSinkProgress;
            shader.uniforms.uTime = mat.userData.uniforms.uTime;
            
            shader.fragmentShader = `
                uniform float uSinkProgress;
                uniform float uTime;
                
                vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
                vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
                vec3 permute(vec3 x) { return mod289(((x*34.0)+1.0)*x); }
                float snoise(vec2 v) {
                  const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
                  vec2 i  = floor(v + dot(v, C.yy) );
                  vec2 x0 = v -   i + dot(i, C.xx);
                  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
                  vec4 x12 = x0.xyxy + C.xxzz;
                  x12.xy -= i1;
                  i = mod289(i);
                  vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 )) + i.x + vec3(0.0, i1.x, 1.0 ));
                  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
                  m = m*m ; m = m*m ;
                  vec3 x = 2.0 * fract(p * C.www) - 1.0;
                  vec3 h = abs(x) - 0.5;
                  vec3 ox = floor(x + 0.5);
                  vec3 a0 = x - ox;
                  m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
                  vec3 g;
                  g.x  = a0.x  * x0.x  + h.x  * x0.y;
                  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
                  return 130.0 * dot(m, g);
                }

                ${shader.fragmentShader}
            `.replace(
                `#include <map_fragment>`,
                `
                #include <map_fragment>
                
                if (uSinkProgress > 0.0) {
                    float n = snoise(vMapUv * 10.0 + uTime * 2.0);
                    float threshold = uSinkProgress * 2.0 - 0.5;
                    float val = vMapUv.y + n * 0.3; // Jagged organic erosion
                    
                    if (threshold > val) {
                        diffuseColor.a = 0.0;
                    } else {
                        // Dissolve edge alpha
                        diffuseColor.a *= smoothstep(threshold, threshold + 0.15, val);
                        
                        // Blue aquatic glowing edge
                        float edge = smoothstep(threshold + 0.15, threshold + 0.25, val);
                        diffuseColor.rgb += vec3(0.0, 0.8, 1.0) * (1.0 - edge) * uSinkProgress * 3.0;
                    }
                }
                `
            );
        };

        const mesh = new THREE.Mesh(planeGeom, mat);
        mesh.position.set((col - 2) * 11, -(row - 2) * 11, 0);
        scene.add(mesh);

        cells.push({
            mesh,
            col,
            row,
            maps,
            isCollection,
            
            baseRoughness: 1.0,
            baseMetalness: 1.0 // orm map drives the actual metalness
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
            if(cell.mesh.material.userData.uniforms) cell.mesh.material.userData.uniforms.uTime.value = t;
            
            if (cell.isCollection) {
                if (t > 1.0) {
                    const sinkTime = t - 1.0;
                    // Progress from 0 to 1 over 2.5 seconds
                    const progress = Math.min(sinkTime / 2.5, 1.0);
                    
                    // Tumbling tilt backwards and sideways
                    cell.mesh.rotation.x = -progress * Math.PI * 0.6; // 108 degrees backwards
                    cell.mesh.rotation.y = progress * 0.4;
                    cell.mesh.rotation.z = progress * 0.2;
                    
                    // Sink drastically down Z and Y
                    cell.mesh.position.z = -progress * 25.0;
                    cell.mesh.position.y = -(cell.row - 2) * 11 - progress * 20.0;
                    
                    // Update shader to erode alpha
                    if(cell.mesh.material.userData.uniforms) cell.mesh.material.userData.uniforms.uSinkProgress.value = progress;
                    
                    // Lose specular shine as it sinks underwater
                    cell.mesh.material.roughness = THREE.MathUtils.lerp(cell.baseRoughness, 1.0, progress * 2.0);
                    cell.mesh.material.metalness = THREE.MathUtils.lerp(cell.baseMetalness, 0.0, progress * 2.0);
                }
            } else {
                // Dim the rest of the board gently to focus on sinking
                if (t > 1.0) {
                    cell.mesh.material.color.lerp(new THREE.Color(0x444444), 0.05);
                }
            }
        });
        
        // Gentle camera drift
        if (t > 1.0) {
            camera.position.z = THREE.MathUtils.lerp(camera.position.z, 65, 0.01);
            camera.position.y = THREE.MathUtils.lerp(camera.position.y, 2, 0.01);
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
