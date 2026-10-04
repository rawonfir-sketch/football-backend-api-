import math
import json
import os
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Football Analytics & Prediction Engine")

# File Logging Directory
LOG_DIR = "match_logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

class MatchInput(BaseModel):
    match_id: str
    home_team: str
    away_team: str
    home_avg_corners: float
    away_avg_corners: float
    home_cards_last5: list[int]
    away_cards_last5: list[int]
    h2h_avg_cards: float
    home_avg_possession: float
    away_avg_possession: float
    market_555_home: float
    market_555_draw: float
    market_555_away: float
    xbet_home: float
    xbet_draw: float
    xbet_away: float

@app.post("/api/analyze")
def analyze_match(data: MatchInput):
    # Corner Calculation
    more_corners = data.home_team if data.home_avg_corners > data.away_avg_corners else data.away_team
    total_corners = round(data.home_avg_corners + data.away_avg_corners, 1)

    # Yellow Card Calculation
    home_cards_avg = sum(data.home_cards_last5) / len(data.home_cards_last5)
    away_cards_avg = sum(data.away_cards_last5) / len(data.away_cards_last5)
    total_predicted_cards = round((home_cards_avg + away_cards_avg + data.h2h_avg_cards) / 2, 1)

    # Possession Calculation
    pos_sum = data.home_avg_possession + data.away_avg_possession
    home_pos = round((data.home_avg_possession / pos_sum) * 100, 1)
    away_pos = round(100 - home_pos, 1)

    # Value Bet Analysis (555 Mix vs 1xBet)
    home_gap = round(((1 / data.xbet_home) - (1 / data.market_555_home)) * 100, 2)
    away_gap = round(((1 / data.xbet_away) - (1 / data.market_555_away)) * 100, 2)
    
    value_bet = "NEUTRAL"
    if home_gap > 3.0:
        value_bet = f"VALUE ON {data.home_team} (1xBet Better)"
    elif away_gap > 3.0:
        value_bet = f"VALUE ON {data.away_team} (1xBet Better)"

    result = {
        "match_id": data.match_id,
        "timestamp": datetime.utcnow().isoformat(),
        "teams": {"home": data.home_team, "away": data.away_team},
        "corners": {"more_corners_team": more_corners, "expected_total": total_corners},
        "cards": {"home_last5_avg": round(home_cards_avg, 1), "away_last5_avg": round(away_cards_avg, 1), "predicted_cards": total_predicted_cards},
        "possession": {"home_pct": home_pos, "away_pct": away_pos},
        "value_bet_recommendation": value_bet
    }

    # Auto Save Log File
    log_file = os.path.join(LOG_DIR, f"{data.match_id}_{data.home_team}_vs_{data.away_team}.json")
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    return {"status": "SUCCESS", "saved_log": log_file, "data": result}
