with open("scripts/vignette_state_8_purge.js", "r") as f:
    code = f.read()

# Remove the hardcoded ready flag
code = code.replace("window.__RENDER_READY = true;", "")

# Add it to the top using a LoadingManager
manager_code = """
const manager = new THREE.LoadingManager();
manager.onLoad = () => {
    console.log("All assets loaded.");
    setTimeout(() => { window.__RENDER_READY = true; }, 500);
};
"""
code = code.replace("const scene = new THREE.Scene();", manager_code + "\nconst scene = new THREE.Scene();")

# Inject manager into loaders
code = code.replace("const textureLoader = new THREE.TextureLoader();", "const textureLoader = new THREE.TextureLoader(manager);")
code = code.replace("const leviathanLoader = new GLTFLoader();", "const leviathanLoader = new GLTFLoader(manager);")

with open("scripts/vignette_state_8_purge.js", "w") as f:
    f.write(code)

