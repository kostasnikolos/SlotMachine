import re

with open('slot_engine/static/sound.js', 'r') as f:
    code = f.read()

new_playWin = """
  playWin() {
    if (!this.ctx || !this.enabled) return;
    const now = this.ctx.currentTime;
    
    // Dark underwater wave/surge instead of fake harp
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    const filter = this.ctx.createBiquadFilter();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(45, now);
    osc.frequency.exponentialRampToValueAtTime(15, now + 0.6); // Deep dive

    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(300, now);
    filter.frequency.linearRampToValueAtTime(80, now + 0.6);

    gain.gain.setValueAtTime(0.001, now);
    gain.gain.linearRampToValueAtTime(0.5, now + 0.1); // Swell up like a wave
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6); // Fade out

    // Add a secondary rumble
    const rumble = this.ctx.createOscillator();
    const rumbleGain = this.ctx.createGain();
    rumble.type = 'sawtooth';
    rumble.frequency.setValueAtTime(60, now);
    rumble.frequency.exponentialRampToValueAtTime(20, now + 0.6);
    rumbleGain.gain.setValueAtTime(0.001, now);
    rumbleGain.gain.linearRampToValueAtTime(0.15, now + 0.2);
    rumbleGain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.6);

    const rumbleFilter = this.ctx.createBiquadFilter();
    rumbleFilter.type = 'lowpass';
    rumbleFilter.frequency.setValueAtTime(150, now);
    rumble.connect(rumbleFilter);
    rumbleFilter.connect(rumbleGain);
    rumbleGain.connect(this.ctx.destination);
    rumble.start(now);
    rumble.stop(now + 0.6);
  }
"""

new_playMeterAbsorb = """
  playMeterAbsorb() {
    if (!this.ctx || !this.enabled) return;
    const now = this.ctx.currentTime;
    
    // Deep, dark suction "glug" sound for symbols going to meter
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    
    osc.type = 'sine';
    osc.frequency.setValueAtTime(120, now);
    // Rapidly drop frequency to simulate suction/gulp
    osc.frequency.exponentialRampToValueAtTime(40, now + 0.3);

    gain.gain.setValueAtTime(0.4, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);

    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.3);
  }
"""

# Replace playWin
code = re.sub(r'  playWin\(\) \{[\s\S]*?  playCascade\(\) \{', new_playWin + '\n  playCascade() {', code)

# Add playMeterAbsorb at the end
code = re.sub(r'\}$', new_playMeterAbsorb + '\n}', code)

with open('slot_engine/static/sound.js', 'w') as f:
    f.write(code)

# Now update game.js to call playMeterAbsorb
with open('slot_engine/static/game.js', 'r') as f:
    game_code = f.read()

game_code = game_code.replace("this.updateDepthProgress(ev.data.depth_level, ev.data.depth_meters, ev.data.accumulated_points);", "audio.playMeterAbsorb();\n            this.updateDepthProgress(ev.data.depth_level, ev.data.depth_meters, ev.data.accumulated_points);")

with open('slot_engine/static/game.js', 'w') as f:
    f.write(game_code)
