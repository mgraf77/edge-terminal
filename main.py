from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json, pathlib

app = FastAPI(title="EDGE Terminal")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
BASE = pathlib.Path(__file__).parent

app.mount("/static", StaticFiles(directory=BASE / "apps/web/static"), name="static")

@app.get("/")
async def root():
    return FileResponse(BASE / "apps/web/static/index.html")

DATA_FILE  = BASE / "data.json"
TEAMS_FILE = BASE / "all_stats.json"

# In-memory store — seeded from data.json on startup
_store = None

def load_data():
    global _store
    if _store is not None:
        return _store
    if DATA_FILE.exists():
        try:
            _store = json.loads(DATA_FILE.read_text())
            return _store
        except: pass
    _store = {"bets": [], "games": [], "balance": 81.81, "balance_history": [81.81]}
    return _store

def save_data(d):
    global _store
    _store = d
    try:
        DATA_FILE.write_text(json.dumps(d, indent=2))
    except: pass

@app.get("/api/summary")
async def summary():
    d = load_data()
    bets = d.get("bets", [])
    wins    = sum(1 for b in bets if b.get("result") == "Win")
    losses  = sum(1 for b in bets if b.get("result") == "Loss")
    wagered = sum(float(b.get("bet_amount", 0)) for b in bets if b.get("result") in ["Win","Loss","Push"])
    net_pl  = sum(float(b.get("profit_loss", 0)) for b in bets)
    settled = sum(1 for b in bets if b.get("result") in ["Win","Loss","Push"])
    mc_yes  = sum(1 for b in bets if b.get("model_correct") in [True,"Yes","\u2705 Yes"])
    model_acc = round(mc_yes / settled * 100, 1) if settled else 89.6
    return {
        "balance": d.get("balance", 81.81),
        "balance_history": d.get("balance_history", [81.81]),
        "wins": wins, "losses": losses,
        "net_pl": round(net_pl, 2),
        "total_wagered": round(wagered, 2),
        "model_accuracy": model_acc,
    }

@app.get("/api/games")
async def get_games():
    return load_data().get("games", [])

@app.post("/api/games")
async def add_game(game: dict):
    d = load_data()
    d["games"].append(game)
    save_data(d)
    return {"ok": True}

@app.get("/api/bets")
async def get_bets():
    return load_data().get("bets", [])

@app.post("/api/bets")
async def add_bet(bet: dict):
    d = load_data()
    d["bets"].append(bet)
    net_pl = sum(float(b.get("profit_loss", 0)) for b in d["bets"])
    d["balance"] = round(81.81 + net_pl - sum(float(b.get("profit_loss",0)) for b in d["bets"]), 2)
    # Recalc properly
    d["balance"] = round(101.41 + net_pl, 2)
    d["balance_history"].append(d["balance"])
    save_data(d)
    return {"ok": True, "balance": d["balance"]}

@app.put("/api/bets/{idx}")
async def update_bet(idx: int, updates: dict):
    d = load_data()
    if 0 <= idx < len(d["bets"]):
        d["bets"][idx].update(updates)
        net_pl = sum(float(b.get("profit_loss", 0)) for b in d["bets"])
        d["balance"] = round(101.41 + net_pl, 2)
        d["balance_history"].append(d["balance"])
        save_data(d)
    return {"ok": True}

@app.get("/api/teams")
async def get_teams():
    if TEAMS_FILE.exists():
        raw = json.loads(TEAMS_FILE.read_text())
        if isinstance(raw, dict):
            return [{"team": k, **v} for k, v in raw.items()]
        return raw
    return []

@app.post("/api/predict")
async def predict(payload: dict):
    team_a   = payload.get("team_a", "")
    team_b   = payload.get("team_b", "")
    seed_a   = float(payload.get("seed_a") or 8)
    seed_b   = float(payload.get("seed_b") or 8)
    ml_a     = payload.get("ml_a")
    bankroll = float(payload.get("bankroll") or 81.81)

    stats = {}
    if TEAMS_FILE.exists():
        raw = json.loads(TEAMS_FILE.read_text())
        stats = raw if isinstance(raw, dict) else {}

    model_file = BASE / "gbm_v2_model.pkl"
    if model_file.exists():
        import pickle, numpy as np
        with open(model_file, "rb") as f: md = pickle.load(f)
        model = md["model"]; scaler = md["scaler"]
        sa = stats.get(team_a, {}); sb = stats.get(team_b, {})
        def fv(s, seed):
            return [s.get("SRS",0), s.get("OffRtg",100), s.get("DefRtg",100),
                    s.get("NetRtg",0), s.get("TOVPct",15), s.get("ORBPct",30),
                    s.get("TSPct",0.52), s.get("STLPct",8), s.get("BLKPct",8),
                    s.get("WinPct",0.5), seed]
        feat = [a-b for a,b in zip(fv(sa,seed_a), fv(sb,seed_b))]
        X = scaler.transform([feat])
        prob_a = float(model.predict_proba(X)[0][1]) * 100
    else:
        sa = stats.get(team_a, {}); sb = stats.get(team_b, {})
        seed_diff = seed_b - seed_a
        srs_diff  = (sa.get("SRS") or 0) - (sb.get("SRS") or 0)
        net_diff  = (sa.get("NetRtg") or 0) - (sb.get("NetRtg") or 0)
        base = 50 + seed_diff * 3.0 + srs_diff * 1.4 + net_diff * 0.8
        # Sanity cap
        srs_b  = sb.get("SRS") or 0
        net_b  = sb.get("NetRtg") or 0
        pas_b  = sb.get("SRS") or 0
        if srs_b > (sa.get("SRS") or 0) + 5 and net_b > (sa.get("NetRtg") or 0) + 8:
            base = min(base, 30)
        prob_a = max(3, min(97, base))

    kelly_fraction = None
    if ml_a:
        ml_a = float(ml_a)
        implied = abs(ml_a)/(abs(ml_a)+100) if ml_a < 0 else 100/(ml_a+100)
        b = (100/abs(ml_a)) if ml_a < 0 else ml_a/100
        p = prob_a / 100; q = 1 - p
        k = (b * p - q) / b
        kelly_fraction = round(max(0, k), 4)

    sa = stats.get(team_a, {})
    return {
        "win_prob_a": round(prob_a, 1),
        "win_prob_b": round(100 - prob_a, 1),
        "kelly_fraction": kelly_fraction,
        "net_rtg_a": sa.get("NetRtg"),
        "srs_a":     sa.get("SRS"),
        "pas_a":     sa.get("SRS"),
        "seed_diff": int(seed_b - seed_a),
        "off_rtg_a": sa.get("OffRtg"),
        "def_rtg_a": sa.get("DefRtg"),
        "win_pct_a": sa.get("WinPct"),
    }

@app.post("/api/seed")
async def seed(data: dict):
    save_data(data)
    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok"}
