#!/usr/bin/env python3
"""KRA V2 — Pure Skill Model (no market features) + Edge Detection"""

import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, log_loss
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import warnings, pickle
warnings.filterwarnings("ignore")

# ─── 1. LOAD ───
print("=" * 60)
print("KRA V2 — Pure Skill Model")
print("=" * 60)
print("\n1. Loading data...")
df = pd.read_csv("kra_seoul_final.csv", encoding="utf-8-sig", dtype=str)
print(f"   Raw: {len(df)} rows, {len(df.columns)} cols")

# ─── 2. CLEAN & TYPE CAST (same as V1) ───
print("\n2. Cleaning & type casting...")

def to_float(s):
    try:
        return float(str(s).replace(":", "").replace(",", "").strip())
    except:
        return np.nan

def time_to_seconds(s):
    try:
        s = str(s).strip()
        if ":" in s:
            parts = s.split(":")
            return float(parts[0]) * 60 + float(parts[1])
        return float(s)
    except:
        return np.nan

df["착순"] = pd.to_numeric(df["착순"], errors="coerce")
df["출주번호"] = pd.to_numeric(df["출주번호"], errors="coerce")
df["부담중량"] = pd.to_numeric(df["부담중량"], errors="coerce")
df["마체중"] = pd.to_numeric(df["마체중"], errors="coerce")
df["마체중증감"] = pd.to_numeric(df["마체중증감"], errors="coerce")
df["단승배당"] = pd.to_numeric(df["단승배당"], errors="coerce")
df["연승배당"] = pd.to_numeric(df["연승배당"], errors="coerce")
df["경주번호"] = pd.to_numeric(df["경주번호"], errors="coerce")
df["함수율"] = df["함수율"].str.replace("%", "").apply(to_float)

df["연령_num"] = df["연령"].str.extract(r"(\d+)").astype(float)
df["거리_num"] = df["거리"].str.extract(r"(\d+)").astype(float)

time_cols = ["S1F기록", "1C기록", "2C기록", "3C기록", "G3F기록", "4C기록", "G1F기록", "3F_G기록", "1F_G기록", "경주기록"]
for c in time_cols:
    df[c + "_sec"] = df[c].apply(time_to_seconds)

pass_cols = ["S1F통과순위", "1C통과순위", "2C통과순위", "3C통과순위", "G3F통과순위", "4C통과순위", "G1F통과순위"]
for c in pass_cols:
    df[c + "_num"] = pd.to_numeric(df[c].str.replace("-", "").str.strip(), errors="coerce")

df["경주일자"] = pd.to_datetime(df["경주일자"], format="%Y%m%d")
df["race_id"] = df["경주일자"].dt.strftime("%Y%m%d") + "_" + df["경주번호"].astype(str)

df["win"] = (df["착순"] == 1).astype(int)
df["place"] = (df["착순"] <= 3).astype(int)
df = df.dropna(subset=["착순"])
print(f"   After cleaning: {len(df)} rows")

# ─── 3. CATEGORICAL ENCODING ───
print("\n3. Encoding categoricals...")

for col in ["성별", "산지", "날씨", "주로상태"]:
    le = LabelEncoder()
    df[col + "_enc"] = le.fit_transform(df[col].fillna("UNK").astype(str))

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

bj_map = {"별정A": 0, "별정B": 1, "정량": 2, "핸디캡": 3}
df["별정_enc"] = df["별정"].map(bj_map).fillna(4)
df["장구_count"] = df["장구현황"].fillna("").apply(lambda x: len([i for i in x.split(",") if i.strip()]))

# ─── 4. FEATURE ENGINEERING ───
print("\n4. Engineering features...")

df = df.sort_values(["마명", "경주일자", "경주번호"]).reset_index(drop=True)

def horse_rolling_features(group):
    g = group.sort_values("경주일자")
    g["최근3전_평균착순"] = g["착순"].shift(1).rolling(3, min_periods=1).mean()
    g["최근5전_평균착순"] = g["착순"].shift(1).rolling(5, min_periods=1).mean()
    g["최근5전_승률"] = g["win"].shift(1).rolling(5, min_periods=1).mean()
    g["최근10전_승률"] = g["win"].shift(1).rolling(10, min_periods=1).mean()
    g["최근5전_복승률"] = g["place"].shift(1).rolling(5, min_periods=1).mean()
    g["통산_승률"] = g["win"].shift(1).expanding(min_periods=1).mean()
    g["통산_출주수"] = g["win"].shift(1).expanding(min_periods=1).count()
    g["체중_3회이동평균"] = g["마체중"].shift(1).rolling(3, min_periods=1).mean()
    g["체중_트렌드"] = g["마체중"] - g["체중_3회이동평균"]
    g["최근_경주기록"] = g["경주기록_sec"].shift(1)
    g["최근3전_평균기록"] = g["경주기록_sec"].shift(1).rolling(3, min_periods=1).mean()
    g["최근3전_G3F"] = g["3F_G기록_sec"].shift(1).rolling(3, min_periods=1).mean()
    g["이전경주일"] = g["경주일자"].shift(1)
    g["휴양일수"] = (g["경주일자"] - g["이전경주일"]).dt.days

    # V2 NEW: 속도 트렌드 (최근3전 기록의 기울기)
    def speed_slope(series):
        vals = series.dropna().values
        if len(vals) < 2:
            return 0.0
        x = np.arange(len(vals))
        return np.polyfit(x, vals, 1)[0]
    g["속도_트렌드"] = g["경주기록_sec"].shift(1).rolling(3, min_periods=2).apply(speed_slope, raw=False)

    # V2 NEW: 승급강등 (이전 등급 대비 현재 등급 변화)
    g["이전_등급"] = g["등급_ord"].shift(1) if "등급_ord" in g.columns else np.nan
    # Note: 등급_ord is lower=better, so positive diff means 강등, negative means 승급
    # We compute after merge since 등급_ord might not be in group yet

    # V2 NEW: 기수교체 여부
    g["이전_기수"] = g["기수명"].shift(1)
    g["기수교체"] = (g["기수명"] != g["이전_기수"]).astype(int)
    # First race for horse → 0
    g.loc[g["이전_기수"].isna(), "기수교체"] = 0

    return g

print("   Computing horse rolling features...")
df = df.groupby("마명", group_keys=False).apply(horse_rolling_features)

# 승급강등 (now that 등급_ord is available)
df["승급강등"] = df.groupby("마명")["등급_ord"].transform(lambda x: x.diff())
# positive = 강등 (등급 숫자 커짐), negative = 승급

# Jockey features
print("   Computing jockey features...")
df = df.sort_values(["기수명", "경주일자"]).reset_index(drop=True)
df["기수_누적승률"] = df.groupby("기수명")["win"].transform(lambda x: x.shift(1).expanding().mean())
df["기수_누적출주"] = df.groupby("기수명")["win"].transform(lambda x: x.shift(1).expanding().count())

# Trainer features
print("   Computing trainer features...")
df = df.sort_values(["조교사명", "경주일자"]).reset_index(drop=True)
df["조교사_누적승률"] = df.groupby("조교사명")["win"].transform(lambda x: x.shift(1).expanding().mean())

# Race-level features
print("   Computing race-level features...")
df = df.sort_values(["경주일자", "경주번호", "출주번호"]).reset_index(drop=True)
df["출전두수"] = df.groupby("race_id")["출주번호"].transform("count")
df["체중순위"] = df.groupby("race_id")["마체중"].rank(method="min")

# Distance affinity
print("   Computing distance affinity...")
df["마_거리_key"] = df["마명"] + "_" + df["거리_num"].astype(str)
df = df.sort_values(["마_거리_key", "경주일자"]).reset_index(drop=True)
df["거리별_승률"] = df.groupby("마_거리_key")["win"].transform(lambda x: x.shift(1).expanding().mean())
df["거리별_출주수"] = df.groupby("마_거리_key")["win"].transform(lambda x: x.shift(1).expanding().count())

# Jockey-Horse combo
print("   Computing jockey-horse combo...")
df["기수마_key"] = df["기수명"] + "_" + df["마명"]
df = df.sort_values(["기수마_key", "경주일자"]).reset_index(drop=True)
df["콤비_승률"] = df.groupby("기수마_key")["win"].transform(lambda x: x.shift(1).expanding().mean())
df["콤비_출주수"] = df.groupby("기수마_key")["win"].transform(lambda x: x.shift(1).expanding().count())

# ─── V2 CROSS FEATURES ───
print("   Computing V2 cross features...")
df["cross_기수거리"] = df["기수_누적승률"] * df["거리_num"]
df["cross_실력등급"] = df["통산_승률"] * df["등급_ord"]
df["cross_체중거리"] = df["마체중"] * df["거리_num"]
df["cross_휴양실력"] = df["휴양일수"] * df["통산_승률"]
df["cross_폼거리"] = df["최근5전_승률"] * df["거리별_승률"]

# ─── 5. FEATURE SELECTION (NO MARKET FEATURES) ───
print("\n5. Selecting features (V2 — no market)...")

FEATURES_V2 = [
    # Horse basics
    "연령_num", "성별_enc", "산지_enc", "부담중량", "마체중", "마체중증감",
    "장구_count",
    # Race conditions
    "거리_num", "등급_ord", "별정_enc", "경주번호", "출전두수",
    "날씨_enc", "주로상태_enc", "함수율",
    # NO MARKET: 단승배당, 연승배당, 시장확률, 배당순위 REMOVED
    # Horse history
    "최근3전_평균착순", "최근5전_평균착순",
    "최근5전_승률", "최근10전_승률", "최근5전_복승률",
    "통산_승률", "통산_출주수",
    # Weight trend
    "체중_3회이동평균", "체중_트렌드", "체중순위",
    # Time history
    "최근_경주기록", "최근3전_평균기록", "최근3전_G3F",
    # Jockey/Trainer
    "기수_누적승률", "기수_누적출주", "조교사_누적승률",
    # Distance affinity
    "거리별_승률", "거리별_출주수",
    # Jockey-Horse combo
    "콤비_승률", "콤비_출주수",
    # Rest days
    "휴양일수",
    # V2 NEW: cross features
    "cross_기수거리", "cross_실력등급", "cross_체중거리", "cross_휴양실력", "cross_폼거리",
    # V2 NEW: additional features
    "승급강등", "속도_트렌드", "기수교체",
]

missing = [f for f in FEATURES_V2 if f not in df.columns]
if missing:
    print(f"   WARNING: Missing features: {missing}")
    FEATURES_V2 = [f for f in FEATURES_V2 if f in df.columns]

print(f"   {len(FEATURES_V2)} features selected")

# ─── 6. TRAIN/TEST SPLIT ───
print("\n6. Time-based train/test split...")

train_mask = df["경주일자"] < "2025-01-01"
test_mask = df["경주일자"] >= "2025-01-01"

X_train = df.loc[train_mask, FEATURES_V2].fillna(-1)
y_train = df.loc[train_mask, "win"]
X_test = df.loc[test_mask, FEATURES_V2].fillna(-1)
y_test = df.loc[test_mask, "win"]
y_train_place = df.loc[train_mask, "place"]
y_test_place = df.loc[test_mask, "place"]

print(f"   Train: {len(X_train)} rows (win rate {y_train.mean():.3f})")
print(f"   Test:  {len(X_test)} rows (win rate {y_test.mean():.3f})")

# ─── 7. XGBOOST V2 ───
print("\n7. Training XGBoost V2...")

model_win = xgb.XGBClassifier(
    n_estimators=500, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=5,
    reg_alpha=0.1, reg_lambda=1.0,
    scale_pos_weight=len(y_train[y_train == 0]) / max(len(y_train[y_train == 1]), 1),
    eval_metric="auc", early_stopping_rounds=50,
    random_state=42, use_label_encoder=False,
)
model_win.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=50)

print("\n   Training Place model...")
model_place = xgb.XGBClassifier(
    n_estimators=500, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=5,
    eval_metric="auc", early_stopping_rounds=50,
    random_state=42, use_label_encoder=False,
)
model_place.fit(X_train, y_train_place, eval_set=[(X_test, y_test_place)], verbose=50)

# ─── 8. EVALUATION & V1 COMPARISON ───
print("\n" + "=" * 60)
print("8. EVALUATION — V1 vs V2 Comparison")
print("=" * 60)

y_pred_win = model_win.predict_proba(X_test)[:, 1]
auc_v2_win = roc_auc_score(y_test, y_pred_win)
ll_v2_win = log_loss(y_test, y_pred_win)

y_pred_place = model_place.predict_proba(X_test)[:, 1]
auc_v2_place = roc_auc_score(y_test_place, y_pred_place)

# Load V1 for comparison
try:
    v1_win = pickle.load(open("model_win.pkl", "rb"))
    # V1 features (includes market)
    FEATURES_V1 = [
        "연령_num", "성별_enc", "산지_enc", "부담중량", "마체중", "마체중증감",
        "장구_count", "거리_num", "등급_ord", "별정_enc", "경주번호", "출전두수",
        "날씨_enc", "주로상태_enc", "함수율",
        "단승배당", "연승배당", "시장확률", "배당순위",
        "최근3전_평균착순", "최근5전_평균착순",
        "최근5전_승률", "최근10전_승률", "최근5전_복승률",
        "통산_승률", "통산_출주수",
        "체중_3회이동평균", "체중_트렌드", "체중순위",
        "최근_경주기록", "최근3전_평균기록", "최근3전_G3F",
        "기수_누적승률", "기수_누적출주", "조교사_누적승률",
        "거리별_승률", "거리별_출주수",
        "콤비_승률", "콤비_출주수",
        "휴양일수",
    ]
    # Need market features for V1
    df["시장확률"] = 1 / df["단승배당"].replace(0, np.nan)
    df["배당순위"] = df.groupby("race_id")["단승배당"].rank(method="min")
    X_test_v1 = df.loc[test_mask, FEATURES_V1].fillna(-1)
    y_pred_v1 = v1_win.predict_proba(X_test_v1)[:, 1]
    auc_v1_win = roc_auc_score(y_test, y_pred_v1)
    has_v1 = True
except Exception as e:
    print(f"   V1 model not found or error: {e}")
    has_v1 = False

print(f"\n   ┌─────────────────────────────────────┐")
print(f"   │         WIN MODEL AUC                │")
if has_v1:
    print(f"   │   V1 (with market):  {auc_v1_win:.4f}          │")
print(f"   │   V2 (pure skill):   {auc_v2_win:.4f}          │")
if has_v1:
    diff = auc_v2_win - auc_v1_win
    print(f"   │   Diff:              {diff:+.4f}          │")
print(f"   │   V2 Log Loss:       {ll_v2_win:.4f}          │")
print(f"   ├─────────────────────────────────────┤")
print(f"   │         PLACE MODEL AUC              │")
print(f"   │   V2:                {auc_v2_place:.4f}          │")
print(f"   └─────────────────────────────────────┘")

# ─── 9. FEATURE IMPORTANCE ───
print("\n9. V2 Feature Importance (Top 15):")
imp = model_win.feature_importances_
imp_df = pd.DataFrame({"feature": FEATURES_V2, "importance": imp}).sort_values("importance", ascending=False)
for _, row in imp_df.head(15).iterrows():
    bar = "█" * int(row["importance"] * 100)
    print(f"   {row['feature']:25s} {row['importance']:.4f} {bar}")

imp_df.to_csv("feature_importance_v2.csv", index=False)

# ─── 10. PIPELINE B: EDGE DETECTION ───
print("\n" + "=" * 60)
print("10. EDGE DETECTION & ROI SIMULATION")
print("=" * 60)

test_df = df.loc[test_mask].copy()
test_df["pred_win_prob"] = y_pred_win
test_df["시장확률"] = 1 / test_df["단승배당"].replace(0, np.nan)

test_df["edge"] = test_df["pred_win_prob"] - test_df["시장확률"]
test_df["kelly_fraction"] = (
    (test_df["단승배당"] - 1) * test_df["pred_win_prob"] - (1 - test_df["pred_win_prob"])
) / (test_df["단승배당"] - 1)
test_df["kelly_fraction"] = test_df["kelly_fraction"].clip(0, 0.1)

# Edge threshold별 ROI
print(f"\n   {'Threshold':>10s} {'Bets':>6s} {'Wins':>5s} {'Hit%':>7s} {'Flat ROI':>10s} {'Kelly ROI':>10s} {'Avg Odds':>9s}")
print(f"   {'─'*10} {'─'*6} {'─'*5} {'─'*7} {'─'*10} {'─'*10} {'─'*9}")

for threshold in [0.00, 0.02, 0.05, 0.10, 0.15, 0.20]:
    sub = test_df[test_df["edge"] > threshold].copy()
    if len(sub) == 0:
        print(f"   {threshold:>9.0%}  {'0':>6s}   —       —          —          —")
        continue
    n = len(sub)
    w = sub["win"].sum()
    hit = w / n if n > 0 else 0
    ret = sub.loc[sub["win"] == 1, "단승배당"].sum()
    flat_roi = (ret - n) / n * 100
    avg_odds = sub.loc[sub["win"] == 1, "단승배당"].mean() if w > 0 else 0

    sub["k_wager"] = sub["kelly_fraction"] * 1000
    sub["k_return"] = sub["k_wager"] * sub["단승배당"] * sub["win"]
    k_roi = (sub["k_return"].sum() - sub["k_wager"].sum()) / sub["k_wager"].sum() * 100 if sub["k_wager"].sum() > 0 else 0

    print(f"   {threshold:>9.0%}  {n:>6d} {w:>5d} {hit:>6.1%} {flat_roi:>+9.1f}% {k_roi:>+9.1f}% {avg_odds:>8.1f}x")

# V1 vs V2 betting comparison
if has_v1:
    print(f"\n   ┌─ V1 vs V2 Betting (edge > 5%) ─────┐")
    for label, preds in [("V1", y_pred_v1), ("V2", y_pred_win)]:
        tmp = test_df.copy()
        tmp["pred"] = preds
        tmp["edge_tmp"] = tmp["pred"] - tmp["시장확률"]
        bets = tmp[tmp["edge_tmp"] > 0.05]
        if len(bets) > 0:
            w = bets["win"].sum()
            n = len(bets)
            ret = bets.loc[bets["win"] == 1, "단승배당"].sum()
            roi = (ret - n) / n * 100
            print(f"   │ {label}: {n} bets, {w} wins ({w/n:.1%}), ROI {roi:+.1f}%  │")
        else:
            print(f"   │ {label}: 0 bets                          │")
    print(f"   └──────────────────────────────────────┘")

# ─── 11. SAVE ───
print("\n11. Saving V2 models...")
pickle.dump(model_win, open("model_v2_win.pkl", "wb"))
pickle.dump(model_place, open("model_v2_place.pkl", "wb"))
print("   Saved: model_v2_win.pkl, model_v2_place.pkl, feature_importance_v2.csv")

print("\n" + "=" * 60)
print("V2 DONE!")
print("=" * 60)
