// ═══════════════════════════════════════════════════════════════════════
// State 8 – The Abyssal Descent / Level-Up Purge
// ═══════════════════════════════════════════════════════════════════════
// Low-pay symbols (Helmet, Compass, Sediment) implode via custom GLSL.
// High-pay symbols & Wild Maw glow red/gold, anchored to the grid.
// Leviathan sweeps Z from -180 → +50, jaws unhinged.
// ═══════════════════════════════════════════════════════════════════════

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// ── Scene ───────────────────────────────────────────────────────────

const manager = new THREE.LoadingManager();
manager.onLoad = () => {
    console.log("All assets loaded.");
    setTimeout(() => { window.__RENDER_READY = true; }, 500);
};

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x010508);
scene.fog = new THREE.FogExp2(0x010508, 0.003);

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 1000);
camera.position.set(0, 0, 72);

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.9;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);

// ── Lights ──────────────────────────────────────────────────────────
const ambientLight = new THREE.AmbientLight(0x112244, 0.6);
scene.add(ambientLight);

const keyLight = new THREE.DirectionalLight(0x3366aa, 2.0);
keyLight.position.set(8, 15, 25);
scene.add(keyLight);

// Deep red point light for purge mood
const purgeLight = new THREE.PointLight(0xff2200, 4.0, 120);
purgeLight.position.set(0, 0, 20);
scene.add(purgeLight);

// Gold rim light for anchored wilds
const rimLight = new THREE.PointLight(0xffaa22, 3.0, 80);
rimLight.position.set(-20, 10, 15);
scene.add(rimLight);

// ── Symbol Classification ───────────────────────────────────────────
const LOW_PAY = ['sym_mid_helmet', 'sym_mid_compass', 'sym_dead_sediment'];
const HIGH_PAY = ['sym_high_angler', 'sym_high_leviathan', 'sym_high_squid', 'sym_high_viper'];
const WILD = ['sym_wild_maw'];

// ── Grid layout: 5 columns × 5 rows ────────────────────────────────
// Intentional placement: scatter low-pay and high-pay with wilds in
// strategic positions to demonstrate the purge contrast.
const GRID = [
    ['sym_mid_helmet',      'sym_high_angler',     'sym_mid_compass',     'sym_high_viper',       'sym_dead_sediment'],
    ['sym_high_squid',      'sym_dead_sediment',   'sym_wild_maw',        'sym_mid_helmet',       'sym_high_angler'],
    ['sym_mid_compass',     'sym_wild_maw',        'sym_high_leviathan',  'sym_wild_maw',         'sym_mid_helmet'],
    ['sym_high_viper',      'sym_mid_helmet',      'sym_wild_maw',        'sym_dead_sediment',    'sym_high_squid'],
    ['sym_dead_sediment',   'sym_high_leviathan',  'sym_mid_compass',     'sym_high_angler',      'sym_mid_compass'],
];

// ── Custom GLSL: Implosion Shader (low-pay only) ────────────────────
const implosionVertexPreamble = `
    uniform float uCrush;   // 0.0 = intact, 1.0 = fully crushed
    uniform float uTime;

    // Pseudo-random from 2D seed
    float hash21(vec2 p) {
        p = fract(p * vec2(123.34, 456.21));
        p += dot(p, p + 45.32);
        return fract(p.x * p.y);
    }
`;

const implosionVertexReplace = `
    #include <begin_vertex>

    // ── Pressure crush: vertices collapse toward center ──
    float crush = clamp(uCrush, 0.0, 1.0);

    // Fragment offset – each vertex gets a unique jitter direction
    float seed = hash21(position.xy * 7.13 + position.yx * 3.77);
    vec3 fragmentDir = normalize(vec3(
        sin(seed * 6.2831 + 1.0) * cos(seed * 3.14),
        cos(seed * 6.2831 + 2.0),
        sin(seed * 4.71 + position.x)
    ));

    // Phase 1 (crush 0→0.6): vertices compress inward
    float compressFactor = smoothstep(0.0, 0.6, crush);
    transformed *= mix(1.0, 0.05, compressFactor);

    // Phase 2 (crush 0.4→1.0): fragment outward burst with spin
    float burstFactor = smoothstep(0.4, 1.0, crush);
    float burstDist = burstFactor * (2.0 + seed * 4.0);
    transformed += fragmentDir * burstDist;

    // Rotation wobble during fracture
    float angle = crush * (3.0 + seed * 5.0);
    float cs = cos(angle);
    float sn = sin(angle);
    mat2 rot = mat2(cs, -sn, sn, cs);
    transformed.xy = rot * transformed.xy;
`;

const implosionFragmentPreamble = `
    uniform float uCrush;
`;

const implosionFragmentReplace = `
    #include <dithering_fragment>

    // Fade out as crush progresses
    float fadeStart = 0.3;
    float alpha = 1.0 - smoothstep(fadeStart, 1.0, uCrush);

    // Pressure heat glow at peak crush
    float heatGlow = smoothstep(0.2, 0.6, uCrush) * (1.0 - smoothstep(0.6, 1.0, uCrush));
    gl_FragColor.rgb += vec3(1.0, 0.15, 0.0) * heatGlow * 4.0;

    gl_FragColor.a *= alpha;
`;

// ── Anchored Wild Glow shader ───────────────────────────────────────
const wildFragmentReplace = `
    #include <dithering_fragment>

    // Pulsing red/gold emissive overlay
    float pulse = 0.5 + 0.5 * sin(uTime * 4.0 + gl_FragCoord.x * 0.01);
    vec3 anchorGlow = mix(vec3(1.0, 0.1, 0.0), vec3(1.0, 0.75, 0.0), pulse);
    gl_FragColor.rgb += anchorGlow * 0.8;
`;

// ── Build Grid ──────────────────────────────────────────────────────
const textureLoader = new THREE.TextureLoader(manager);
const CELL_SIZE = 11;
const lowPayMeshes = [];   // track for animation
const highPayMeshes = [];
const wildMeshes = [];
const allUniforms = [];

const planeGeom = new THREE.PlaneGeometry(10, 10, 48, 48); // high subdiv for vertex deformation

for (let row = 0; row < 5; row++) {
    for (let col = 0; col < 5; col++) {
        const sym = GRID[row][col];
        const basePath = `../slot_engine/static/assets/pbr/${sym}`;
        const isLowPay = LOW_PAY.includes(sym);
        const isWild = WILD.includes(sym);
        const isHighPay = HIGH_PAY.includes(sym);

        // Load PBR textures
        const albedo = textureLoader.load(`${basePath}_albedo.png`);
        albedo.colorSpace = THREE.SRGBColorSpace;
        const normal = textureLoader.load(`${basePath}_normal.png`);
        const orm = textureLoader.load(`${basePath}_orm.png`);
        const emissive = textureLoader.load(`${basePath}_emissive.png`);
        emissive.colorSpace = THREE.SRGBColorSpace;

        const mat = new THREE.MeshStandardMaterial({
            map: albedo,
            normalMap: normal,
            aoMap: orm,
            roughnessMap: orm,
            metalnessMap: orm,
            emissiveMap: emissive,
            emissive: new THREE.Color(0xffffff),
            emissiveIntensity: isWild ? 3.5 : (isHighPay ? 2.0 : 1.0),
            transparent: true,
            side: THREE.DoubleSide,
        });

        const uniforms = {
            uTime: { value: 0 },
            uCrush: { value: 0 },
        };
        allUniforms.push(uniforms);

        mat.onBeforeCompile = (shader) => {
            shader.uniforms.uTime = uniforms.uTime;
            shader.uniforms.uCrush = uniforms.uCrush;

            if (isLowPay) {
                // ── Implosion shader for low-pay ──
                shader.vertexShader = implosionVertexPreamble + shader.vertexShader;
                shader.vertexShader = shader.vertexShader.replace(
                    `#include <begin_vertex>`,
                    implosionVertexReplace
                );
                shader.fragmentShader = implosionFragmentPreamble + shader.fragmentShader;
                shader.fragmentShader = shader.fragmentShader.replace(
                    `#include <dithering_fragment>`,
                    implosionFragmentReplace
                );
            } else if (isWild) {
                // ── Anchored wild glow ──
                shader.vertexShader = `uniform float uTime;\n${shader.vertexShader}`;
                shader.fragmentShader = `uniform float uTime;\n${shader.fragmentShader}`;
                shader.fragmentShader = shader.fragmentShader.replace(
                    `#include <dithering_fragment>`,
                    wildFragmentReplace
                );
            } else if (isHighPay) {
                // ── High-pay: subtle breathing + enhanced emissive ──
                shader.vertexShader = `uniform float uTime;\n${shader.vertexShader}`;
                shader.vertexShader = shader.vertexShader.replace(
                    `#include <begin_vertex>`,
                    `#include <begin_vertex>
                    float breath = sin(uTime * 3.0 + position.x * 0.3) * 0.25;
                    transformed.z += breath;`
                );
            }
        };

        const mesh = new THREE.Mesh(planeGeom, mat);
        mesh.position.set((col - 2) * CELL_SIZE, -(row - 2) * CELL_SIZE, 0);
        scene.add(mesh);

        if (isLowPay) lowPayMeshes.push({ mesh, uniforms });
        else if (isWild) wildMeshes.push({ mesh, uniforms });
        else highPayMeshes.push({ mesh, uniforms });
    }
}

// ── Leviathan ───────────────────────────────────────────────────────
let leviathan = null;
const leviathanLoader = new GLTFLoader(manager);

leviathanLoader.load('../slot_engine/static/assets/models/custom_leviathan.glb', (gltf) => {
    leviathan = gltf.scene;
    leviathan.position.set(0, -5, -180);
    leviathan.scale.set(12, 12, 12);
    leviathan.rotation.y = Math.PI; // facing forward

    leviathan.traverse((child) => {
        if (child.isMesh && child.material) {
            child.material.emissive = new THREE.Color(0x881100);
            child.material.emissiveIntensity = 3.0;
            child.material.transparent = true;
            child.material.side = THREE.DoubleSide;
        }
    });

    scene.add(leviathan);
    console.log('[State 8] Leviathan loaded.');
}, undefined, (error) => {
    console.error('[State 8] Leviathan FAILED to load:', error);
});

// ── Deep Volumetric Fog Particles ───────────────────────────────────
function createVolumetricFog() {
    const count = 3000;
    const positions = new Float32Array(count * 3);
    const alphas = new Float32Array(count);

    for (let i = 0; i < count; i++) {
        positions[i * 3]     = (Math.random() - 0.5) * 160;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 120;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 200 - 40;
        alphas[i] = Math.random() * 0.3 + 0.05;
    }

    const fogGeom = new THREE.BufferGeometry();
    fogGeom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    fogGeom.setAttribute('alpha', new THREE.BufferAttribute(alphas, 1));

    const fogMat = new THREE.ShaderMaterial({
        uniforms: {
            uTime: { value: 0 },
            uColor: { value: new THREE.Color(0x0a3050) },
        },
        vertexShader: `
            attribute float alpha;
            varying float vAlpha;
            uniform float uTime;

            void main() {
                vAlpha = alpha;
                vec3 pos = position;
                pos.x += sin(uTime * 0.2 + position.y * 0.05) * 3.0;
                pos.y += cos(uTime * 0.15 + position.x * 0.03) * 2.0;
                pos.z += sin(uTime * 0.1 + position.z * 0.02) * 4.0;

                gl_PointSize = 4.0 + alpha * 8.0;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
            }
        `,
        fragmentShader: `
            uniform vec3 uColor;
            varying float vAlpha;

            void main() {
                float d = length(gl_PointCoord - 0.5);
                if (d > 0.5) discard;
                float soft = 1.0 - smoothstep(0.0, 0.5, d);
                gl_FragColor = vec4(uColor, vAlpha * soft * 1.2);
            }
        `,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
    });

    const fogPoints = new THREE.Points(fogGeom, fogMat);
    scene.add(fogPoints);
    return fogMat.uniforms;
}

const fogUniforms = createVolumetricFog();

// ── Animation ───────────────────────────────────────────────────────
// Timeline:
//   0.0s – 1.0s : build-up (crush ramps 0→0.3, leviathan starts moving)
//   1.0s – 3.0s : main crush (crush 0.3→1.0, leviathan sweeps through grid)
//   3.0s – 4.5s : aftermath (leviathan exits, wilds pulse)

const ANIM_DURATION = 4.5;
const LEVIATHAN_Z_START = -180;
const LEVIATHAN_Z_END = 50;

const clock = new THREE.Clock();

function animate() {
    requestAnimationFrame(animate);
    const elapsed = clock.getElapsedTime();
    const t = Math.min(elapsed / ANIM_DURATION, 1.0);

    // ── Crush progression ──
    // Ramp: ease-in from 0→1 over the animation
    const crushRaw = t < 0.15
        ? t / 0.15 * 0.15           // slow build 0→0.15
        : 0.15 + (t - 0.15) / 0.85 * 0.85;   // linear ramp rest
    const crush = THREE.MathUtils.smoothstep(crushRaw, 0, 1);

    // Update low-pay implosion
    lowPayMeshes.forEach(({ uniforms }) => {
        uniforms.uCrush.value = crush;
        uniforms.uTime.value = elapsed;
    });

    // Update high-pay breathing
    highPayMeshes.forEach(({ uniforms }) => {
        uniforms.uTime.value = elapsed;
    });

    // Update wilds – ramp emissive during purge
    wildMeshes.forEach(({ mesh, uniforms }) => {
        uniforms.uTime.value = elapsed;
        // Scale emissive intensity with purge progress
        mesh.material.emissiveIntensity = 3.5 + crush * 4.0;
    });

    // ── Leviathan sweep ──
    if (leviathan) {
        const levT = THREE.MathUtils.smoothstep(t, 0.1, 0.85);
        leviathan.position.z = THREE.MathUtils.lerp(LEVIATHAN_Z_START, LEVIATHAN_Z_END, levT);

        // Slight vertical undulation
        leviathan.position.y = -5 + Math.sin(elapsed * 2.0) * 3.0;

        // Jaw unhinge: rotate lower jaw open as it approaches
        const jawOpen = THREE.MathUtils.smoothstep(levT, 0.3, 0.7);
        leviathan.rotation.x = jawOpen * 0.15;  // slight pitch up = jaws open feel

        // Subtle roll
        leviathan.rotation.z = Math.sin(elapsed * 1.5) * 0.05;
    }

    // ── Fog animation ──
    fogUniforms.uTime.value = elapsed;

    // ── Purge light flicker ──
    purgeLight.intensity = 4.0 + Math.sin(elapsed * 8.0) * 1.5 * crush;
    rimLight.intensity = 3.0 + crush * 2.0;

    renderer.render(scene, camera);
}

animate();

// ── Signal readiness for Playwright ─────────────────────────────────


window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
