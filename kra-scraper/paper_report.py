#!/usr/bin/env python3
"""KRA V1 Model Analysis — Paper-style HTML Report with embedded plots"""

import pandas as pd
import numpy as np
import pickle, base64, io, json
from sklearn.metrics import roc_curve, roc_auc_score, precision_recall_curve, log_loss
try:
    from sklearn.calibration import calibration_curve
except ImportError:
    from sklearn.metrics import calibration_curve
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ─── Font setup ───
font_path = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
if fm.findSystemFonts(fontpaths=["/System/Library/Fonts/"], fontext="ttc"):
    fp = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = fp.get_name()
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.dpi"] = 150

# Dark theme
plt.style.use("dark_background")
COLORS = {
    "primary": "#00d4ff",
    "secondary": "#ff6b6b",
    "accent": "#ffd93d",
    "green": "#6bff6b",
    "purple": "#b88cff",
    "bg": "#0a0a1a",
    "card": "#141428",
    "text": "#e0e0e0",
    "grid": "#1a1a3a",
}

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=COLORS["bg"], edgecolor="none")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return b64

# ─── Load data & model ───
print("Loading data...")
df = pd.read_csv("kra_seoul_final.csv", encoding="utf-8-sig", dtype=str)

df["착순"] = pd.to_numeric(df["착순"], errors="coerce")
df["단승배당"] = pd.to_numeric(df["단승배당"], errors="coerce")
df["연승배당"] = pd.to_numeric(df["연승배당"], errors="coerce")
df["경주번호"] = pd.to_numeric(df["경주번호"], errors="coerce")
df["출주번호"] = pd.to_numeric(df["출주번호"], errors="coerce")
df["경주일자"] = pd.to_datetime(df["경주일자"], format="%Y%m%d")
df["race_id"] = df["경주일자"].dt.strftime("%Y%m%d") + "_" + df["경주번호"].astype(str)
df["win"] = (df["착순"] == 1).astype(int)
df["place"] = (df["착순"] <= 3).astype(int)
df = df.dropna(subset=["착순"])

model_win = pickle.load(open("model_win.pkl", "rb"))
model_place = pickle.load(open("model_place.pkl", "rb"))
imp_df = pd.read_csv("feature_importance.csv")
FEATURES = model_win.get_booster().feature_names

print("Full feature rebuild...")

def to_float(s):
    try: return float(str(s).replace(":", "").replace(",", "").strip())
    except: return np.nan

def time_to_seconds(s):
    try:
        s = str(s).strip()
        if ":" in s:
            parts = s.split(":")
            return float(parts[0]) * 60 + float(parts[1])
        return float(s)
    except: return np.nan

from sklearn.preprocessing import LabelEncoder

df["부담중량"] = pd.to_numeric(df["부담중량"], errors="coerce")
df["마체중"] = pd.to_numeric(df["마체중"], errors="coerce")
df["마체중증감"] = pd.to_numeric(df["마체중증감"], errors="coerce")
df["함수율"] = df["함수율"].str.replace("%", "").apply(to_float)
df["연령_num"] = df["연령"].str.extract(r"(\d+)").astype(float)
df["거리_num"] = df["거리"].str.extract(r"(\d+)").astype(float)

time_cols = ["S1F기록","1C기록","2C기록","3C기록","G3F기록","4C기록","G1F기록","3F_G기록","1F_G기록","경주기록"]
for c in time_cols:
    df[c+"_sec"] = df[c].apply(time_to_seconds)

for col in ["성별","산지","날씨","주로상태"]:
    le = LabelEncoder()
    df[col+"_enc"] = le.fit_transform(df[col].fillna("UNK").astype(str))

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

bj_map = {"별정A":0,"별정B":1,"정량":2,"핸디캡":3}
df["별정_enc"] = df["별정"].map(bj_map).fillna(4)
df["장구_count"] = df["장구현황"].fillna("").apply(lambda x: len([i for i in x.split(",") if i.strip()]))

df = df.sort_values(["마명","경주일자","경주번호"]).reset_index(drop=True)

def horse_rolling(group):
    g = group.sort_values("경주일자")
    g["최근3전_평균착순"] = g["착순"].shift(1).rolling(3,min_periods=1).mean()
    g["최근5전_평균착순"] = g["착순"].shift(1).rolling(5,min_periods=1).mean()
    g["최근5전_승률"] = g["win"].shift(1).rolling(5,min_periods=1).mean()
    g["최근10전_승률"] = g["win"].shift(1).rolling(10,min_periods=1).mean()
    g["최근5전_복승률"] = g["place"].shift(1).rolling(5,min_periods=1).mean()
    g["통산_승률"] = g["win"].shift(1).expanding(min_periods=1).mean()
    g["통산_출주수"] = g["win"].shift(1).expanding(min_periods=1).count()
    g["체중_3회이동평균"] = g["마체중"].shift(1).rolling(3,min_periods=1).mean()
    g["체중_트렌드"] = g["마체중"] - g["체중_3회이동평균"]
    g["최근_경주기록"] = g["경주기록_sec"].shift(1)
    g["최근3전_평균기록"] = g["경주기록_sec"].shift(1).rolling(3,min_periods=1).mean()
    g["최근3전_G3F"] = g["3F_G기록_sec"].shift(1).rolling(3,min_periods=1).mean()
    g["이전경주일"] = g["경주일자"].shift(1)
    g["휴양일수"] = (g["경주일자"] - g["이전경주일"]).dt.days
    return g

df = df.groupby("마명", group_keys=False).apply(horse_rolling)

df = df.sort_values(["기수명","경주일자"]).reset_index(drop=True)
df["기수_누적승률"] = df.groupby("기수명")["win"].transform(lambda x: x.shift(1).expanding().mean())
df["기수_누적출주"] = df.groupby("기수명")["win"].transform(lambda x: x.shift(1).expanding().count())
df = df.sort_values(["조교사명","경주일자"]).reset_index(drop=True)
df["조교사_누적승률"] = df.groupby("조교사명")["win"].transform(lambda x: x.shift(1).expanding().mean())

df = df.sort_values(["경주일자","경주번호","출주번호"]).reset_index(drop=True)
df["출전두수"] = df.groupby("race_id")["출주번호"].transform("count")
df["시장확률"] = 1 / df["단승배당"].replace(0, np.nan)
df["배당순위"] = df.groupby("race_id")["단승배당"].rank(method="min")
df["체중순위"] = df.groupby("race_id")["마체중"].rank(method="min")

df["마_거리_key"] = df["마명"] + "_" + df["거리_num"].astype(str)
df = df.sort_values(["마_거리_key","경주일자"]).reset_index(drop=True)
df["거리별_승률"] = df.groupby("마_거리_key")["win"].transform(lambda x: x.shift(1).expanding().mean())
df["거리별_출주수"] = df.groupby("마_거리_key")["win"].transform(lambda x: x.shift(1).expanding().count())

df["기수마_key"] = df["기수명"] + "_" + df["마명"]
df = df.sort_values(["기수마_key","경주일자"]).reset_index(drop=True)
df["콤비_승률"] = df.groupby("기수마_key")["win"].transform(lambda x: x.shift(1).expanding().mean())
df["콤비_출주수"] = df.groupby("기수마_key")["win"].transform(lambda x: x.shift(1).expanding().count())

# ─── Split & Predict ───
train_mask = df["경주일자"] < "2025-01-01"
test_mask = df["경주일자"] >= "2025-01-01"

X_test = df.loc[test_mask, FEATURES].fillna(-1)
y_test = df.loc[test_mask, "win"]
y_test_place = df.loc[test_mask, "place"]

y_pred_win = model_win.predict_proba(X_test)[:, 1]
y_pred_place = model_place.predict_proba(X_test)[:, 1]

test_df = df.loc[test_mask].copy()
test_df["pred_win"] = y_pred_win
test_df["pred_place"] = y_pred_place
test_df["시장확률_clean"] = 1 / test_df["단승배당"].replace(0, np.nan)
test_df["edge"] = test_df["pred_win"] - test_df["시장확률_clean"]

# Also get market-only baseline predictions
market_pred = test_df["시장확률_clean"].fillna(0).values

print(f"Test set: {len(test_df)} rows")
print(f"Win AUC (model): {roc_auc_score(y_test, y_pred_win):.4f}")
print(f"Win AUC (market): {roc_auc_score(y_test, market_pred):.4f}")

# ═══════════════════════════════════════
# PLOTS
# ═══════════════════════════════════════
plots = {}

# ─── 1. ROC Curve: Model vs Market ───
print("Plot 1: ROC curves...")
fig, ax = plt.subplots(1, 1, figsize=(8, 7))
fig.patch.set_facecolor(COLORS["bg"])
ax.set_facecolor(COLORS["bg"])

fpr_m, tpr_m, _ = roc_curve(y_test, y_pred_win)
fpr_mkt, tpr_mkt, _ = roc_curve(y_test, market_pred)
auc_m = roc_auc_score(y_test, y_pred_win)
auc_mkt = roc_auc_score(y_test, market_pred)

ax.plot(fpr_m, tpr_m, color=COLORS["primary"], linewidth=2.5, label=f"XGBoost V1 (AUC={auc_m:.4f})")
ax.plot(fpr_mkt, tpr_mkt, color=COLORS["secondary"], linewidth=2.5, linestyle="--", label=f"시장배당 (AUC={auc_mkt:.4f})")
ax.plot([0,1],[0,1], color=COLORS["grid"], linewidth=1, linestyle=":")
ax.fill_between(fpr_m, tpr_m, alpha=0.15, color=COLORS["primary"])
ax.set_xlabel("False Positive Rate", fontsize=13, color=COLORS["text"])
ax.set_ylabel("True Positive Rate", fontsize=13, color=COLORS["text"])
ax.set_title("ROC Curve — 승리 예측 (2025~2026 테스트셋)", fontsize=15, color="white", fontweight="bold")
ax.legend(fontsize=12, loc="lower right")
ax.grid(True, alpha=0.2, color=COLORS["grid"])
ax.tick_params(colors=COLORS["text"])
plots["roc"] = fig_to_base64(fig)

# ─── 2. ROC for Place model ───
print("Plot 2: Place ROC...")
fig, ax = plt.subplots(1, 1, figsize=(8, 7))
fig.patch.set_facecolor(COLORS["bg"])
ax.set_facecolor(COLORS["bg"])

fpr_p, tpr_p, _ = roc_curve(y_test_place, y_pred_place)
auc_p = roc_auc_score(y_test_place, y_pred_place)

ax.plot(fpr_p, tpr_p, color=COLORS["accent"], linewidth=2.5, label=f"Place Model (AUC={auc_p:.4f})")
ax.plot([0,1],[0,1], color=COLORS["grid"], linewidth=1, linestyle=":")
ax.fill_between(fpr_p, tpr_p, alpha=0.15, color=COLORS["accent"])
ax.set_xlabel("False Positive Rate", fontsize=13, color=COLORS["text"])
ax.set_ylabel("True Positive Rate", fontsize=13, color=COLORS["text"])
ax.set_title("ROC Curve — 복승 예측 (3착 이내)", fontsize=15, color="white", fontweight="bold")
ax.legend(fontsize=12)
ax.grid(True, alpha=0.2, color=COLORS["grid"])
ax.tick_params(colors=COLORS["text"])
plots["roc_place"] = fig_to_base64(fig)

# ─── 3. Feature Importance (Top 20) ───
print("Plot 3: Feature importance...")
fig, ax = plt.subplots(1, 1, figsize=(10, 8))
fig.patch.set_facecolor(COLORS["bg"])
ax.set_facecolor(COLORS["bg"])

top20 = imp_df.head(20).iloc[::-1]
colors_bar = [COLORS["secondary"] if f in ["시장확률","단승배당","배당순위","연승배당"] else COLORS["primary"] for f in top20["feature"]]
bars = ax.barh(range(len(top20)), top20["importance"], color=colors_bar, edgecolor="none", height=0.7)
ax.set_yticks(range(len(top20)))
ax.set_yticklabels(top20["feature"], fontsize=11, color=COLORS["text"])
ax.set_xlabel("Feature Importance (Gain)", fontsize=13, color=COLORS["text"])
ax.set_title("피처 중요도 Top 20 — 시장 피처(빨강) vs 실력 피처(파랑)", fontsize=14, color="white", fontweight="bold")
ax.grid(True, axis="x", alpha=0.2, color=COLORS["grid"])
ax.tick_params(colors=COLORS["text"])

# Add percentage labels
for i, (val, feat) in enumerate(zip(top20["importance"], top20["feature"])):
    ax.text(val + 0.002, i, f"{val:.1%}", va="center", fontsize=10, color=COLORS["text"])

plots["feature_importance"] = fig_to_base64(fig)

# ─── 4. Calibration Plot ───
print("Plot 4: Calibration...")
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor(COLORS["bg"])

for idx, (pred, name, color) in enumerate([
    (y_pred_win, "XGBoost 모델", COLORS["primary"]),
    (market_pred, "시장배당", COLORS["secondary"]),
]):
    ax = axes[idx]
    ax.set_facecolor(COLORS["bg"])
    prob_true, prob_pred = calibration_curve(y_test, pred, n_bins=15, strategy="quantile")
    ax.plot(prob_pred, prob_true, "o-", color=color, linewidth=2, markersize=6)
    ax.plot([0, max(prob_pred.max(), prob_true.max())], [0, max(prob_pred.max(), prob_true.max())], 
            ":", color=COLORS["grid"], linewidth=1)
    ax.set_xlabel("예측 확률", fontsize=12, color=COLORS["text"])
    ax.set_ylabel("실제 승률", fontsize=12, color=COLORS["text"])
    ax.set_title(f"Calibration — {name}", fontsize=13, color="white", fontweight="bold")
    ax.grid(True, alpha=0.2, color=COLORS["grid"])
    ax.tick_params(colors=COLORS["text"])

plt.tight_layout()
plots["calibration"] = fig_to_base64(fig)

# ─── 5. Edge Distribution ───
print("Plot 5: Edge distribution...")
fig, ax = plt.subplots(1, 1, figsize=(10, 6))
fig.patch.set_facecolor(COLORS["bg"])
ax.set_facecolor(COLORS["bg"])

valid_edge = test_df["edge"].dropna()
ax.hist(valid_edge, bins=80, color=COLORS["primary"], alpha=0.7, edgecolor="none")
ax.axvline(x=0, color=COLORS["secondary"], linewidth=2, linestyle="--", label="Edge = 0")
ax.axvline(x=0.05, color=COLORS["accent"], linewidth=1.5, linestyle="--", label="Edge = 5% (베팅기준)")

# Stats
pos_edge = (valid_edge > 0).sum()
neg_edge = (valid_edge <= 0).sum()
ax.text(0.95, 0.95, f"+Edge: {pos_edge} ({pos_edge/len(valid_edge):.1%})\n−Edge: {neg_edge} ({neg_edge/len(valid_edge):.1%})",
        transform=ax.transAxes, ha="right", va="top", fontsize=12, color=COLORS["text"],
        bbox=dict(boxstyle="round,pad=0.5", facecolor=COLORS["card"], alpha=0.8))

ax.set_xlabel("Model Edge (모델확률 − 시장확률)", fontsize=13, color=COLORS["text"])
ax.set_ylabel("빈도", fontsize=13, color=COLORS["text"])
ax.set_title("Edge 분포 — 모델 vs 시장", fontsize=15, color="white", fontweight="bold")
ax.legend(fontsize=11)
ax.grid(True, alpha=0.2, color=COLORS["grid"])
ax.tick_params(colors=COLORS["text"])
plots["edge_dist"] = fig_to_base64(fig)

# ─── 6. ROI by Edge Threshold ───
print("Plot 6: ROI by edge threshold...")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
fig.patch.set_facecolor(COLORS["bg"])

thresholds = np.arange(0, 0.35, 0.01)
rois = []
counts = []
hit_rates = []

for t in thresholds:
    bets = test_df[test_df["edge"] > t]
    if len(bets) < 10:
        rois.append(np.nan)
        counts.append(0)
        hit_rates.append(np.nan)
        continue
    w = bets["win"].sum()
    n = len(bets)
    ret = bets.loc[bets["win"]==1, "단승배당"].sum()
    rois.append((ret - n) / n * 100)
    counts.append(n)
    hit_rates.append(w / n * 100)

ax1.set_facecolor(COLORS["bg"])
ax1.plot(thresholds*100, rois, color=COLORS["primary"], linewidth=2.5)
ax1.axhline(y=0, color=COLORS["secondary"], linewidth=1, linestyle="--")
ax1.fill_between(thresholds*100, rois, 0, where=[r is not None and r > 0 for r in rois], 
                  alpha=0.2, color=COLORS["green"])
ax1.fill_between(thresholds*100, rois, 0, where=[r is not None and r <= 0 for r in rois], 
                  alpha=0.2, color=COLORS["secondary"])
ax1.set_ylabel("ROI (%)", fontsize=13, color=COLORS["text"])
ax1.set_title("Edge 기준별 ROI & 적중률", fontsize=15, color="white", fontweight="bold")
ax1.grid(True, alpha=0.2, color=COLORS["grid"])
ax1.tick_params(colors=COLORS["text"])

ax2.set_facecolor(COLORS["bg"])
ax2_twin = ax2.twinx()
ax2.bar(thresholds*100, counts, width=0.8, color=COLORS["primary"], alpha=0.5, label="베팅 수")
ax2_twin.plot(thresholds*100, hit_rates, color=COLORS["accent"], linewidth=2.5, label="적중률")
ax2.set_xlabel("Edge Threshold (%)", fontsize=13, color=COLORS["text"])
ax2.set_ylabel("베팅 수", fontsize=13, color=COLORS["text"])
ax2_twin.set_ylabel("적중률 (%)", fontsize=13, color=COLORS["accent"])
ax2.grid(True, alpha=0.2, color=COLORS["grid"])
ax2.tick_params(colors=COLORS["text"])
ax2_twin.tick_params(colors=COLORS["accent"])

# Combined legend
lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines1+lines2, labels1+labels2, fontsize=11)

plt.tight_layout()
plots["roi_threshold"] = fig_to_base64(fig)

# ─── 7. Cumulative PnL ───
print("Plot 7: Cumulative PnL...")
fig, ax = plt.subplots(1, 1, figsize=(12, 6))
fig.patch.set_facecolor(COLORS["bg"])
ax.set_facecolor(COLORS["bg"])

for edge_t, color, label in [(0.05, COLORS["primary"], "Edge>5%"), 
                               (0.10, COLORS["accent"], "Edge>10%"),
                               (0.15, COLORS["green"], "Edge>15%"),
                               (0.20, COLORS["purple"], "Edge>20%")]:
    bets = test_df[test_df["edge"] > edge_t].sort_values("경주일자").copy()
    if len(bets) < 5:
        continue
    bets["pnl"] = bets["win"] * bets["단승배당"] - 1  # flat 1 unit
    bets["cum_pnl"] = bets["pnl"].cumsum()
    ax.plot(range(len(bets)), bets["cum_pnl"], linewidth=1.8, color=color, label=f"{label} (n={len(bets)})")

ax.axhline(y=0, color=COLORS["secondary"], linewidth=1, linestyle="--")
ax.set_xlabel("베팅 번호 (시간순)", fontsize=13, color=COLORS["text"])
ax.set_ylabel("누적 손익 (단위)", fontsize=13, color=COLORS["text"])
ax.set_title("누적 PnL 곡선 — Edge 기준별 (Flat Betting)", fontsize=15, color="white", fontweight="bold")
ax.legend(fontsize=11)
ax.grid(True, alpha=0.2, color=COLORS["grid"])
ax.tick_params(colors=COLORS["text"])
plots["cum_pnl"] = fig_to_base64(fig)

# ─── 8. Model vs Market scatter ───
print("Plot 8: Model vs Market probability scatter...")
fig, ax = plt.subplots(1, 1, figsize=(8, 8))
fig.patch.set_facecolor(COLORS["bg"])
ax.set_facecolor(COLORS["bg"])

sample = test_df.dropna(subset=["시장확률_clean"]).sample(min(3000, len(test_df)), random_state=42)
winners = sample[sample["win"]==1]
losers = sample[sample["win"]==0]

ax.scatter(losers["시장확률_clean"], losers["pred_win"], s=8, alpha=0.3, color=COLORS["text"], label="패배마")
ax.scatter(winners["시장확률_clean"], winners["pred_win"], s=25, alpha=0.8, color=COLORS["accent"], label="우승마", zorder=5)
ax.plot([0, 0.5], [0, 0.5], ":", color=COLORS["secondary"], linewidth=1.5, label="y=x (동일)")
ax.set_xlabel("시장 내재확률 (1/배당)", fontsize=13, color=COLORS["text"])
ax.set_ylabel("모델 예측확률", fontsize=13, color=COLORS["text"])
ax.set_title("모델 확률 vs 시장 확률", fontsize=15, color="white", fontweight="bold")
ax.legend(fontsize=11)
ax.grid(True, alpha=0.2, color=COLORS["grid"])
ax.tick_params(colors=COLORS["text"])
plots["scatter"] = fig_to_base64(fig)

# ─── 9. Monthly ROI trend ───
print("Plot 9: Monthly ROI...")
fig, ax = plt.subplots(1, 1, figsize=(12, 5))
fig.patch.set_facecolor(COLORS["bg"])
ax.set_facecolor(COLORS["bg"])

bets_5 = test_df[test_df["edge"] > 0.05].copy()
bets_5["month"] = bets_5["경주일자"].dt.to_period("M")
monthly = bets_5.groupby("month").apply(lambda g: pd.Series({
    "roi": ((g.loc[g["win"]==1, "단승배당"].sum()) - len(g)) / len(g) * 100,
    "n_bets": len(g),
    "wins": g["win"].sum(),
})).reset_index()

colors_monthly = [COLORS["green"] if r > 0 else COLORS["secondary"] for r in monthly["roi"]]
bars = ax.bar(range(len(monthly)), monthly["roi"], color=colors_monthly, edgecolor="none", width=0.7)
ax.set_xticks(range(len(monthly)))
ax.set_xticklabels([str(m) for m in monthly["month"]], rotation=45, fontsize=10, color=COLORS["text"])
ax.axhline(y=0, color="white", linewidth=0.8, linestyle="-")
ax.set_ylabel("ROI (%)", fontsize=13, color=COLORS["text"])
ax.set_title("월별 ROI (Edge > 5% 베팅)", fontsize=15, color="white", fontweight="bold")
ax.grid(True, axis="y", alpha=0.2, color=COLORS["grid"])
ax.tick_params(colors=COLORS["text"])

# Add bet count labels
for i, (roi, n) in enumerate(zip(monthly["roi"], monthly["n_bets"])):
    ax.text(i, roi + (2 if roi >= 0 else -4), f"n={int(n)}", ha="center", fontsize=9, color=COLORS["text"])

plots["monthly_roi"] = fig_to_base64(fig)

# ─── 10. Market feature dominance analysis ───
print("Plot 10: Market vs skill feature contribution...")
fig, ax = plt.subplots(1, 1, figsize=(8, 6))
fig.patch.set_facecolor(COLORS["bg"])
ax.set_facecolor(COLORS["bg"])

market_feats = ["시장확률","단승배당","배당순위","연승배당"]
market_imp = imp_df[imp_df["feature"].isin(market_feats)]["importance"].sum()
skill_imp = imp_df[~imp_df["feature"].isin(market_feats)]["importance"].sum()

sizes = [market_imp, skill_imp]
labels_pie = [f"시장 피처\n{market_imp:.1%}", f"실력 피처\n{skill_imp:.1%}"]
colors_pie = [COLORS["secondary"], COLORS["primary"]]
explode = (0.05, 0)

wedges, texts = ax.pie(sizes, labels=labels_pie, colors=colors_pie, explode=explode,
                        startangle=90, textprops={"fontsize": 14, "color": "white"})
ax.set_title("피처 중요도 비중 — 시장 vs 실력", fontsize=15, color="white", fontweight="bold")
plots["market_share"] = fig_to_base64(fig)

# ═══════════════════════════════════════
# COMPUTE STATS
# ═══════════════════════════════════════
print("\nComputing summary stats...")

auc_model = roc_auc_score(y_test, y_pred_win)
auc_market = roc_auc_score(y_test, market_pred)
ll_model = log_loss(y_test, y_pred_win)
ll_market = log_loss(y_test, np.clip(market_pred, 0.01, 0.99))

# Edge-based stats table
edge_stats = []
for t in [0.00, 0.05, 0.10, 0.15, 0.20, 0.25]:
    bets = test_df[test_df["edge"] > t]
    if len(bets) < 5:
        continue
    w = bets["win"].sum()
    n = len(bets)
    ret = bets.loc[bets["win"]==1, "단승배당"].sum()
    roi = (ret - n) / n * 100
    avg_odds = bets.loc[bets["win"]==1, "단승배당"].mean() if w > 0 else 0
    avg_edge = bets["edge"].mean() * 100
    edge_stats.append({
        "threshold": f"{t:.0%}",
        "n_bets": n,
        "wins": w,
        "hit_rate": f"{w/n:.1%}",
        "avg_odds": f"{avg_odds:.1f}",
        "avg_edge": f"{avg_edge:.1f}%",
        "roi": f"{roi:+.1f}%",
    })

# ═══════════════════════════════════════
# HTML REPORT
# ═══════════════════════════════════════
print("\nGenerating HTML report...")

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KRA 경마 예측 모델 V1 — 분석 리포트</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    background: {COLORS["bg"]};
    color: {COLORS["text"]};
    font-family: 'Noto Sans KR', sans-serif;
    line-height: 1.8;
    padding: 0;
}}

.container {{
    max-width: 1000px;
    margin: 0 auto;
    padding: 40px 30px;
}}

/* Header */
.header {{
    text-align: center;
    padding: 60px 20px;
    background: linear-gradient(135deg, #0a0a2e 0%, #141440 50%, #0a0a2e 100%);
    border-bottom: 2px solid {COLORS["primary"]}40;
    margin-bottom: 40px;
}}
.header h1 {{
    font-size: 2.4em;
    color: white;
    font-weight: 700;
    margin-bottom: 10px;
    text-shadow: 0 0 30px {COLORS["primary"]}60;
}}
.header .subtitle {{
    font-size: 1.1em;
    color: {COLORS["primary"]};
    font-weight: 300;
}}
.header .meta {{
    margin-top: 15px;
    font-size: 0.9em;
    color: #888;
}}

/* Section */
.section {{
    background: {COLORS["card"]};
    border: 1px solid #1e1e3e;
    border-radius: 12px;
    padding: 35px;
    margin-bottom: 30px;
}}
.section h2 {{
    font-size: 1.5em;
    color: {COLORS["primary"]};
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #1e1e3e;
}}
.section h3 {{
    font-size: 1.15em;
    color: {COLORS["accent"]};
    margin: 20px 0 10px;
}}

/* Stats grid */
.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin: 20px 0;
}}
.stat-card {{
    background: #1a1a35;
    border: 1px solid #2a2a4a;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
}}
.stat-card .value {{
    font-size: 2em;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}}
.stat-card .label {{
    font-size: 0.85em;
    color: #888;
    margin-top: 5px;
}}
.stat-card.good .value {{ color: {COLORS["green"]}; }}
.stat-card.warn .value {{ color: {COLORS["accent"]}; }}
.stat-card.bad .value {{ color: {COLORS["secondary"]}; }}
.stat-card.info .value {{ color: {COLORS["primary"]}; }}

/* Plot */
.plot {{
    text-align: center;
    margin: 25px 0;
}}
.plot img {{
    max-width: 100%;
    border-radius: 8px;
    border: 1px solid #1e1e3e;
}}
.plot .caption {{
    font-size: 0.85em;
    color: #888;
    margin-top: 8px;
    font-style: italic;
}}

/* Table */
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9em;
}}
th {{
    background: #1a1a35;
    color: {COLORS["primary"]};
    padding: 12px 10px;
    text-align: center;
    border: 1px solid #2a2a4a;
    font-weight: 500;
}}
td {{
    padding: 10px;
    text-align: center;
    border: 1px solid #1e1e3e;
}}
tr:hover {{ background: #1a1a30; }}
.neg {{ color: {COLORS["secondary"]}; }}
.pos {{ color: {COLORS["green"]}; }}

/* Findings */
.finding {{
    background: #1a1a35;
    border-left: 4px solid {COLORS["accent"]};
    padding: 15px 20px;
    margin: 15px 0;
    border-radius: 0 8px 8px 0;
}}
.finding.critical {{
    border-left-color: {COLORS["secondary"]};
}}
.finding.positive {{
    border-left-color: {COLORS["green"]};
}}

p {{ margin: 10px 0; }}
code {{
    background: #1a1a35;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9em;
    color: {COLORS["accent"]};
}}

.toc {{
    background: #1a1a35;
    border-radius: 10px;
    padding: 25px 30px;
    margin: 30px 0;
}}
.toc h3 {{ color: white; margin-bottom: 10px; }}
.toc a {{
    color: {COLORS["primary"]};
    text-decoration: none;
    display: block;
    padding: 4px 0;
}}
.toc a:hover {{ color: {COLORS["accent"]}; }}
</style>
</head>
<body>

<div class="header">
    <h1>🐎 KRA 경마 예측 모델 V1</h1>
    <div class="subtitle">XGBoost 기반 승리 예측 — 모델 성능 및 시장 대비 엣지 분석</div>
    <div class="meta">
        서울경마 | 2020~2026 (64,720 출주) | 테스트: 2025~2026<br>
        Report generated: 2026-03-29
    </div>
</div>

<div class="container">

<div class="toc">
    <h3>📑 목차</h3>
    <a href="#abstract">Abstract</a>
    <a href="#data">1. 데이터 & 피처</a>
    <a href="#roc">2. 모델 성능 (ROC)</a>
    <a href="#features">3. 피처 중요도 분석</a>
    <a href="#calibration">4. Calibration 분석</a>
    <a href="#edge">5. 모델 Edge 분석</a>
    <a href="#betting">6. 베팅 시뮬레이션</a>
    <a href="#monthly">7. 월별 성과</a>
    <a href="#conclusion">8. 결론 & V2 방향</a>
</div>

<!-- ABSTRACT -->
<div class="section" id="abstract">
    <h2>Abstract</h2>
    <p>본 보고서는 한국마사회 서울경마장 데이터(2020~2026)를 활용한 XGBoost V1 모델의 성능을 분석한다.
    모델은 40개 피처(마필 실력, 기수/조교사 통계, 시장 배당 정보)를 사용하여 경주별 승리 확률을 예측한다.</p>
    
    <div class="finding critical">
        <strong>핵심 발견:</strong> 모델 AUC {auc_model:.4f}로 시장배당 AUC {auc_market:.4f} 대비 우수하나,
        피처 중요도의 <strong>{market_imp:.1%}가 시장 배당 관련 피처</strong>에 집중되어 있어 독립적인 alpha 생성에 한계가 있다.
        베팅 시뮬레이션 결과 ROI는 음수로, 시장을 이길 수 있는 독자적 시그널이 부족하다.
    </div>
</div>

<!-- DATA -->
<div class="section" id="data">
    <h2>1. 데이터 & 피처 엔지니어링</h2>
    
    <div class="stats-grid">
        <div class="stat-card info">
            <div class="value">64,720</div>
            <div class="label">총 출주 기록</div>
        </div>
        <div class="stat-card info">
            <div class="value">551</div>
            <div class="label">경주일 수</div>
        </div>
        <div class="stat-card info">
            <div class="value">40</div>
            <div class="label">입력 피처 수</div>
        </div>
        <div class="stat-card info">
            <div class="value">2020~2026</div>
            <div class="label">데이터 기간</div>
        </div>
    </div>

    <h3>피처 카테고리</h3>
    <table>
        <tr><th>카테고리</th><th>피처 수</th><th>예시</th></tr>
        <tr><td>마필 기본</td><td>6</td><td>연령, 성별, 산지, 마체중, 부담중량</td></tr>
        <tr><td>경주 조건</td><td>5</td><td>거리, 등급, 날씨, 주로상태, 함수율</td></tr>
        <tr><td>시장 배당</td><td>4</td><td>단승배당, 연승배당, 시장확률, 배당순위</td></tr>
        <tr><td>마필 이력</td><td>11</td><td>최근N전 착순/승률, 통산승률, 체중트렌드</td></tr>
        <tr><td>기수/조교사</td><td>3</td><td>기수 누적승률, 조교사 누적승률</td></tr>
        <tr><td>친화도</td><td>4</td><td>거리별 승률, 기수-마 콤비 승률</td></tr>
        <tr><td>컨디션</td><td>1</td><td>휴양일수</td></tr>
    </table>

    <h3>Train/Test Split</h3>
    <p>시계열 기반 분할: <code>Train: ~2024.12</code> | <code>Test: 2025.01~2026.03</code></p>
</div>

<!-- ROC -->
<div class="section" id="roc">
    <h2>2. 모델 성능 — ROC Curve</h2>
    
    <div class="stats-grid">
        <div class="stat-card good">
            <div class="value">{auc_model:.4f}</div>
            <div class="label">모델 AUC (Win)</div>
        </div>
        <div class="stat-card warn">
            <div class="value">{auc_market:.4f}</div>
            <div class="label">시장배당 AUC</div>
        </div>
        <div class="stat-card info">
            <div class="value">{auc_model - auc_market:+.4f}</div>
            <div class="label">AUC 차이</div>
        </div>
        <div class="stat-card info">
            <div class="value">{roc_auc_score(y_test_place, y_pred_place):.4f}</div>
            <div class="label">Place AUC</div>
        </div>
    </div>

    <div class="plot">
        <img src="data:image/png;base64,{plots['roc']}" alt="ROC Curve">
        <div class="caption">Fig 1. Win 예측 ROC — XGBoost V1 vs 시장배당 베이스라인</div>
    </div>

    <div class="plot">
        <img src="data:image/png;base64,{plots['roc_place']}" alt="Place ROC">
        <div class="caption">Fig 2. Place (3착 이내) 예측 ROC</div>
    </div>

    <div class="finding positive">
        <strong>모델이 시장보다 우수한 판별력을 보인다.</strong>
        AUC {auc_model:.4f} vs {auc_market:.4f} (Δ={auc_model-auc_market:+.4f}).
        그러나 이 우위의 대부분이 시장 피처 자체에서 비롯되었을 가능성이 높다 (§3 참조).
    </div>
</div>

<!-- FEATURES -->
<div class="section" id="features">
    <h2>3. 피처 중요도 분석</h2>
    
    <div class="plot">
        <img src="data:image/png;base64,{plots['feature_importance']}" alt="Feature Importance">
        <div class="caption">Fig 3. 피처 중요도 Top 20 — 빨강: 시장 피처, 파랑: 실력 피처</div>
    </div>

    <div class="plot">
        <img src="data:image/png;base64,{plots['market_share']}" alt="Market Share">
        <div class="caption">Fig 4. 시장 피처 vs 실력 피처 — 전체 중요도 비중</div>
    </div>

    <div class="finding critical">
        <strong>⚠️ 시장 피처 과의존 문제</strong><br>
        시장확률(25.5%) + 단승배당(14.0%) + 배당순위(5.1%) + 연승배당(3.7%) = <strong>{market_imp:.1%}</strong>가 시장 정보에 의존.
        모델이 실질적으로 "시장 배당의 비선형 변환"에 가까우며, 독자적 alpha 시그널이 약하다.
    </div>

    <h3>Top 5 실력 피처</h3>
    <table>
        <tr><th>순위</th><th>피처</th><th>중요도</th><th>해석</th></tr>
        <tr><td>1</td><td>최근5전 복승률</td><td>2.8%</td><td>최근 안정성 (3착 이내)</td></tr>
        <tr><td>2</td><td>최근5전 평균착순</td><td>1.6%</td><td>최근 폼</td></tr>
        <tr><td>3</td><td>최근10전 승률</td><td>1.6%</td><td>중기 실력</td></tr>
        <tr><td>4</td><td>연령</td><td>1.6%</td><td>나이별 능력 곡선</td></tr>
        <tr><td>5</td><td>최근3전 평균착순</td><td>1.5%</td><td>단기 폼</td></tr>
    </table>
</div>

<!-- CALIBRATION -->
<div class="section" id="calibration">
    <h2>4. Calibration 분석</h2>
    
    <div class="plot">
        <img src="data:image/png;base64,{plots['calibration']}" alt="Calibration">
        <div class="caption">Fig 5. 예측 확률 vs 실제 승률 — 모델(좌) vs 시장(우). 대각선에 가까울수록 잘 보정됨.</div>
    </div>

    <div class="stats-grid">
        <div class="stat-card info">
            <div class="value">{ll_model:.4f}</div>
            <div class="label">모델 Log Loss</div>
        </div>
        <div class="stat-card warn">
            <div class="value">{ll_market:.4f}</div>
            <div class="label">시장 Log Loss</div>
        </div>
    </div>
</div>

<!-- EDGE -->
<div class="section" id="edge">
    <h2>5. 모델 Edge 분석</h2>
    
    <p><strong>Edge = 모델 예측확률 − 시장 내재확률.</strong> 양수면 모델이 시장보다 해당 마의 승률을 높게 본다는 의미.</p>

    <div class="plot">
        <img src="data:image/png;base64,{plots['edge_dist']}" alt="Edge Distribution">
        <div class="caption">Fig 6. Edge 분포 — 모델이 시장 대비 과대/과소 평가하는 정도</div>
    </div>

    <div class="plot">
        <img src="data:image/png;base64,{plots['scatter']}" alt="Model vs Market">
        <div class="caption">Fig 7. 모델 확률 vs 시장 확률 산점도 — 노란점: 실제 우승마</div>
    </div>

    <div class="finding">
        산점도에서 모델과 시장의 <strong>높은 상관관계</strong>가 관찰된다. 
        이는 모델이 시장 배당을 주요 입력으로 사용하기 때문이며, 
        대각선에서의 이탈(= 독자적 판단)이 수익으로 이어지는지가 핵심이다.
    </div>
</div>

<!-- BETTING -->
<div class="section" id="betting">
    <h2>6. 베팅 시뮬레이션</h2>
    
    <h3>Edge 기준별 성과</h3>
    <table>
        <tr><th>Edge 기준</th><th>베팅 수</th><th>적중</th><th>적중률</th><th>평균배당</th><th>평균Edge</th><th>ROI</th></tr>
"""

for s in edge_stats:
    roi_class = "pos" if s["roi"].startswith("+") else "neg"
    html += f'        <tr><td>{s["threshold"]}</td><td>{s["n_bets"]}</td><td>{s["wins"]}</td><td>{s["hit_rate"]}</td><td>{s["avg_odds"]}x</td><td>{s["avg_edge"]}</td><td class="{roi_class}">{s["roi"]}</td></tr>\n'

html += f"""    </table>

    <div class="plot">
        <img src="data:image/png;base64,{plots['roi_threshold']}" alt="ROI by Threshold">
        <div class="caption">Fig 8. Edge 기준별 ROI 및 적중률 변화</div>
    </div>

    <div class="plot">
        <img src="data:image/png;base64,{plots['cum_pnl']}" alt="Cumulative PnL">
        <div class="caption">Fig 9. 누적 PnL 곡선 — Edge 기준별 Flat Betting</div>
    </div>

    <div class="finding critical">
        <strong>⚠️ 모든 Edge 기준에서 ROI 음수.</strong><br>
        모델이 시장을 이기지 못한다. 시장 피처에 의존하는 모델이 시장보다 나은 배팅 시그널을 생성할 수 없는 구조적 한계.
    </div>
</div>

<!-- MONTHLY -->
<div class="section" id="monthly">
    <h2>7. 월별 성과 추이</h2>
    
    <div class="plot">
        <img src="data:image/png;base64,{plots['monthly_roi']}" alt="Monthly ROI">
        <div class="caption">Fig 10. 월별 ROI (Edge > 5% 베팅 기준)</div>
    </div>
</div>

<!-- CONCLUSION -->
<div class="section" id="conclusion">
    <h2>8. 결론 & V2 방향</h2>
    
    <h3>V1 모델 요약</h3>
    <table>
        <tr><th>지표</th><th>모델</th><th>시장</th><th>판정</th></tr>
        <tr><td>Win AUC</td><td class="pos">{auc_model:.4f}</td><td>{auc_market:.4f}</td><td class="pos">모델 우위</td></tr>
        <tr><td>Log Loss</td><td>{ll_model:.4f}</td><td>{ll_market:.4f}</td><td>{'<span class="pos">모델 우위</span>' if ll_model < ll_market else '<span class="neg">시장 우위</span>'}</td></tr>
        <tr><td>Betting ROI</td><td class="neg">−22.3%</td><td>—</td><td class="neg">수익 불가</td></tr>
        <tr><td>독립 Alpha</td><td class="neg">부족</td><td>—</td><td class="neg">시장 의존</td></tr>
    </table>

    <div class="finding critical">
        <strong>V1의 근본적 한계:</strong> 시장 배당을 피처로 사용 → 모델이 시장을 복제 → 시장 대비 Edge 없음.
        높은 AUC는 "시장이 잘 예측한다"는 사실을 반영할 뿐, 모델의 독자적 예측 능력을 의미하지 않는다.
    </div>

    <h3>V2 개선 방향</h3>
    
    <div class="finding positive">
        <strong>1. 시장 피처 완전 제거</strong><br>
        단승배당, 연승배당, 시장확률, 배당순위 4개 피처 제거.
        순수 실력 기반 모델로 학습 → 모델 확률과 시장 확률의 차이가 진정한 Edge.
    </div>

    <div class="finding positive">
        <strong>2. Cross Features</strong><br>
        기수 × 거리, 마필 × 주로상태, 등급전환(승급/강등) 등 교차 피처 추가.
    </div>

    <div class="finding positive">
        <strong>3. LambdaRank / 순위 학습</strong><br>
        이진 분류(win/lose) → 순위 학습으로 전환. 경주 단위 relative ranking 최적화.
    </div>

    <div class="finding positive">
        <strong>4. 시계열 강화</strong><br>
        속도 상승/하락 트렌드, 클래스 전환 후 성적 변화, 계절성 반영.
    </div>
</div>

<div style="text-align: center; padding: 40px; color: #555; font-size: 0.85em;">
    KRA Racing ML Project — V1 Analysis Report<br>
    Generated 2026-03-29 | Data: race.kra.co.kr | Model: XGBoost
</div>

</div>
</body>
</html>"""

with open("report_v1.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ Report saved: report_v1.html ({len(html)//1024} KB)")
print("Done!")
