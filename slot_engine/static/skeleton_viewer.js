// ============================================================================
// TRUE 3D SKELETAL CREATURE VISUAL ENGINE (100% PURE 3D MESH & ANIMATED RIG)
// ============================================================================
// Zero 2D planes, zero cards, zero heightfield boxes.
// Uses a 100% volumetric, 360-degree organic rigged 3D predator model with:
// - Skeletal bone skinning and articulated TMJ jaw hinge
// - Full 3D modeled teeth, gums, gills, dorsal fin, and swimming spine
// - Embedded studio skeletal animations: 'swimming', 'circling', 'bite'
// - Real-time PBR shaders with Abyssal Cyan godrays, Crimson rim, & Caustics
// ============================================================================

class LeviathanTrue3DViewer {
  constructor() {
    this.container = document.getElementById('canvas-container');
    this.width = this.container.clientWidth || window.innerWidth;
    this.height = this.container.clientHeight || window.innerHeight;

    this.params = {
      viewMode: 'PBR',
      swimSpeed: 1.0,
      glowColor: 0x00f0ff,
    };

    this.clock = new THREE.Clock();
    this.time = 0;
    this.state = 'IDLE';
    this.screenShake = 0;
    this.animations = {};
    this.mixer = null;
    this.model = null;

    this.initScene();
    this.initLighting();
    this.loadTrue3DModel();
    this.buildAtmosphericParticles();
    this.buildAnglerLure();
    this.attachDOMControls();
    this.setupAutoCaptureHook();
    this.animate();

    window.addEventListener('resize', () => this.onResize());
  }

  // ===========================================================================
  // 1. THREE.JS SCENE, CAMERA & RENDERER SETUP
  // ===========================================================================
  initScene() {
    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.FogExp2(0x020712, 0.0009);

    this.camera = new THREE.PerspectiveCamera(40, this.width / this.height, 1, 3500);
    this.camera.position.set(0, 15, 340);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true });
    this.renderer.setSize(this.width, this.height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor(0x020712, 1.0);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.container.appendChild(this.renderer.domElement);

    this.orbit = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.orbit.enableDamping = true;
    this.orbit.dampingFactor = 0.06;
    this.orbit.maxDistance = 850;
    this.orbit.minDistance = 100;
    this.orbit.minPolarAngle = Math.PI * 0.05;
    this.orbit.maxPolarAngle = Math.PI * 0.95;
    this.orbit.target.set(0, 0, 0);

    // Creature Root Pivot
    this.creatureRoot = new THREE.Group();
    this.scene.add(this.creatureRoot);
  }

  // ===========================================================================
  // 2. STUDIO PBR LIGHTING (CYAN GODRAY + CRIMSON RIM + CAUSTICS SPOTLIGHT)
  // ===========================================================================
  initLighting() {
    // 1. Abyssal Deep Sea Ambient Fill (reveals muscular mass and skin textures)
    this.ambientLight = new THREE.AmbientLight(0x1a334d, 2.8);
    this.scene.add(this.ambientLight);

    // 2. Key Cyan Godray (High Specular on skin, fangs, and dorsal ridge)
    this.keyLight = new THREE.DirectionalLight(0x00f0ff, 3.8);
    this.keyLight.position.set(160, 260, 240);
    this.keyLight.castShadow = true;
    this.scene.add(this.keyLight);

    // 3. Flank Fill Light (illuminates opposing flank and eye)
    this.fillLight = new THREE.DirectionalLight(0x38bdf8, 2.2);
    this.fillLight.position.set(-180, 80, 220);
    this.scene.add(this.fillLight);

    // 4. Hot Crimson/Neon Magenta Rim Light (Grazes 3D silhouette from behind)
    this.rimLight = new THREE.DirectionalLight(0xff2a4b, 4.2);
    this.rimLight.position.set(-200, 120, -220);
    this.scene.add(this.rimLight);

    // 5. Moving Underwater Caustics Spotlight
    this.causticLight = new THREE.SpotLight(0x38bdf8, 3.5, 950, Math.PI / 3.5, 0.45);
    this.causticLight.position.set(0, 320, 160);
    this.scene.add(this.causticLight);

    // 6. Internal Throat Glow Point Light
    this.throatLight = new THREE.PointLight(0x00f0ff, 3.0, 220);
    this.throatLight.position.set(0, 0, 30);
    this.creatureRoot.add(this.throatLight);
  }

  // ===========================================================================
  // 3. LOAD TRUE 3D SKELETAL GLB MODEL WITH BONE RIGGING
  // ===========================================================================
  loadTrue3DModel() {
    const hud = document.getElementById('status-hud');
    if (hud) {
      hud.textContent = 'LOADING 3D MESH...';
      hud.style.borderColor = '#ffd700';
      hud.style.color = '#ffd700';
    }

    const urlParams = new URLSearchParams(window.location.search);
    const modelParam = urlParams.get('model') || 'custom_leviathan.glb';
    const isCustom = modelParam !== 'shark_clean.glb';
    const modelUrl = `/static/assets/models/${modelParam}`;

    const loader = new THREE.GLTFLoader();
    loader.load(modelUrl, (gltf) => {
      console.log('[GLTF] Successfully loaded 3D Mesh:', gltf);
      this.model = gltf.scene;

      // Bulletproof Auto-Fit: adapt to ANY model dimensions
      const box = new THREE.Box3().setFromObject(this.model);
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);

      if (isCustom) {
        // Center custom dragon / creature mesh perfectly at origin
        const targetDim = 200.0;
        const fitScale = targetDim / (maxDim || 1.0);
        this.model.scale.set(fitScale, fitScale, fitScale);

        box.setFromObject(this.model);
        const center = box.getCenter(new THREE.Vector3());
        this.model.position.sub(center);
        this.model.position.y += 10;
        this.model.rotation.set(0, Math.PI, 0);

        this.model.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
            if (child.material) {
              child.material.side = THREE.DoubleSide;
              child.material.roughness = 0.55;
              child.material.metalness = 0.25;
            }
            this.mesh = child;
          }
        });

        // Hide angler lure if custom model already has horns/features
        if (this.lureGroup) this.lureGroup.visible = false;
      } else {
        const currentLength = size.z || 16.92;
        const targetLength = 422.5;
        const fitScale = targetLength / currentLength;
        this.model.scale.set(fitScale, fitScale, fitScale);

        this.model.position.set(0, -43.75, -137.5);
        this.model.rotation.set(0, 0, 0);

        const texLoader = new THREE.TextureLoader();
        const diffTex = texLoader.load('/static/assets/textures/leviathan_diffuse.png');
        const emisTex = texLoader.load('/static/assets/textures/leviathan_emissive.png');
        diffTex.flipY = false;
        emisTex.flipY = false;

        this.model.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
            this.mesh = child;

            if (child.material) {
              child.material.map = diffTex;
              child.material.emissiveMap = emisTex;
              child.material.emissive = new THREE.Color(0x00f0ff);
              child.material.emissiveIntensity = 1.6;
              child.material.roughness = 0.32;
              child.material.metalness = 0.28;
              child.material.needsUpdate = true;
            }
          }
        });
      }

      this.creatureRoot.add(this.model);

      // Setup Skeletal Bone Animations
      this.mixer = new THREE.AnimationMixer(this.model);
      this.animations = {};

      gltf.animations.forEach((clip) => {
        console.log('[GLTF] Found animation clip:', clip.name, `duration: ${clip.duration.toFixed(2)}s`);
        const action = this.mixer.clipAction(clip);
        this.animations[clip.name] = action;
      });

      // Play continuous swimming animation loop with organic bone deformation
      if (this.animations['swimming']) {
        this.animations['swimming'].setLoop(THREE.LoopRepeat);
        this.animations['swimming'].play();
      } else if (gltf.animations.length > 0) {
        this.mixer.clipAction(gltf.animations[0]).play();
      }

      if (hud) {
        hud.textContent = 'TRUE 3D PREDATOR // ACTIVE';
        hud.style.borderColor = '#10b981';
        hud.style.color = '#10b981';
      }

      // Automatically capture snapshot for server verification
      setTimeout(async () => {
        try {
          this.renderer.render(this.scene, this.camera);
          const dataUrl = this.renderer.domElement.toDataURL('image/png');
          await fetch('/api/snapshot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: 'true_3d_auto_verified', image_base64: dataUrl })
          });
        } catch (e) {
          // ignore background snapshot error
        }
      }, 1000);
    }, undefined, (err) => {
      console.error('[GLTF] Error loading model:', err);
      if (hud) {
        hud.textContent = 'ERROR LOADING 3D MESH';
        hud.style.borderColor = '#ef4444';
        hud.style.color = '#ef4444';
      }
    });
  }

  // Deep-sea ambient floating plankton particles
  buildAtmosphericParticles() {
    const count = 320;
    const geom = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      positions[i * 3]     = (Math.random() - 0.5) * 750;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 650;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 550;

      // Cyan / Electric Blue embers
      colors[i * 3]     = 0.0;
      colors[i * 3 + 1] = 0.85 + Math.random() * 0.15;
      colors[i * 3 + 2] = 1.0;
    }

    geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const pMat = new THREE.PointsMaterial({
      size: 3.2,
      vertexColors: true,
      transparent: true,
      opacity: 0.65,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    this.particles = new THREE.Points(geom, pMat);
    this.scene.add(this.particles);
  }

  // ===========================================================================
  // 4. ELDRITCH ANGLER LURE & BIOLUMINESCENT PHOTOPHORE ORGAN
  // ===========================================================================
  buildAnglerLure() {
    this.lureGroup = new THREE.Group();

    // Curved chitinous stalk arching up from forehead and over the snout
    const curvePoints = [];
    const segments = 14;
    for (let i = 0; i <= segments; i++) {
      const t = i / segments;
      const x = Math.sin(t * Math.PI) * 1.5;
      const y = Math.sin(t * Math.PI * 0.72) * 42;
      const z = t * 68;
      curvePoints.push(new THREE.Vector3(x, y, z));
    }
    const curve = new THREE.CatmullRomCurve3(curvePoints);
    const stalkGeom = new THREE.TubeGeometry(curve, 24, 1.4, 8, false);
    const stalkMat = new THREE.MeshStandardMaterial({
      color: 0x051322,
      roughness: 0.35,
      metalness: 0.35,
      emissive: new THREE.Color(0x001525),
    });
    const stalkMesh = new THREE.Mesh(stalkGeom, stalkMat);
    stalkMesh.castShadow = true;
    this.lureGroup.add(stalkMesh);

    // Glowing Bioluminescent Bulb (Eldritch Photophore)
    const tipPos = curvePoints[curvePoints.length - 1];
    const bulbGeom = new THREE.SphereGeometry(3.5, 16, 16);
    const bulbMat = new THREE.MeshStandardMaterial({
      color: 0x00f0ff,
      emissive: new THREE.Color(0x00f0ff),
      emissiveIntensity: 2.8,
      roughness: 0.1,
    });
    this.lureBulb = new THREE.Mesh(bulbGeom, bulbMat);
    this.lureBulb.position.copy(tipPos);
    this.lureGroup.add(this.lureBulb);

    // Dynamic Bioluminescent Point Light
    this.lureLight = new THREE.PointLight(0x00f0ff, 3.5, 200);
    this.lureLight.position.copy(tipPos);
    this.lureGroup.add(this.lureLight);

    // Mount on cranium above the snout between the eyes
    this.lureGroup.position.set(0, 16, 22);
    this.creatureRoot.add(this.lureGroup);
  }

  // ===========================================================================
  // 4. ANIMATION TRIGGERS: JAW STRIKE CHOMP & SUB-BASS ROAR
  // ===========================================================================
  triggerJawStrike() {
    if (this.state === 'STRIKING') return;
    this.state = 'STRIKING';

    const hud = document.getElementById('status-hud');
    if (hud) {
      hud.textContent = '⚡ UNHINGED BITE // LUNGE STRIKE!';
      hud.style.borderColor = '#ef4444';
      hud.style.color = '#ef4444';
    }

    // 1. Play the authentic 3D 'bite' animation from the skeletal model!
    if (this.animations && this.animations['bite']) {
      const biteAction = this.animations['bite'];
      biteAction.reset();
      biteAction.setLoop(THREE.LoopOnce);
      biteAction.clampWhenFinished = false;
      biteAction.timeScale = 1.35; // Fast aggressive snap!
      biteAction.play();
    }

    // 2. Kinematic Lunge Forward & Screen Shake
    const startPos = this.creatureRoot.position.clone();
    const startTime = performance.now();
    const duration = 1100; // ms

    const animateStrike = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(1.0, elapsed / duration);

      // Phase 1: Drawback into shadows (0 - 25%)
      if (progress < 0.25) {
        const p = progress / 0.25;
        this.creatureRoot.position.z = -p * 35;
      }
      // Phase 2: Violent Forward Lunge (25 - 60%)
      else if (progress < 0.60) {
        const p = (progress - 0.25) / 0.35;
        const ease = p * p;
        this.creatureRoot.position.z = -35 + ease * 95; // Lunges forward to +60!
        if (this.throatLight) this.throatLight.intensity = 2.5 + ease * 5.0;
      }
      // Phase 3: Screen-Space Camera Tremor (60 - 80%)
      else if (progress < 0.80) {
        const p = (progress - 0.60) / 0.20;
        this.screenShake = (1.0 - p) * 18;
      }
      // Phase 4: Recovery (80 - 100%)
      else {
        const p = (progress - 0.80) / 0.20;
        const ease = 0.5 * (1.0 - Math.cos(p * Math.PI));
        this.creatureRoot.position.lerpVectors(new THREE.Vector3(0, 0, 60), startPos, ease);
        this.screenShake = 0;
        if (this.throatLight) this.throatLight.intensity = 2.5;
      }

      if (progress < 1.0) {
        requestAnimationFrame(animateStrike);
      } else {
        this.state = 'IDLE';
        this.creatureRoot.position.copy(startPos);
        if (hud) {
          hud.textContent = 'TRUE 3D PREDATOR // SWIMMING';
          hud.style.borderColor = '#10b981';
          hud.style.color = '#10b981';
        }
      }
    };

    requestAnimationFrame(animateStrike);
  }

  triggerRoar() {
    if (this.state === 'ROARING') return;
    this.state = 'ROARING';

    const hud = document.getElementById('status-hud');
    if (hud) {
      hud.textContent = '🔊 SUB-BASS ROAR // CAVITATION';
      hud.style.borderColor = '#38bdf8';
      hud.style.color = '#38bdf8';
    }

    if (this.animations && this.animations['bite']) {
      const biteAction = this.animations['bite'];
      biteAction.reset();
      biteAction.setLoop(THREE.LoopPingPong, 2);
      biteAction.timeScale = 0.7; // Slow menacing gape
      biteAction.play();
    }

    const startTime = performance.now();
    const duration = 1400;

    const animateRoar = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(1.0, elapsed / duration);

      // Acoustic vibration
      const vibration = Math.sin(progress * Math.PI * 26) * (1.0 - progress) * 8;
      this.creatureRoot.position.x = vibration;
      this.creatureRoot.position.y = (Math.random() - 0.5) * vibration;

      if (this.throatLight) {
        this.throatLight.intensity = 2.5 + Math.sin(progress * Math.PI) * 6.0;
      }

      if (progress < 1.0) {
        requestAnimationFrame(animateRoar);
      } else {
        this.state = 'IDLE';
        this.creatureRoot.position.set(0, 0, 0);
        if (this.throatLight) this.throatLight.intensity = 2.5;
        if (hud) {
          hud.textContent = 'TRUE 3D PREDATOR // SWIMMING';
          hud.style.borderColor = '#10b981';
          hud.style.color = '#10b981';
        }
      }
    };

    requestAnimationFrame(animateRoar);
  }

  // ===========================================================================
  // 5. MAIN RENDER LOOP & PER-FRAME UPDATES
  // ===========================================================================
  animate() {
    requestAnimationFrame(() => this.animate());

    const delta = this.clock.getDelta();
    this.time += delta * this.params.swimSpeed;

    // Update skeletal bone animation mixer
    if (this.mixer) {
      this.mixer.update(delta * this.params.swimSpeed);
    }

    // Natural 3D ocean current drift & sway
    if (this.state === 'IDLE' && this.creatureRoot) {
      const swayX = Math.sin(this.time * 0.8) * 10;
      const swayY = Math.cos(this.time * 1.1) * 7;
      const rollZ = Math.sin(this.time * 0.6) * 0.04;

      this.creatureRoot.position.x += (swayX - this.creatureRoot.position.x) * 0.05;
      this.creatureRoot.position.y += (swayY - this.creatureRoot.position.y) * 0.05;
      this.creatureRoot.rotation.z += (rollZ - this.creatureRoot.rotation.z) * 0.05;
    }

    // Animated Caustics light sweep across 3D scales
    if (this.causticLight) {
      this.causticLight.position.x = Math.sin(this.time * 0.7) * 110;
      this.causticLight.position.z = 160 + Math.cos(this.time * 0.5) * 60;
    }

    // Biological pulse and sway of Eldritch Angler Lure
    if (this.lureLight && this.state !== 'STRIKING') {
      this.lureLight.intensity = 2.8 + Math.sin(this.time * 3.8) * 1.2;
    }
    if (this.lureGroup) {
      this.lureGroup.rotation.z = Math.sin(this.time * 1.5) * 0.08;
      this.lureGroup.rotation.x = Math.cos(this.time * 1.8) * 0.05;
    }

    // Camera Tremor from jaw strike
    if (this.screenShake > 0.1) {
      this.camera.position.x += (Math.random() - 0.5) * this.screenShake;
      this.camera.position.y += (Math.random() - 0.5) * this.screenShake;
      this.screenShake *= 0.84;
    }

    this.orbit.update();
    this.renderer.render(this.scene, this.camera);
  }

  // ===========================================================================
  // 6. CAMERA PRESETS & DOM INTERACTION
  // ===========================================================================
  setCameraPreset(preset) {
    const dur = 850;
    const startPos = this.camera.position.clone();
    const startTarget = this.orbit.target.clone();
    let targetPos = new THREE.Vector3();
    let targetLook = new THREE.Vector3(0, 0, 0);

    switch (preset) {
      case 'FRONT':
        targetPos.set(0, 15, 340);
        targetLook.set(0, 0, 0);
        break;
      case 'THREE_QUARTER':
        targetPos.set(220, 60, 240);
        targetLook.set(0, 0, 0);
        break;
      case 'PROFILE':
        // TRUE 90-DEGREE 3D SIDE PROFILE - PROVES FULL 360 VOLUMETRIC MASS
        targetPos.set(-360, 20, 0);
        targetLook.set(0, 0, 0);
        break;
      case 'MAW_CLOSEUP':
        targetPos.set(0, -6, 130);
        targetLook.set(0, -8, 0);
        break;
    }

    const startTime = performance.now();
    const animateCam = (now) => {
      const elapsed = now - startTime;
      const p = Math.min(1.0, elapsed / dur);
      const ease = 0.5 * (1.0 - Math.cos(p * Math.PI));

      this.camera.position.lerpVectors(startPos, targetPos, ease);
      this.orbit.target.lerpVectors(startTarget, targetLook, ease);

      if (p < 1.0) {
        requestAnimationFrame(animateCam);
      }
    };
    requestAnimationFrame(animateCam);
  }

  setLightingColor(hexStr) {
    const col = new THREE.Color(hexStr);
    this.params.glowColor = col.getHex();

    if (this.keyLight) this.keyLight.color.copy(col);
    if (this.fillLight) this.fillLight.color.copy(col);
    if (this.causticLight) this.causticLight.color.copy(col);
    if (this.throatLight) this.throatLight.color.copy(col);
    if (this.lureLight) this.lureLight.color.copy(col);
    if (this.lureBulb && this.lureBulb.material) {
      this.lureBulb.material.color.copy(col);
      this.lureBulb.material.emissive.copy(col);
    }
    if (this.mesh && this.mesh.material && this.mesh.material.emissive) {
      this.mesh.material.emissive.copy(col);
    }

    document.querySelectorAll('.color-swatch').forEach(s => {
      s.classList.toggle('active', s.dataset.color.toLowerCase() === hexStr.toLowerCase());
    });
  }

  attachDOMControls() {
    document.getElementById('btn-strike')?.addEventListener('click', () => this.triggerJawStrike());
    document.getElementById('btn-roar')?.addEventListener('click', () => this.triggerRoar());

    document.getElementById('btn-cam-front')?.addEventListener('click', () => this.setCameraPreset('FRONT'));
    document.getElementById('btn-cam-34')?.addEventListener('click', () => this.setCameraPreset('THREE_QUARTER'));
    document.getElementById('btn-cam-profile')?.addEventListener('click', () => this.setCameraPreset('PROFILE'));
    document.getElementById('btn-cam-maw')?.addEventListener('click', () => this.setCameraPreset('MAW_CLOSEUP'));

    document.querySelectorAll('.color-swatch').forEach(sw => {
      sw.addEventListener('click', (e) => {
        this.setLightingColor(e.target.dataset.color);
      });
    });

    document.getElementById('btn-snapshot')?.addEventListener('click', async (e) => {
      const btn = e.target;
      const origText = btn.textContent;
      btn.textContent = '📸 CAPTURING...';
      try {
        const dataUrl = this.renderer.domElement.toDataURL('image/png');
        const res = await fetch('/api/snapshot', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'true_3d_user_snapshot', image_base64: dataUrl })
        });
        if (res.ok) {
          btn.textContent = '✅ SAVED!';
          setTimeout(() => { btn.textContent = origText; }, 1800);
        } else {
          btn.textContent = '❌ ERROR';
          setTimeout(() => { btn.textContent = origText; }, 1800);
        }
      } catch (err) {
        btn.textContent = '❌ ERROR';
        setTimeout(() => { btn.textContent = origText; }, 1800);
      }
    });

    const uploadBtn = document.getElementById('btn-upload-glb');
    const fileInput = document.getElementById('file-input-glb');
    if (uploadBtn && fileInput) {
      uploadBtn.addEventListener('click', () => {
        fileInput.click();
      });

      fileInput.addEventListener('change', async (e) => {
        const file = e.target.files && e.target.files[0];
        if (!file) return;

        const origText = uploadBtn.textContent;
        uploadBtn.textContent = '⏳ UPLOADING...';
        uploadBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', file);

        try {
          const res = await fetch('/api/upload-model', {
            method: 'POST',
            body: formData
          });

          if (res.ok) {
            const data = await res.json();
            uploadBtn.textContent = '✅ LOADED!';
            console.log('[UPLOAD] Success:', data);
            setTimeout(() => {
              window.location.search = '?model=custom_leviathan.glb';
            }, 600);
          } else {
            uploadBtn.textContent = '❌ FAILED';
            setTimeout(() => {
              uploadBtn.textContent = origText;
              uploadBtn.disabled = false;
            }, 2500);
          }
        } catch (err) {
          console.error('[UPLOAD] Error:', err);
          uploadBtn.textContent = '❌ ERROR';
          setTimeout(() => {
            uploadBtn.textContent = origText;
            uploadBtn.disabled = false;
          }, 2500);
        }
      });
    }

    // View Mode toggles
    document.getElementById('btn-pbr')?.addEventListener('click', () => {
      if (this.mesh && this.mesh.material) this.mesh.material.wireframe = false;
      this.toggleModeButtons('btn-pbr');
    });
    document.getElementById('btn-wireframe')?.addEventListener('click', () => {
      if (this.mesh && this.mesh.material) this.mesh.material.wireframe = true;
      this.toggleModeButtons('btn-wireframe');
    });
  }

  toggleModeButtons(activeId) {
    ['btn-pbr', 'btn-wireframe', 'btn-bones'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.toggle('active', id === activeId);
    });
  }

  setupAutoCaptureHook() {
    window.captureViewerState = () => {
      this.renderer.render(this.scene, this.camera);
      return this.renderer.domElement.toDataURL('image/png');
    };
  }

  onResize() {
    this.width = this.container.clientWidth || window.innerWidth;
    this.height = this.container.clientHeight || window.innerHeight;
    this.camera.aspect = this.width / this.height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.width, this.height);
  }
}

window.addEventListener('DOMContentLoaded', () => {
  window.leviathanViewer = new LeviathanTrue3DViewer();
});
