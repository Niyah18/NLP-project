import pandas as pd
import difflib
import random

# ============================================
# 1. LOAD DATASET
# ============================================

df = pd.read_csv("ball_by_ball_ipl.csv")

# Fix column names to match this dataset
df = df.rename(columns={
    "batter": "Batter",
    "bowler": "Bowler",
    "batsman_run": "Batter Runs",
    "total_run": "Runs From Ball",
    "isWicketDelivery": "Wicket",
    "ID": "Match ID"
})

# Valid Ball = all deliveries
df["Valid Ball"] = True
df["Wicket"] = df["Wicket"].astype(int)
df["Ball"] = 1

batters = df["Batter"].dropna().unique().tolist()
bowlers = df["Bowler"].dropna().unique().tolist()

# ============================================
# 2. INTENT PATTERNS
# ============================================

INTENT_PATTERNS = {
    "recommend_bowler": [
        "who should bowl",
        "best bowler",
        "bowling option",
        "who can stop",
        "bowler for",
        "bowl against",
        "best bowling",
        "which bowler",
        "how to stop"
    ],
    "recommend_batsman": [
        "who should bat",
        "best batsman",
        "batting option",
        "who can face",
        "batsman against",
        "best batting",
        "who should face",
        "who to send"
    ],
    "player_performance": [
        "performance",
        "stats",
        "record",
        "history",
        "how has",
        "career",
        "show",
        "analysis"
    ]
}

# ============================================
# 3. INTENT CLASSIFICATION
# ============================================

def classify_intent(query):
    q = query.lower()
    scores = {
        "recommend_bowler": 0,
        "recommend_batsman": 0,
        "player_performance": 0
    }
    for intent, patterns in INTENT_PATTERNS.items():
        for p in patterns:
            if p in q:
                scores[intent] += 2
    if "bowl" in q or "bowler" in q:
        scores["recommend_bowler"] += 1
    if "bat" in q or "batsman" in q or "face" in q:
        scores["recommend_batsman"] += 1
    if "stat" in q or "record" in q or "performance" in q:
        scores["player_performance"] += 1
    best_intent = max(scores, key=scores.get)
    return best_intent if scores[best_intent] > 0 else "unknown"

# ============================================
# 4. ENTITY EXTRACTION
# ============================================

def extract_entity(query, entity_list):
    q = query.lower()
    for e in entity_list:
        if e.lower() in q:
            return e
    matches = difflib.get_close_matches(
        q, [e.lower() for e in entity_list], n=1, cutoff=0.6
    )
    if matches:
        return next(e for e in entity_list if e.lower() == matches[0])
    words = q.split()
    mapping = {e.lower(): e for e in entity_list}
    for word in words:
        match = difflib.get_close_matches(word, mapping.keys(), n=1, cutoff=0.75)
        if match:
            return mapping[match[0]]
    return None

# ============================================
# 5. BEST BOWLER vs BATSMAN
# ============================================

def recommend_best_bowler_vs_batsman(df, batsman):
    filtered = df[(df["Batter"] == batsman) & (df["Valid Ball"])]
    stats = filtered.groupby("Bowler").agg(
        runs=("Runs From Ball", "sum"),
        balls=("Ball", "count"),
        wickets=("Wicket", "sum")
    ).reset_index()
    stats["Overs"] = stats["balls"] / 6
    stats["Economy"] = stats["runs"] / stats["Overs"]
    return stats.sort_values(
        by=["wickets", "Economy"], ascending=[False, True]
    ).iloc[0]

def explain_best_bowler(batsman, r):
    confidence = min(95, 60 + int(r["wickets"]) * 5)
    interpretations = [
        f"{r['Bowler']} has consistently disrupted {batsman}'s scoring rhythm.",
        f"The matchup data favors {r['Bowler']} with wicket-taking ability.",
        f"{batsman} has struggled to score freely against {r['Bowler']}.",
        f"This head-to-head shows {r['Bowler']}'s tactical dominance."
    ]
    result = "==================================================\n"
    result += "CRICKET STRATEGY DECISION | BOWLING MATCHUP\n"
    result += "==================================================\n\n"
    result += f"RECOMMENDED BOWLER\n"
    result += f"Name              : {r['Bowler']}\n"
    result += f"Confidence Index  : {confidence}%\n\n"
    result += f"HEAD-TO-HEAD METRICS\n"
    result += f"Batsman Faced     : {batsman}\n"
    result += f"Wickets Taken     : {int(r['wickets'])}\n"
    result += f"Economy Rate      : {r['Economy']:.2f}\n\n"
    result += f"MATCHUP INTERPRETATION\n"
    result += f"{random.choice(interpretations)}\n\n"
    result += f"TACTICAL RECOMMENDATION\n"
    result += f"Use {r['Bowler']} during powerplay or middle overs.\n"
    result += "=================================================="
    return result

# ============================================
# 6. BEST BATSMAN vs BOWLER
# ============================================

def recommend_best_batsman_vs_bowler(df, bowler, min_balls=6):
    filtered = df[(df["Bowler"] == bowler) & (df["Valid Ball"])]
    stats = filtered.groupby("Batter").agg(
        runs=("Batter Runs", "sum"),
        balls=("Ball", "count"),
        dismissals=("Wicket", "sum")
    ).reset_index()
    stats = stats[stats["balls"] >= min_balls]
    if stats.empty:
        return None
    stats["Strike Rate"] = (stats["runs"] / stats["balls"]) * 100
    return stats.sort_values(
        by=["Strike Rate", "dismissals"], ascending=[False, True]
    ).iloc[0]

def explain_best_batsman(bowler, r):
    confidence = min(95, int(r["Strike Rate"] // 2))
    interpretations = [
        f"{r['Batter']} scores freely against {bowler} with minimal risk.",
        f"The data indicates {r['Batter']} reads {bowler} exceptionally well.",
        f"{bowler} has struggled to contain {r['Batter']}.",
        f"This matchup strongly favors {r['Batter']}."
    ]
    result = "==================================================\n"
    result += "CRICKET STRATEGY DECISION | BATTING MATCHUP\n"
    result += "==================================================\n\n"
    result += f"RECOMMENDED BATSMAN\n"
    result += f"Name              : {r['Batter']}\n"
    result += f"Confidence Index  : {confidence}%\n\n"
    result += f"HEAD-TO-HEAD METRICS\n"
    result += f"Bowler Faced      : {bowler}\n"
    result += f"Strike Rate       : {r['Strike Rate']:.2f}\n"
    result += f"Times Dismissed   : {int(r['dismissals'])}\n\n"
    result += f"MATCHUP INTERPRETATION\n"
    result += f"{random.choice(interpretations)}\n\n"
    result += f"TACTICAL RECOMMENDATION\n"
    result += f"Promote {r['Batter']} when {bowler} is bowling.\n"
    result += "=================================================="
    return result

# ============================================
# 7. PLAYER PERFORMANCE
# ============================================

def player_performance(df, player):
    filtered = df[(df["Batter"] == player) & (df["Valid Ball"])]
    runs = filtered["Batter Runs"].sum()
    balls = filtered["Ball"].count()
    matches = filtered["Match ID"].nunique()
    sr = (runs / balls) * 100 if balls else 0
    efficiency = "High" if sr >= 130 else "Moderate" if sr >= 110 else "Low"
    result = "==================================================\n"
    result += "PLAYER PERFORMANCE PROFILE\n"
    result += "==================================================\n\n"
    result += f"Player Name        : {player}\n"
    result += f"Matches Analyzed   : {matches}\n\n"
    result += f"CORE METRICS\n"
    result += f"Total Runs         : {runs}\n"
    result += f"Balls Faced        : {balls}\n"
    result += f"Strike Rate        : {sr:.2f}\n\n"
    result += f"ASSESSMENT\n"
    result += f"Scoring Efficiency : {efficiency}\n"
    result += "=================================================="
    return result

# ============================================
# 8. QUERY ROUTER
# ============================================

def process_query(query):
    intent = classify_intent(query)
    if intent == "recommend_bowler":
        batsman = extract_entity(query, batters)
        if not batsman:
            return "❌ Could not identify the batsman."
        return explain_best_bowler(batsman,
               recommend_best_bowler_vs_batsman(df, batsman))
    elif intent == "recommend_batsman":
        bowler = extract_entity(query, bowlers)
        if not bowler:
            return "❌ Could not identify the bowler."
        result = recommend_best_batsman_vs_bowler(df, bowler)
        if result is None:
            return "❌ Not enough data for this bowler."
        return explain_best_batsman(bowler, result)
    elif intent == "player_performance":
        player = extract_entity(query, batters)
        if not player:
            return "❌ Could not identify the player."
        return player_performance(df, player)
    else:
        return "⚠️ Unable to understand the query. Try rephrasing."
