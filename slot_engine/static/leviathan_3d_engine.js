/**
 * Leviathan3DEngine
 * -----------------
 * Studio-Grade Three.js WebGL Foreground Layer for The Descent Slot Machine.
 * Inspired by Nolimit City (San Quentin, Beheaded) & Push Gaming (Razor Shark).
 *
 * Behavioral Architecture:
 *  - Idle State: Completely dormant and submerged in the deep pitch-black trench abyss.
 *    The grid and symbols remain 100% clean, crisp, unobstructed, and legible.
 *  - Triggered Action ('riseAndDevour'): Surges violently UP & FORWARD directly OVER the
 *    reels grid in the foreground (z-index: 25). Angles its ferocious fangs over targeted
 *    cells, unhinges its maw, triggers bioluminescent vaporisation of symbols, and
 *    plunges back down into the abyss!
 *  - Seamless DOM synchronization with Sonar Depth telemetry and test devour button.
 */

class Leviathan3DEngine {
  constructor(containerId = 'leviathan-3d-canvas-container') {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.warn('[3D Engine] Container not found:', containerId);
      return;
    }

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(44, this.container.clientWidth / this.container.clientHeight, 1, 2000);
    this.camera.position.set(0, 0, 310);

    this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'high-performance' });
    this.renderer.setSize(this.container.clientWidth || 400, this.container.clientHeight || 400);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.outputEncoding = THREE.sRGBEncoding;
    this.renderer.setClearColor(0x000000, 0); // Fully transparent clear
    this.container.appendChild(this.renderer.domElement);

    this.creatureRoot = new THREE.Group();
    this.scene.add(this.creatureRoot);

    this.isActionActive = false;
    this.isLoaded = false;
    this.pendingDevour = null;

    // Submerged deep in the Hadal trench void when idle
    this.dormantY = -360;
    this.dormantZ = -200;
    this.creatureRoot.position.set(0, this.dormantY, this.dormantZ);
    this.creatureRoot.visible = false; // Start hidden so reels are 100% unobstructed
    this.container.style.display = 'none'; // Ensure canvas does not composite over grid when idle
    this.container.style.pointerEvents = 'none';

    this.setupLighting();
    this.loadModel();
    this.animate();

    window.addEventListener('resize', () => this.onResize());
  }

  setupLighting() {
    // 1. Oceanic Deep Ambient
    this.ambient = new THREE.AmbientLight(0x040e1c, 2.0);
    this.scene.add(this.ambient);

    // 2. High-intensity Abyssal Cyan Key Light
    this.keyLight = new THREE.DirectionalLight(0x00f0ff, 3.2);
    this.keyLight.position.set(90, 160, 200);
    this.scene.add(this.keyLight);

    // 3. Volcanic Crimson Rim Light on Horns & Spines
    this.rimLight = new THREE.DirectionalLight(0xff2a4b, 2.2);
    this.rimLight.position.set(-140, -80, -120);
    this.scene.add(this.rimLight);

    // 4. Throat Bioluminescent Point Light (Inside the Maw)
    this.throatLight = new THREE.PointLight(0x00f0ff, 2.0, 450);
    this.throatLight.position.set(0, 10, 25);
    this.creatureRoot.add(this.throatLight);

    // 5. Caustic Spotlight
    this.causticLight = new THREE.PointLight(0x00f0ff, 3.5, 500);
    this.causticLight.position.set(0, 100, 150);
    this.scene.add(this.causticLight);
  }

  loadModel() {
    const loader = new THREE.GLTFLoader();
    console.log('[3D Engine] Loading custom 3D Leviathan mesh...');

    loader.load('/static/assets/models/custom_leviathan.glb', (gltf) => {
      this.model = gltf.scene;

      const box = new THREE.Box3().setFromObject(this.model);
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      const fitScale = 280.0 / (maxDim || 1.0);
      this.model.scale.set(fitScale, fitScale, fitScale);

      box.setFromObject(this.model);
      const center = box.getCenter(new THREE.Vector3());
      this.model.position.sub(center);
      this.model.position.y += 14;

      // Rotate 180 degrees so ferocious fangs face forward into camera & reels
      this.model.rotation.set(0, Math.PI, 0);

      this.model.traverse((child) => {
        if (child.isMesh && child.material) {
          child.castShadow = true;
          child.receiveShadow = true;
          child.material.side = THREE.DoubleSide;
          child.material.roughness = 0.52;
          child.material.metalness = 0.30;
        }
      });

      this.creatureRoot.add(this.model);
      this.isLoaded = true;
      console.log('[3D Engine] 1,028K vertex Abyssal Leviathan loaded and armed!');

      // Update UI button and status indicators
      const devourBtn = document.getElementById('btn-test-devour');
      if (devourBtn) {
        devourBtn.innerHTML = '🐉 3D DEVOUR (READY)';
        devourBtn.style.borderColor = '#00f0ff';
        devourBtn.style.boxShadow = '0 0 20px rgba(0, 240, 255, 0.5)';
      }
      const creatureVal = document.getElementById('sonar-creature-val');
      if (creatureVal) {
        creatureVal.textContent = 'DORMANT IN ABYSS';
      }

      // Execute any queued devour request
      if (this.pendingDevour) {
        const fn = this.pendingDevour;
        this.pendingDevour = null;
        fn();
      }
    }, undefined, (err) => {
      console.error('[3D Engine] Failed to load custom_leviathan.glb:', err);
    });
  }

  /**
   * The Signature Nolimit Cinematic Sequence:
   * Surges up from the deep trench OVER the reels in the foreground,
   * unhinges its fanged maw directly over target symbols,
   * evaporates them into bioluminescent energy, chomps shut, and submerges!
   */
  riseAndDevour(targetCells = [], onDevourCallback = null) {
    if (!this.isLoaded || !this.model) {
      console.log('[3D Engine] 3D mesh is still loading, queuing devour action...');
      const devourBtn = document.getElementById('btn-test-devour');
      if (devourBtn) devourBtn.innerHTML = '⏳ LOADING 3D MESH...';
      this.pendingDevour = () => this.riseAndDevour(targetCells, onDevourCallback);
      return;
    }

    if (this.isActionActive) return;
    this.isActionActive = true;
    this.container.style.display = 'block';
    this.creatureRoot.visible = true;

    const creatureVal = document.getElementById('sonar-creature-val');
    if (creatureVal) {
      creatureVal.textContent = 'DEVOURING GRID!';
      creatureVal.style.color = '#ff2a4b';
    }

    if (window.audio) {
      window.audio.playCreatureRoar();
      setTimeout(() => window.audio.playJawChomp(), 550);
      setTimeout(() => window.audio.playSoulAbsorb(), 750);
    }

    // Determine target 3D centroid from targetCells
    let targetX = 0;
    let targetY = 12;
    if (targetCells && targetCells.length > 0 && this.container) {
      const cRect = this.container.getBoundingClientRect();
      let sumX = 0, sumY = 0;
      targetCells.forEach(cell => {
        const r = cell.getBoundingClientRect();
        sumX += (r.left + r.width / 2);
        sumY += (r.top + r.height / 2);
      });
      const avgX = sumX / targetCells.length;
      const avgY = sumY / targetCells.length;
      targetX = ((avgX - cRect.left) / cRect.width - 0.5) * 150;
      targetY = -((avgY - cRect.top) / cRect.height - 0.5) * 150 + 12;
    }

    const duration = 1800; // ms
    const startTime = performance.now();

    const animateDevour = (now) => {
      const elapsed = now - startTime;
      const p = Math.min(1.0, elapsed / duration);

      // Phase 1: Rapid Surge UP & FORWARD over the Grid (0% - 32%)
      if (p < 0.32) {
        const t = p / 0.32;
        const ease = 1 - Math.cos((t * Math.PI) / 2); // easeIn
        this.creatureRoot.position.x = THREE.MathUtils.lerp(0, targetX, ease);
        this.creatureRoot.position.y = THREE.MathUtils.lerp(this.dormantY, targetY, ease);
        this.creatureRoot.position.z = THREE.MathUtils.lerp(this.dormantZ, 70, ease);
        this.creatureRoot.rotation.x = -0.32 * ease; // Head angles down toward grid
        this.creatureRoot.rotation.y = Math.PI - (targetX / 180) * ease;
        this.throatLight.intensity = 2.0 + ease * 16.0;
        this.keyLight.intensity = 3.2 + ease * 5.0;
      }
      // Phase 2: Maw Unhinged, Symbol Evaporation & Screen Shake (32% - 68%)
      else if (p < 0.68) {
        const t = (p - 0.32) / 0.36;
        this.creatureRoot.position.x = targetX + Math.sin(t * Math.PI * 8) * 2;
        this.creatureRoot.position.y = targetY + Math.sin(t * Math.PI * 6) * 4;
        this.creatureRoot.position.z = 70 + t * 16; // Lunging right at the player / symbols

        // Trigger symbol evaporation on grid at peak opening
        if (t > 0.25 && onDevourCallback) {
          onDevourCallback();
          onDevourCallback = null;
        }

        // Screen Shake
        const vp = document.getElementById('viewport-frame');
        if (vp) {
          const shakeMag = (1 - t * 0.5) * 14;
          vp.style.transform = `translate(${(Math.random()-0.5)*shakeMag}px, ${(Math.random()-0.5)*shakeMag}px)`;
        }
      }
      // Phase 3: Screen Impact Snap & Retreat back into Abyss (68% - 100%)
      else {
        const t = (p - 0.68) / 0.32;
        const ease = 0.5 * (1 - Math.cos(t * Math.PI)); // easeInOut
        this.creatureRoot.position.x = THREE.MathUtils.lerp(targetX, 0, ease);
        this.creatureRoot.position.y = THREE.MathUtils.lerp(targetY, this.dormantY, ease);
        this.creatureRoot.position.z = THREE.MathUtils.lerp(86, this.dormantZ, ease);
        this.creatureRoot.rotation.x = THREE.MathUtils.lerp(-0.32, 0, ease);
        this.creatureRoot.rotation.y = THREE.MathUtils.lerp(Math.PI - (targetX / 180), Math.PI, ease);
        this.throatLight.intensity = THREE.MathUtils.lerp(18.0, 2.0, ease);
        this.keyLight.intensity = THREE.MathUtils.lerp(8.2, 3.2, ease);

        const vp = document.getElementById('viewport-frame');
        if (vp) vp.style.transform = 'none';
      }

      if (p < 1.0) {
        requestAnimationFrame(animateDevour);
      } else {
        this.creatureRoot.position.set(0, this.dormantY, this.dormantZ);
        this.creatureRoot.rotation.set(0, Math.PI, 0);
        this.creatureRoot.visible = false; // Submerge back into darkness
        this.container.style.display = 'none'; // Completely hide container so symbols are 100% visible
        this.isActionActive = false;

        const creatureVal = document.getElementById('sonar-creature-val');
        if (creatureVal) {
          creatureVal.textContent = 'DORMANT IN ABYSS';
          creatureVal.style.color = '#00f0ff';
        }
      }
    };

    requestAnimationFrame(animateDevour);
  }

  triggerRoar() {
    this.riseAndDevour([]);
  }

  setDepthLighting(level) {
    if (!this.keyLight) return;
    const colors = [
      0x00f0ff, // Level 0: Sunlight Surface Cyan
      0x38bdf8, // Level 1: Twilight Deep Cyan
      0xffd700, // Level 2: Midnight Sulfur Gold
      0xa855f7, // Level 3: The Abyss Void Amethyst
      0xec4899, // Level 4: Hadal Trench Magenta
      0xff2a4b  // Level 5: Leviathan Core Blood Crimson
    ];
    const targetColor = new THREE.Color(colors[level] || 0x00f0ff);
    this.keyLight.color.copy(targetColor);
    this.causticLight.color.copy(targetColor);
    this.throatLight.color.copy(targetColor);
  }

  onResize() {
    if (!this.container) return;
    const w = this.container.clientWidth || window.innerWidth;
    const h = this.container.clientHeight || window.innerHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    // Only render full Three.js scene when creature is actively visible / striking
    if (this.creatureRoot.visible && this.renderer) {
      const time = performance.now() * 0.001;
      if (this.causticLight) {
        this.causticLight.position.x = Math.sin(time * 1.6) * 90;
        this.causticLight.position.z = 130 + Math.cos(time * 1.1) * 40;
      }
      this.renderer.render(this.scene, this.camera);
    }
  }
}
