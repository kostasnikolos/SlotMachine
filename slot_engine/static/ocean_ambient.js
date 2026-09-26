// The Descent: Abyssal Leviathan - Living Ambient Ocean Simulation Engine

class OceanAmbient {
  constructor(canvasId = 'ambient-ocean-canvas') {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.width = 0;
    this.height = 0;
    this.depthLevel = 0;
    this.time = 0;
    this.turbulence = 1.0;

    // Entities
    this.fishSchool = [];
    this.jellyfishList = [];
    this.bubbles = [];
    this.marineSnow = [];
    this.leviathanShadow = {
      x: -400,
      y: 350,
      vx: 1.2,
      targetY: 350,
      bodyPoints: [],
      length: 700,
      segments: 24,
      eyeGlow: 0.8,
      visible: true,
    };

    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.initEntities();
    this.loop();
  }

  resize() {
    if (!this.canvas || !this.canvas.parentElement) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.width = rect.width;
    this.height = rect.height;
    this.canvas.width = this.width;
    this.canvas.height = this.height;
  }

  initEntities() {
    // 1. Fish School (Boids flocking)
    this.fishSchool = [];
    const fishCount = 28;
    for (let i = 0; i < fishCount; i++) {
      this.fishSchool.push({
        x: Math.random() * this.width,
        y: 100 + Math.random() * (this.height - 250),
        vx: (Math.random() - 0.5) * 2,
        vy: (Math.random() - 0.5) * 1.5,
        size: 7 + Math.random() * 5,
        wigglePhase: Math.random() * Math.PI * 2,
        hue: 185 + Math.random() * 20, // Cyan/Aqua
        fear: 0,
      });
    }

    // 2. Bioluminescent Jellyfish
    this.jellyfishList = [];
    const jellyCount = 5;
    for (let i = 0; i < jellyCount; i++) {
      this.jellyfishList.push({
        x: 80 + Math.random() * (this.width - 160),
        y: Math.random() * this.height,
        size: 16 + Math.random() * 14,
        pulsePhase: Math.random() * Math.PI * 2,
        speed: 0.35 + Math.random() * 0.25,
        tentacleLength: 40 + Math.random() * 30,
        tentacles: 5,
        hue: i % 2 === 0 ? 190 : 280, // Cyan or Magenta/Violet
      });
    }

    // 3. Marine Snow / Organic Particulates
    this.marineSnow = [];
    const snowCount = 65;
    for (let i = 0; i < snowCount; i++) {
      this.marineSnow.push({
        x: Math.random() * this.width,
        y: Math.random() * this.height,
        vy: 0.3 + Math.random() * 0.6,
        vx: (Math.random() - 0.5) * 0.3,
        size: 1 + Math.random() * 2.5,
        alpha: 0.2 + Math.random() * 0.5,
      });
    }

    // 4. Initial Leviathan Segment Nodes
    this.leviathanShadow.bodyPoints = [];
    for (let i = 0; i < this.leviathanShadow.segments; i++) {
      this.leviathanShadow.bodyPoints.push({
        x: this.leviathanShadow.x - i * 30,
        y: this.leviathanShadow.y,
      });
    }
  }

  setDepthLevel(level) {
    this.depthLevel = level;
    // Adjust wildlife and mood based on depth
    if (level >= 3) {
      this.spawnVentBubbleBurst(15);
    }
  }

  scatterFish() {
    // Scatter fish in panic away from the center
    const centerX = this.width / 2;
    const centerY = this.height / 2;
    for (const f of this.fishSchool) {
      const dx = f.x - centerX;
      const dy = f.y - centerY;
      const dist = Math.max(1, Math.hypot(dx, dy));
      f.vx = (dx / dist) * (5 + Math.random() * 4);
      f.vy = (dy / dist) * (4 + Math.random() * 3);
      f.fear = 1.0;
    }
    this.turbulence = 2.5;
  }

  spawnVentBubbleBurst(count = 20) {
    for (let i = 0; i < count; i++) {
      this.bubbles.push({
        x: 200 + Math.random() * (this.width - 400),
        y: this.height + 10,
        vy: -2.0 - Math.random() * 3.5,
        vx: (Math.random() - 0.5) * 1.5,
        wobble: Math.random() * Math.PI * 2,
        wobbleSpeed: 0.08 + Math.random() * 0.06,
        size: 3 + Math.random() * 8,
        color: this.depthLevel >= 5 ? '#ff4500' : (this.depthLevel >= 3 ? '#ff9100' : '#00f0ff'),
      });
    }
  }

  loop() {
    this.time += 0.018;
    this.turbulence = Math.max(1.0, this.turbulence * 0.985);

    this.ctx.clearRect(0, 0, this.width, this.height);

    this.renderAtmosphereGrading();
    // Only real 3D Leviathan model is rendered in foreground, no 2D eel shadow
    this.renderJellyfish();
    this.renderFishSchool();
    this.renderBubbles();
    this.renderMarineSnow();

    requestAnimationFrame(() => this.loop());
  }

  renderAtmosphereGrading() {
    // Dynamic deep Hadal trench void ambient wash
    const grad = this.ctx.createLinearGradient(0, 0, 0, this.height);
    if (this.depthLevel === 0) {
      grad.addColorStop(0, 'rgba(1, 4, 10, 0.55)');
      grad.addColorStop(1, 'rgba(0, 2, 6, 0.85)');
    } else if (this.depthLevel === 1) {
      grad.addColorStop(0, 'rgba(2, 6, 16, 0.65)');
      grad.addColorStop(1, 'rgba(0, 3, 8, 0.90)');
    } else if (this.depthLevel === 2) {
      grad.addColorStop(0, 'rgba(4, 3, 20, 0.72)');
      grad.addColorStop(1, 'rgba(0, 2, 6, 0.94)');
    } else if (this.depthLevel === 3) {
      grad.addColorStop(0, 'rgba(20, 4, 35, 0.78)');
      grad.addColorStop(1, 'rgba(2, 1, 8, 0.96)');
    } else if (this.depthLevel === 4) {
      grad.addColorStop(0, 'rgba(35, 6, 30, 0.82)');
      grad.addColorStop(1, 'rgba(6, 1, 5, 0.98)');
    } else {
      // Level 5 - Leviathan Core Blood Alarm
      const pulse = 0.45 + 0.15 * Math.sin(this.time * 4);
      grad.addColorStop(0, `rgba(80, 5, 15, ${pulse})`);
      grad.addColorStop(1, 'rgba(12, 0, 2, 0.98)');
    }
    this.ctx.fillStyle = grad;
    this.ctx.fillRect(0, 0, this.width, this.height);
  }

  renderCaustics() {
    // Shimmering light refraction wave lines
    this.ctx.save();
    this.ctx.lineWidth = 2.5;
    const waveCount = 6;
    const step = this.width / waveCount;

    for (let i = 0; i < waveCount; i++) {
      const x = i * step + Math.sin(this.time * 1.5 + i) * 35;
      const grad = this.ctx.createLinearGradient(x, 0, x + 50, this.height);
      const alpha = this.depthLevel >= 5 ? 0.08 : (0.12 / (this.depthLevel + 1));
      
      const lightColor = this.depthLevel >= 5 ? '#ff2a4b' : (this.depthLevel >= 3 ? '#c084fc' : '#00f0ff');
      grad.addColorStop(0, lightColor);
      grad.addColorStop(0.7, 'transparent');

      this.ctx.strokeStyle = grad;
      this.ctx.globalAlpha = alpha;
      this.ctx.beginPath();
      this.ctx.moveTo(x, 0);
      this.ctx.bezierCurveTo(
        x + Math.sin(this.time + i) * 60, this.height * 0.35,
        x - Math.cos(this.time * 0.8 + i) * 60, this.height * 0.7,
        x + Math.sin(this.time * 1.2) * 40, this.height
      );
      this.ctx.stroke();
    }
    this.ctx.restore();
  }

  renderLeviathanShadow() {
    const lev = this.leviathanShadow;
    lev.x += lev.vx * (this.depthLevel >= 3 ? 1.4 : 1.0);
    lev.y = lev.targetY + Math.sin(this.time * 0.8) * 45;

    // Reset when swimming off right screen
    if (lev.x > this.width + 500) {
      lev.x = -600;
      lev.targetY = 200 + Math.random() * (this.height - 400);
      lev.vx = 1.0 + Math.random() * 0.8;
    }

    // Update serpent body segments
    const head = lev.bodyPoints[0];
    head.x = lev.x;
    head.y = lev.y;
    for (let i = 1; i < lev.segments; i++) {
      const prev = lev.bodyPoints[i - 1];
      const curr = lev.bodyPoints[i];
      const dx = prev.x - curr.x;
      const dy = prev.y - curr.y;
      const angle = Math.atan2(dy, dx);
      curr.x = prev.x - Math.cos(angle) * 28;
      curr.y = prev.y - Math.sin(angle) * 28;
    }

    // Draw shadowy colossal serpent
    this.ctx.save();
    this.ctx.lineCap = 'round';
    this.ctx.lineJoin = 'round';

    const shadowOpacity = this.depthLevel === 0 ? 0.15 : (0.25 + this.depthLevel * 0.08);
    this.ctx.globalAlpha = Math.min(0.75, shadowOpacity);

    // Spine & Mass
    for (let i = lev.segments - 1; i > 0; i--) {
      const p1 = lev.bodyPoints[i];
      const p2 = lev.bodyPoints[i - 1];
      const radius = Math.sin((i / lev.segments) * Math.PI) * 45 + 12;

      this.ctx.strokeStyle = this.depthLevel >= 5 ? '#2a0208' : '#030d1a';
      this.ctx.lineWidth = radius * 2;
      this.ctx.beginPath();
      this.ctx.moveTo(p1.x, p1.y);
      this.ctx.lineTo(p2.x, p2.y);
      this.ctx.stroke();

      // Bioluminescent dorsal spines
      if (i % 2 === 0 && i < lev.segments - 2) {
        this.ctx.save();
        this.ctx.strokeStyle = this.depthLevel >= 5 ? '#ff2a4b' : '#00f0ff';
        this.ctx.lineWidth = 3;
        this.ctx.shadowBlur = 12;
        this.ctx.shadowColor = this.depthLevel >= 5 ? '#ff2a4b' : '#00f0ff';
        this.ctx.beginPath();
        this.ctx.moveTo(p1.x, p1.y);
        this.ctx.lineTo(p1.x - 10, p1.y - radius - 15);
        this.ctx.stroke();
        this.ctx.restore();
      }
    }

    // Glowing Monster Eyes
    const eyeX = head.x + 20;
    const eyeY = head.y - 10;
    this.ctx.fillStyle = this.depthLevel >= 5 ? '#ff0033' : '#ffd700';
    this.ctx.shadowBlur = 18;
    this.ctx.shadowColor = this.ctx.fillStyle;
    this.ctx.beginPath();
    this.ctx.ellipse(eyeX, eyeY, 8, 4, Math.PI / 12, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.restore();
  }

  renderFishSchool() {
    this.ctx.save();
    for (const f of this.fishSchool) {
      // Natural flocking & boundary steering
      if (f.fear > 0) {
        f.fear *= 0.96;
        f.x += f.vx;
        f.y += f.vy;
      } else {
        f.x += f.vx + Math.sin(this.time * 2 + f.wigglePhase) * 0.8;
        f.y += f.vy + Math.cos(this.time * 1.5 + f.wigglePhase) * 0.5;

        // Soft screen bounce
        if (f.x < -40) f.x = this.width + 20;
        if (f.x > this.width + 40) f.x = -20;
        if (f.y < 60) f.vy = Math.abs(f.vy) + 0.3;
        if (f.y > this.height - 80) f.vy = -Math.abs(f.vy) - 0.3;
      }

      // Draw Fish
      const angle = Math.atan2(f.vy, f.vx);
      const wag = Math.sin(this.time * 12 + f.wigglePhase) * 4;

      this.ctx.save();
      this.ctx.translate(f.x, f.y);
      this.ctx.rotate(angle);

      // Bioluminescent Glow
      this.ctx.shadowBlur = 8;
      this.ctx.shadowColor = `hsl(${f.hue}, 90%, 60%)`;
      this.ctx.fillStyle = `hsl(${f.hue}, 85%, 65%)`;

      // Fish Torpedo Body
      this.ctx.beginPath();
      this.ctx.moveTo(f.size, 0);
      this.ctx.quadraticCurveTo(0, -f.size * 0.45, -f.size, 0);
      this.ctx.quadraticCurveTo(0, f.size * 0.45, f.size, 0);
      this.ctx.fill();

      // Wagging Tail Fin
      this.ctx.beginPath();
      this.ctx.moveTo(-f.size, 0);
      this.ctx.lineTo(-f.size - 6, -f.size * 0.5 + wag);
      this.ctx.lineTo(-f.size - 6, f.size * 0.5 + wag);
      this.ctx.closePath();
      this.ctx.fill();

      this.ctx.restore();
    }
    this.ctx.restore();
  }

  renderJellyfish() {
    this.ctx.save();
    for (const j of this.jellyfishList) {
      j.pulsePhase += 0.045;
      const pulse = Math.sin(j.pulsePhase);
      const bellWidth = j.size * (1.0 + pulse * 0.25);
      const bellHeight = j.size * (1.1 - pulse * 0.2);

      // Upward propulsion during contraction
      if (pulse > 0) {
        j.y -= j.speed * (1.2 + pulse);
      } else {
        j.y -= j.speed * 0.4;
      }
      j.x += Math.sin(this.time * 0.8 + j.pulsePhase) * 0.5;

      // Wrap around top/bottom
      if (j.y < -100) {
        j.y = this.height + 80;
        j.x = 80 + Math.random() * (this.width - 160);
      }

      this.ctx.save();
      this.ctx.translate(j.x, j.y);

      // Translucent Bioluminescent Bell
      this.ctx.shadowBlur = 14;
      this.ctx.shadowColor = `hsl(${j.hue}, 90%, 65%)`;
      this.ctx.fillStyle = `hsla(${j.hue}, 80%, 60%, 0.28)`;
      this.ctx.strokeStyle = `hsla(${j.hue}, 90%, 75%, 0.8)`;
      this.ctx.lineWidth = 1.8;

      this.ctx.beginPath();
      this.ctx.arc(0, 0, bellWidth, Math.PI, 0, false);
      this.ctx.quadraticCurveTo(bellWidth * 0.5, bellHeight * 0.4, 0, bellHeight * 0.3);
      this.ctx.quadraticCurveTo(-bellWidth * 0.5, bellHeight * 0.4, -bellWidth, 0);
      this.ctx.fill();
      this.ctx.stroke();

      // Inner Glowing Organ
      this.ctx.fillStyle = `hsla(${j.hue}, 100%, 80%, 0.75)`;
      this.ctx.beginPath();
      this.ctx.arc(0, -bellHeight * 0.3, bellWidth * 0.3, 0, Math.PI * 2);
      this.ctx.fill();

      // Undulating Tentacles
      this.ctx.strokeStyle = `hsla(${j.hue}, 85%, 70%, 0.4)`;
      this.ctx.lineWidth = 1.2;
      for (let t = -2; t <= 2; t++) {
        const tx = t * (bellWidth * 0.35);
        this.ctx.beginPath();
        this.ctx.moveTo(tx, bellHeight * 0.3);
        const wave = Math.sin(this.time * 3 + t * 0.8) * 8;
        this.ctx.bezierCurveTo(
          tx + wave, bellHeight + j.tentacleLength * 0.35,
          tx - wave, bellHeight + j.tentacleLength * 0.7,
          tx + wave * 0.5, bellHeight + j.tentacleLength
        );
        this.ctx.stroke();
      }

      this.ctx.restore();
    }
    this.ctx.restore();
  }

  renderBubbles() {
    // Constantly generate small ambient bubbles from seafloor
    if (Math.random() < 0.18 * (this.depthLevel + 1)) {
      this.bubbles.push({
        x: 150 + Math.random() * (this.width - 300),
        y: this.height + 5,
        vy: -1.5 - Math.random() * 2.2,
        vx: (Math.random() - 0.5) * 0.8,
        wobble: Math.random() * Math.PI * 2,
        wobbleSpeed: 0.08,
        size: 2.5 + Math.random() * 5.5,
        color: this.depthLevel >= 5 ? '#ff4500' : (this.depthLevel >= 3 ? '#ff9100' : '#00f0ff'),
      });
    }

    this.ctx.save();
    for (let i = this.bubbles.length - 1; i >= 0; i--) {
      const b = this.bubbles[i];
      b.wobble += b.wobbleSpeed;
      b.y += b.vy;
      b.x += b.vx + Math.sin(b.wobble) * 1.0;

      // Draw shimmering bubble
      this.ctx.shadowBlur = 6;
      this.ctx.shadowColor = b.color;
      this.ctx.strokeStyle = b.color;
      this.ctx.lineWidth = 1.2;
      this.ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';

      this.ctx.beginPath();
      this.ctx.arc(b.x, b.y, b.size, 0, Math.PI * 2);
      this.ctx.stroke();
      this.ctx.fill();

      // Specular Highlight
      this.ctx.fillStyle = '#ffffff';
      this.ctx.beginPath();
      this.ctx.arc(b.x - b.size * 0.35, b.y - b.size * 0.35, b.size * 0.25, 0, Math.PI * 2);
      this.ctx.fill();

      if (b.y < -20) {
        this.bubbles.splice(i, 1);
      }
    }
    this.ctx.restore();
  }

  renderMarineSnow() {
    this.ctx.save();
    this.ctx.fillStyle = '#ffffff';
    for (const s of this.marineSnow) {
      s.y += s.vy;
      s.x += s.vx + Math.sin(this.time + s.y * 0.02) * 0.3;

      if (s.y > this.height) {
        s.y = -10;
        s.x = Math.random() * this.width;
      }

      this.ctx.globalAlpha = s.alpha * (this.depthLevel === 0 ? 0.3 : 0.65);
      this.ctx.beginPath();
      this.ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
      this.ctx.fill();
    }
    this.ctx.restore();
  }
}

window.addEventListener('DOMContentLoaded', () => {
  window.oceanAmbient = new OceanAmbient('ambient-ocean-canvas');
});
