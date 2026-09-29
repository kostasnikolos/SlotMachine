import re

with open('slot_engine/static/sound.js', 'r') as f:
    code = f.read()

new_playSoulBurn = """
  playSoulBurn() {
    if (!this.ctx || !this.enabled) return;
    const now = this.ctx.currentTime;
    
    // Deep liquid bubble pop
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    
    osc.type = 'sine';
    // Start mid-low, drop fast to simulate a bubble bursting
    osc.frequency.setValueAtTime(400, now);
    osc.frequency.exponentialRampToValueAtTime(100, now + 0.15);

    gain.gain.setValueAtTime(0.001, now);
    gain.gain.linearRampToValueAtTime(0.3, now + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);

    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.15);
  }
"""

new_playSoulAbsorb = """
  playSoulAbsorb() {
    if (!this.ctx || !this.enabled) return;
    const now = this.ctx.currentTime;
    
    // Watery swoosh / suction sound entering the meter
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    const filter = this.ctx.createBiquadFilter();

    // Noise burst for watery splash
    const bufferSize = this.ctx.sampleRate * 0.4;
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1);
    }
    const noise = this.ctx.createBufferSource();
    noise.buffer = buffer;

    filter.type = 'bandpass';
    // Swoosh up to simulate suction
    filter.frequency.setValueAtTime(200, now);
    filter.frequency.exponentialRampToValueAtTime(800, now + 0.3);
    filter.Q.setValueAtTime(1.5, now);

    gain.gain.setValueAtTime(0.001, now);
    gain.gain.linearRampToValueAtTime(0.4, now + 0.1);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);

    noise.connect(filter);
    filter.connect(gain);
    gain.connect(this.ctx.destination);
    noise.start(now);
    noise.stop(now + 0.4);
    
    // Low sub hit
    const subOsc = this.ctx.createOscillator();
    const subGain = this.ctx.createGain();
    subOsc.type = 'sine';
    subOsc.frequency.setValueAtTime(80, now);
    subOsc.frequency.exponentialRampToValueAtTime(30, now + 0.4);
    subGain.gain.setValueAtTime(0.2, now);
    subGain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
    subOsc.connect(subGain);
    subGain.connect(this.ctx.destination);
    subOsc.start(now);
    subOsc.stop(now + 0.4);
  }
"""

# Replace playSoulBurn
code = re.sub(r'  playSoulBurn\(\) \{.*?(?=  playSoulAbsorb\(\) \{)', new_playSoulBurn + '\n', code, flags=re.DOTALL)

# Replace playSoulAbsorb
code = re.sub(r'  playSoulAbsorb\(\) \{.*?(?=  playSonarPing\(\) \{)', new_playSoulAbsorb + '\n', code, flags=re.DOTALL)

with open('slot_engine/static/sound.js', 'w') as f:
    f.write(code)
