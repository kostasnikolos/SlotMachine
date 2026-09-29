import re
with open("slot_engine/static/game.js", "r") as f:
    code = f.read()

replacement = """    const spinStartTime = Date.now();
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
      
      const elapsed = Date.now() - spinStartTime;
      const minDelay = this.turbo ? 400 : 1500;
      if (elapsed < minDelay) {
          await new Promise(r => setTimeout(r, minDelay - elapsed));
      }
      
      await this.playbackTimeline(data);"""

code = re.sub(r'    try \{\n      const res = await fetch\(\'/api/slot/spin\', \{.*?\n      \}\);\n      const data = await res\.json\(\);\n      await this\.playbackTimeline\(data\);', replacement, code, flags=re.DOTALL)

with open("slot_engine/static/game.js", "w") as f:
    f.write(code)
