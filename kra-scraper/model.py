#!/usr/bin/env python3
"""KRA Horse Racing — Feature Engineering + XGBoost Win Prediction"""

import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score, classification_report, log_loss
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import warnings, pickle, json
warnings.filterwarnings("ignore")

# ─── 1. LOAD ───
print("=" * 60)
print("1. Loading data...")
df = pd.read_csv("kra_seoul_final.csv", encoding="utf-8-sig", dtype=str)
print(f"   Raw: {len(df)} rows, {len(df.columns)} cols")

# ─── 2. CLEAN & TYPE CAST ───
print("\n2. Cleaning & type casting...")

# Parse numeric columns
def to_float(s):
    try:
        return float(str(s).replace(":", "").replace(",", "").strip())
    except:
        return np.nan

def time_to_seconds(s):
    """Convert '0:13.9' or '1:23.1' to seconds."""
    try:
        s = str(s).strip()
        if ":" in s:
            parts = s.split(":")
            return float(parts[0]) * 60 + float(parts[1])
        return float(s)
    except:
        return np.nan

# Core numeric
df["착순"] = pd.to_numeric(df["착순"], errors="coerce")
df["출주번호"] = pd.to_numeric(df["출주번호"], errors="coerce")
df["부담중량"] = pd.to_numeric(df["부담중량"], errors="coerce")
df["마체중"] = pd.to_numeric(df["마체중"], errors="coerce")
df["마체중증감"] = pd.to_numeric(df["마체중증감"], errors="coerce")
df["단승배당"] = pd.to_numeric(df["단승배당"], errors="coerce")
df["연승배당"] = pd.to_numeric(df["연승배당"], errors="coerce")
df["경주번호"] = pd.to_numeric(df["경주번호"], errors="coerce")
df["함수율"] = df["함수율"].str.replace("%", "").apply(to_float)

# Parse 연령 (e.g., "3세" → 3)
df["연령_num"] = df["연령"].str.extract(r"(\d+)").astype(float)

# Parse 거리 (e.g., "1300M" → 1300)
df["거리_num"] = df["거리"].str.extract(r"(\d+)").astype(float)

# Time columns → seconds
time_cols = ["S1F기록", "1C기록", "2C기록", "3C기록", "G3F기록", "4C기록", "G1F기록", "3F_G기록", "1F_G기록", "경주기록"]
for c in time_cols:
    df[c + "_sec"] = df[c].apply(time_to_seconds)

# Parse 통과순위
pass_cols = ["S1F통과순위", "1C통과순위", "2C통과순위", "3C통과순위", "G3F통과순위", "4C통과순위", "G1F통과순위"]
for c in pass_cols:
    df[c + "_num"] = pd.to_numeric(df[c].str.replace("-", "").str.strip(), errors="coerce")

# Date
df["경주일자"] = pd.to_datetime(df["경주일자"], format="%Y%m%d")
df["race_id"] = df["경주일자"].dt.strftime("%Y%m%d") + "_" + df["경주번호"].astype(str)

# Labels
df["win"] = (df["착순"] == 1).astype(int)
df["place"] = (df["착순"] <= 3).astype(int)

# Drop rows without valid 착순
df = df.dropna(subset=["착순"])
print(f"   After cleaning: {len(df)} rows")
print(f"   Win rate: {df['win'].mean():.3f}, Place rate: {df['place'].mean():.3f}")

# ─── 3. CATEGORICAL ENCODING ───
print("\n3. Encoding categoricals...")

cat_cols = {
    "성별": None,
    "산지": None,
    "날씨": None,
    "주로상태": None,
}
encoders = {}
for col in cat_cols:
    le = LabelEncoder()
    df[col + "_enc"] = le.fit_transform(df[col].fillna("UNK").astype(str))
    encoders[col] = le

# 등급 → ordinal
grade_map = {}
for g in df["등급"].unique():
    s = str(g)
    if "1등급" in s: grade_map[g] = 1
    elif "2등급" in s: grade_map[g] = 2
    elif "3등급" in s: grade_map[g] = 3
    elif "4등급" in s: grade_map[g] = 4
    elif "5등급" in s: grade_map[g] = 5
    elif "6등급" in s: grade_map[g] = 6
    elif "오픈" in s or "국제" in s: grade_map[g] = 0
    else: grade_map[g] = 7
df["등급_ord"] = df["등급"].map(grade_map)

# 별정
bj_map = {"별정A": 0, "별정B": 1, "정량": 2, "핸디캡": 3}
df["별정_enc"] = df["별정"].map(bj_map).fillna(4)

# 장구현황 → count of equipment items
df["장구_count"] = df["장구현황"].fillna("").apply(lambda x: len([i for i in x.split(",") if i.strip()]))

# ─── 4. FEATURE ENGINEERING ───
print("\n4. Engineering features...")

# Sort for rolling computations
df = df.sort_values(["마명", "경주일자", "경주번호"]).reset_index(drop=True)

# ── Per-horse historical features ──
def horse_rolling_features(group):
    """Compute rolling stats per horse."""
    g = group.sort_values("경주일자")
    
    # 최근 N전 평균착순
    g["최근3전_평균착순"] = g["착순"].shift(1).rolling(3, min_periods=1).mean()
    g["최근5전_평균착순"] = g["착순"].shift(1).rolling(5, min_periods=1).mean()
    
    # 최근 N전 승률
    g["최근5전_승률"] = g["win"].shift(1).rolling(5, min_periods=1).mean()
    g["최근10전_승률"] = g["win"].shift(1).rolling(10, min_periods=1).mean()
    
    # 최근 N전 3착이내율
    g["최근5전_복승률"] = g["place"].shift(1).rolling(5, min_periods=1).mean()
    
    # 통산 승률 (expanding)
    g["통산_승률"] = g["win"].shift(1).expanding(min_periods=1).mean()
    g["통산_출주수"] = g["win"].shift(1).expanding(min_periods=1).count()
    
    # 마체중 트렌드
    g["체중_3회이동평균"] = g["마체중"].shift(1).rolling(3, min_periods=1).mean()
    g["체중_트렌드"] = g["마체중"] - g["체중_3회이동평균"]
    
    # 최근 경주기록 (seconds)
    g["최근_경주기록"] = g["경주기록_sec"].shift(1)
    g["최근3전_평균기록"] = g["경주기록_sec"].shift(1).rolling(3, min_periods=1).mean()
    
    # G3F (마지막 600m) 평균
    g["최근3전_G3F"] = g["3F_G기록_sec"].shift(1).rolling(3, min_periods=1).mean()
    
    # 휴양일수
    g["이전경주일"] = g["경주일자"].shift(1)
    g["휴양일수"] = (g["경주일자"] - g["이전경주일"]).dt.days
    
    return g

print("   Computing horse rolling features...")
df = df.groupby("마명", group_keys=False).apply(horse_rolling_features)

# ── Per-jockey features ──
print("   Computing jockey features...")
jockey_stats = df.groupby("기수명").apply(
    lambda g: pd.Series({
        "기수_통산승률": g["win"].shift(1).expanding().mean().iloc[-1] if len(g) > 1 else 0,
        "기수_출주수": len(g),
    })
).reset_index()
# Use a simpler approach: compute cumulative jockey win rate up to each date
df = df.sort_values(["기수명", "경주일자"]).reset_index(drop=True)
df["기수_누적승률"] = df.groupby("기수명")["win"].transform(lambda x: x.shift(1).expanding().mean())
df["기수_누적출주"] = df.groupby("기수명")["win"].transform(lambda x: x.shift(1).expanding().count())

# ── Per-trainer features ──
print("   Computing trainer features...")
df = df.sort_values(["조교사명", "경주일자"]).reset_index(drop=True)
df["조교사_누적승률"] = df.groupby("조교사명")["win"].transform(lambda x: x.shift(1).expanding().mean())

# ── Race-level features ──
print("   Computing race-level features...")
df = df.sort_values(["경주일자", "경주번호", "출주번호"]).reset_index(drop=True)

# 경주 내 출전두수
df["출전두수"] = df.groupby("race_id")["출주번호"].transform("count")

# 단승배당 → 시장내재확률
df["시장확률"] = 1 / df["단승배당"].replace(0, np.nan)

# 경주 내 레이팅 순위 (낮을수록 강함 — 배당 기준)
df["배당순위"] = df.groupby("race_id")["단승배당"].rank(method="min")

# 경주 내 마체중 순위
df["체중순위"] = df.groupby("race_id")["마체중"].rank(method="min")

# ── Distance affinity ──
# 해당 거리에서의 과거 성적
print("   Computing distance affinity...")
df["마_거리_key"] = df["마명"] + "_" + df["거리_num"].astype(str)
df = df.sort_values(["마_거리_key", "경주일자"]).reset_index(drop=True)
df["거리별_승률"] = df.groupby("마_거리_key")["win"].transform(lambda x: x.shift(1).expanding().mean())
df["거리별_출주수"] = df.groupby("마_거리_key")["win"].transform(lambda x: x.shift(1).expanding().count())

# ── Jockey-Horse combo ──
print("   Computing jockey-horse combo...")
df["기수마_key"] = df["기수명"] + "_" + df["마명"]
df = df.sort_values(["기수마_key", "경주일자"]).reset_index(drop=True)
df["콤비_승률"] = df.groupby("기수마_key")["win"].transform(lambda x: x.shift(1).expanding().mean())
df["콤비_출주수"] = df.groupby("기수마_key")["win"].transform(lambda x: x.shift(1).expanding().count())

# ─── 5. FEATURE SELECTION ───
print("\n5. Selecting features...")

FEATURES = [
    # Horse basics
    "연령_num", "성별_enc", "산지_enc", "부담중량", "마체중", "마체중증감",
    "장구_count",
    # Race conditions
    "거리_num", "등급_ord", "별정_enc", "경주번호", "출전두수",
    "날씨_enc", "주로상태_enc", "함수율",
    # Market
    "단승배당", "연승배당", "시장확률", "배당순위",
    # Horse history
    "최근3전_평균착순", "최근5전_평균착순",
    "최근5전_승률", "최근10전_승률", "최근5전_복승률",
    "통산_승률", "통산_출주수",
    # Weight trend
    "체중_3회이동평균", "체중_트렌드", "체중순위",
    # Time history
    "최근_경주기록", "최근3전_평균기록", "최근3전_G3F",
    # Section times (current race — only for training, NOT for prediction)
    # We'll exclude these since they're not available pre-race
    # Jockey/Trainer
    "기수_누적승률", "기수_누적출주", "조교사_누적승률",
    # Distance affinity
    "거리별_승률", "거리별_출주수",
    # Jockey-Horse combo
    "콤비_승률", "콤비_출주수",
    # Rest days
    "휴양일수",
    # Pass positions (from PREVIOUS race — shift needed)
]

# Verify all features exist
missing = [f for f in FEATURES if f not in df.columns]
if missing:
    print(f"   WARNING: Missing features: {missing}")
    FEATURES = [f for f in FEATURES if f in df.columns]

print(f"   {len(FEATURES)} features selected")

# ─── 6. TRAIN/TEST SPLIT (Time-based) ───
print("\n6. Time-based train/test split...")

# Use 2025+ as test
train_mask = df["경주일자"] < "2025-01-01"
test_mask = df["경주일자"] >= "2025-01-01"

X_train = df.loc[train_mask, FEATURES].copy()
y_train = df.loc[train_mask, "win"].copy()
X_test = df.loc[test_mask, FEATURES].copy()
y_test = df.loc[test_mask, "win"].copy()

# Also keep place labels
y_train_place = df.loc[train_mask, "place"].copy()
y_test_place = df.loc[test_mask, "place"].copy()

# Fill NaN with -1 for XGBoost
X_train = X_train.fillna(-1)
X_test = X_test.fillna(-1)

print(f"   Train: {len(X_train)} rows ({train_mask.sum()} | {y_train.mean():.3f} win rate)")
print(f"   Test:  {len(X_test)} rows ({test_mask.sum()} | {y_test.mean():.3f} win rate)")

# ─── 7. XGBOOST ───
print("\n7. Training XGBoost...")

# Win model
model_win = xgb.XGBClassifier(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=5,
    reg_alpha=0.1,
    reg_lambda=1.0,
    scale_pos_weight=len(y_train[y_train == 0]) / max(len(y_train[y_train == 1]), 1),
    eval_metric="auc",
    early_stopping_rounds=50,
    random_state=42,
    use_label_encoder=False,
)

model_win.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=50,
)

# Place model
print("\n   Training Place model...")
model_place = xgb.XGBClassifier(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=5,
    eval_metric="auc",
    early_stopping_rounds=50,
    random_state=42,
    use_label_encoder=False,
)

model_place.fit(
    X_train, y_train_place,
    eval_set=[(X_test, y_test_place)],
    verbose=50,
)

# ─── 8. EVALUATION ───
print("\n" + "=" * 60)
print("8. EVALUATION")
print("=" * 60)

# Win predictions
y_pred_win = model_win.predict_proba(X_test)[:, 1]
auc_win = roc_auc_score(y_test, y_pred_win)
ll_win = log_loss(y_test, y_pred_win)

# Place predictions
y_pred_place = model_place.predict_proba(X_test)[:, 1]
auc_place = roc_auc_score(y_test_place, y_pred_place)

print(f"\n   ┌─────────────────────────────────┐")
print(f"   │ WIN MODEL                       │")
print(f"   │   ROC AUC:  {auc_win:.4f}              │")
print(f"   │   Log Loss: {ll_win:.4f}              │")
print(f"   └─────────────────────────────────┘")
print(f"   ┌─────────────────────────────────┐")
print(f"   │ PLACE MODEL                     │")
print(f"   │   ROC AUC:  {auc_place:.4f}              │")
print(f"   └─────────────────────────────────┘")

# ─── 9. FEATURE IMPORTANCE ───
print("\n9. Feature Importance (Top 15):")
imp = model_win.feature_importances_
imp_df = pd.DataFrame({"feature": FEATURES, "importance": imp}).sort_values("importance", ascending=False)
for i, row in imp_df.head(15).iterrows():
    bar = "█" * int(row["importance"] * 100)
    print(f"   {row['feature']:25s} {row['importance']:.4f} {bar}")

# ─── 10. BETTING SIMULATION ───
print("\n" + "=" * 60)
print("10. BETTING SIMULATION (2025~2026 Test Set)")
print("=" * 60)

test_df = df.loc[test_mask].copy()
test_df["pred_win_prob"] = y_pred_win
test_df["시장확률_clean"] = 1 / test_df["단승배당"].replace(0, np.nan)

# Kelly Criterion
test_df["edge"] = test_df["pred_win_prob"] - test_df["시장확률_clean"]
test_df["kelly_fraction"] = ((test_df["단승배당"] - 1) * test_df["pred_win_prob"] - (1 - test_df["pred_win_prob"])) / (test_df["단승배당"] - 1)
test_df["kelly_fraction"] = test_df["kelly_fraction"].clip(0, 0.1)  # Cap at 10%

# Only bet when we have positive edge
bets = test_df[test_df["edge"] > 0.05].copy()  # min 5% edge
print(f"\n   Total test races (horse-level): {len(test_df)}")
print(f"   Bets placed (edge > 5%): {len(bets)}")

if len(bets) > 0:
    # Flat betting simulation
    wins = bets["win"].sum()
    total_bets = len(bets)
    hit_rate = wins / total_bets
    avg_odds = bets.loc[bets["win"] == 1, "단승배당"].mean() if wins > 0 else 0
    
    # ROI calculation (flat 1 unit per bet)
    total_wagered = total_bets
    total_return = (bets.loc[bets["win"] == 1, "단승배당"]).sum()
    roi = (total_return - total_wagered) / total_wagered * 100
    
    # Kelly-weighted
    bets["kelly_wager"] = bets["kelly_fraction"] * 1000  # 1000 unit bankroll
    bets["kelly_return"] = bets["kelly_wager"] * bets["단승배당"] * bets["win"]
    kelly_roi = (bets["kelly_return"].sum() - bets["kelly_wager"].sum()) / bets["kelly_wager"].sum() * 100
    
    print(f"\n   ┌─ FLAT BETTING ─────────────────┐")
    print(f"   │ Hit Rate: {hit_rate:.1%} ({wins}/{total_bets})     │")
    print(f"   │ Avg Win Odds: {avg_odds:.1f}x             │")
    print(f"   │ ROI: {roi:+.1f}%                       │")
    print(f"   └─────────────────────────────────┘")
    print(f"   ┌─ KELLY BETTING ─────────────────┐")
    print(f"   │ Kelly ROI: {kelly_roi:+.1f}%                │")
    print(f"   │ Total Wagered: {bets['kelly_wager'].sum():.0f} units    │")
    print(f"   │ Total Return:  {bets['kelly_return'].sum():.0f} units    │")
    print(f"   └─────────────────────────────────┘")
    
    # Edge distribution
    print(f"\n   Edge Distribution:")
    for threshold in [0.05, 0.10, 0.15, 0.20]:
        sub = test_df[test_df["edge"] > threshold]
        if len(sub) > 0:
            w = sub["win"].sum()
            n = len(sub)
            ret = sub.loc[sub["win"] == 1, "단승배당"].sum()
            r = (ret - n) / n * 100
            print(f"     Edge>{threshold:.0%}: {n} bets, {w} wins ({w/n:.1%}), ROI {r:+.1f}%")

# ─── 11. SAVE ───
print("\n11. Saving models...")
pickle.dump(model_win, open("model_win.pkl", "wb"))
pickle.dump(model_place, open("model_place.pkl", "wb"))
imp_df.to_csv("feature_importance.csv", index=False)
print("   Saved: model_win.pkl, model_place.pkl, feature_importance.csv")

print("\n" + "=" * 60)
print("DONE!")
print("=" * 60)
