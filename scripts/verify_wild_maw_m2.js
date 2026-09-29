// verify_wild_maw_m2.js

const scene = new THREE.Scene();

// Set camera at a slight angle to prove parallax depth
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(3, 3, 6);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
// Important for PBR
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
document.body.appendChild(renderer.domElement);

// Add lighting (PBR needs good lighting)
const ambientLight = new THREE.AmbientLight(0xffffff, 0.3); 
scene.add(ambientLight);

const pointLight = new THREE.PointLight(0xffffff, 5.0, 50);
pointLight.position.set(3, 4, 5);
scene.add(pointLight);

const rimLight = new THREE.PointLight(0xaaaaff, 3.0, 50);
rimLight.position.set(-3, 3, -5);
scene.add(rimLight);

const manager = new THREE.LoadingManager();
manager.onLoad = function () {
    console.log('Textures loaded. Ready for render.');
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

// Midground: full PBR with Vertex Breathing Shader
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
    transparent: true
});

// Vertex Breathing Injection
midMaterial.onBeforeCompile = function (shader) {
    // Inject custom uniforms
    shader.uniforms.uTime = { value: 0.785 }; // Fix time to 0.785 (pi/4) so sin(uTime * 2) = 1 (max deformation)
    midMaterial.userData.shader = shader;
    
    // Vertex shader modifications
    shader.vertexShader = `uniform float uTime;\n` + shader.vertexShader;
    shader.vertexShader = shader.vertexShader.replace(
        '#include <begin_vertex>',
        `
        #include <begin_vertex>
        
        // Center of the texture
        float dist = distance(uv, vec2(0.5));
        
        // Breathing expansion logic
        float expansion = sin(uTime * 2.0) * 0.5 + 0.5; // 0 to 1
        
        // Displace vertices outward based on distance from center
        transformed.x += (uv.x - 0.5) * expansion * 1.5;
        transformed.y += (uv.y - 0.5) * expansion * 1.5;
        
        // Add Z-depth breathing (bulging out)
        transformed.z += sin(dist * 3.14) * expansion * 1.0;
        `
    );
};

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
    opacity: 1.0,
    depthWrite: false
});

// Create planes with different Z depths
// Important: Midground needs higher segment count for vertex displacement!
const bgGeometry = new THREE.PlaneGeometry(4, 4);
const fgGeometry = new THREE.PlaneGeometry(4, 4);
const midGeometry = new THREE.PlaneGeometry(4, 4, 32, 32);

const bgMesh = new THREE.Mesh(bgGeometry, bgMaterial);
bgMesh.position.z = -2.5; 

const midMesh = new THREE.Mesh(midGeometry, midMaterial);
midMesh.position.z = 0; 

const fgMesh = new THREE.Mesh(fgGeometry, fgMaterial);
fgMesh.position.z = 2.5; 

scene.add(bgMesh);
scene.add(midMesh);
scene.add(fgMesh);

function animate() {
    requestAnimationFrame(animate);
    
    // Animate the shader if rendering continuously
    if (midMaterial.userData.shader) {
        // We can increment uTime here for a live view, but for snapshot it's fine
        // midMaterial.userData.shader.uniforms.uTime.value += 0.05;
    }
    
    renderer.render(scene, camera);
}

animate();
