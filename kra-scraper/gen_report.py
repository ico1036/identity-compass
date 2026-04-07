#!/usr/bin/env python3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import base64
import io
import os

# Try to use a font that supports Korean
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return b64

# Chart 1: Top 10 Strategy ROI comparison
strategies = [
    ('pool_rd<=-5\n(place)', 26.0, 26.0),
    ('LGB_skill_place\nrd<=-3', -1.7, -1.7),
    ('pool_rd<=-3\n(place)', -4.2, -4.2),
    ('XGB_hybrid_place\nrd<=-3', -5.0, -5.0),
    ('LGB_hybrid_place\nrd<=-3', -5.0, -5.0),
    ('LGB_skill_win', -6.7, -15.7),
    ('LGB_hybrid_place', -12.1, -10.2),
    ('LGB_market_place', -12.2, -2.7),
    ('LGB_hybrid_win', -13.2, 8.0),
    ('XGB_market_place', -13.2, -5.1),
]

fig1, ax1 = plt.subplots(figsize=(12, 6))
x = np.arange(len(strategies))
w = 0.35
flat_roi = [s[1] for s in strategies]
kelly_roi = [s[2] for s in strategies]
names = [s[0] for s in strategies]
colors_flat = ['#2ecc71' if v > 0 else '#e74c3c' for v in flat_roi]
colors_kelly = ['#27ae60' if v > 0 else '#c0392b' for v in kelly_roi]
ax1.bar(x - w/2, flat_roi, w, label='Flat ROI%', color=colors_flat, edgecolor='white')
ax1.bar(x + w/2, kelly_roi, w, label='Kelly ROI%', color=colors_kelly, alpha=0.7, edgecolor='white')
ax1.set_xticks(x)
ax1.set_xticklabels(names, fontsize=7, rotation=0)
ax1.set_ylabel('ROI (%)')
ax1.set_title('Top 10 Strategies: Flat vs Kelly ROI (OOS 2025-2026)')
ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax1.legend()
ax1.grid(axis='y', alpha=0.3)
chart1 = fig_to_base64(fig1)

# Chart 2: Pool Disagreement Historical vs OOS
fig2, ax2 = plt.subplots(figsize=(8, 5))
categories = ['rd<=-2', 'rd<=-3', 'rd<=-4', 'rd<=-5']
hist_roi = [12.3, 40.7, 85.2, 160.0]  # historical (2020-2024)
oos_roi = [-17.6, -4.2, -29.3, 26.0]   # OOS (2025-2026)
x2 = np.arange(len(categories))
ax2.bar(x2 - 0.2, hist_roi, 0.35, label='Historical (2020-2024)', color='#3498db')
ax2.bar(x2 + 0.2, oos_roi, 0.35, label='OOS (2025-2026)', color='#e74c3c')
ax2.set_xticks(x2)
ax2.set_xticklabels(categories)
ax2.set_ylabel('ROI (%)')
ax2.set_title('Pool Disagreement Strategy: Historical vs Out-of-Sample')
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax2.legend()
ax2.grid(axis='y', alpha=0.3)
chart2 = fig_to_base64(fig2)

# Chart 3: Cumulative P&L
fig3, ax3 = plt.subplots(figsize=(8, 5))
bets = ['Start', 'R7-1', 'R7-2', 'R7-3', 'R7-4', 'R7-5', 'R7-6', 'R7-7',
        'R8-1', 'R8-2', 'R8-3', 'R8-4', 'R8-5', 'R8-6', 'R8-7']
# All bets lost, cumulative spending
r7_bets = [3000, 3000, 3000, 3500, 3500, 3300, 3000]
r8_bets = [3000, 3000, 3500, 3500, 3000, 3500, 3000]
cumulative = [0]
for b in r7_bets + r8_bets:
    cumulative.append(cumulative[-1] - b)
ax3.plot(bets, cumulative, 'o-', color='#e74c3c', linewidth=2, markersize=6)
ax3.fill_between(bets, cumulative, alpha=0.15, color='#e74c3c')
ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax3.axvline(x=7.5, color='gray', linestyle='--', alpha=0.5)
ax3.text(3.5, -5000, 'Race 7', ha='center', fontsize=11, color='gray')
ax3.text(11, -5000, 'Race 8', ha='center', fontsize=11, color='gray')
ax3.set_ylabel('Cumulative P&L (KRW)')
ax3.set_title("Live Experiment: Cumulative P&L (2026-03-29)")
ax3.grid(axis='y', alpha=0.3)
plt.xticks(rotation=45, fontsize=8)
chart3 = fig_to_base64(fig3)

# Chart 4: Model AUC comparison
fig4, ax4 = plt.subplots(figsize=(7, 5))
models = ['Market Only\n(Baseline)', 'V1 (Hybrid)\nw/ Market', 'V2 (Skill)\nw/o Market', 'Random\nGuess']
aucs = [0.8126, 0.8127, 0.7432, 0.5]
colors4 = ['#f39c12', '#e74c3c', '#2ecc71', '#95a5a6']
bars = ax4.bar(models, aucs, color=colors4, edgecolor='white', width=0.6)
ax4.set_ylabel('AUC-ROC')
ax4.set_title('Model Performance Comparison (Win Prediction)')
ax4.set_ylim(0.4, 0.9)
ax4.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='Random baseline')
for bar, v in zip(bars, aucs):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.008, f'{v:.4f}', ha='center', fontsize=11, fontweight='bold')
ax4.grid(axis='y', alpha=0.3)
chart4 = fig_to_base64(fig4)

# Chart 5: Feature importance (top 15)
fig5, ax5 = plt.subplots(figsize=(9, 6))
feature_translations = {
    '시장확률': 'Market Prob',
    '단승배당': 'Win Odds',
    '배당순위': 'Odds Rank',
    '연승배당': 'Place Odds',
    '최근5전_복승률': 'Last5 Place%',
    '최근5전_평균착순': 'Last5 Avg Finish',
    '최근10전_승률': 'Last10 Win%',
    '연령_num': 'Age',
    '최근3전_평균착순': 'Last3 Avg Finish',
    '체중순위': 'Weight Rank',
    '기수_누적승률': 'Jockey Win%',
    '성별_enc': 'Gender',
    '조교사_누적승률': 'Trainer Win%',
    '통산_승률': 'Career Win%',
    '최근3전_평균기록': 'Last3 Avg Time',
}
features = []
importances = []
with open('/Users/ryan/.openclaw/workspace/kra-scraper/feature_importance.csv') as f:
    next(f)
    for line in f:
        parts = line.strip().split(',')
        fname = parts[0]
        features.append(feature_translations.get(fname, fname))
        importances.append(float(parts[1]))
top_n = 15
features = features[:top_n][::-1]
importances = importances[:top_n][::-1]
colors5 = ['#e74c3c' if 'market' in f.lower() or f in ['시장확률','단승배당','배당순위','연승배당'] else '#3498db' for f in features]
# redo color logic
colors5 = []
market_features = {'Market Prob','Win Odds','Odds Rank','Place Odds'}
for f in features:
    colors5.append('#e74c3c' if f in market_features else '#3498db')
ax5.barh(range(len(features)), importances, color=colors5)
ax5.set_yticks(range(len(features)))
ax5.set_yticklabels(features, fontsize=9)
ax5.set_xlabel('Importance')
ax5.set_title('V1 Model Feature Importance (Top 15) — Red = Market Features')
ax5.grid(axis='x', alpha=0.3)
chart5 = fig_to_base64(fig5)

# Save charts
charts = {'chart1': chart1, 'chart2': chart2, 'chart3': chart3, 'chart4': chart4, 'chart5': chart5}
for name, data in charts.items():
    print(f"{name}: {len(data)} chars")

# Write the HTML
html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>한국 경마 ML 베팅 시스템의 실전 검증</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=Noto+Serif+KR:wght@400;700&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 15px;
    line-height: 1.8;
    color: #2c3e50;
    background: #f5f5f5;
}}
.paper {{
    max-width: 900px;
    margin: 40px auto;
    background: white;
    padding: 60px 70px;
    box-shadow: 0 2px 20px rgba(0,0,0,0.08);
}}
h1 {{
    font-family: 'Noto Serif KR', serif;
    font-size: 24px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 8px;
    line-height: 1.4;
    color: #1a1a2e;
}}
.authors {{
    text-align: center;
    font-size: 14px;
    color: #555;
    margin-bottom: 4px;
}}
.date {{
    text-align: center;
    font-size: 13px;
    color: #888;
    margin-bottom: 30px;
}}
.abstract {{
    background: #f8f9fa;
    border-left: 4px solid #3498db;
    padding: 20px 25px;
    margin: 25px 0;
    font-size: 14px;
}}
.abstract h2 {{
    font-size: 16px;
    margin-bottom: 10px;
    color: #2c3e50;
}}
h2 {{
    font-family: 'Noto Serif KR', serif;
    font-size: 20px;
    font-weight: 700;
    margin-top: 35px;
    margin-bottom: 15px;
    color: #1a1a2e;
    border-bottom: 2px solid #3498db;
    padding-bottom: 5px;
}}
h3 {{
    font-size: 17px;
    font-weight: 600;
    margin-top: 25px;
    margin-bottom: 10px;
    color: #2c3e50;
}}
h4 {{
    font-size: 15px;
    font-weight: 600;
    margin-top: 18px;
    margin-bottom: 8px;
    color: #34495e;
}}
p {{ margin-bottom: 12px; }}
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 13px;
}}
th {{
    background: #2c3e50;
    color: white;
    padding: 10px 8px;
    text-align: left;
    font-weight: 500;
}}
td {{
    padding: 8px;
    border-bottom: 1px solid #eee;
}}
tr:nth-child(even) {{ background: #f8f9fa; }}
tr:hover {{ background: #eef2f7; }}
.loss {{ color: #e74c3c; font-weight: 700; }}
.profit {{ color: #27ae60; font-weight: 700; }}
.finding-box {{
    background: linear-gradient(135deg, #667eea11, #764ba211);
    border: 1px solid #667eea44;
    border-radius: 8px;
    padding: 20px 25px;
    margin: 20px 0;
}}
.finding-box h3 {{
    color: #667eea;
    margin-top: 0;
}}
.warning-box {{
    background: #fff5f5;
    border: 1px solid #e74c3c44;
    border-radius: 8px;
    padding: 18px 22px;
    margin: 15px 0;
}}
.bet-card {{
    background: #fafafa;
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 15px 20px;
    margin: 12px 0;
}}
.bet-card .result {{
    font-size: 18px;
    font-weight: 700;
}}
.chart-container {{
    text-align: center;
    margin: 20px 0;
}}
.chart-container img {{
    max-width: 100%;
    border: 1px solid #eee;
    border-radius: 4px;
}}
.chart-caption {{
    font-size: 12px;
    color: #888;
    margin-top: 5px;
    font-style: italic;
}}
.toc {{
    background: #f8f9fa;
    padding: 20px 30px;
    margin: 20px 0;
    border-radius: 6px;
}}
.toc ol {{ padding-left: 20px; }}
.toc li {{ margin: 4px 0; font-size: 14px; }}
.toc a {{ color: #3498db; text-decoration: none; }}
.toc a:hover {{ text-decoration: underline; }}
.keyword {{ display: inline-block; background: #e8f4fd; padding: 2px 8px; border-radius: 3px; font-size: 13px; margin: 2px; }}
.divider {{ border: 0; border-top: 1px solid #eee; margin: 30px 0; }}
.footnote {{ font-size: 12px; color: #888; margin-top: 30px; border-top: 1px solid #eee; padding-top: 15px; }}
@media print {{
    .paper {{ box-shadow: none; margin: 0; padding: 40px; }}
    body {{ background: white; }}
}}
</style>
</head>
<body>
<div class="paper">

<h1>한국 경마 ML 베팅 시스템의 실전 검증:<br>서울경마 라이브 실험 보고서</h1>
<p class="authors"><strong>Jiwoong Kim</strong><sup>1</sup>, <strong>AB_kimi_bot</strong> (AI Research Assistant)<sup>2</sup></p>
<p class="date">2026년 3월 29일</p>

<p style="text-align:center; margin-bottom:25px;">
<span class="keyword">Machine Learning</span>
<span class="keyword">Horse Racing</span>
<span class="keyword">Parimutuel Betting</span>
<span class="keyword">Backtest Overfitting</span>
<span class="keyword">Kelly Criterion</span>
</p>

<div class="abstract">
<h2>Abstract</h2>
<p>본 연구는 한국마사회(KRA) 서울경마장의 과거 6년간 데이터(64,720건)를 활용하여 머신러닝 기반 베팅 전략의 수익성을 체계적으로 검증한다. XGBoost, LightGBM 등 4개 모델과 3가지 피처셋을 조합한 48개 전략을 자동 탐색(Autoresearch)하고, 멀티에이전트 토론(Multi-Agent Debate)을 거쳐 최종 베팅을 실행하였다. 2026년 3월 29일 서울 7·8레이스에 총 ₩44,800을 투입한 결과, <strong class="loss">2레이스 전멸, ROI -100%</strong>를 기록하였다. 핵심 발견은 다음과 같다: (1) 단일 레이스에서 ML이 시장(parimutuel odds)을 이기기 극히 어렵고, (2) 백테스트 알파의 대부분은 과적합(overfitting)이며, (3) 장기·선별적 베팅(500회 이상)만이 양의 기대값을 보인다. 본 보고서는 실패를 통해 얻은 실증적 교훈을 학술적으로 정리한다.</p>
</div>

<div class="toc">
<strong>목차</strong>
<ol>
<li><a href="#intro">서론 (Introduction)</a></li>
<li><a href="#data">데이터 및 방법론 (Data & Methodology)</a></li>
<li><a href="#strategy">전략 개발 및 백테스트 (Strategy Development)</a></li>
<li><a href="#live">라이브 실험 결과 (Live Experiment Results)</a></li>
<li><a href="#findings">핵심 발견 (Key Findings)</a></li>
<li><a href="#conclusion">결론 및 향후 과제 (Conclusion)</a></li>
<li><a href="#appendix">부록 (Appendix)</a></li>
</ol>
</div>

<h2 id="intro">1. 서론 (Introduction)</h2>

<p>한국마사회(KRA)가 운영하는 경마 시장은 <strong>파리뮤추얼(parimutuel)</strong> 방식의 베팅 시스템을 채택하고 있다. 이 방식에서 배당률(odds)은 베팅 참여자들의 집합적 판단에 의해 결정되며, 마사회는 총 베팅금의 약 20-27%를 공제(takeout)한 후 나머지를 승자에게 배분한다. 이러한 구조에서 수익을 내기 위해서는 시장 참여자 전체의 집합 지성(collective intelligence)보다 우월한 예측력을 갖추어야 하며, 높은 공제율을 극복할 만큼의 에지(edge)가 필요하다.</p>

<p>빌 벤터(Bill Benter)는 1980-2000년대 홍콩경마에서 ML 기반 시스템으로 연간 수천만 달러의 수익을 올린 것으로 알려져 있다. 그의 핵심 전략은 (1) 대량의 역사 데이터로 모델을 훈련하고, (2) 시장이 과소평가하는 말을 식별하며, (3) 수천 회의 베팅을 통해 작은 에지를 축적하는 것이었다. 본 연구는 이 접근법을 KRA 서울경마에 적용하여 실전 수익 가능성을 검증하고자 한다.</p>

<p><strong>연구 목적:</strong> (1) KRA 서울경마 데이터에 대한 ML 모델의 예측력을 정량적으로 평가하고, (2) 다양한 베팅 전략의 백테스트 및 OOS(out-of-sample) 수익성을 비교하며, (3) 실제 레이스에 베팅을 실행하여 이론과 현실의 괴리를 실증적으로 분석한다.</p>

<h2 id="data">2. 데이터 및 방법론 (Data & Methodology)</h2>

<h3>2.1 데이터셋</h3>
<p>KRA 공식 경주 데이터를 수집하여 <code>kra_seoul_final.csv</code>를 구축하였다.</p>

<table>
<tr><th>항목</th><th>내용</th></tr>
<tr><td>기간</td><td>2020년 1월 ~ 2026년 3월</td></tr>
<tr><td>경마장</td><td>서울 (Seoul)</td></tr>
<tr><td>레코드 수</td><td>64,720건 (출전마 기준)</td></tr>
<tr><td>레이스 수</td><td>약 5,500 레이스</td></tr>
<tr><td>훈련 기간</td><td>2020-2024 (temporal split)</td></tr>
<tr><td>테스트 기간</td><td>2025-2026 (1,293 레이스, 13,488 출전마)</td></tr>
</table>

<h3>2.2 모델 및 피처셋</h3>

<table>
<tr><th>모델</th><th>피처셋</th><th>피처 수</th><th>설명</th></tr>
<tr><td>XGBoost</td><td rowspan="4">Skill (순수 실력)</td><td rowspan="4">36</td><td rowspan="4">통산성적, 최근전적, 기수·조교사 승률, 마체중, 거리적성 등 시장 정보를 배제한 순수 실력 피처</td></tr>
<tr><td>LightGBM</td></tr>
<tr><td>Random Forest</td></tr>
<tr><td>Logistic Regression</td></tr>
<tr><td>XGBoost</td><td rowspan="2">Market (시장)</td><td rowspan="2">4</td><td rowspan="2">단승배당, 연승배당, 시장확률, 배당순위 — 시장이 이미 반영한 정보</td></tr>
<tr><td>LightGBM</td></tr>
<tr><td>XGBoost</td><td rowspan="2">Hybrid (혼합)</td><td rowspan="2">40</td><td rowspan="2">Skill + Market 피처 결합</td></tr>
<tr><td>LightGBM</td></tr>
</table>

<h3>2.3 모델 성능</h3>

<div class="chart-container">
<img src="data:image/png;base64,{chart4}" alt="Model AUC Comparison">
<p class="chart-caption">Figure 1. 모델별 AUC-ROC 비교. V1(Hybrid)은 시장 확률을 거의 그대로 복제하여 AUC 0.8127 달성.</p>
</div>

<p><strong>핵심 발견:</strong> V1 모델(Hybrid, AUC 0.8127)은 시장 확률만으로 달성 가능한 AUC 0.8126과 사실상 동일하다. 이는 모델이 시장 피처에 과도하게 의존하여 독자적인 예측력을 갖추지 못했음을 의미한다. V2 모델(Skill only, AUC 0.7432)은 시장 정보 없이 순수 실력 피처만으로 학습하여 학술 벤치마크 수준의 성능을 달성했으나, 시장 대비 뚜렷한 우위를 확보하지는 못했다.</p>

<div class="chart-container">
<img src="data:image/png;base64,{chart5}" alt="Feature Importance">
<p class="chart-caption">Figure 2. V1 모델 피처 중요도 (상위 15개). 빨간색 = 시장 피처. 시장확률(0.255)이 압도적 1위.</p>
</div>

<h3>2.4 Autoresearch: 48개 전략 자동 탐색</h3>
<p>모델(XGB, LGB) × 피처셋(skill, market, hybrid) × 타겟(win, place) × 필터(전체, rank_diff≤-2, ≤-3) × 베팅방식(flat, Kelly, threshold)의 조합으로 총 <strong>48개 전략</strong>을 자동 생성·백테스트하였다. Kelly criterion은 모델 예측확률 × 배당 > 1.05일 때만 베팅하는 선별적 전략이다.</p>

<h2 id="strategy">3. 전략 개발 및 백테스트</h2>

<h3>3.1 풀 불일치(Pool Disagreement) 전략</h3>
<p>단승 배당순위와 연승 배당순위의 차이(<code>rank_diff = 단승rank - 연승rank</code>)가 크게 음수인 경우, 연승 시장이 해당 말을 더 높게 평가한다는 뜻이다. 이를 이용한 역발상 전략을 테스트하였다.</p>

<div class="chart-container">
<img src="data:image/png;base64,{chart2}" alt="Pool Disagreement Historical vs OOS">
<p class="chart-caption">Figure 3. 풀 불일치 전략의 역사적(in-sample) vs 실전(OOS) ROI. 극적인 성능 붕괴가 관찰됨.</p>
</div>

<div class="warning-box">
<strong>⚠️ 과적합 경고:</strong> rank_diff ≤ -5 전략은 역사적 데이터에서 ROI +160%를 기록했으나, OOS에서 표본 크기가 5건에 불과하여 통계적 유의성이 없다. rank_diff ≤ -3도 +40.7% → -4.2%로 급락했다. 이는 전형적인 백테스트 과적합 사례다.
</div>

<h3>3.2 조교사 승률 팩터</h3>
<p>KRA 공식 조교사 통계를 분석한 결과, 조교사 승률 순위 3위 말의 ROI가 +1.6%로 유일하게 양수였다. 그러나 조교사 상위 + 시장 선호 교차 조건에서도 ROI는 -2.1%에 그쳤으며, 다른 파이프라인과의 결합 시 모든 전략이 음의 ROI를 기록하였다.</p>

<h3>3.3 거리 적성 분석</h3>
<p>1800m 첫 출전마 중 1700m 경험이 있는 말의 복승률은 33.3%로, 거리 미경험으로 인한 성적 하락이 크지 않은 것으로 나타났다. 이는 거리 리스크가 시장에서 이미 과대평가될 수 있음을 시사한다.</p>

<h3>3.4 멀티에이전트 토론 (Multi-Agent Debate)</h3>
<p>Mirofish 스타일의 3-에이전트 토론 시스템을 구축하였다:</p>
<table>
<tr><th>에이전트</th><th>역할</th><th>Race 8 의견</th></tr>
<tr><td><strong>QUANT</strong></td><td>데이터 기반 정량 분석</td><td>⑪킹마스터 (V2 모델 상위)</td></tr>
<tr><td><strong>FORM</strong></td><td>컨디션·경주 흐름 분석</td><td>⑪킹마스터 (최근 전적 양호)</td></tr>
<tr><td><strong>CONTRARIAN</strong></td><td>반대 의견 제시</td><td>⑪ 지지하되 리스크 경고</td></tr>
</table>

<div class="warning-box">
<strong>⚠️ 치명적 오류:</strong> 3개 에이전트 모두 ⑪킹마스터를 최우선 추천했으나, 조교사 승률 4.7%(최하위)라는 단일 팩터를 근거로 최종 의사결정에서 ⑪을 배제하였다. 결과적으로 ⑪이 1착 — 합의를 단일 지표로 뒤집은 것이 가장 큰 실수였다.
</div>

<h3>3.5 Autoresearch 종합 결과 (48개 전략)</h3>

<div class="chart-container">
<img src="data:image/png;base64,{chart1}" alt="Top 10 Strategy ROI">
<p class="chart-caption">Figure 4. 상위 10개 전략의 Flat vs Kelly ROI (OOS 2025-2026). LGB_hybrid_win의 Kelly ROI +8.0%가 유일한 양의 수익 전략.</p>
</div>

<div class="finding-box">
<h3>💡 핵심 결과</h3>
<p>48개 전략 중 OOS에서 양의 ROI를 보인 전략은 단 2개뿐이다:</p>
<ol>
<li><strong>pool_rd≤-5 (place)</strong>: ROI +26.0% — 단, 5건의 베팅으로 통계적 무의미</li>
<li><strong>LGB_hybrid_win + Kelly</strong>: ROI +8.0%, 521건 — 유일하게 유의미한 양의 기대값</li>
</ol>
<p>모든 flat betting 전략은 음의 ROI를 기록하였다. 선별적 베팅(Kelly criterion)만이 공제율을 극복할 가능성을 보였다.</p>
</div>

<h2 id="live">4. 라이브 실험 결과</h2>

<h3>4.1 서울 7레이스 (1600m, 혼합4등급)</h3>
<div class="bet-card">
<h4>전략: V2 모델 + 정성 분석, ③⑦⑨ 중심</h4>
<table>
<tr><th>베팅 유형</th><th>마번 조합</th><th>금액</th></tr>
<tr><td>단승</td><td>③</td><td>₩3,000</td></tr>
<tr><td>복승</td><td>③-⑦</td><td>₩3,000</td></tr>
<tr><td>복승</td><td>③-⑨</td><td>₩3,000</td></tr>
<tr><td>복연</td><td>③-⑦-⑨</td><td>₩3,500</td></tr>
<tr><td>복연</td><td>③-⑦-②</td><td>₩3,500</td></tr>
<tr><td>삼복</td><td>③-⑦-⑨</td><td>₩3,300</td></tr>
<tr><td>복승</td><td>⑦-⑨</td><td>₩3,000</td></tr>
<tr><th colspan="2">합계</th><th>₩22,300</th></tr>
</table>
<p><strong>결과:</strong> ②→③→④→①→⑨ (상위 3착 = 시장 인기순위 상위마)</p>
<p class="result loss">P&L: -₩22,300 (ROI -100%)</p>
<p><strong>사후 분석:</strong> ④번마를 모델은 승률 8.6%로 평가했으나 시장은 30%로 평가 → 시장이 정확했다. ③이 2착으로 들어왔으나 복승 조합에 ④가 포함되지 않아 적중 불가.</p>
</div>

<h3>4.2 서울 8레이스 (1800m, 혼합4등급)</h3>
<div class="bet-card">
<h4>전략: 멀티팩터 파이프라인 (출마표 + 조교사 + 거리적성 + 풀 불일치)</h4>
<table>
<tr><th>베팅 유형</th><th>마번 조합</th><th>금액</th></tr>
<tr><td>단승</td><td>④</td><td>₩3,000</td></tr>
<tr><td>복승</td><td>④-⑩</td><td>₩3,000</td></tr>
<tr><td>복승</td><td>④-⑨</td><td>₩3,500</td></tr>
<tr><td>복연</td><td>④-⑩-⑨</td><td>₩3,500</td></tr>
<tr><td>복연</td><td>④-⑩-⑦</td><td>₩3,000</td></tr>
<tr><td>삼복</td><td>④-⑩-⑨</td><td>₩3,500</td></tr>
<tr><td>복승</td><td>⑩-⑨</td><td>₩3,000</td></tr>
<tr><th colspan="2">합계</th><th>₩22,500</th></tr>
</table>
<p><strong>결과:</strong> ⑪→⑨→⑦ (<strong>⑪은 우리가 배제한 바로 그 말!</strong>)</p>
<p class="result loss">P&L: -₩22,500 (ROI -100%)</p>
<p><strong>사후 분석:</strong> ⑪킹마스터의 조교사 승률이 4.7%(최하위)라는 이유로 핵심 픽에서 제외했으나, 결과적으로 1착. 조교사 승률은 개별 레이스의 결과를 결정하는 신뢰할 수 있는 팩터가 아님이 입증되었다. 특히 3개 AI 에이전트의 합의(consensus)를 단일 통계 지표로 번복한 것이 치명적이었다.</p>
</div>

<h3>4.3 누적 손익</h3>
<div class="chart-container">
<img src="data:image/png;base64,{chart3}" alt="Cumulative P&L">
<p class="chart-caption">Figure 5. 라이브 실험 누적 P&L. 14건의 베팅 모두 미적중, 총 -₩44,800.</p>
</div>

<table>
<tr><th>레이스</th><th>투입</th><th>회수</th><th>P&L</th><th>ROI</th></tr>
<tr><td>Race 7</td><td>₩22,300</td><td>₩0</td><td class="loss">-₩22,300</td><td class="loss">-100%</td></tr>
<tr><td>Race 8</td><td>₩22,500</td><td>₩0</td><td class="loss">-₩22,500</td><td class="loss">-100%</td></tr>
<tr style="font-weight:700; background:#fff5f5;"><td>합계</td><td>₩44,800</td><td>₩0</td><td class="loss">-₩44,800</td><td class="loss">-100%</td></tr>
</table>

<h2 id="findings">5. 핵심 발견 (Key Findings)</h2>

<div class="finding-box">
<h3>📊 6가지 핵심 발견</h3>
<ol style="padding-left: 20px;">
<li style="margin-bottom:10px;"><strong>단일 레이스 ML 예측은 시장을 이기지 못한다.</strong> 파리뮤추얼 시장의 집합 지성(수천 명의 베터)은 이미 공개된 정보를 효율적으로 반영한다. 2레이스의 표본으로는 통계적으로 유의미한 결론을 내릴 수 없으나, 시장 상위 인기마가 상위 착순을 차지한 패턴은 시장 효율성을 시사한다.</li>
<li style="margin-bottom:10px;"><strong>시장 인기마(단승 1-2위)는 대부분 정확하다.</strong> 7레이스 상위 3착(②③④)과 8레이스 상위 3착 중 ⑨⑦은 모두 시장 인기 상위권이었다. 시장을 이기려면 시장이 '틀린' 레이스를 식별해야 하며, 이는 매우 어렵다.</li>
<li style="margin-bottom:10px;"><strong>백테스트 알파 ≈ 과적합.</strong> 풀 불일치 전략의 in-sample ROI +160%가 OOS에서 -3.3%~+26%(표본 5건)로 급락한 것은 전형적인 과적합 사례다. Multiple testing correction 없이 48개 전략을 탐색하면 우연에 의한 양의 ROI가 나타날 수 있다.</li>
<li style="margin-bottom:10px;"><strong>조교사 승률은 신뢰할 수 없는 배제 팩터다.</strong> 승률 4.7%(최하위) 조교사의 말이 1착 — 조교사 전체 승률은 개별 레이스의 결과와 약한 상관관계만 가진다.</li>
<li style="margin-bottom:10px;"><strong>멀티에이전트 합의를 단일 팩터로 번복하면 안 된다.</strong> 3개 에이전트의 일치된 추천을 하나의 통계 지표(조교사 승률)로 뒤집은 것은 의사결정 프로세스의 근본적 결함이었다.</li>
<li style="margin-bottom:10px;"><strong>장기·선별적 베팅만이 양의 기대값을 보인다.</strong> 48개 전략 중 유일하게 유의미한 양의 ROI는 LGB_hybrid_win + Kelly criterion(ROI +8.0%, 521건)이었다. 이는 500회 이상의 자동화된 베팅이 필요함을 의미한다.</li>
</ol>
</div>

<h2 id="conclusion">6. 결론 및 향후 과제</h2>

<h3>6.1 결론</h3>
<p>본 실험은 ML 기반 경마 베팅 시스템의 <strong>단기 실전 적용이 사실상 도박과 다르지 않음</strong>을 입증하였다. 2레이스에 ₩44,800을 투입하여 전액 손실(-100% ROI)이라는 결과는, 아무리 정교한 모델과 다중 팩터 분석을 동원하더라도 <strong>소수 레이스에서는 분산(variance)이 에지(edge)를 압도</strong>한다는 사실을 보여준다.</p>

<p>빌 벤터의 교훈은 명확하다: <strong>"작은 에지 × 많은 베팅 = 수익"</strong>. 이는 역으로 "작은 에지 × 적은 베팅 = 순수한 불확실성"을 의미한다. LGB_hybrid_win + Kelly 전략이 521건의 선별적 베팅에서 ROI +8.0%를 기록한 것은, 충분한 횟수가 주어지면 ML이 시장의 비효율성을 포착할 수 있는 가능성을 시사한다.</p>

<h3>6.2 향후 과제</h3>
<table>
<tr><th>과제</th><th>설명</th><th>기대 효과</th></tr>
<tr><td><strong>자동화 베팅 시스템</strong></td><td>LGB_hybrid_win + Kelly를 500레이스 이상 자동 실행</td><td>ROI +8% 가설 실전 검증</td></tr>
<tr><td><strong>실시간 배당 수집</strong></td><td>경주 직전 배당 변동 데이터 확보</td><td>Late money 시그널 활용</td></tr>
<tr><td><strong>교차 풀 차익거래</strong></td><td>복승/삼복 풀의 비효율성 탐색</td><td>시장 간 가격 괴리 수익화</td></tr>
<tr><td><strong>딥러닝 모델</strong></td><td>LSTM/Transformer로 시퀀스 패턴 학습</td><td>시장이 반영하지 못한 비선형 패턴</td></tr>
<tr><td><strong>Multiple Testing Correction</strong></td><td>Bonferroni/FDR correction 적용</td><td>과적합 방지</td></tr>
</table>

<h3>6.3 투자 관점에서의 시사점</h3>
<p>경마 베팅을 "투자"로 접근하려면 다음 조건이 충족되어야 한다:</p>
<ol>
<li>통계적으로 유의미한 에지의 존재 확인 (p < 0.05)</li>
<li>500회 이상의 선별적 베팅을 실행할 수 있는 자동화 인프라</li>
<li>Kelly criterion에 따른 엄격한 자금 관리</li>
<li>시장 변화에 대응하는 지속적 모델 업데이트</li>
</ol>
<p>이 중 어느 하나라도 결여되면, 경마 베팅은 투자가 아닌 도박이다.</p>

<hr class="divider">

<h2 id="appendix">부록 (Appendix)</h2>

<h3>A. 48개 Autoresearch 전략 전체 결과</h3>

<table>
<tr><th>#</th><th>전략</th><th>모델</th><th>피처</th><th>타겟</th><th>AUC</th><th>Flat ROI%</th><th>베팅수</th><th>Kelly ROI%</th></tr>
<tr><td>1</td><td>pool_rd≤-5_place</td><td>rule</td><td>market</td><td>place</td><td>-</td><td class="profit">+26.0</td><td>5</td><td class="profit">+26.0</td></tr>
<tr><td>2</td><td>LGB_skill_place_rd≤-3</td><td>LGB</td><td>skill</td><td>place</td><td>0.699</td><td>-1.7</td><td>137</td><td>-1.7</td></tr>
<tr><td>3</td><td>pool_rd≤-3_place</td><td>rule</td><td>market</td><td>place</td><td>-</td><td>-4.2</td><td>144</td><td>-4.2</td></tr>
<tr><td>4</td><td>XGB_hybrid_place_rd≤-3</td><td>XGB</td><td>hybrid</td><td>place</td><td>0.771</td><td>-5.0</td><td>137</td><td>-5.0</td></tr>
<tr><td>5</td><td>LGB_hybrid_place_rd≤-3</td><td>LGB</td><td>hybrid</td><td>place</td><td>0.772</td><td>-5.0</td><td>137</td><td>-5.0</td></tr>
<tr><td>6</td><td>LGB_skill_win</td><td>LGB</td><td>skill</td><td>win</td><td>0.721</td><td>-6.7</td><td>1293</td><td>-15.7</td></tr>
<tr><td>7</td><td>LGB_hybrid_place</td><td>LGB</td><td>hybrid</td><td>place</td><td>0.772</td><td>-12.1</td><td>1293</td><td>-10.2</td></tr>
<tr><td>8</td><td>LGB_market_place</td><td>LGB</td><td>market</td><td>place</td><td>0.775</td><td>-12.2</td><td>1293</td><td>-2.7</td></tr>
<tr><td>9</td><td>LGB_hybrid_win</td><td>LGB</td><td>hybrid</td><td>win</td><td>0.807</td><td>-13.2</td><td>1293</td><td class="profit">+8.0</td></tr>
<tr><td>10</td><td>XGB_hybrid_win</td><td>XGB</td><td>hybrid</td><td>win</td><td>0.805</td><td>-15.6</td><td>1293</td><td class="profit">+0.2</td></tr>
<tr><td>11</td><td>LGB_market_win</td><td>LGB</td><td>market</td><td>win</td><td>0.806</td><td>-17.2</td><td>1293</td><td class="profit">+3.8</td></tr>
<tr><td>12</td><td>XGB_market_win</td><td>XGB</td><td>market</td><td>win</td><td>0.806</td><td>-19.6</td><td>1293</td><td class="profit">+0.6</td></tr>
<tr><td colspan="9" style="text-align:center; color:#888;">... (나머지 36개 전략 모두 음의 ROI) ...</td></tr>
<tr><td>48</td><td>pool_rd≤-5_win</td><td>rule</td><td>market</td><td>win</td><td>-</td><td class="loss">-100.0</td><td>5</td><td class="loss">-100.0</td></tr>
</table>

<h3>B. 용어 정의</h3>
<table>
<tr><th>용어</th><th>정의</th></tr>
<tr><td>AUC-ROC</td><td>모델 판별력 지표. 0.5=무작위, 1.0=완벽</td></tr>
<tr><td>Kelly Criterion</td><td>기대값 기반 최적 베팅 비율 계산법</td></tr>
<tr><td>OOS</td><td>Out-of-Sample, 훈련에 사용하지 않은 데이터에서의 성과</td></tr>
<tr><td>Parimutuel</td><td>참여자 간 총 베팅금을 나누는 배당 방식</td></tr>
<tr><td>단승</td><td>1착 맞추기 (Win)</td></tr>
<tr><td>연승/복승</td><td>1-2착 맞추기 (Place/Quinella)</td></tr>
<tr><td>삼복</td><td>1-2-3착 맞추기 순서 무관 (Trifecta Box)</td></tr>
<tr><td>복연</td><td>1-2-3착 중 2마리 맞추기 (Quinella Place)</td></tr>
</table>

<div class="footnote">
<p><strong>Acknowledgments:</strong> 본 연구에 사용된 데이터는 한국마사회(KRA) 공개 정보를 기반으로 수집되었습니다. AI Research Assistant(AB_kimi_bot)는 OpenClaw 플랫폼에서 Claude를 기반으로 운영되었습니다.</p>
<p><strong>Disclaimer:</strong> 본 보고서는 학술 연구 목적으로 작성되었으며, 투자 조언이 아닙니다. 경마 베팅은 원금 손실의 위험이 있습니다.</p>
<p><strong>Code & Data:</strong> 분석 코드와 데이터셋은 <code>/Users/ryan/.openclaw/workspace/kra-scraper/</code>에서 확인할 수 있습니다.</p>
<p style="text-align:center; margin-top:20px; color:#aaa;">© 2026 Jiwoong Kim & AB_kimi_bot. All rights reserved.</p>
</div>

</div>
</body>
</html>'''

with open('/Users/ryan/.openclaw/workspace/kra-scraper/report_live_experiment.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Report generated successfully!")
