from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json, os, pathlib

app = FastAPI(title="EDGE Terminal")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
BASE = pathlib.Path(__file__).parent

app.mount("/static", StaticFiles(directory=BASE / "apps/web/static"), name="static")

@app.get("/")
async def root():
    return FileResponse(BASE / "apps/web/static/index.html")

DATA_FILE = BASE / "data.json"

SEED_DATA = {"bets":[{"matchup":"Ohio State vs TCU","pick":"Ohio State -8.5","bet_type":"Spread","odds":"-110","bet_amount":5.12,"result":"Pending","profit_loss":0,"model_correct":null,"running_balance":101.41},{"matchup":"Michigan vs Howard","pick":"Michigan -29.5","bet_type":"Spread","odds":"-110","bet_amount":2.5,"result":"Pending","profit_loss":0,"model_correct":null,"running_balance":101.41},{"matchup":"Wisconsin vs High Point","pick":"Wisconsin -10.5","bet_type":"Spread","odds":"-110","bet_amount":3.21,"result":"Pending","profit_loss":0,"model_correct":null,"running_balance":101.41},{"matchup":"Vanderbilt vs McNeese","pick":"Vanderbilt -12.5","bet_type":"Spread","odds":"-110","bet_amount":2.88,"result":"Pending","profit_loss":0,"model_correct":null,"running_balance":101.41},{"matchup":"Nebraska vs Troy","pick":"Nebraska -17.5","bet_type":"Spread","odds":"-110","bet_amount":2.5,"result":"Pending","profit_loss":0,"model_correct":null,"running_balance":101.41},{"matchup":"North Carolina vs VCU","pick":"VCU +3","bet_type":"Spread","odds":"-110","bet_amount":1.74,"result":"Pending","profit_loss":0,"model_correct":null,"running_balance":101.41},{"matchup":"Saint Mary's vs Texas A&M","pick":"Saint Mary's ML","bet_type":"Moneyline","odds":"-190","bet_amount":2.17,"result":"Pending","profit_loss":0,"model_correct":null,"running_balance":101.41},{"matchup":"Georgia vs Saint Louis","pick":"Saint Louis ML","bet_type":"Moneyline","odds":"+175","bet_amount":0.87,"result":"Pending","profit_loss":0,"model_correct":null,"running_balance":101.41},{"matchup":"Louisville vs South Florida","pick":"South Florida ML","bet_type":"Moneyline","odds":"+310","bet_amount":0.87,"result":"Pending","profit_loss":0,"model_correct":null,"running_balance":101.41},{"matchup":"BYU vs Texas","pick":"Texas ML","bet_type":"Moneyline","odds":"-130","bet_amount":1.74,"result":"Pending","profit_loss":0,"model_correct":null,"running_balance":101.41}],"games":[{"game":"Ohio State vs TCU","team_a":"Ohio State","team_b":"TCU","seed_a":3,"seed_b":14,"model_prob_a":88.9,"dk_spread_a":-8.5,"dk_ml_a":-400,"round":"R64","game_time":"12:15 PM ET","status":"upcoming","injury_flag":false},{"game":"Michigan vs Howard","team_a":"Michigan","team_b":"Howard","seed_a":1,"seed_b":16,"model_prob_a":98.1,"dk_spread_a":-29.5,"dk_ml_a":-10000,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"Wisconsin vs High Point","team_a":"Wisconsin","team_b":"High Point","seed_a":5,"seed_b":12,"model_prob_a":78.3,"dk_spread_a":-10.5,"dk_ml_a":-350,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"Vanderbilt vs McNeese","team_a":"Vanderbilt","team_b":"McNeese","seed_a":5,"seed_b":12,"model_prob_a":72.1,"dk_spread_a":-12.5,"dk_ml_a":-700,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"Nebraska vs Troy","team_a":"Nebraska","team_b":"Troy","seed_a":4,"seed_b":13,"model_prob_a":91.2,"dk_spread_a":-17.5,"dk_ml_a":-900,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"Duke vs Siena","team_a":"Duke","team_b":"Siena","seed_a":1,"seed_b":16,"model_prob_a":98.4,"dk_spread_a":-28.5,"dk_ml_a":-5000,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":true},{"game":"BYU vs Texas","team_a":"BYU","team_b":"Texas","seed_a":6,"seed_b":11,"model_prob_a":44.1,"dk_spread_a":2.5,"dk_ml_a":110,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":true},{"game":"North Carolina vs VCU","team_a":"North Carolina","team_b":"VCU","seed_a":4,"seed_b":13,"model_prob_a":52.3,"dk_spread_a":-3.0,"dk_ml_a":-165,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":true},{"game":"Saint Mary's vs Texas A&M","team_a":"Saint Mary's","team_b":"Texas A&M","seed_a":5,"seed_b":12,"model_prob_a":61.4,"dk_spread_a":-3.5,"dk_ml_a":-190,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"Georgia vs Saint Louis","team_a":"Georgia","team_b":"Saint Louis","seed_a":6,"seed_b":11,"model_prob_a":32.1,"dk_spread_a":4.5,"dk_ml_a":175,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"Houston vs Idaho","team_a":"Houston","team_b":"Idaho","seed_a":2,"seed_b":15,"model_prob_a":97.8,"dk_spread_a":-27.5,"dk_ml_a":-5000,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"Michigan State vs North Dakota State","team_a":"Michigan State","team_b":"North Dakota State","seed_a":4,"seed_b":13,"model_prob_a":90.5,"dk_spread_a":-16.5,"dk_ml_a":-800,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"Illinois vs Penn","team_a":"Illinois","team_b":"Penn","seed_a":3,"seed_b":14,"model_prob_a":87.6,"dk_spread_a":-13.5,"dk_ml_a":-500,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"Louisville vs South Florida","team_a":"Louisville","team_b":"South Florida","seed_a":7,"seed_b":10,"model_prob_a":17.1,"dk_spread_a":8.5,"dk_ml_a":310,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":true},{"game":"Arkansas vs Hawaii","team_a":"Arkansas","team_b":"Hawaii","seed_a":4,"seed_b":13,"model_prob_a":89.3,"dk_spread_a":-15.5,"dk_ml_a":-800,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"Gonzaga vs Kennesaw State","team_a":"Gonzaga","team_b":"Kennesaw State","seed_a":4,"seed_b":13,"model_prob_a":83.2,"dk_spread_a":-12.5,"dk_ml_a":-550,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":true},{"game":"Florida vs Prairie View A&M","team_a":"Florida","team_b":"Prairie View A&M","seed_a":2,"seed_b":15,"model_prob_a":96.1,"dk_spread_a":-28.5,"dk_ml_a":-4000,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"Tennessee vs Miami (OH)","team_a":"Tennessee","team_b":"Miami (OH)","seed_a":2,"seed_b":15,"model_prob_a":95.4,"dk_spread_a":-22.5,"dk_ml_a":-3500,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"Iowa State vs Tennessee State","team_a":"Iowa State","team_b":"Tennessee State","seed_a":2,"seed_b":15,"model_prob_a":96.8,"dk_spread_a":-26.5,"dk_ml_a":-4500,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"Alabama vs Hofstra","team_a":"Alabama","team_b":"Hofstra","seed_a":3,"seed_b":14,"model_prob_a":89.0,"dk_spread_a":-15.5,"dk_ml_a":-600,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":true},{"game":"Clemson vs Iowa","team_a":"Clemson","team_b":"Iowa","seed_a":7,"seed_b":10,"model_prob_a":46.2,"dk_spread_a":1.5,"dk_ml_a":105,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"Miami (FL) vs Missouri","team_a":"Miami (FL)","team_b":"Missouri","seed_a":7,"seed_b":10,"model_prob_a":51.8,"dk_spread_a":-1.5,"dk_ml_a":-125,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false},{"game":"UCLA vs UCF","team_a":"UCLA","team_b":"UCF","seed_a":6,"seed_b":11,"model_prob_a":58.3,"dk_spread_a":-4.5,"dk_ml_a":-230,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":true},{"game":"Villanova vs Utah State","team_a":"Villanova","team_b":"Utah State","seed_a":8,"seed_b":9,"model_prob_a":48.2,"dk_spread_a":0.5,"dk_ml_a":105,"round":"R64","game_time":"TBD","status":"upcoming","injury_flag":false}],"balance":101.41,"balance_history":[101.41]}

def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except: pass
    return json.loads(SEED_DATA)

def save_data(d):
    DATA_FILE.write_text(json.dumps(d, indent=2))

@app.get("/api/summary")
async def summary():
    d = load_data()
    bets = d.get("bets", [])
    wins   = sum(1 for b in bets if b.get("result") == "Win")
    losses = sum(1 for b in bets if b.get("result") == "Loss")
    wagered = sum(float(b.get("bet_amount", 0)) for b in bets if b.get("result") not in [None,"Pending"])
    net_pl  = sum(float(b.get("profit_loss", 0)) for b in bets)
    settled = sum(1 for b in bets if b.get("result") in ["Win","Loss","Push"])
    model_correct = sum(1 for b in bets if b.get("model_correct") in [True,"Yes","\u2705 Yes"])
    model_acc = (model_correct / settled * 100) if settled else 89.6
    return {"balance": d.get("balance", 101.41), "balance_history": d.get("balance_history", [101.41]),
            "wins": wins, "losses": losses, "net_pl": round(net_pl,2),
            "total_wagered": round(wagered,2), "model_accuracy": round(model_acc,1)}

@app.get("/api/games")
async def get_games():
    return load_data().get("games", [])

@app.post("/api/games")
async def add_game(game: dict):
    d = load_data(); d["games"].append(game); save_data(d)
    return {"ok": True}

@app.get("/api/bets")
async def get_bets():
    return load_data().get("bets", [])

@app.post("/api/bets")
async def add_bet(bet: dict):
    d = load_data(); d["bets"].append(bet)
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

@app.get("/api/teams")
async def get_teams():
    teams_file = BASE / "all_stats.json"
    if teams_file.exists():
        raw = json.loads(teams_file.read_text())
        if isinstance(raw, dict):
            return [{"team": k, **v} for k, v in raw.items()]
        return raw
    return []

@app.post("/api/predict")
async def predict(payload: dict):
    team_a = payload.get("team_a", ""); team_b = payload.get("team_b", "")
    seed_a = payload.get("seed_a") or 8; seed_b = payload.get("seed_b") or 8
    ml_a = payload.get("ml_a"); bankroll = float(payload.get("bankroll", 101.41))
    d = load_data(); teams_file = BASE / "all_stats.json"
    stats = {}
    if teams_file.exists():
        raw = json.loads(teams_file.read_text())
        stats = raw if isinstance(raw, dict) else {}
    model_file = BASE / "gbm_v2_model.pkl"
    if model_file.exists():
        import pickle, numpy as np
        with open(model_file,"rb") as f: md = pickle.load(f)
        model=md["model"]; scaler=md["scaler"]
        sa=stats.get(team_a,{}); sb=stats.get(team_b,{})
        def fv(s,seed): return [s.get("SRS",0),s.get("OffRtg",100),s.get("DefRtg",100),s.get("NetRtg",0),s.get("TOVPct",15),s.get("ORBPct",30),s.get("TSPct",0.52),s.get("STLPct",8),s.get("BLKPct",8),s.get("WinPct",0.5),seed]
        feat=[a-b for a,b in zip(fv(sa,seed_a),fv(sb,seed_b))]
        X=scaler.transform([feat]); prob_a=float(model.predict_proba(X)[0][1])*100
    else:
        seed_diff=float(seed_b)-float(seed_a)
        sa=stats.get(team_a,{}); sb=stats.get(team_b,{})
        base=50+seed_diff*3.2+(sa.get("SRS",0)-sb.get("SRS",0))*1.5
        prob_a=max(5,min(95,base))
    kelly_fraction=None
    if ml_a:
        ml_a=float(ml_a); implied=abs(ml_a)/(abs(ml_a)+100) if ml_a<0 else 100/(ml_a+100)
        b=(100/abs(ml_a)) if ml_a<0 else ml_a/100; p=prob_a/100; q=1-p
        k=(b*p-q)/b; kelly_fraction=round(max(0,k),4)
    sa=stats.get(team_a,{})
    return {"win_prob_a":round(prob_a,1),"win_prob_b":round(100-prob_a,1),"kelly_fraction":kelly_fraction,
            "net_rtg_a":sa.get("NetRtg"),"srs_a":sa.get("SRS"),"pas_a":sa.get("PAS"),"seed_diff":int(seed_b)-int(seed_a)}

@app.post("/api/seed")
async def seed(data: dict):
    save_data(data); return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok"}
