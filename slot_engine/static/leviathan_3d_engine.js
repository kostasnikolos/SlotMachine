/**
 * Pragmatic-Style Shark Engine
 * -----------------
 * The Shark character floats menacingly on the right side of the screen.
 * When he helps the player, he dives deep down before a Wild appears.
 */

class Leviathan3DEngine {
  constructor(containerId = 'leviathan-3d-canvas-container') {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(44, this.container.clientWidth / this.container.clientHeight, 1, 2000);
    this.camera.position.set(0, 0, 310);

    this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'high-performance' });
    this.renderer.setSize(this.container.clientWidth || 400, this.container.clientHeight || 400);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.outputEncoding = THREE.sRGBEncoding;
    this.renderer.setClearColor(0x000000, 0); 
    this.container.appendChild(this.renderer.domElement);

    this.creatureRoot = new THREE.Group();
    this.scene.add(this.creatureRoot);

    this.isActionActive = false;
    this.isLoaded = false;

    // Pragmatic right-side positioning
    this.dormantX = 170;
    this.dormantY = -10;
    this.dormantZ = -80;
    this.creatureRoot.position.set(this.dormantX, this.dormantY, this.dormantZ);
    // Angle slightly towards the reels
    this.creatureRoot.rotation.y = -0.5;
    this.creatureRoot.rotation.x = 0.1;

    this.setupLighting();
    this.loadLeviathan();
    
    this.clock = new THREE.Clock();
    this.render();

    window.addEventListener('resize', () => {
      this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    });
  }

  setupLighting() {
    this.ambientLight = new THREE.AmbientLight(0x0a1526, 2.5);
    this.scene.add(this.ambientLight);

    this.keyLight = new THREE.DirectionalLight(0x00f0ff, 3.5);
    this.keyLight.position.set(90, 160, 200);
    this.scene.add(this.keyLight);

    this.rimLight = new THREE.DirectionalLight(0xff0044, 4.0);
    this.rimLight.position.set(-140, -80, -120);
    this.scene.add(this.rimLight);
  }

  loadLeviathan() {
    const loader = new THREE.GLTFLoader();
    console.log('[3D Engine] Loading Shark mesh...');

    loader.load('/static/assets/models/shark.glb', (gltf) => {
      this.model = gltf.scene;

      const box = new THREE.Box3().setFromObject(this.model);
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      // Scale down so he fits well on the right
      const fitScale = 140.0 / (maxDim || 1.0);
      this.model.scale.set(fitScale, fitScale, fitScale);

      box.setFromObject(this.model);
      const center = box.getCenter(new THREE.Vector3());
      this.model.position.sub(center);

      this.model.traverse((child) => {
        if (child.isMesh) {
          child.material.envMapIntensity = 1.5;
          child.material.needsUpdate = true;
        }
      });

      this.creatureRoot.add(this.model);

      if (gltf.animations && gltf.animations.length > 0) {
        this.mixer = new THREE.AnimationMixer(this.model);
        const action = this.mixer.clipAction(gltf.animations[0]);
        action.play();
      }

      this.isLoaded = true;
      console.log('[3D Engine] Shark loaded and swimming on the right!');

      const devourBtn = document.getElementById('btn-test-devour');
      if (devourBtn) {
        devourBtn.innerHTML = '🦈 SHARK DIVE (READY)';
      }
      const creatureVal = document.getElementById('sonar-creature-val');
      if (creatureVal) {
        creatureVal.textContent = 'PATROLLING TRENCH';
      }

      if (this.pendingDevour) {
        const fn = this.pendingDevour;
        this.pendingDevour = null;
        fn();
      }
    });
  }

  riseAndDevour(targetCells = [], onDevourCallback = null) {
    if (!this.isLoaded || !this.model) {
      console.log('[3D Engine] 3D mesh is still loading, queuing dive...');
      this.pendingDevour = () => this.riseAndDevour(targetCells, onDevourCallback);
      return;
    }

    if (this.isActionActive) return;
    this.isActionActive = true;
    
    const creatureVal = document.getElementById('sonar-creature-val');
    if (creatureVal) {
      creatureVal.textContent = 'SHARK DIVE!';
      creatureVal.style.color = '#ff2a4b';
    }

    if (window.audio) {
      window.audio.playCreatureRoar(); 
      // Replace with sinking sound later if needed
    }

    const duration = 2.0; 
    const startTime = this.clock.getElapsedTime();
    const startY = this.creatureRoot.position.y;
    const startXRot = this.creatureRoot.rotation.x;

    const animateDive = () => {
      const now = this.clock.getElapsedTime();
      let t = (now - startTime) / duration;

      if (t >= 1.0) {
        // Reset and finish
        this.creatureRoot.position.y = this.dormantY;
        this.creatureRoot.rotation.x = this.creatureRoot.rotation.x;
        this.isActionActive = false;
        if (creatureVal) {
          creatureVal.textContent = 'PATROLLING TRENCH';
          creatureVal.style.color = '#00f0ff';
        }
        return;
      }

      // 0.0 to 0.3: Shark dives DOWN fast
      if (t < 0.3) {
        let diveT = t / 0.3;
        this.creatureRoot.position.y = THREE.MathUtils.lerp(startY, -400, diveT * diveT);
        this.creatureRoot.rotation.x = THREE.MathUtils.lerp(startXRot, 1.5, diveT);
      } 
      // 0.3: Fire the callback! (The Wild appears!)
      else if (t >= 0.3 && t < 0.32) {
        if (onDevourCallback && !this.callbackFired) {
            onDevourCallback();
            this.callbackFired = true;
        }
      }
      // 0.3 to 1.0: Shark slowly swims back up to position
      else {
        let riseT = (t - 0.3) / 0.7;
        let easeOut = 1 - Math.pow(1 - riseT, 3);
        this.creatureRoot.position.y = THREE.MathUtils.lerp(-400, this.dormantY, easeOut);
        this.creatureRoot.rotation.x = THREE.MathUtils.lerp(1.5, startXRot, easeOut);
      }

      requestAnimationFrame(animateDive);
    };

    this.callbackFired = false;
    animateDive();
  }

  render() {
    requestAnimationFrame(() => this.render());
    const delta = this.clock.getDelta();
    const time = this.clock.getElapsedTime();

    if (this.mixer) {
      this.mixer.update(delta);
    }

    if (!this.isActionActive && this.isLoaded) {
      // Gentle bobbing and swimming in idle
      this.creatureRoot.position.y = this.dormantY + Math.sin(time * 1.5) * 8;
      this.creatureRoot.position.x = this.dormantX + Math.sin(time * 0.8) * 4;
      this.creatureRoot.rotation.x = 0.1 + Math.sin(time * 2.0) * 0.05;
      this.creatureRoot.rotation.z = Math.sin(time * 1.2) * 0.02;
    }

    this.renderer.render(this.scene, this.camera);
  }

  setDepthLighting(level) {
    if (!this.ambientLight || !this.keyLight || !this.rimLight) return;
    const depthColors = [
      { a: 0x0a1526, k: 0x00f0ff, r: 0xff0044 },
      { a: 0x081020, k: 0x00d0ff, r: 0xff0044 },
      { a: 0x060c18, k: 0x00a0ff, r: 0xcc0033 },
      { a: 0x040810, k: 0x0070cc, r: 0xaa0022 },
      { a: 0x020408, k: 0x004099, r: 0x880011 },
      { a: 0x1a0505, k: 0xff2a4b, r: 0xff8800 }
    ];
    const colors = depthColors[Math.min(level, 5)];
    this.ambientLight.color.setHex(colors.a);
    this.keyLight.color.setHex(colors.k);
    this.rimLight.color.setHex(colors.r);
    
    if (level >= 5) {
      this.keyLight.intensity = 5.0;
      this.rimLight.intensity = 5.0;
    } else {
      this.keyLight.intensity = 3.5;
      this.rimLight.intensity = 4.0;
    }
  }
}

if(typeof window !== 'undefined') {
  window.Leviathan3DEngine = Leviathan3DEngine;
}
