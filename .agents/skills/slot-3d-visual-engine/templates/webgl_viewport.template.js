// ============================================================================
// WebGL 3D Slot Viewport Engine (Three.js)
// Reusable template for high-performance 3D slot reels & physics
// ============================================================================

class WebGLSlotViewport {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.options = Object.assign({
      rows: 5,
      cols: 5,
      cellSize: 84,
      gap: 8,
      fov: 48,
    }, options);

    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.FogExp2(0x020a14, 0.0022);

    this.camera = new THREE.PerspectiveCamera(
      this.options.fov,
      this.canvas.clientWidth / this.canvas.clientHeight,
      1,
      2000
    );
    this.camera.position.set(0, 0, 480);

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance',
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight, false);

    this.initLighting();
    this.initReelsGrid();

    window.addEventListener('resize', () => this.onResize());
    this.renderLoop();
  }

  initLighting() {
    this.ambientLight = new THREE.AmbientLight(0x1a365d, 1.2);
    this.scene.add(this.ambientLight);

    this.dirLight = new THREE.DirectionalLight(0x00f0ff, 1.0);
    this.dirLight.position.set(100, 200, 200);
    this.scene.add(this.dirLight);
  }

  initReelsGrid() {
    this.reelsRoot = new THREE.Group();
    this.scene.add(this.reelsRoot);

    this.cells = [];
    this.textureLoader = new THREE.TextureLoader();
    this.textureCache = {};

    this.rebuildGrid(this.options.rows, this.options.cols);
  }

  rebuildGrid(rows, cols) {
    // Clear existing
    while (this.reelsRoot.children.length > 0) {
      this.reelsRoot.remove(this.reelsRoot.children[0]);
    }
    this.cells = [];

    const cellW = this.options.cellSize;
    const cellH = this.options.cellSize;
    const gap = this.options.gap;

    const startX = -((cols - 1) * (cellW + gap)) / 2;
    const startY = ((rows - 1) * (cellH + gap)) / 2;

    for (let r = 0; r < rows; r++) {
      const row = [];
      for (let c = 0; c < cols; c++) {
        const x = startX + c * (cellW + gap);
        const y = startY - r * (cellH + gap);

        const tileGeom = new THREE.BoxGeometry(cellW, cellH, 8);
        const tileMat = new THREE.MeshStandardMaterial({
          color: 0x091e3a,
          roughness: 0.4,
          metalness: 0.3,
        });

        const tileMesh = new THREE.Mesh(tileGeom, tileMat);
        tileMesh.position.set(x, y, 0);
        this.reelsRoot.add(tileMesh);

        row.push({
          mesh: tileMesh,
          basePos: new THREE.Vector3(x, y, 0),
          targetPos: new THREE.Vector3(x, y, 0),
          scale: new THREE.Vector3(1, 1, 1),
          targetScale: new THREE.Vector3(1, 1, 1),
          vy: 0,
        });
      }
      this.cells.push(row);
    }
  }

  setCellSymbol(r, c, textureUrl) {
    if (!this.cells[r] || !this.cells[r][c]) return;
    const cell = this.cells[r][c];

    if (!this.textureCache[textureUrl]) {
      this.textureCache[textureUrl] = this.textureLoader.load(textureUrl);
    }

    const tex = this.textureCache[textureUrl];
    cell.mesh.material = new THREE.MeshStandardMaterial({
      map: tex,
      roughness: 0.3,
      metalness: 0.2,
    });
  }

  async dropCellWithBounce(r, c, dropDistance = 140, delay = 0) {
    const cell = this.cells[r][c];
    await new Promise(res => setTimeout(res, delay));

    cell.mesh.position.y = cell.basePos.y + dropDistance;
    cell.mesh.scale.set(0.9, 1.25, 1); // Velocity stretch

    const duration = 280;
    const start = performance.now();
    const startY = cell.mesh.position.y;
    const targetY = cell.basePos.y;

    return new Promise(resolve => {
      const step = now => {
        const p = Math.min(1, (now - start) / duration);
        // Bounce overshoot curve
        const ease = Math.sin(p * Math.PI * 0.5);
        cell.mesh.position.y = startY + (targetY - startY) * ease;

        if (p >= 1) {
          // Landing impact squash
          cell.mesh.position.y = targetY;
          cell.mesh.scale.set(1.15, 0.85, 1);
          setTimeout(() => cell.mesh.scale.set(1, 1, 1), 120);
          resolve();
        } else {
          requestAnimationFrame(step);
        }
      };
      requestAnimationFrame(step);
    });
  }

  async plungeAndEvaporate(r, c) {
    const cell = this.cells[r][c];
    if (!cell) return;

    // Plunge backward into Z depth
    const duration = 300;
    const start = performance.now();
    return new Promise(resolve => {
      const step = now => {
        const p = Math.min(1, (now - start) / duration);
        cell.mesh.position.z = -p * 180;
        cell.mesh.scale.set(1 - p * 0.7, 1 - p * 0.7, 1);
        if (cell.mesh.material.opacity !== undefined) {
          cell.mesh.material.transparent = true;
          cell.mesh.material.opacity = 1 - p;
        }
        if (p >= 1) resolve();
        else requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    });
  }

  onResize() {
    if (!this.canvas || !this.renderer) return;
    const width = this.canvas.clientWidth;
    const height = this.canvas.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
  }

  setAtmosphere(level) {
    const colors = [0x003366, 0x021d42, 0x030d29, 0x1f0438, 0x3d072b, 0x420008];
    const hex = colors[level] || colors[0];
    this.scene.fog.color.setHex(hex);
    this.ambientLight.color.setHex(hex);
  }

  renderLoop() {
    if (this.creature) this.creature.update();
    this.renderer.render(this.scene, this.camera);
    requestAnimationFrame(() => this.renderLoop());
  }
}
