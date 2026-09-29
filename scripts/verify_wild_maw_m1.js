// verify_wild_maw_m1.js

const scene = new THREE.Scene();

// Set camera at a slight angle to prove parallax depth
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(2, 2, 8);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
// Important for PBR
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
document.body.appendChild(renderer.domElement);

// Add lighting (PBR needs good lighting)
const ambientLight = new THREE.AmbientLight(0xffffff, 0.3); // low ambient
scene.add(ambientLight);

// Key light to catch normals and specular gloss
const pointLight = new THREE.PointLight(0xffffff, 5.0, 50);
pointLight.position.set(3, 4, 5);
scene.add(pointLight);

// Rim light for depth
const rimLight = new THREE.PointLight(0xaaaaff, 3.0, 50);
rimLight.position.set(-3, 3, -5);
scene.add(rimLight);

const manager = new THREE.LoadingManager();
manager.onLoad = function () {
    console.log('Textures loaded. Ready for render.');
    // Force a render immediately after loading
    renderer.render(scene, camera);
    window.__RENDER_READY = true;
};
manager.onError = function (url) {
    console.error('There was an error loading ' + url);
};

const textureLoader = new THREE.TextureLoader(manager);

const timestamp = new Date().getTime();

function loadTex(path, isColor = false) {
    const tex = textureLoader.load('../slot_engine/static/textures/' + path + '?v=' + timestamp);
    if (isColor) {
        tex.encoding = THREE.sRGBEncoding;
    }
    return tex;
}

// Background: just albedo
const bgAlbedo = loadTex('maw_bg_albedo.png', true);
const bgMaterial = new THREE.MeshStandardMaterial({
    map: bgAlbedo,
    transparent: false,
    roughness: 0.9,
    metalness: 0.1
});

// Midground: full PBR
const midAlbedo = loadTex('maw_mid_albedo.png', true);
const midNormal = loadTex('maw_mid_normal.png', false);
const midOrm = loadTex('maw_mid_orm.png', false);
const midEmissive = loadTex('maw_mid_emissive.png', true);

const midMaterial = new THREE.MeshStandardMaterial({
    map: midAlbedo,
    normalMap: midNormal,
    aoMap: midOrm,
    roughnessMap: midOrm,
    metalnessMap: midOrm,
    emissiveMap: midEmissive,
    emissive: new THREE.Color(0xffffff),
    emissiveIntensity: 1.0,
    roughness: 1.0,
    metalness: 1.0,
    transparent: true,
    alphaTest: 0.05
});

// Foreground: highly transparent gloss
const fgAlbedo = loadTex('maw_fg_albedo.png', true);
const fgOrm = loadTex('maw_fg_orm.png', false);
const fgMaterial = new THREE.MeshStandardMaterial({
    map: fgAlbedo,
    aoMap: fgOrm,
    roughnessMap: fgOrm,
    metalnessMap: fgOrm,
    roughness: 1.0,
    metalness: 1.0,
    transparent: true,
    opacity: 1.0, // Let texture alpha handle it
    depthWrite: false
});

// Create planes with different Z depths
const geometry = new THREE.PlaneGeometry(4, 4);

const bgMesh = new THREE.Mesh(geometry, bgMaterial);
bgMesh.position.z = -2.5; // push back

const midMesh = new THREE.Mesh(geometry, midMaterial);
midMesh.position.z = 0; 

const fgMesh = new THREE.Mesh(geometry, fgMaterial);
fgMesh.position.z = 2.5; // pull forward

scene.add(bgMesh);
scene.add(midMesh);
scene.add(fgMesh);

// Make the camera angle a bit more extreme to see the separation
camera.position.set(3, 3, 6);
camera.lookAt(0, 0, 0);

function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}

animate();
