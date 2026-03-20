from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json, pathlib

app = FastAPI(title="EDGE Terminal")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
BASE = pathlib.Path(__file__).parent
STATIC = BASE / "apps" / "web" / "static"
DATA_FILE  = BASE / "data.json"
TEAMS_FILE = BASE / "all_stats.json"

app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

@app.get("/")
async def root():
    return FileResponse(str(STATIC / "index.html"))

# ── in-memory store — seeded from data.json at startup ───────────────────────
_store = None

def get_store():
    global _store
    if _store is None:
        if DATA_FILE.exists():
            try:
                _store = json.loads(DATA_FILE.read_text())
            except Exception as e:
                print(f"data.json load error: {e}")
                _store = _empty()
        else:
            _store = _empty()
    return _store

def _empty():
    return {"bets": [], "games": [], "balance": 81.81, "balance_history": [81.81]}

def save(d):
    global _store
    _store = d
    try:
        DATA_FILE.write_text(json.dumps(d, indent=2))
    except Exception as e:
        print(f"save error: {e}")

# ── summary ───────────────────────────────────────────────────────────────────
@app.get("/api/summary")
async def summary():
    d = get_store()
    bets = d.get("bets", [])
    wins    = sum(1 for b in bets if b.get("result") == "Win")
    losses  = sum(1 for b in bets if b.get("result") == "Loss")
    wagered = sum(float(b.get("bet_amount", 0)) for b in bets if b.get("result") in ["Win","Loss","Push"])
    net_pl  = sum(float(b.get("profit_loss", 0)) for b in bets)
    settled = wins + losses + sum(1 for b in bets if b.get("result") == "Push")
    mc      = sum(1 for b in bets if b.get("model_correct") in [True, "Yes", "\u2705 Yes"])
    model_acc = round(mc / settled * 100, 1) if settled else 89.6
    return {
        "balance":         d.get("balance", 81.81),
        "balance_history": d.get("balance_history", [81.81]),
        "wins": wins, "losses": losses,
        "net_pl":          round(net_pl, 2),
        "total_wagered":   round(wagered, 2),
        "model_accuracy":  model_acc,
    }

# ── games ─────────────────────────────────────────────────────────────────────
@app.get("/api/games")
async def get_games():
    return get_store().get("games", [])

@app.post("/api/games")
async def add_game(game: dict):
    d = get_store(); d["games"].append(game); save(d)
    return {"ok": True}

# ── bets ──────────────────────────────────────────────────────────────────────
@app.get("/api/bets")
async def get_bets():
    return get_store().get("bets", [])

@app.post("/api/bets")
async def add_bet(bet: dict):
    d = get_store(); d["bets"].append(bet)
    d["balance"] = round(101.41 + sum(float(b.get("profit_loss", 0)) for b in d["bets"]), 2)
    d["balance_history"].append(d["balance"])
    save(d); return {"ok": True, "balance": d["balance"]}

@app.put("/api/bets/{idx}")
async def update_bet(idx: int, updates: dict):
    d = get_store()
    if 0 <= idx < len(d["bets"]):
        d["bets"][idx].update(updates)
        d["balance"] = round(101.41 + sum(float(b.get("profit_loss", 0)) for b in d["bets"]), 2)
        d["balance_history"].append(d["balance"])
        save(d)
    return {"ok": True}

# ── teams ─────────────────────────────────────────────────────────────────────
@app.get("/api/teams")
async def get_teams():
    if TEAMS_FILE.exists():
        raw = json.loads(TEAMS_FILE.read_text())
        if isinstance(raw, dict):
            return [{"team": k, **v} for k, v in raw.items()]
        return raw
    return []

# ── predict ───────────────────────────────────────────────────────────────────
@app.post("/api/predict")
async def predict(payload: dict):
    team_a = payload.get("team_a", ""); team_b = payload.get("team_b", "")
    seed_a = float(payload.get("seed_a") or 8); seed_b = float(payload.get("seed_b") or 8)
    ml_a   = payload.get("ml_a"); bankroll = float(payload.get("bankroll") or 81.81)

    stats = {}
    if TEAMS_FILE.exists():
        raw = json.loads(TEAMS_FILE.read_text())
        stats = raw if isinstance(raw, dict) else {}

    model_file = BASE / "gbm_v2_model.pkl"
    if model_file.exists():
        import pickle, numpy as np
        with open(model_file, "rb") as f: md = pickle.load(f)
        sa = stats.get(team_a, {}); sb = stats.get(team_b, {})
        def fv(s, seed): return [s.get("SRS",0), s.get("OffRtg",100), s.get("DefRtg",100),
            s.get("NetRtg",0), s.get("TOVPct",15), s.get("ORBPct",30),
            s.get("TSPct",0.52), s.get("STLPct",8), s.get("BLKPct",8),
            s.get("WinPct",0.5), seed]
        feat = [a-b for a,b in zip(fv(sa,seed_a), fv(sb,seed_b))]
        X = md["scaler"].transform([feat])
        prob_a = float(md["model"].predict_proba(X)[0][1]) * 100
    else:
        sa = stats.get(team_a, {}); sb = stats.get(team_b, {})
        base = (50
            + (seed_b - seed_a) * 3.0
            + ((sa.get("SRS") or 0) - (sb.get("SRS") or 0)) * 1.4
            + ((sa.get("NetRtg") or 0) - (sb.get("NetRtg") or 0)) * 0.8)
        # sanity cap
        if ((sb.get("SRS") or 0) > (sa.get("SRS") or 0) + 5 and
            (sb.get("NetRtg") or 0) > (sa.get("NetRtg") or 0) + 8):
            base = min(base, 30)
        prob_a = max(3, min(97, base))

    kelly_fraction = None
    if ml_a:
        ml = float(ml_a)
        implied = abs(ml)/(abs(ml)+100) if ml < 0 else 100/(ml+100)
        b = (100/abs(ml)) if ml < 0 else ml/100
        k = (b*(prob_a/100) - (1-prob_a/100)) / b
        kelly_fraction = round(max(0, k), 4)

    sa = stats.get(team_a, {})
    return {"win_prob_a": round(prob_a,1), "win_prob_b": round(100-prob_a,1),
            "kelly_fraction": kelly_fraction, "net_rtg_a": sa.get("NetRtg"),
            "srs_a": sa.get("SRS"), "pas_a": sa.get("SRS"),
            "seed_diff": int(seed_b-seed_a), "off_rtg_a": sa.get("OffRtg"),
            "def_rtg_a": sa.get("DefRtg"), "win_pct_a": sa.get("WinPct")}

# ── seed (bulk replace) ───────────────────────────────────────────────────────
@app.post("/api/seed")
async def seed(data: dict):
    save(data); return {"ok": True, "bets": len(data.get("bets",[])), "games": len(data.get("games",[]))}

# ── health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    d = get_store()
    return {"status": "ok", "bets": len(d.get("bets",[])), "games": len(d.get("games",[]))}
