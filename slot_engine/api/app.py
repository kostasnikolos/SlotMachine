"""FastAPI Application for The Descent: Abyssal Leviathan Slot Engine."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from slot_engine.config.symbols import (
    SymbolType,
    SymbolCategory,
    DepthLevel,
    FeatureBuyType,
    SYMBOL_PAYTABLE,
    SYMBOL_PRESSURE_POINTS,
    DEPTH_LEVEL_THRESHOLDS,
    DEPTH_METADATA,
    GAME_RULES,
)
from slot_engine.config.rtp_profiles import get_active_rtp_profile
from slot_engine.core.state_machine import SlotStateMachine
from slot_engine.core.rng import SlotRNG

app = FastAPI(
    title="The Descent: Abyssal Leviathan",
    description="High-volatility deep sea Eldritch slot machine engine.",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Engine instance
engine = SlotStateMachine(rng=SlotRNG())

# Static directory
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class SpinRequest(BaseModel):
    bet: float = Field(default=1.0, ge=0.10, le=100.0, description="Base stake in currency units")
    feature_buy: str = Field(default="NONE", description="Feature bet or buy type")


class BonusBuyRequest(BaseModel):
    bet: float = Field(default=1.0, ge=0.10, le=100.0, description="Base stake unit for the bonus")
    feature_type: str = Field(default="STANDARD_BONUS_100X", description="Bonus buy package")


def outcome_to_dict(outcome) -> Dict[str, Any]:
    return {
        "spin_id": outcome.spin_id,
        "bet": outcome.bet,
        "feature_type": outcome.feature_type.value,
        "total_payout": round(outcome.total_payout, 2),
        "payout_multiplier": round(outcome.payout_multiplier, 2),   # vs. round cost (bet)
        "base_bet": outcome.base_bet,
        "win_x_base_bet": outcome.win_x_base_bet,                  # vs. base stake (big-win tiers)
        "max_win_capped": outcome.max_win_capped,
        "final_depth_level": outcome.final_depth_level.value,
        "depth_name": outcome.depth_name,
        "total_cascades": outcome.total_cascades,
        "events": [
            {
                "step": ev.step,
                "event_type": ev.event_type,
                "data": ev.data,
            }
            for ev in outcome.events
        ],
    }


@app.get("/")
async def serve_index():
    # The Descent frontend, generated from descent/design/Main.dc.html by scripts/descent/dc_to_web.py
    index_path = STATIC_DIR / "descent" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"status": "The Descent Slot Engine Online", "docs": "/docs"}


@app.get("/legacy")
async def serve_legacy_index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Legacy frontend not found")


@app.get("/api/slot/health")
async def get_health():
    rtp_profile = get_active_rtp_profile()
    return {
        "status": "ONLINE",
        "game": "The Descent: Abyssal Leviathan",
        "rtp": f"{rtp_profile.target_rtp * 100:.2f}%",
        "max_win": f"{rtp_profile.max_win_multiplier:,.0f}x",
        "features": [f.value for f in FeatureBuyType],
    }


@app.get("/api/slot/paytable")
async def get_paytable():
    return {
        "paytable": {
            sym.value: payouts
            for sym, payouts in SYMBOL_PAYTABLE.items()
        },
        "pressure_points": {
            sym.value: pts
            for sym, pts in SYMBOL_PRESSURE_POINTS.items()
        },
        "depth_thresholds": {
            level.value: thresh
            for level, thresh in DEPTH_LEVEL_THRESHOLDS.items()
        },
        "depth_metadata": {
            level.value: meta
            for level, meta in DEPTH_METADATA.items()
        },
        "feature_buys": {
            FeatureBuyType.XBET_SONAR_2X.value: {"cost_mult": 2.0, "name": "Abyssal Sonar xBet", "desc": f"Start directly at Level 1 (Twilight Zone, 500m) with 10s purged and {GAME_RULES['xbet_start_points']} pressure points!"},
            FeatureBuyType.STANDARD_BONUS_100X.value: {"cost_mult": 100.0, "name": "Abyssal Descent (Standard)", "desc": f"Level 3 Abyss (5,000m), {GAME_RULES['standard_bonus_spins']} Free Spins, Hydrothermal Vents active!"},
            FeatureBuyType.ULTRA_BONUS_350X.value: {"cost_mult": 350.0, "name": "Leviathan Awakening (Ultra)", "desc": f"Level 5 Core (11,000m), 6x5 Grid (15,625 ways), {GAME_RULES['ultra_bonus_spins']} Spins, {GAME_RULES['core_global_multiplier']}x Global Multiplier, 100% Lows purged!"},
            FeatureBuyType.MYSTERY_BUY_200X.value: {"cost_mult": 200.0, "name": "Mystery Trench Abyss", "desc": f"{round(100 * (1 - GAME_RULES['mystery_ultra_probability']))}% chance Standard Bonus / {round(100 * GAME_RULES['mystery_ultra_probability'])}% chance Ultra Bonus!"},
        }
    }


@app.post("/api/slot/spin")
async def spin(req: SpinRequest):
    try:
        buy_enum = FeatureBuyType[req.feature_buy]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid feature_buy: {req.feature_buy}")

    outcome = engine.execute_spin(base_bet=req.bet, feature_buy=buy_enum)
    return outcome_to_dict(outcome)


@app.post("/api/slot/buy-bonus")
async def buy_bonus(req: BonusBuyRequest):
    try:
        buy_enum = FeatureBuyType[req.feature_type]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid feature_type: {req.feature_type}")

    if buy_enum == FeatureBuyType.NONE:
        raise HTTPException(status_code=400, detail="Must specify a bonus feature buy type")

    outcome = engine.execute_spin(base_bet=req.bet, feature_buy=buy_enum)
    return outcome_to_dict(outcome)


class SnapshotRequest(BaseModel):
    name: str = Field(default="leviathan_snapshot", description="Snapshot file identifier")
    image_base64: str = Field(..., description="Base64 encoded data URI or raw base64 string")


@app.post("/api/snapshot")
async def save_snapshot(req: SnapshotRequest):
    import base64
    import re

    raw = req.image_base64
    if "," in raw:
        raw = raw.split(",", 1)[1]
    
    img_data = base64.b64decode(raw)
    
    # 1. Save to static snapshots directory
    snap_dir = STATIC_DIR / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    snap_path = snap_dir / f"{req.name}.png"
    with open(snap_path, "wb") as f:
        f.write(img_data)
        
    # 2. Save directly to brain artifact directory if exists
    artifact_dir = Path("/Users/kosta/.gemini/antigravity/brain/c8ee4d6f-219a-45e7-ba86-3151e9bd0b1a")
    if artifact_dir.exists():
        art_path = artifact_dir / f"{req.name}.png"
        with open(art_path, "wb") as f:
            f.write(img_data)

    return {"status": "SUCCESS", "saved_to": str(snap_path), "size_bytes": len(img_data)}


@app.post("/api/upload-model")
async def upload_model(file: UploadFile = File(...)):
    content = await file.read()
    models_dir = STATIC_DIR / "assets" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / "custom_leviathan.glb"
    with open(model_path, "wb") as f:
        f.write(content)
        
    artifact_dir = Path("/Users/kosta/.gemini/antigravity/brain/c8ee4d6f-219a-45e7-ba86-3151e9bd0b1a")
    if artifact_dir.exists():
        art_path = artifact_dir / "custom_leviathan.glb"
        with open(art_path, "wb") as f:
            f.write(content)
            
    return {
        "status": "SUCCESS",
        "filename": file.filename,
        "size_bytes": len(content),
        "viewer_url": "/static/skeleton_viewer.html?model=custom_leviathan.glb"
    }

