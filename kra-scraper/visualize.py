#!/usr/bin/env python3
"""Generate visualization charts for KRA model results."""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pickle, json
from sklearn.metrics import roc_curve, roc_auc_score, precision_recall_curve
from sklearn.calibration import calibration_curve

# Try Korean font
for fname in ["/System/Library/Fonts/AppleSDGothicNeo.ttc", "/System/Library/Fonts/Supplemental/AppleGothic.ttf"]:
    try:
        font_manager.fontManager.addfont(fname)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=fname).get_name()
        break
    except:
        pass
plt.rcParams["axes.unicode_minus"] = False

# ─── Load data ───
df = pd.read_csv("kra_seoul_final.csv", encoding="utf-8-sig", dtype=str)

# Quick re-run feature engineering (load from saved predictions if available)
# For simplicity, re-load model and recompute
model_win = pickle.load(open("model_win.pkl", "rb"))
model_place = pickle.load(open("model_place.pkl", "rb"))
fi = pd.read_csv("feature_importance.csv")

# ═══════════════════════════════════════════
# CHART 1: Feature Importance (Top 15)
# ═══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 7))
top15 = fi.head(15).iloc[::-1]
colors = plt.cm.viridis(np.linspace(0.3, 0.9, 15))
bars = ax.barh(top15["feature"], top15["importance"], color=colors)
ax.set_xlabel("Importance (Gain)", fontsize=12)
ax.set_title("Feature Importance — Win Model (Top 15)", fontsize=14, fontweight="bold")
for bar, val in zip(bars, top15["importance"]):
    ax.text(val + 0.002, bar.get_y() + bar.get_height()/2, f"{val:.3f}", va="center", fontsize=9)
plt.tight_layout()
plt.savefig("chart_feature_importance.png", dpi=150)
plt.close()
print("✅ chart_feature_importance.png")

# ═══════════════════════════════════════════
# CHART 2: ROC Curve (need predictions — regenerate quickly)
# ═══════════════════════════════════════════
# We need to regenerate predictions. Load the engineered data.
# Since model.py already ran, let's just regenerate test predictions.
exec(open("model.py").read().split("# ─── 7. XGBOOST")[0])  # Run up to feature engineering

test_mask = df["경주일자"] >= "2025-01-01"
train_mask = df["경주일자"] < "2025-01-01"
FEATURES = [c for c in model_win.get_booster().feature_names]
X_test = df.loc[test_mask, FEATURES].fillna(-1)
y_test_win = df.loc[test_mask, "win"]
y_test_place = df.loc[test_mask, "place"]

y_pred_win = model_win.predict_proba(X_test)[:, 1]
y_pred_place = model_place.predict_proba(X_test)[:, 1]

# ROC curves
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for ax, y_true, y_pred, title, auc_val in [
    (axes[0], y_test_win, y_pred_win, "Win Model", roc_auc_score(y_test_win, y_pred_win)),
    (axes[1], y_test_place, y_pred_place, "Place Model", roc_auc_score(y_test_place, y_pred_place)),
]:
    fpr, tpr, _ = roc_curve(y_true, y_pred)
    ax.plot(fpr, tpr, "b-", linewidth=2, label=f"AUC = {auc_val:.4f}")
    ax.plot([0, 1], [0, 1], "r--", alpha=0.5, label="Random")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(f"ROC Curve — {title}", fontweight="bold")
    ax.legend(fontsize=12, loc="lower right")
    ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig("chart_roc_curve.png", dpi=150)
plt.close()
print("✅ chart_roc_curve.png")

# ═══════════════════════════════════════════
# CHART 3: Calibration Plot
# ═══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 8))
prob_true, prob_pred = calibration_curve(y_test_win, y_pred_win, n_bins=15, strategy="quantile")
ax.plot(prob_pred, prob_true, "bo-", linewidth=2, markersize=8, label="Win Model")
ax.plot([0, 1], [0, 1], "r--", alpha=0.5, label="Perfect Calibration")
ax.set_xlabel("Predicted Probability", fontsize=12)
ax.set_ylabel("Actual Win Rate", fontsize=12)
ax.set_title("Calibration Plot — Win Model", fontsize=14, fontweight="bold")
ax.legend(fontsize=12)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("chart_calibration.png", dpi=150)
plt.close()
print("✅ chart_calibration.png")

# ═══════════════════════════════════════════
# CHART 4: Betting Simulation — Cumulative P&L
# ═══════════════════════════════════════════
test_df = df.loc[test_mask].copy()
test_df["pred_win_prob"] = y_pred_win
test_df["시장확률_clean"] = 1 / pd.to_numeric(test_df["단승배당"], errors="coerce").replace(0, np.nan)
test_df["edge"] = test_df["pred_win_prob"] - test_df["시장확률_clean"]
test_df["단승배당_num"] = pd.to_numeric(test_df["단승배당"], errors="coerce")

fig, axes = plt.subplots(2, 1, figsize=(14, 10))

for ax, threshold, color, label in [
    (axes[0], 0.05, "blue", "Edge > 5%"),
    (axes[0], 0.10, "green", "Edge > 10%"),
    (axes[0], 0.15, "orange", "Edge > 15%"),
    (axes[0], 0.20, "red", "Edge > 20%"),
]:
    bets = test_df[test_df["edge"] > threshold].copy()
    bets = bets.sort_values("경주일자")
    # Flat: -1 per bet, +odds if win
    bets["pnl"] = bets.apply(lambda r: r["단승배당_num"] - 1 if r["win"] == 1 else -1, axis=1)
    bets["cum_pnl"] = bets["pnl"].cumsum()
    ax.plot(range(len(bets)), bets["cum_pnl"].values, color=color, alpha=0.8, label=f"{label} (n={len(bets)})")

axes[0].axhline(y=0, color="black", linestyle="-", alpha=0.3)
axes[0].set_xlabel("Bet #")
axes[0].set_ylabel("Cumulative P&L (units)")
axes[0].set_title("Cumulative P&L by Edge Threshold (Flat Betting)", fontweight="bold")
axes[0].legend()
axes[0].grid(alpha=0.3)

# By predicted probability decile
test_df["pred_decile"] = pd.qcut(test_df["pred_win_prob"], 10, labels=False, duplicates="drop")
decile_stats = test_df.groupby("pred_decile").agg(
    count=("win", "count"),
    wins=("win", "sum"),
    avg_pred=("pred_win_prob", "mean"),
    avg_odds=("단승배당_num", "mean"),
).reset_index()
decile_stats["actual_wr"] = decile_stats["wins"] / decile_stats["count"]
decile_stats["roi"] = (decile_stats.apply(
    lambda r: test_df[(test_df["pred_decile"] == r["pred_decile"]) & (test_df["win"] == 1)]["단승배당_num"].sum() - r["count"],
    axis=1
)) / decile_stats["count"] * 100

x = range(len(decile_stats))
axes[1].bar(x, decile_stats["actual_wr"] * 100, alpha=0.7, color="steelblue", label="Actual Win %")
axes[1].plot(x, decile_stats["avg_pred"] * 100, "ro-", label="Predicted Win %")
ax2 = axes[1].twinx()
ax2.plot(x, decile_stats["roi"], "g^-", linewidth=2, markersize=8, label="ROI %")
ax2.axhline(y=0, color="green", linestyle="--", alpha=0.3)
ax2.set_ylabel("ROI %", color="green")
axes[1].set_xlabel("Prediction Decile (0=lowest, 9=highest)")
axes[1].set_ylabel("Win Rate %")
axes[1].set_title("Win Rate & ROI by Prediction Decile", fontweight="bold")
axes[1].legend(loc="upper left")
ax2.legend(loc="upper right")
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("chart_betting_simulation.png", dpi=150)
plt.close()
print("✅ chart_betting_simulation.png")

# ═══════════════════════════════════════════
# CHART 5: Data Summary Table
# ═══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 8))
ax.axis("off")

# Summary stats
summary_data = [
    ["Dataset", "Seoul Racecourse (서울경마장)", "", ""],
    ["Period", "2020/01 ~ 2026/03", "Race Days", "551"],
    ["Total Rows", "64,720", "Features", "40"],
    ["Train Set", "51,232 (< 2025)", "Test Set", "13,488 (2025~)"],
    ["", "", "", ""],
    ["Model", "Win (1착)", "Place (3착↑)", ""],
    ["ROC AUC", "0.8127", "0.7799", ""],
    ["", "", "", ""],
    ["Edge Filter", "Bets", "Hit Rate", "ROI"],
    ["> 5%", "12,327", "10.4%", "-22.3%"],
    ["> 10%", "10,542", "11.9%", "-20.3%"],
    ["> 15%", "9,289", "13.0%", "-17.9%"],
    ["> 20%", "8,129", "14.1%", "-17.8%"],
    ["", "", "", ""],
    ["Top 3 Features", "시장확률 (25.5%)", "단승배당 (14.0%)", "배당순위 (5.1%)"],
]

table = ax.table(cellText=summary_data, cellLoc="center", loc="center",
                 colWidths=[0.2, 0.3, 0.25, 0.25])
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 1.8)

# Style header rows
for i in [0, 5, 8, 14]:
    for j in range(4):
        table[i, j].set_facecolor("#2c3e50")
        table[i, j].set_text_props(color="white", fontweight="bold")

for i in [4, 7, 13]:
    for j in range(4):
        table[i, j].set_facecolor("white")
        table[i, j].set_edgecolor("white")

ax.set_title("KRA Horse Racing ML — Model Summary", fontsize=16, fontweight="bold", pad=20)
plt.tight_layout()
plt.savefig("chart_summary_table.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ chart_summary_table.png")

print("\n🎉 All charts generated!")
