from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json, os, pathlib

app = FastAPI(title="EDGE Terminal")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

BASE = pathlib.Path(__file__).parent

# ── Static files ──────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=BASE / "apps/web/static"), name="static")

# ── Serve index.html at root ──────────────────────────────────
@app.get("/")
async def root():
    return FileResponse(BASE / "apps/web/static/index.html")

# ── Data store (in-memory, persisted to JSON) ─────────────────
DATA_FILE = BASE / "data.json"

def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {"bets": [], "games": [], "balance": 101.41, "balance_history": [101.41]}

def save_data(d):
    DATA_FILE.write_text(json.dumps(d, indent=2))

# ── API: Summary ──────────────────────────────────────────────
@app.get("/api/summary")
async def summary():
    d = load_data()
    bets = d.get("bets", [])
    wins   = sum(1 for b in bets if b.get("result") == "Win")
    losses = sum(1 for b in bets if b.get("result") == "Loss")
    wagered = sum(float(b.get("bet_amount", 0)) for b in bets)
    net_pl  = sum(float(b.get("profit_loss", 0)) for b in bets)
    model_correct = sum(1 for b in bets if b.get("model_correct") in [True, "Yes", "✅ Yes"])
    settled = sum(1 for b in bets if b.get("result") in ["Win","Loss","Push"])
    model_acc = (model_correct / settled * 100) if settled else 89.6
    return {
        "balance": d.get("balance", 101.41),
        "balance_history": d.get("balance_history", [101.41]),
        "wins": wins, "losses": losses,
        "net_pl": round(net_pl, 2),
        "total_wagered": round(wagered, 2),
        "model_accuracy": round(model_acc, 1)
    }

# ── API: Games ────────────────────────────────────────────────
@app.get("/api/games")
async def get_games():
    return load_data().get("games", [])

@app.post("/api/games")
async def add_game(game: dict):
    d = load_data()
    d["games"].append(game)
    save_data(d)
    return {"ok": True}

# ── API: Bets ─────────────────────────────────────────────────
@app.get("/api/bets")
async def get_bets():
    return load_data().get("bets", [])

@app.post("/api/bets")
async def add_bet(bet: dict):
    d = load_data()
    d["bets"].append(bet)
    # recalc balance
    net_pl = sum(float(b.get("profit_loss", 0)) for b in d["bets"])
    d["balance"] = round(101.41 + net_pl, 2)
    d["balance_history"].append(d["balance"])
    save_data(d)
    return {"ok": True, "balance": d["balance"]}

@app.put("/api/bets/{idx}")
async def update_bet(idx: int, updates: dict):
    d = load_data()
    if idx < len(d["bets"]):
        d["bets"][idx].update(updates)
        net_pl = sum(float(b.get("profit_loss", 0)) for b in d["bets"])
        d["balance"] = round(101.41 + net_pl, 2)
        d["balance_history"].append(d["balance"])
        save_data(d)
    return {"ok": True}

# ── API: Teams ────────────────────────────────────────────────
@app.get("/api/teams")
async def get_teams():
    teams_file = BASE / "all_stats.json"
    if teams_file.exists():
        raw = json.loads(teams_file.read_text())
        if isinstance(raw, dict):
            return [{"team": k, **v} for k, v in raw.items()]
        return raw
    return []

# ── API: Predict ──────────────────────────────────────────────
@app.post("/api/predict")
async def predict(payload: dict):
    import math
    team_a = payload.get("team_a", "")
    team_b = payload.get("team_b", "")
    seed_a = payload.get("seed_a") or 8
    seed_b = payload.get("seed_b") or 8
    ml_a   = payload.get("ml_a")
    bankroll = float(payload.get("bankroll", 101.41))

    # Load stats if available
    d = load_data()
    teams_file = BASE / "all_stats.json"
    stats = {}
    if teams_file.exists():
        raw = json.loads(teams_file.read_text())
        stats = raw if isinstance(raw, dict) else {}

    model_file = BASE / "gbm_v2_model.pkl"
    if model_file.exists():
        import pickle, numpy as np
        with open(model_file, "rb") as f:
            md = pickle.load(f)
        model  = md["model"]
        scaler = md["scaler"]
        FEATS  = md["features"]

        sa = stats.get(team_a, {})
        sb = stats.get(team_b, {})

        def fv(s, seed):
            return [
                s.get("SRS", 0), s.get("OffRtg", 100), s.get("DefRtg", 100),
                s.get("NetRtg", 0), s.get("TOVPct", 15), s.get("ORBPct", 30),
                s.get("TSPct", 0.52), s.get("STLPct", 8), s.get("BLKPct", 8),
                s.get("WinPct", 0.5), seed
            ]

        feat = [a - b for a, b in zip(fv(sa, seed_a), fv(sb, seed_b))]
        X = scaler.transform([feat])
        prob_a = float(model.predict_proba(X)[0][1]) * 100
    else:
        # Fallback: seed-based heuristic
        seed_diff = seed_b - seed_a
        base = 50 + seed_diff * 3.2
        srs_a = stats.get(team_a, {}).get("SRS", 0)
        srs_b = stats.get(team_b, {}).get("SRS", 0)
        base += (srs_a - srs_b) * 1.5
        prob_a = max(5, min(95, base))

    # Kelly
    kelly_fraction = None
    if ml_a:
        ml_a = float(ml_a)
        implied = abs(ml_a)/(abs(ml_a)+100) if ml_a < 0 else 100/(ml_a+100)
        b = (100/abs(ml_a)) if ml_a < 0 else ml_a/100
        p = prob_a / 100
        q = 1 - p
        k = (b * p - q) / b
        kelly_fraction = round(max(0, k), 4)

    sa = stats.get(team_a, {})
    return {
        "win_prob_a": round(prob_a, 1),
        "win_prob_b": round(100 - prob_a, 1),
        "kelly_fraction": kelly_fraction,
        "net_rtg_a": sa.get("NetRtg"),
        "srs_a": sa.get("SRS"),
        "pas_a": sa.get("PAS"),
        "seed_diff": int(seed_b) - int(seed_a),
    }

# ── Health ────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}
