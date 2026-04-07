#!/usr/bin/env python3
"""Generate charts from saved model results — standalone, no re-training needed."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd

# Korean font
for fname in ["/System/Library/Fonts/AppleSDGothicNeo.ttc", "/System/Library/Fonts/Supplemental/AppleGothic.ttf"]:
    try:
        font_manager.fontManager.addfont(fname)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=fname).get_name()
        break
    except:
        pass
plt.rcParams["axes.unicode_minus"] = False

# ═══ CHART 1: Feature Importance ═══
fi = pd.read_csv("feature_importance.csv")
top15 = fi.head(15).iloc[::-1]

fig, ax = plt.subplots(figsize=(10, 7))
colors = plt.cm.viridis(np.linspace(0.3, 0.9, 15))
bars = ax.barh(range(15), top15["importance"].values, color=colors)
ax.set_yticks(range(15))
ax.set_yticklabels(top15["feature"].values, fontsize=10)
ax.set_xlabel("Importance (Gain)", fontsize=12)
ax.set_title("🏇 Feature Importance — Win Model (Top 15)", fontsize=14, fontweight="bold")
for i, (bar, val) in enumerate(zip(bars, top15["importance"].values)):
    ax.text(val + 0.003, i, f"{val:.3f}", va="center", fontsize=9)
plt.tight_layout()
plt.savefig("chart_feature_importance.png", dpi=150)
plt.close()
print("✅ chart_feature_importance.png")

# ═══ CHART 2: Summary Dashboard ═══
fig = plt.figure(figsize=(16, 12))

# ── Panel 1: Model Performance ──
ax1 = fig.add_subplot(2, 2, 1)
models = ["Win Model\n(1착 예측)", "Place Model\n(3착이내 예측)"]
aucs = [0.8127, 0.7799]
colors = ["#2ecc71", "#3498db"]
bars = ax1.bar(models, aucs, color=colors, width=0.5, edgecolor="white", linewidth=2)
for bar, val in zip(bars, aucs):
    ax1.text(bar.get_x() + bar.get_width()/2, val + 0.01, f"{val:.4f}",
             ha="center", va="bottom", fontsize=14, fontweight="bold")
ax1.set_ylim(0.5, 0.9)
ax1.axhline(y=0.5, color="red", linestyle="--", alpha=0.5, label="Random (0.5)")
ax1.set_ylabel("ROC AUC", fontsize=12)
ax1.set_title("모델 성능 (ROC AUC)", fontsize=13, fontweight="bold")
ax1.legend()
ax1.grid(axis="y", alpha=0.3)

# ── Panel 2: Betting ROI by Edge ──
ax2 = fig.add_subplot(2, 2, 2)
edges = ["5%", "10%", "15%", "20%"]
bets_n = [12327, 10542, 9289, 8129]
hit_rates = [10.4, 11.9, 13.0, 14.1]
rois = [-22.3, -20.3, -17.9, -17.8]

x = np.arange(len(edges))
ax2b = ax2.twinx()
bars = ax2.bar(x - 0.15, hit_rates, 0.3, color="#e74c3c", alpha=0.7, label="Hit Rate %")
line = ax2b.plot(x, rois, "go-", markersize=10, linewidth=2, label="ROI %")
ax2b.axhline(y=0, color="green", linestyle="--", alpha=0.3)

for i, (h, r, n) in enumerate(zip(hit_rates, rois, bets_n)):
    ax2.text(i - 0.15, h + 0.3, f"{h}%", ha="center", fontsize=9)
    ax2b.text(i + 0.05, r + 1, f"{r:+.1f}%", ha="center", fontsize=9, color="green")

ax2.set_xticks(x)
ax2.set_xticklabels([f"Edge>{e}\n(n={n:,})" for e, n in zip(edges, bets_n)])
ax2.set_ylabel("Hit Rate %", color="#e74c3c")
ax2b.set_ylabel("ROI %", color="green")
ax2.set_title("Edge별 적중률 & ROI", fontsize=13, fontweight="bold")
ax2.legend(loc="upper left")
ax2b.legend(loc="upper right")
ax2.grid(axis="y", alpha=0.3)

# ── Panel 3: Data Overview ──
ax3 = fig.add_subplot(2, 2, 3)
years = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
rows = [7404, 10482, 10863, 11232, 10986, 11020, 2733]
colors_yr = ["#95a5a6"] * 4 + ["#3498db"] + ["#e74c3c"] * 2
bars = ax3.bar(years, rows, color=colors_yr, edgecolor="white")
for bar, val in zip(bars, rows):
    ax3.text(bar.get_x() + bar.get_width()/2, val + 200, f"{val:,}",
             ha="center", fontsize=9)
ax3.axvline(x=2024.5, color="red", linestyle="--", alpha=0.7)
ax3.text(2024.7, max(rows) * 0.9, "← Train | Test →", fontsize=10, color="red")
ax3.set_xlabel("Year")
ax3.set_ylabel("Rows")
ax3.set_title("데이터 분포 (연도별 rows)", fontsize=13, fontweight="bold")
ax3.grid(axis="y", alpha=0.3)

# ── Panel 4: Key Stats Table ──
ax4 = fig.add_subplot(2, 2, 4)
ax4.axis("off")

stats = [
    ["항목", "값"],
    ["총 데이터", "64,720 rows"],
    ["피처 수", "40개"],
    ["기간", "2020.01 ~ 2026.03"],
    ["경주일수", "551일"],
    ["모델", "XGBoost"],
    ["Win AUC", "0.8127"],
    ["Place AUC", "0.7799"],
    ["Top 피처", "시장확률 (25.5%)"],
    ["2nd 피처", "단승배당 (14.0%)"],
    ["3rd 피처", "배당순위 (5.1%)"],
    ["", ""],
    ["⚠️ 문제점", "시장확률 의존도 과다"],
    ["→ 개선", "순수 실력 모델 필요"],
]

table = ax4.table(cellText=stats, cellLoc="center", loc="center", colWidths=[0.4, 0.6])
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 1.6)
table[0, 0].set_facecolor("#2c3e50")
table[0, 0].set_text_props(color="white", fontweight="bold")
table[0, 1].set_facecolor("#2c3e50")
table[0, 1].set_text_props(color="white", fontweight="bold")
for i in [12, 13]:
    table[i, 0].set_facecolor("#fff3cd")
    table[i, 1].set_facecolor("#fff3cd")

ax4.set_title("모델 요약", fontsize=13, fontweight="bold")

plt.suptitle("🏇 KRA 서울경마 ML 예측 모델 — V1 Results", fontsize=16, fontweight="bold", y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig("chart_dashboard.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ chart_dashboard.png")

print("\n🎉 Done!")
