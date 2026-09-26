// ============================================================================
// Articulated 3D Procedural Creature Rig (Three.js)
// Reusable template for Nolimit-style slot mascots / deep-sea predators
// ============================================================================

class CreatureRig3D {
  constructor(scene, options = {}) {
    this.scene = scene;
    this.options = Object.assign({
      segments: 14,
      scale: 1.0,
      primaryColor: 0x051a2e,
      glowColor: 0x00f0ff,
      fangColor: 0xe2e8f0,
      baseZ: -200,
    }, options);

    this.root = new THREE.Group();
    this.scene.add(this.root);

    this.bodySegments = [];
    this.time = 0;
    this.state = 'IDLE'; // IDLE | HUNTING | STRIKING | ROARING
    this.targetPos = new THREE.Vector3(0, 0, this.options.baseZ);
    this.jawAngle = 0;
    this.targetJawAngle = 0;

    this.initSkeleton();
  }

  initSkeleton() {
    const opt = this.options;

    // 1. Head Cranium & Brow Armor
    this.head = new THREE.Group();
    this.root.add(this.head);

    const skullMat = new THREE.MeshStandardMaterial({
      color: opt.primaryColor,
      roughness: 0.35,
      metalness: 0.45,
      flatShading: true,
    });

    const skullGeom = new THREE.ConeGeometry(38, 75, 7);
    skullGeom.rotateX(Math.PI / 2);
    this.skullMesh = new THREE.Mesh(skullGeom, skullMat);
    this.head.add(this.skullMesh);

    // 2. Unhinging Lower Jaw (pivots down & forward)
    this.jawPivot = new THREE.Group();
    this.jawPivot.position.set(0, -14, -10);
    this.head.add(this.jawPivot);

    const jawGeom = new THREE.ConeGeometry(32, 65, 5);
    jawGeom.rotateX(Math.PI / 2);
    jawGeom.scale(1, 0.4, 1);
    this.jawMesh = new THREE.Mesh(jawGeom, skullMat);
    this.jawMesh.position.set(0, -4, 25);
    this.jawPivot.add(this.jawMesh);

    // 3. Razor Fangs (Conical double rows)
    const fangMat = new THREE.MeshStandardMaterial({
      color: opt.fangColor,
      roughness: 0.1,
      metalness: 0.6,
    });
    for (let side = -1; side <= 1; side += 2) {
      for (let f = 0; f < 5; f++) {
        // Upper Teeth
        const toothUp = new THREE.Mesh(new THREE.ConeGeometry(2.5, 12, 4), fangMat);
        toothUp.rotation.x = Math.PI;
        toothUp.position.set(side * (12 - f * 2), -10, 10 + f * 10);
        this.head.add(toothUp);

        // Lower Teeth
        const toothDown = new THREE.Mesh(new THREE.ConeGeometry(2.5, 12, 4), fangMat);
        toothDown.position.set(side * (10 - f * 1.8), 2, f * 9);
        this.jawPivot.add(toothDown);
      }
    }

    // 4. Bioluminescent Predatory Eyes
    const eyeMat = new THREE.MeshBasicMaterial({ color: opt.glowColor });
    for (let side of [-1, 1]) {
      const eye = new THREE.Mesh(new THREE.SphereGeometry(4.5, 8, 8), eyeMat);
      eye.position.set(side * 20, 8, 12);
      this.head.add(eye);
    }

    // 5. Angler Lure Stalk & Emissive Orb
    this.lureStalk = new THREE.Group();
    this.lureStalk.position.set(0, 18, 0);
    this.head.add(this.lureStalk);

    const lureGeom = new THREE.CylinderGeometry(1.5, 3, 40, 6);
    lureGeom.rotateX(Math.PI / 4);
    const stalkMesh = new THREE.Mesh(lureGeom, skullMat);
    stalkMesh.position.set(0, 15, 15);
    this.lureStalk.add(stalkMesh);

    this.lureOrb = new THREE.Mesh(new THREE.SphereGeometry(6, 12, 12), eyeMat);
    this.lureOrb.position.set(0, 28, 30);
    this.lureStalk.add(this.lureOrb);

    // Dynamic light cast by lure
    this.lureLight = new THREE.PointLight(opt.glowColor, 2.5, 350);
    this.lureLight.position.copy(this.lureOrb.position);
    this.lureStalk.add(this.lureLight);

    // 6. Articulated Spinal Vertebrae Chain
    let parentNode = this.head;
    for (let i = 0; i < opt.segments; i++) {
      const radius = Math.sin((i / opt.segments) * Math.PI) * 28 + 8;
      const segGroup = new THREE.Group();
      segGroup.position.set(0, 0, -28);
      parentNode.add(segGroup);

      const segGeom = new THREE.CylinderGeometry(radius * 0.8, radius, 28, 7);
      segGeom.rotateX(Math.PI / 2);
      const segMesh = new THREE.Mesh(segGeom, skullMat);
      segGroup.add(segMesh);

      // Dorsal Fin Spines
      if (i % 2 === 0) {
        const finGeom = new THREE.ConeGeometry(radius * 0.6, 22, 3);
        const finMesh = new THREE.Mesh(finGeom, eyeMat);
        finMesh.position.set(0, radius + 8, 0);
        segGroup.add(finMesh);
      }

      this.bodySegments.push(segGroup);
      parentNode = segGroup;
    }

    this.head.position.set(0, 100, opt.baseZ);
  }

  update(dt = 0.016) {
    this.time += dt;

    // Jaw interpolation
    this.jawAngle += (this.targetJawAngle - this.jawAngle) * 0.15;
    this.jawPivot.rotation.x = this.jawAngle;

    if (this.state === 'IDLE') {
      // Natural swimming sinusoidal undulation
      const sway = Math.sin(this.time * 1.5) * 45;
      const bob = Math.cos(this.time * 1.2) * 20;
      this.head.position.x += ((sway) - this.head.position.x) * 0.04;
      this.head.position.y += ((100 + bob) - this.head.position.y) * 0.04;
      this.head.position.z += (this.options.baseZ - this.head.position.z) * 0.04;

      // Trailing spinal ripple
      for (let i = 0; i < this.bodySegments.length; i++) {
        const seg = this.bodySegments[i];
        seg.rotation.y = Math.sin(this.time * 2.5 - i * 0.45) * 0.22;
        seg.rotation.x = Math.cos(this.time * 2.0 - i * 0.35) * 0.08;
      }

      // Breathing throat dilation
      const breath = 1.0 + Math.sin(this.time * 3.0) * 0.04;
      this.skullMesh.scale.set(breath, breath, 1);

      // Lure sway
      this.lureStalk.rotation.x = Math.sin(this.time * 2.0) * 0.15;
      this.lureLight.intensity = 2.0 + Math.sin(this.time * 5.0) * 0.8;
    }
  }

  async strikeAt(targetX, targetY, targetZ = 30) {
    this.state = 'STRIKING';
    const startX = this.head.position.x;
    const startY = this.head.position.y;
    const startZ = this.head.position.z;

    // 1. Unhinge Jaws & Lunge Forward
    this.targetJawAngle = 1.25; // 72 degrees open
    const lungeDuration = 280;
    const startTime = performance.now();

    await new Promise(resolve => {
      const step = now => {
        const progress = Math.min(1, (now - startTime) / lungeDuration);
        const ease = Math.pow(progress, 2.5); // accelerating strike
        this.head.position.x = startX + (targetX - startX) * ease;
        this.head.position.y = startY + (targetY - startY) * ease;
        this.head.position.z = startZ + (targetZ - startZ) * ease;
        if (progress < 1) requestAnimationFrame(step);
        else resolve();
      };
      requestAnimationFrame(step);
    });

    // 2. Clamp Jaws Shut (Violent Snap)
    this.targetJawAngle = 0.0;
    await new Promise(r => setTimeout(r, 90));

    // 3. Recoil back to deep trench
    const recoilStart = performance.now();
    const recoilDuration = 450;
    await new Promise(resolve => {
      const step = now => {
        const progress = Math.min(1, (now - recoilStart) / recoilDuration);
        const ease = 1 - Math.pow(1 - progress, 3); // smooth decelerate
        this.head.position.x = targetX + (0 - targetX) * ease;
        this.head.position.y = targetY + (100 - targetY) * ease;
        this.head.position.z = targetZ + (this.options.baseZ - targetZ) * ease;
        if (progress < 1) requestAnimationFrame(step);
        else resolve();
      };
      requestAnimationFrame(step);
    });

    this.state = 'IDLE';
  }

  setAtmosphere(colorHex) {
    this.lureLight.color.setHex(colorHex);
  }
}
