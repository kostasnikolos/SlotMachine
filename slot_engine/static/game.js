// The Descent: Abyssal Leviathan - Game Client with Live Burns & Creature Lifelines

const SYMBOL_ASSETS = {
  HIGH_LEVIATHAN: '/static/assets/sym_high_leviathan.jpg',
  HIGH_SQUID: '/static/assets/sym_high_squid.jpg',
  HIGH_ANGLER: '/static/assets/sym_high_angler.jpg',
  HIGH_VIPER: '/static/assets/sym_high_viper.jpg',
  MID_HELMET: '/static/assets/sym_mid_helmet.jpg',
  MID_COMPASS: '/static/assets/sym_mid_compass.jpg',
  WILD_MAW: '/static/assets/sym_wild_maw.jpg',
  DEAD_SEDIMENT: '/static/assets/sym_dead_sediment.jpg',
  PEARL_TOKEN: '/static/assets/token_abyssal_pearl.jpg',
  // Low runes mapped to dark carved basalt glowing runestones
  LOW_10: '/static/assets/rune_10.svg',
  LOW_J:  '/static/assets/rune_j.svg',
  LOW_Q:  '/static/assets/rune_q.svg',
  LOW_K:  '/static/assets/rune_k.svg',
  LOW_A:  '/static/assets/rune_a.svg',
};

const LOW_SYMBOLS = {
  LOW_10: { label: '10', class: 'low-10' },
  LOW_J:  { label: 'J',  class: 'low-J' },
  LOW_Q:  { label: 'Q',  class: 'low-Q' },
  LOW_K:  { label: 'K',  class: 'low-K' },
  LOW_A:  { label: 'A',  class: 'low-A' },
};

const DEPTH_LEVELS = [
  { level: 0, name: 'Sunlight Zone', depth: '0m', thresh: 0, color: '#0088cc' },
  { level: 1, name: 'Twilight Zone', depth: '500m', thresh: 15, color: '#38bdf8' },
  { level: 2, name: 'Midnight Zone', depth: '2,000m', thresh: 35, color: '#818cf8' },
  { level: 3, name: 'The Abyssal Plains', depth: '5,000m', thresh: 65, color: '#a855f7' },
  { level: 4, name: 'Hadal Trench', depth: '8,000m', thresh: 160, color: '#ec4899' },
  { level: 5, name: 'The Leviathan Core', depth: '11,000m', thresh: 260, color: '#ff2a4b' },
];

const DEPTH_METADATA_CLIENT = {
  0: { creatureName: 'THE LURKER', creatureDesc: 'Dormant at surface. Reach Level 1 to awaken 1x1 Maw lifeline on cascade stalls.' },
  1: { creatureName: 'THE LURKER (1x1)', creatureDesc: 'Active! 10 purged. Devours weak adjacent runes and transmutes to Mid equipment (+1 spin).' },
  2: { creatureName: 'THE STALKER (2x1)', creatureDesc: 'Active! 10 & J purged. 2x1 Maw devours equipment and transmutes to high predators (+1 spin).' },
  3: { creatureName: 'THE MAELSTROM (2x2)', creatureDesc: 'Standard Bonus! 10, J, Q purged. 2x2 Wild with multipliers + Hydrothermal Vents online!' },
  4: { creatureName: 'THE KRAKEN (3x3)', creatureDesc: 'Active! 10, J, Q, K purged. 3x3 Eldritch Tentacles zone triggers xSplit on passing wins.' },
  5: { creatureName: 'LEVIATHAN AWAKENED', creatureDesc: 'Ultra Core! 100% Lows purged. 6x5 Grid (7,776 ways), doubled 2x global multiplier + Roaming Wild.' },
};

// Canvas Particle FX System for Live Burns, Water Plunge Ripples, Steam Evaporation, and Soul Flight
class ParticleFX {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas ? canvas.getContext('2d') : null;
    this.particles = [];
    if (this.canvas) {
      this.resize();
      window.addEventListener('resize', () => this.resize());
      this.loop();
    }
  }

  resize() {
    if (!this.canvas || !this.canvas.parentElement) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width;
    this.canvas.height = rect.height;
  }

  spawnBurnEmbers(x, y, count = 8) {
    if (!this.ctx) return;
    for (let i = 0; i < count; i++) {
      this.particles.push({
        type: 'ember',
        x: x + (Math.random() * 40 - 20),
        y: y + (Math.random() * 40 - 20),
        vx: (Math.random() - 0.5) * 2.2,
        vy: -Math.random() * 3.5 - 1.2,
        size: Math.random() * 3 + 2,
        life: 1.0,
        decay: Math.random() * 0.035 + 0.02,
        color: Math.random() > 0.4 ? '#ff5500' : '#ffaa00',
      });
    }
  }

  spawnWaterSplash(x, y, count = 12) {
    if (!this.ctx) return;
    // Concentric shockwave water ripples
    for (let r = 0; r < 2; r++) {
      this.particles.push({
        type: 'ripple',
        x,
        y,
        radius: 8 + r * 6,
        dr: 2.2 + r * 0.8,
        maxRadius: 55,
        alpha: 0.85,
        decay: 0.035,
        color: '#00f0ff',
        lineWidth: 2.5 - r * 0.5,
      });
    }

    // High speed cavitation droplets
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 2.0 + Math.random() * 4.5;
      this.particles.push({
        type: 'splash_droplet',
        x,
        y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 1.5,
        size: 1.5 + Math.random() * 2.5,
        alpha: 1.0,
        decay: 0.03 + Math.random() * 0.02,
        color: Math.random() > 0.3 ? '#38bdf8' : '#e0f2fe',
      });
    }
  }

  spawnSteamCloud(x, y, count = 10) {
    if (!this.ctx) return;
    for (let i = 0; i < count; i++) {
      this.particles.push({
        type: 'steam',
        x: x + (Math.random() * 30 - 15),
        y: y + (Math.random() * 20 - 10),
        vx: (Math.random() - 0.5) * 1.2,
        vy: -1.2 - Math.random() * 2.2,
        radius: 10 + Math.random() * 12,
        dr: 0.45 + Math.random() * 0.35,
        alpha: 0.75,
        decay: 0.025 + Math.random() * 0.015,
        time: Math.random() * Math.PI * 2,
      });
    }
  }

  spawnSoulFlight(startX, startY, endX, endY, count = 4, onHit = null) {
    if (!this.ctx) return;
    for (let i = 0; i < count; i++) {
      const delay = i * 70;
      setTimeout(() => {
        const ctrlX = (startX + endX) / 2 + (Math.random() - 0.5) * 100;
        const ctrlY = Math.min(startY, endY) - 60 - Math.random() * 50;
        this.particles.push({
          type: 'soul',
          t: 0,
          speed: 0.03 + Math.random() * 0.015,
          p0: { x: startX, y: startY },
          p1: { x: ctrlX, y: ctrlY },
          p2: { x: endX, y: endY },
          trail: [],
          size: 4.5,
          color: Math.random() > 0.3 ? '#00f0ff' : '#c084fc',
          onHit: i === count - 1 ? onHit : null,
        });
      }, delay);
    }
  }

  loop() {
    if (!this.ctx) return;
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];

      if (p.type === 'ember') {
        p.x += p.vx;
        p.y += p.vy;
        p.life -= p.decay;
        if (p.life <= 0) {
          this.particles.splice(i, 1);
          continue;
        }
        this.ctx.save();
        this.ctx.globalAlpha = p.life;
        this.ctx.fillStyle = p.color;
        this.ctx.shadowBlur = 8;
        this.ctx.shadowColor = p.color;
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.restore();
      } else if (p.type === 'ripple') {
        p.radius += p.dr;
        p.alpha -= p.decay;
        if (p.alpha <= 0 || p.radius >= p.maxRadius) {
          this.particles.splice(i, 1);
          continue;
        }
        this.ctx.save();
        this.ctx.globalAlpha = Math.max(0, p.alpha);
        this.ctx.strokeStyle = p.color;
        this.ctx.lineWidth = p.lineWidth;
        this.ctx.shadowBlur = 10;
        this.ctx.shadowColor = p.color;
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        this.ctx.stroke();
        this.ctx.restore();
      } else if (p.type === 'splash_droplet') {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.15; // gentle gravity/water drag
        p.alpha -= p.decay;
        if (p.alpha <= 0) {
          this.particles.splice(i, 1);
          continue;
        }
        this.ctx.save();
        this.ctx.globalAlpha = Math.max(0, p.alpha);
        this.ctx.fillStyle = p.color;
        this.ctx.shadowBlur = 6;
        this.ctx.shadowColor = p.color;
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.restore();
      } else if (p.type === 'steam') {
        p.time += 0.05;
        p.x += p.vx + Math.sin(p.time) * 0.4;
        p.y += p.vy;
        p.radius += p.dr;
        p.alpha -= p.decay;
        if (p.alpha <= 0) {
          this.particles.splice(i, 1);
          continue;
        }
        this.ctx.save();
        const grad = this.ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius);
        grad.addColorStop(0, `rgba(240, 249, 255, ${Math.max(0, p.alpha * 0.7)})`);
        grad.addColorStop(0.5, `rgba(125, 211, 252, ${Math.max(0, p.alpha * 0.4)})`);
        grad.addColorStop(1, 'rgba(14, 165, 233, 0)');
        this.ctx.fillStyle = grad;
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.restore();
      } else if (p.type === 'soul') {
        p.t += p.speed;
        const u = 1 - p.t;
        const curX = u * u * p.p0.x + 2 * u * p.t * p.p1.x + p.t * p.t * p.p2.x;
        const curY = u * u * p.p0.y + 2 * u * p.t * p.p1.y + p.t * p.t * p.p2.y;

        p.trail.push({ x: curX, y: curY });
        if (p.trail.length > 7) p.trail.shift();

        for (let j = 0; j < p.trail.length; j++) {
          const pt = p.trail[j];
          this.ctx.save();
          this.ctx.globalAlpha = (j / p.trail.length) * 0.7;
          this.ctx.fillStyle = p.color;
          this.ctx.beginPath();
          this.ctx.arc(pt.x, pt.y, p.size * (j / p.trail.length), 0, Math.PI * 2);
          this.ctx.fill();
          this.ctx.restore();
        }

        this.ctx.save();
        this.ctx.fillStyle = '#ffffff';
        this.ctx.shadowBlur = 12;
        this.ctx.shadowColor = p.color;
        this.ctx.beginPath();
        this.ctx.arc(curX, curY, p.size, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.restore();

        if (p.t >= 1.0) {
          if (p.onHit) p.onHit();
          this.particles.splice(i, 1);
        }
      }
    }

    requestAnimationFrame(() => this.loop());
  }
}

class SlotGame {
  constructor() {
    this.balance = 1000.00;
    this.bet = 1.00;
    this.currentWin = 0.00;
    this.isSpinning = false;
    this.turbo = false;
    this.xbetActive = false;
    this.rows = 5;
    this.cols = 5;
    this.gridState = [];
    this.currentDepthLevel = 0;

    // DOM Elements
    this.gameWrapper = document.getElementById('game-wrapper');
    this.gridEl = document.getElementById('slot-grid');
    this.ventsEl = document.getElementById('vents-row');
    this.depthFillEl = document.getElementById('pressure-fill');
    this.depthValEl = document.getElementById('depth-val');
    this.levelBadgeEl = document.getElementById('level-badge');
    this.balanceEl = document.getElementById('stat-balance');
    this.betEl = document.getElementById('stat-bet');
    this.winEl = document.getElementById('stat-win');
    this.spinBtn = document.getElementById('btn-spin');
    this.xbetBtn = document.getElementById('btn-xbet');
    this.bonusModal = document.getElementById('bonus-modal');

    // Free Spins & Bonus HUD
    this.freeSpinsHud = document.getElementById('free-spins-hud');
    this.hudModeTitle = document.getElementById('hud-mode-title');
    this.hudSpinCounter = document.getElementById('hud-spin-counter');
    this.hudMultiplier = document.getElementById('hud-multiplier');

    // Viewport & Creature Layer
    this.viewportFrame = document.getElementById('viewport-frame');
    this.gridCreatureLayer = document.getElementById('grid-creature-layer');

    // Level Up Splash
    this.levelUpSplash = document.getElementById('level-up-splash');
    this.splashLevelTitle = document.getElementById('splash-level-title');
    this.splashLevelName = document.getElementById('splash-level-name');
    this.splashRewards = document.getElementById('splash-rewards');

    // Cockpit Sidebars
    this.purgedCountEl = document.getElementById('purged-count');
    this.sidebarDepthEl = document.getElementById('sidebar-depth');
    this.sidebarTierEl = document.getElementById('sidebar-tier');

    // Sonar Dial Elements
    this.sonarProgressRing = document.getElementById('sonar-progress-ring');
    this.sonarLevelTitle = document.getElementById('sonar-level-title');
    this.sonarPtsNeeded = document.getElementById('sonar-pts-needed');
    this.sonarSub = document.getElementById('sonar-sub');
    this.sonarLifelineVal = document.getElementById('sonar-lifeline-val');
    this.sonarVentsVal = document.getElementById('sonar-vents-val');
    this.sonarWaysVal = document.getElementById('sonar-ways-val');
    this.sonarBoostVal = document.getElementById('sonar-boost-val');

    // Particle FX Canvas
    const canvas = document.getElementById('fx-canvas');
    this.fx = new ParticleFX(canvas);

    this.init();
  }

  init() {
    this.updateStats();
    this.renderInitialGrid();
    this.attachEventListeners();
    this.updatePurgedRunes([]);
    this.updateDepthProgress(0, 0, 0);

    // Initialize 3D WebGL Leviathan Engine
    try {
      if (typeof Leviathan3DEngine !== 'undefined') {
        this.leviathan3D = new Leviathan3DEngine('leviathan-3d-canvas-container');
        window.leviathan3D = this.leviathan3D;
      }
    } catch (e) {
      console.warn('[3D Engine] Init failed:', e);
    }

    // Unlock Web Audio context on mobile touch
    window.addEventListener('touchstart', () => audio.init(), { once: true });
    window.addEventListener('resize', () => {
      this.updateGridColumnSizes(this.cols);
    });
  }

  updateGridColumnSizes(cols = 5) {
    const isMobile = window.innerWidth <= 900;
    if (isMobile) {
      const maxGridWidth = Math.min(window.innerWidth * 0.92, 390);
      const gap = 5;
      const padding = 12;
      const cellSize = Math.max(46, Math.floor((maxGridWidth - padding - (cols - 1) * gap) / cols));
      this.gridEl.style.gridTemplateColumns = `repeat(${cols}, ${cellSize}px)`;
      this.gridEl.style.gridTemplateRows = `repeat(5, ${cellSize}px)`;
      if (this.ventsEl) {
        this.ventsEl.style.gridTemplateColumns = `repeat(${cols}, ${cellSize}px)`;
      }
    } else {
      this.gridEl.style.gridTemplateColumns = `repeat(${cols}, 84px)`;
      this.gridEl.style.gridTemplateRows = `repeat(5, 84px)`;
      if (this.ventsEl) {
        this.ventsEl.style.gridTemplateColumns = `repeat(${cols}, 84px)`;
      }
    }
  }

  updateStats() {
    this.balanceEl.textContent = '$' + this.balance.toFixed(2);
    const effectiveBet = this.xbetActive ? this.bet * 2 : this.bet;
    this.betEl.textContent = '$' + effectiveBet.toFixed(2);
    this.winEl.textContent = '$' + this.currentWin.toFixed(2);
  }

  renderInitialGrid() {
    this.gridEl.innerHTML = '';
    this.gridEl.className = 'grid-container';
    this.gridState = [];
    this.updateGridColumnSizes(5);

    const defaultSymbols = [
      ['HIGH_ANGLER', 'MID_HELMET', 'LOW_10', 'MID_COMPASS', 'HIGH_VIPER'],
      ['MID_COMPASS', 'HIGH_SQUID', 'LOW_J', 'HIGH_LEVIATHAN', 'LOW_Q'],
      ['HIGH_VIPER', 'LOW_K', 'WILD_MAW', 'LOW_A', 'MID_HELMET'],
      ['LOW_10', 'HIGH_ANGLER', 'LOW_J', 'HIGH_SQUID', 'LOW_K'],
      ['MID_HELMET', 'LOW_Q', 'HIGH_VIPER', 'MID_COMPASS', 'HIGH_ANGLER'],
    ];

    for (let r = 0; r < 5; r++) {
      const row = [];
      for (let c = 0; c < 5; c++) {
        const cell = document.createElement('div');
        cell.className = 'symbol-cell';
        cell.id = 'cell-' + r + '-' + c;
        
        const sym = defaultSymbols[r][c];
        cell.appendChild(this.createSymbolElement(sym));
        this.gridEl.appendChild(cell);
        row.push({ symbol: sym, cellEl: cell });
      }
      this.gridState.push(row);
    }
    
    if (window.webglEngine) {
      window.webglEngine.updateGrid(defaultSymbols);
    }
  }

  createSymbolElement(symType, hasPearl = false) {
    const wrap = document.createElement('div');
    wrap.style.width = '100%';
    wrap.style.height = '100%';
    wrap.style.position = 'relative';

    if (SYMBOL_ASSETS[symType]) {
      const img = document.createElement('img');
      img.src = SYMBOL_ASSETS[symType];
      img.alt = symType;
      img.style.opacity = '0';
      if (symType.startsWith('LOW_')) {
        img.className = 'rune-cell-img';
      }
      wrap.appendChild(img);
    } else if (LOW_SYMBOLS[symType]) {
      const img = document.createElement('img');
      img.src = `/static/assets/rune_${LOW_SYMBOLS[symType].label.toLowerCase()}.svg`;
      img.alt = symType;
      img.className = 'rune-cell-img';
      img.style.opacity = '0';
      wrap.appendChild(img);
    }

    if (hasPearl) {
      const pearl = document.createElement('div');
      pearl.className = 'pearl-overlay-icon';
      wrap.appendChild(pearl);
    }

    return wrap;
  }

  attachEventListeners() {
    this.spinBtn.addEventListener('click', () => {
      audio.init();
      this.triggerSpin();
    });

    this.xbetBtn.addEventListener('click', () => {
      this.xbetActive = !this.xbetActive;
      this.xbetBtn.classList.toggle('active', this.xbetActive);
      this.updateStats();
      if (this.xbetActive) {
        this.updatePurgedRunes(['LOW_10']);
        this.updateDepthProgress(1, 500, 15);
      } else {
        this.updatePurgedRunes([]);
        this.updateDepthProgress(0, 0, 0);
      }
    });

    document.getElementById('btn-bonus-open').addEventListener('click', () => {
      this.bonusModal.classList.add('active');
    });

    document.getElementById('btn-bonus-close').addEventListener('click', () => {
      this.bonusModal.classList.remove('active');
    });

    document.querySelectorAll('.bonus-option-card').forEach(card => {
      card.addEventListener('click', () => {
        const buyType = card.dataset.buy;
        this.bonusModal.classList.remove('active');
        audio.init();
        if (buyType === 'XBET_SONAR_2X') {
          this.xbetBtn.click();
        } else {
          this.triggerBonusBuy(buyType);
        }
      });
    });

    document.getElementById('btn-bet-plus').addEventListener('click', () => {
      if (this.bet < 50) this.bet = Math.min(50, this.bet + 1.0);
      this.updateStats();
    });
    document.getElementById('btn-bet-minus').addEventListener('click', () => {
      if (this.bet > 0.20) this.bet = Math.max(0.20, this.bet - 0.50);
      this.updateStats();
    });
    document.getElementById('btn-turbo').addEventListener('click', (e) => {
      this.turbo = !this.turbo;
      e.target.classList.toggle('active', this.turbo);
    });

    // 3D Leviathan Devour Demo Button
    document.getElementById('btn-test-devour')?.addEventListener('click', () => {
      audio.init();
      this.trigger3DDevourDemo();
    });

    // Spacebar shortcut to spin
    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space' && !this.isSpinning && !this.bonusModal.classList.contains('active')) {
        e.preventDefault();
        audio.init();
        this.triggerSpin();
      }
    });
  }

  trigger3DDevourDemo() {
    if (this.isSpinning) return;

    // Pick 3-4 target cells currently on the reels grid to devour
    const targetCells = [];
    const coords = [[1, 1], [1, 2], [2, 2], [3, 2], [2, 3]];
    coords.forEach(([r, c]) => {
      const el = document.getElementById(`cell-${r}-${c}`);
      if (el) targetCells.push(el);
    });

    if (this.leviathan3D) {
      this.leviathan3D.riseAndDevour(targetCells, () => {
        // Evaporate symbols into glowing steam clouds
        targetCells.forEach((cell, idx) => {
          setTimeout(() => {
            cell.classList.add('evaporating');
            if (this.fx) {
              const r = cell.getBoundingClientRect();
              const cr = this.fx.canvas.getBoundingClientRect();
              this.fx.spawnSteamCloud(r.left + r.width / 2 - cr.left, r.top + r.height / 2 - cr.top, 14);
            }
          }, idx * 60);
        });

        // After evaporation, transmute into high-paying WILD MAW symbols!
        setTimeout(() => {
          targetCells.forEach(cell => {
            cell.classList.remove('evaporating');
            cell.innerHTML = '';
            cell.appendChild(this.createSymbolElement('WILD_MAW'));
            cell.classList.add('wild-pulse');
          });
          audio.playWin();
          this.currentWin = this.bet * 15.0;
          this.updateStats();
        }, 650);
      });
    } else {
      console.warn('[SlotGame] 3D Leviathan Engine not initialized');
    }
  }

  async triggerSpin() {
    if (this.isSpinning) return;
    const cost = this.xbetActive ? this.bet * 2 : this.bet;
    if (this.balance < cost) {
      alert('Insufficient balance!');
      return;
    }

    this.balance -= cost;
    this.currentWin = 0;
    this.updateStats();
    this.isSpinning = true;
    this.spinBtn.disabled = true;

    audio.playSpin();
    if (window.oceanAmbient) window.oceanAmbient.scatterFish();

    try {
      const res = await fetch('/api/slot/spin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bet: this.bet,
          feature_buy: this.xbetActive ? 'XBET_SONAR_2X' : 'NONE'
        })
      });
      const data = await res.json();
      await this.playbackTimeline(data);
    } catch (err) {
      console.error('Spin error:', err);
    } finally {
      this.isSpinning = false;
      this.spinBtn.disabled = false;
      this.updateStats();
    }
  }

  async triggerBonusBuy(buyType) {
    if (this.isSpinning) return;
    let costMult = 100;
    if (buyType === 'ULTRA_BONUS_350X') costMult = 350;
    if (buyType === 'MYSTERY_BUY_200X') costMult = 200;

    const totalCost = this.bet * costMult;
    if (this.balance < totalCost) {
      alert('Insufficient balance for ' + buyType + '! Required: $' + totalCost.toFixed(2));
      return;
    }

    this.balance -= totalCost;
    this.currentWin = 0;
    this.updateStats();
    this.isSpinning = true;
    this.spinBtn.disabled = true;

    try {
      const res = await fetch('/api/slot/buy-bonus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bet: this.bet,
          feature_type: buyType
        })
      });
      const data = await res.json();
      await this.playbackTimeline(data);
    } catch (err) {
      console.error('Bonus buy error:', err);
    } finally {
      this.isSpinning = false;
      this.spinBtn.disabled = false;
      this.updateStats();
    }
  }

  async playbackTimeline(outcome) {
    const delay = ms => new Promise(r => setTimeout(r, ms));
    const speed = this.turbo ? 0.35 : 1.0;
    let totalSpins = 0;
    let currentSpinNum = 1;

    for (const ev of outcome.events) {
      switch (ev.event_type) {
        case 'FEATURE_ACTIVATED':
          if (this.freeSpinsHud) {
            this.freeSpinsHud.style.display = 'flex';
            let title = 'ABYSSAL EXPEDITION';
            if (ev.data.type === 'STANDARD_BONUS_AWARDED') title = 'ABYSSAL DESCENT (100X)';
            if (ev.data.type === 'ULTRA_BONUS_AWARDED') title = 'LEVIATHAN AWAKENING (350X)';
            if (ev.data.type === 'MYSTERY_STANDARD_AWARDED') title = 'MYSTERY: ABYSSAL DESCENT';
            if (ev.data.type === 'MYSTERY_ULTRA_AWARDED') title = 'MYSTERY: LEVIATHAN ULTRA!';
            this.hudModeTitle.textContent = title;
            totalSpins = ev.data.spins || 6;
            this.hudSpinCounter.textContent = 'BANKED: ' + totalSpins + ' FREE SPINS';
          }
          audio.playSonarPing();
          await delay(600 * speed);
          break;

        case 'SPIN_STARTED':
          this.currentDepthLevel = ev.data.depth_level;
          audio.playMeterAbsorb();
            this.updateDepthProgress(ev.data.depth_level, ev.data.depth_meters, ev.data.accumulated_points);
          this.updatePurgedRunes(ev.data.purged_symbols || []);

          if (ev.data.is_free_spin) {
            if (this.freeSpinsHud) {
              this.freeSpinsHud.style.display = 'flex';
              const remaining = ev.data.spins_remaining;
              this.hudSpinCounter.textContent = 'FREE SPIN ' + currentSpinNum + ' (' + remaining + ' LEFT)';
              currentSpinNum++;
              if (this.hudMultiplier) {
                this.hudMultiplier.textContent = (ev.data.spin_multiplier || 1) + 'X BOOST';
              }
            }
          }
          break;

        case 'GRID_EXPANSION_6X5':
          this.gridEl.classList.add('grid-6x5');
          if (this.ventsEl) {
            this.ventsEl.classList.add('grid-6x5');
            const v5 = document.getElementById('vent-5');
            if (v5) v5.style.display = 'flex';
          }
          this.cols = 6;
          audio.playCreatureRoar();
          if (window.oceanAmbient) window.oceanAmbient.scatterFish();
          await delay(450 * speed);
          break;

        case 'GRID_DROP':
          await this.animateGridDrop(ev.data, speed);
          break;

        case 'VENTS_ERUPTED':
          this.showVents(ev.data.active_vents);
          audio.playVentEruption();
          await delay(350 * speed);
          break;

        case 'WIN_EVALUATION':
          await this.highlightWins(ev.data.wins, ev.data.cumulative_payout, speed);
          this.currentWin = ev.data.cumulative_payout;
          this.updateStats();
          if (ev.data.accumulated_points !== undefined) {
            audio.playMeterAbsorb();
            this.updateDepthProgress(ev.data.depth_level, ev.data.depth_meters, ev.data.accumulated_points);
          }
          await delay(350 * speed);
          break;

        case 'LEVEL_UP':
          audio.playLevelUp();
          audio.playSonarPing();
          this.showLevelUpSplash(ev.data.new_level, ev.data.name, ev.data.depth, ev.data.spins_added);
          this.updateDepthProgress(ev.data.new_level, ev.data.depth, ev.data.accumulated_points || 0);
          if (ev.data.purged && ev.data.purged.length > 0) {
            this.updatePurgedRunes(ev.data.purged);
          }
          await delay(1200 * speed);
          break;

        case 'CASCADE_DROP':
          audio.playCascade();
          await this.animateCascade(ev.data, speed);
          this.clearVents();
          break;

        case 'CREATURE_LIFELINE_STRIKE':
          await this.animateCreatureStrike(ev.data, speed);
          break;

        case 'PEARLS_COLLECTED':
          audio.playSoulAbsorb();
          await delay(250 * speed);
          break;

        case 'MAX_WIN_CAP_TRIGGERED':
        case 'SPIN_COMPLETE':
          this.balance += outcome.total_payout;
          this.currentWin = outcome.total_payout;
          this.updateStats();
          if (outcome.payout_multiplier >= 20.0) {
            this.showBigWin(outcome.total_payout);
          }
          const resetDelay = (outcome.feature_type && outcome.feature_type !== 'NONE') ? 3500 : 1200;
          setTimeout(() => {
            if (this.freeSpinsHud) this.freeSpinsHud.style.display = 'none';
            if (this.cols === 6) {
              this.gridEl.classList.remove('grid-6x5');
              if (this.ventsEl) {
                this.ventsEl.classList.remove('grid-6x5');
                const v5 = document.getElementById('vent-5');
                if (v5) v5.style.display = 'none';
              }
              this.cols = 5;
            }
            if (this.xbetActive) {
              this.updatePurgedRunes(['LOW_10']);
              this.updateDepthProgress(1, 500, 15);
            } else {
              this.updatePurgedRunes([]);
              this.updateDepthProgress(0, 0, 0);
            }
          }, resetDelay);
          break;
      }
    }
  }

  async animateGridDrop(gridData, speed) {
    const rows = gridData.rows;
    const cols = gridData.cols;
    this.gridEl.innerHTML = '';
    this.updateGridColumnSizes(cols);

    const pearlSet = new Set((gridData.pearl_tokens || []).map(pt => pt[0] + ',' + pt[1]));

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const sym = gridData.grid[r][c];
        const hasP = pearlSet.has(r + ',' + c);
        const cell = document.createElement('div');
        cell.className = 'symbol-cell';
        cell.id = 'cell-' + r + '-' + c;
        cell.appendChild(this.createSymbolElement(sym, hasP));
        this.gridEl.appendChild(cell);

        cell.style.opacity = '0';
        cell.style.transform = 'translateY(-40px)';
        setTimeout(() => {
          cell.style.transition = 'all ' + (0.25 * speed) + 's cubic-bezier(0.34, 1.56, 0.64, 1)';
          cell.style.opacity = '1';
          cell.style.transform = 'translateY(0)';
          audio.playReelStop();
        }, (c * 45 + r * 15) * speed);
      }
    }
    
    if (window.webglEngine && gridData.grid) {
      window.webglEngine.updateGrid(gridData.grid);
      if (this.isSpinning) {
        window.webglEngine.startSpin();
      } else {
        window.webglEngine.startCascade();
      }
    }

    await new Promise(r => setTimeout(r, (cols * 45 + 160) * speed));
  }

  async highlightWins(wins, cumulativePayout, speed) {
    audio.playSoulBurn();
    audio.playWin();

    const canvasRect = this.fx.canvas ? this.fx.canvas.getBoundingClientRect() : { left: 0, top: 0 };
    const sonarDial = document.querySelector('.sonar-radar-container');
    const gaugeRect = sonarDial ? sonarDial.getBoundingClientRect() : { left: 0, top: 0, width: 0, height: 0 };
    const endX = gaugeRect.left + gaugeRect.width / 2 - canvasRect.left;
    const endY = gaugeRect.top + gaugeRect.height / 2 - canvasRect.top;

    for (const win of wins) {
      for (const coord of win.coords) {
        const cell = document.getElementById('cell-' + coord[0] + '-' + coord[1]);
        if (cell) {
          cell.classList.add('burning');

          // Floating Cash Tag
          const cashTag = document.createElement('div');
          cashTag.className = 'win-float-tag';
          cashTag.textContent = '+$' + win.payout.toFixed(2);
          cell.appendChild(cashTag);

          // Floating Soul Points Tag
          const ptsTag = document.createElement('div');
          ptsTag.className = 'win-float-tag pts';
          ptsTag.textContent = '+PTS';
          cell.appendChild(ptsTag);

          // Spawn Burn Embers on Canvas
          const cellRect = cell.getBoundingClientRect();
          const startX = cellRect.left + cellRect.width / 2 - canvasRect.left;
          const startY = cellRect.top + cellRect.height / 2 - canvasRect.top;
          this.fx.spawnBurnEmbers(startX, startY, 8);

          // Soul Energy Flight Arc into Circular Sonar Dial
          this.fx.spawnSoulFlight(startX, startY, endX, endY, 4, () => {
            audio.playSoulAbsorb();
            if (this.sonarProgressRing) {
              this.sonarProgressRing.style.filter = 'drop-shadow(0 0 16px #00f0ff)';
              setTimeout(() => {
                if (this.sonarProgressRing) this.sonarProgressRing.style.filter = 'drop-shadow(0 0 8px rgba(0, 240, 255, 0.6))';
              }, 140);
            }
          });
        }
      }
    }
    await new Promise(r => setTimeout(r, 650 * speed));
  }

  // Symbol Destruction Physics: Plunge/Dive backwards into water ripples, then evaporate to steam clouds
  async animateCascade(cascadeData, speed) {
    const canvasRect = this.fx.canvas ? this.fx.canvas.getBoundingClientRect() : { left: 0, top: 0 };

    // Phase 1: Sub-surface Plunge & Cavitation Splash Ripples
    audio.playWaterPlunge();
    for (const coord of cascadeData.removed_coords) {
      const cell = document.getElementById('cell-' + coord[0] + '-' + coord[1]);
      if (cell) {
        cell.classList.remove('burning');
        cell.classList.add('diving');
        const cellRect = cell.getBoundingClientRect();
        const cx = cellRect.left + cellRect.width / 2 - canvasRect.left;
        const cy = cellRect.top + cellRect.height / 2 - canvasRect.top;
        this.fx.spawnWaterSplash(cx, cy, 14);
      }
    }
    await new Promise(r => setTimeout(r, 220 * speed));

    // Phase 2: Steam Dissolution & Evaporation Hiss
    audio.playSteamHiss();
    for (const coord of cascadeData.removed_coords) {
      const cell = document.getElementById('cell-' + coord[0] + '-' + coord[1]);
      if (cell) {
        cell.classList.remove('diving');
        cell.classList.add('evaporating');
        const cellRect = cell.getBoundingClientRect();
        const cx = cellRect.left + cellRect.width / 2 - canvasRect.left;
        const cy = cellRect.top + cellRect.height / 2 - canvasRect.top;
        this.fx.spawnSteamCloud(cx, cy, 10);
      }
    }
    await new Promise(r => setTimeout(r, 280 * speed));

    // Scatter ambient fish due to explosion shockwave
    if (window.oceanAmbient) window.oceanAmbient.scatterFish();

    // Phase 3: Grid Drop with Cascade Tiles
    if (cascadeData.grid) {
      await this.animateGridDrop(cascadeData.grid, speed);
    }
  }

  // PHYSICAL ON-GRID LEVIATHAN STRIKE (True 3D Foreground Surge!)
  async animateCreatureStrike(data, speed) {
    const transmutedList = data.transmuted || [];
    const targetCells = [];
    for (const t of transmutedList) {
      const [r, c] = t.coord;
      const cell = document.getElementById(`cell-${r}-${c}`);
      if (cell) targetCells.push(cell);
    }

    // 1. Audio & Ambient Scatter
    if (window.oceanAmbient) window.oceanAmbient.scatterFish();

    // 2. Trigger True 3D Leviathan Foreground Surge directly over target cells
    if (this.leviathan3D) {
      await new Promise(resolve => {
        this.leviathan3D.riseAndDevour(targetCells, () => {
          // Evaporate targeted cells under the fangs into glowing steam
          targetCells.forEach((cell, idx) => {
            setTimeout(() => {
              cell.classList.add('evaporating');
              if (this.fx) {
                const r = cell.getBoundingClientRect();
                const cr = this.fx.canvas.getBoundingClientRect();
                this.fx.spawnSteamCloud(r.left + r.width / 2 - cr.left, r.top + r.height / 2 - cr.top, 16);
              }
            }, idx * 40);
          });
          resolve();
        });
      });
    }

    await new Promise(r => setTimeout(r, 350 * speed));

    // 3. Transmute devouring cells into Glowing Electric Wild Maws
    const canvasRect = this.fx.canvas ? this.fx.canvas.getBoundingClientRect() : { left: 0, top: 0 };
    for (const trans of transmutedList) {
      const r = trans.coord[0];
      const c = trans.coord[1];
      const cell = document.getElementById('cell-' + r + '-' + c);
      if (cell) {
        cell.classList.remove('evaporating');
        cell.innerHTML = '';
        cell.appendChild(this.createSymbolElement(trans.new_symbol));
        cell.style.borderColor = '#00f0ff';
        cell.style.boxShadow = '0 0 35px #00f0ff, inset 0 0 15px #00f0ff';
        cell.style.transform = 'scale(1.18)';

        const cellRect = cell.getBoundingClientRect();
        const cx = cellRect.left + cellRect.width / 2 - canvasRect.left;
        const cy = cellRect.top + cellRect.height / 2 - canvasRect.top;
        this.fx.spawnWaterSplash(cx, cy, 14);

        setTimeout(() => {
          if (cell) {
            cell.style.transform = 'scale(1.0)';
            cell.style.boxShadow = '';
          }
        }, 1200 * speed);
      }
    }

    await new Promise(r => setTimeout(r, 400 * speed));
  }

  showVents(activeVents) {
    for (let c = 0; c < 6; c++) {
      const v = document.getElementById('vent-' + c);
      if (!v) continue;
      if (activeVents && activeVents[c]) {
        v.textContent = activeVents[c] + 'X';
        v.classList.add('active');
      } else {
        v.classList.remove('active');
      }
    }
  }

  clearVents() {
    for (let c = 0; c < 6; c++) {
      const v = document.getElementById('vent-' + c);
      if (v) v.classList.remove('active');
    }
  }

  updatePurgedRunes(purgedList = []) {
    const purgedSet = new Set(purgedList.map(s => s.replace('LOW_', '')));
    const runes = ['10', 'J', 'Q', 'K', 'A'];
    let count = 0;
    runes.forEach(r => {
      const card = document.getElementById('rune-card-' + r);
      const status = document.getElementById('status-' + r);
      if (!card) return;
      if (purgedSet.has(r)) {
        count++;
        card.classList.add('purged');
        if (status) status.textContent = 'PURGED';
      } else {
        card.classList.remove('purged');
        if (status) status.textContent = 'ACTIVE';
      }
    });
    if (this.purgedCountEl) {
      this.purgedCountEl.textContent = count + '/5 PURGED';
    }
  }

  // Sleek Circular Sonar Depth Gauge and Countdown System
  updateDepthProgress(lvl, depthMeters, accumulatedPoints) {
    const meta = DEPTH_LEVELS[lvl] || DEPTH_LEVELS[0];
    this.depthValEl.textContent = depthMeters + 'M';
    this.levelBadgeEl.textContent = meta.name;
    this.levelBadgeEl.style.borderColor = meta.color;
    this.levelBadgeEl.style.boxShadow = '0 0 15px ' + meta.color;

    if (this.sidebarDepthEl) this.sidebarDepthEl.textContent = depthMeters + 'M';
    if (this.sidebarTierEl) this.sidebarTierEl.textContent = meta.name.toUpperCase();

    if (this.gameWrapper) {
      this.gameWrapper.className = 'depth-' + lvl;
    }

    // Set ambient ocean lighting / water tint according to depth
    if (window.oceanAmbient) {
      window.oceanAmbient.setDepthLevel(lvl);
    }

    let percent = 0;
    let ptsInTier = 0;
    let tierSpan = 15;
    let ptsNeeded = 0;

    if (lvl >= 5) {
      percent = 100;
      ptsNeeded = 0;
      ptsInTier = 50;
      tierSpan = 50;
    } else {
      const currentThresh = DEPTH_LEVELS[lvl].thresh;
      const nextThresh = DEPTH_LEVELS[lvl + 1].thresh;
      const currentPts = accumulatedPoints || 0;
      ptsNeeded = Math.max(0, nextThresh - currentPts);
      ptsInTier = Math.max(0, currentPts - currentThresh);
      tierSpan = Math.max(1, nextThresh - currentThresh);
      percent = Math.min(100, Math.max(0, (ptsInTier / tierSpan) * 100));
    }

    // Top horizontal pressure bar fill
    if (this.depthFillEl) {
      this.depthFillEl.style.width = Math.max(5, percent) + '%';
    }

    // Numerical Progression Counter (e.g. "8 / 15 PTS")
    const ptsCurEl = document.getElementById('sonar-pts-current');
    const ptsTargEl = document.getElementById('sonar-pts-target');
    const ptsFillEl = document.getElementById('sonar-bar-fill');
    const targetDescEl = document.getElementById('sonar-target-desc');

    if (ptsCurEl) ptsCurEl.textContent = ptsInTier;
    if (ptsTargEl) ptsTargEl.textContent = tierSpan;
    if (ptsFillEl) ptsFillEl.style.width = percent + '%';
    if (targetDescEl) {
      if (lvl >= 5) {
        targetDescEl.textContent = 'CORE MAXIMUM REACHED';
      } else {
        const nextMeta = DEPTH_LEVELS[lvl + 1];
        targetDescEl.textContent = `NEXT: ${nextMeta.name} (${nextMeta.depth}M)`;
      }
    }

    // Left Sidebar Depth Barometer Ticks
    for (let i = 0; i <= 5; i++) {
      const tick = document.getElementById(`tier-tick-${i}`);
      if (tick) {
        if (i === lvl) {
          tick.className = 'depth-tier-tick active';
        } else if (i < lvl) {
          tick.className = 'depth-tier-tick cleared';
        } else {
          tick.className = 'depth-tier-tick';
        }
      }
    }

    // Left Sidebar Submersible Vital Telemetry
    const pressureEl = document.getElementById('telemetry-pressure');
    if (pressureEl) {
      const atm = Math.round(1 + (depthMeters / 10));
      pressureEl.textContent = atm.toLocaleString() + ' ATM';
    }
    const proxEl = document.getElementById('telemetry-proximity');
    if (proxEl) {
      const prox = ((depthMeters / 11000) * 100).toFixed(1);
      proxEl.textContent = prox + '%';
    }
    const stressEl = document.getElementById('telemetry-stress');
    if (stressEl) {
      if (lvl >= 5) {
        stressEl.textContent = 'CRITICAL';
        stressEl.className = 'telemetry-value';
        stressEl.style.color = '#ff2a4b';
      } else if (lvl >= 3) {
        stressEl.textContent = 'HIGH';
        stressEl.className = 'telemetry-value';
        stressEl.style.color = '#ff9100';
      } else {
        stressEl.textContent = 'NOMINAL';
        stressEl.className = 'telemetry-value status-nominal';
        stressEl.style.color = '';
      }
    }

    // Circular Sonar Progress Ring (r = 68 => circumference ~= 427.26)
    if (this.sonarProgressRing) {
      const circumference = 427.26;
      this.sonarProgressRing.style.strokeDasharray = `${circumference}`;
      const offset = circumference - (percent / 100) * circumference;
      this.sonarProgressRing.style.strokeDashoffset = `${offset}`;
      this.sonarProgressRing.style.stroke = meta.color;
    }

    // Dial Center Dynamic Readouts
    if (this.sonarLevelTitle) {
      this.sonarLevelTitle.textContent = lvl >= 5 ? 'CORE LVL 5' : `LVL ${lvl}`;
      this.sonarLevelTitle.style.color = meta.color;
    }

    if (this.sonarPtsNeeded) {
      if (lvl >= 5) {
        this.sonarPtsNeeded.textContent = 'MAX REACHED';
        this.sonarPtsNeeded.style.fontSize = '12px';
      } else {
        this.sonarPtsNeeded.textContent = `${ptsNeeded} PTS`;
        this.sonarPtsNeeded.style.fontSize = '16px';
      }
    }

    if (this.sonarSub) {
      this.sonarSub.textContent = `${depthMeters}M DEPTH`;
    }

    // Quick Status Metrics Card
    if (this.sonarVentsVal) {
      this.sonarVentsVal.textContent = lvl >= 3 ? 'ONLINE' : 'LOCKED';
      this.sonarVentsVal.style.color = lvl >= 3 ? '#ff9100' : '#94a3b8';
    }
    if (this.sonarBoostVal) {
      this.sonarBoostVal.textContent = lvl >= 5 ? '2X MULTIPLIER' : '1X BASE';
      this.sonarBoostVal.style.color = lvl >= 5 ? '#ff2a4b' : '#38bdf8';
    }

    this.updateWaysCount(lvl >= 5 ? 7776 : 3125);

    if (this.leviathan3D) {
      this.leviathan3D.setDepthLighting(lvl);
    }
  }

  updateWaysCount(ways) {
    const banner = document.getElementById('ways-banner');
    const countEl = document.getElementById('ways-count-val');
    if (countEl) {
      countEl.textContent = Number(ways).toLocaleString();
      if (banner) {
        banner.classList.add('pulse');
        setTimeout(() => banner.classList.remove('pulse'), 450);
      }
    }
    if (this.sonarWaysVal) {
      this.sonarWaysVal.textContent = Number(ways).toLocaleString() + ' WAYS';
    }
  }

  showLevelUpSplash(lvl, name, depth, spinsAdded) {
    if (!this.levelUpSplash) return;
    this.splashLevelTitle.textContent = 'LEVEL ' + lvl + ': ' + depth + 'M';
    this.splashLevelName.textContent = name.toUpperCase();
    
    const rewards = [];
    if (spinsAdded > 0) rewards.push('🎁 +' + spinsAdded + ' FREE SPINS BANKED');
    if (lvl === 1) rewards.push('🔥 LOW 10 PURGED FROM REELS', '⚡ 1x1 LURKER MAW UNLOCKED');
    if (lvl === 2) rewards.push('🔥 LOW J PURGED FROM REELS', '⚡ 2x1 TENTACLE STALKER UNLOCKED');
    if (lvl === 3) rewards.push('🔥 LOW Q PURGED FROM REELS', '🌋 HYDROTHERMAL VENTS ONLINE', '⚡ 2x2 MAELSTROM WILD UNLOCKED');
    if (lvl === 4) rewards.push('🔥 LOW K PURGED FROM REELS', '⚡ 3x3 KRAKEN TENTACLES UNLOCKED');
    if (lvl === 5) rewards.push('💥 100% LOW RUNES PURGED!', '📐 6x5 GRID EXPANSION (7,776 WAYS)', '🔥 2X GLOBAL MULTIPLIER DOUBLED');

    this.splashRewards.innerHTML = rewards.map(r => `<div>${r}</div>`).join('');
    this.levelUpSplash.classList.add('active');

    setTimeout(() => {
      this.levelUpSplash.classList.remove('active');
    }, 2200);
  }

  showBigWin(amount) {
    const banner = document.getElementById('big-win-banner');
    const amtEl = document.getElementById('big-win-amount');
    amtEl.textContent = '$' + amount.toFixed(2);
    banner.classList.add('active');
    setTimeout(() => {
      banner.classList.remove('active');
    }, 2800);
  }
}

window.addEventListener('DOMContentLoaded', () => {
  if (typeof WebGLGameEngine !== 'undefined') {
    window.webglEngine = new WebGLGameEngine('webgl-grid-container');
    window.webglEngine.init().then(() => {
      window.slotGame = new SlotGame();
    });
  } else {
    window.slotGame = new SlotGame();
  }
});
