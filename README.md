# 🎰 The Descent: Abyssal Leviathan — Studio Slot Engine

High-volatility 3D WebGL deep-sea eldritch slot machine engine inspired by Nolimit City (*Mental*, *Das xBoot*, *Blood & Shadow 2*) and Push Gaming (*Razor Returns*).

---

## ⚡ Architecture & Features
- **Reel Mechanics:** 5x5 Ways (3,125 ways) expanding to 6x5 (7,776 ways) in Hadal Core Void.
- **Cascading Depth Gauge:** 6 depth tiers (0m Sunlight down to 11,000m Core) with real-time symbol purging (10, J, Q, K).
- **Hydrothermal Vents:** Dynamic column multiplier eruptions (2x, 3x, 5x, 10x).
- **3D Leviathan Viewport:** WebGL Three.js rigged creature with bioluminescent point lighting and foreground devour attacks.
- **Procedural Web Audio Engine:** Sub-bass hydrophones, sonar pings, creature roars, and jaw snaps synthesized natively via Web Audio API.

---

## 🚀 Quickstart

### 1. Run the Engine Server
```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI engine & static UI
python3 -m uvicorn slot_engine.api.app:app --host 0.0.0.0 --port 8080 --reload
```

### 2. Run Tests
```bash
python3 -m pytest tests/ -v
```
