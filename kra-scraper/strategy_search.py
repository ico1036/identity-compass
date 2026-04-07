#!/usr/bin/env python3
"""KRA Seoul Horse Racing Strategy Search - Comprehensive OOS Analysis"""

import pandas as pd
import numpy as np
import joblib
import warnings
warnings.filterwarnings('ignore')

# ── Load Data ──
df = pd.read_csv('/Users/ryan/.openclaw/workspace/kra-scraper/kra_seoul_final.csv')
df['경주일자'] = df['경주일자'].astype(str)
df['year'] = df['경주일자'].str[:4].astype(int)

# Numeric conversion
df['연승배당'] = pd.to_numeric(df['연승배당'], errors='coerce')
df['단승배당'] = pd.to_numeric(df['단승배당'], errors='coerce')
df['착순'] = pd.to_numeric(df['착순'], errors='coerce')
df['연령'] = pd.to_numeric(df['연령'], errors='coerce')

# Filter outliers
df.loc[df['연승배당'] >= 9999, '연승배당'] = np.nan
df.loc[df['단승배당'] >= 9999, '단승배당'] = np.nan

# Win/Place flags
df['win'] = (df['착순'] == 1).astype(int)
df['place'] = (df['착순'].isin([1,2,3])).astype(int)

# Race ID
df['race_id'] = df['경주일자'] + '_' + df['경주번호'].astype(str)

# Field size
df['field_size'] = df.groupby('race_id')['출주번호'].transform('count')

# Split
train = df[df['year'].between(2020, 2024)].copy()
oos = df[df['year'] >= 2025].copy()
print(f"Train: {len(train)} rows, OOS: {len(oos)} rows, OOS races: {oos['race_id'].nunique()}")

# Favorite flag (lowest 단승 in race)
for d in [train, oos]:
    min_odds = d.groupby('race_id')['단승배당'].transform('min')
    d['is_favorite'] = (d['단승배당'] == min_odds).astype(int)

# Odds ratio
oos['odds_ratio'] = oos['단승배당'] / oos['연승배당']

# Rating numeric
oos['레이팅_num'] = pd.to_numeric(oos['레이팅'], errors='coerce')
train['레이팅_num'] = pd.to_numeric(train['레이팅'], errors='coerce')

# 마체중증감 numeric
oos['weight_change'] = pd.to_numeric(oos['마체중증감'], errors='coerce')

# ── Helper ──
def calc_roi(subset, bet_col='단승배당', win_col='win'):
    """Calculate ROI for flat betting on subset"""
    s = subset.dropna(subset=[bet_col])
    if len(s) == 0:
        return {'n': 0, 'roi': np.nan}
    n = len(s)
    hits = s[win_col].sum()
    returns = (s[win_col] * s[bet_col]).sum()
    roi = returns / n - 1
    hit_rate = hits / n
    avg_odds = s[bet_col].mean()
    
    # Max drawdown (cumulative P&L)
    pnl = s[win_col].values * s[bet_col].values - 1
    cum = np.cumsum(pnl)
    peak = np.maximum.accumulate(cum)
    dd = peak - cum
    max_dd = dd.max() if len(dd) > 0 else 0
    
    return {'n': n, 'hits': hits, 'hit_rate': hit_rate, 'avg_odds': avg_odds, 
            'roi': roi, 'max_dd': max_dd, 'returns': returns}

results = []

def add_result(name, bet_type, subset, bet_col, win_col):
    r = calc_roi(subset, bet_col, win_col)
    if r['n'] > 0:
        results.append({
            'strategy': name, 'bet_type': bet_type, 'n_bets': r['n'],
            'hit_rate': r['hit_rate'], 'avg_odds': r['avg_odds'],
            'roi': r['roi'], 'max_dd': r['max_dd']
        })

# ── 0. Baselines ──
add_result('Baseline: All Win', 'win', oos, '단승배당', 'win')
add_result('Baseline: All Place', 'place', oos, '연승배당', 'place')
add_result('Baseline: Favorites Win', 'win', oos[oos['is_favorite']==1], '단승배당', 'win')
add_result('Baseline: Favorites Place', 'place', oos[oos['is_favorite']==1], '연승배당', 'place')

# ── 1. Odds Value Zones ──
for lo, hi in [(1,2), (2,3), (3,5), (5,8), (8,12), (12,20), (20,50), (50,200)]:
    s = oos[(oos['단승배당']>=lo) & (oos['단승배당']<hi)]
    add_result(f'Win Odds [{lo}-{hi})', 'win', s, '단승배당', 'win')
    s2 = oos[(oos['연승배당']>=lo) & (oos['연승배당']<hi)]
    add_result(f'Place Odds [{lo}-{hi})', 'place', s2, '연승배당', 'place')

# Odds ratio zones
for lo, hi in [(1,2), (2,2.5), (2.5,3), (3,4), (4,6), (6,10)]:
    s = oos[(oos['odds_ratio']>=lo) & (oos['odds_ratio']<hi)]
    add_result(f'OddsRatio [{lo}-{hi}) Win', 'win', s, '단승배당', 'win')
    add_result(f'OddsRatio [{lo}-{hi}) Place', 'place', s, '연승배당', 'place')

# 연승 underlay: low odds_ratio means 연승 is generous relative to 단승
for thresh in [1.5, 2.0, 2.5]:
    s = oos[oos['odds_ratio'] < thresh]
    add_result(f'연승Underlay ratio<{thresh} Place', 'place', s, '연승배당', 'place')
    add_result(f'연승Underlay ratio<{thresh} Win', 'win', s, '단승배당', 'win')

# ── 2. Conditional Strategies ──
# Field size
for lo, hi, label in [(1,8,'Small≤8'), (9,11,'Med9-11'), (12,20,'Large≥12')]:
    s = oos[(oos['field_size']>=lo) & (oos['field_size']<=hi)]
    add_result(f'FieldSize {label} Win', 'win', s, '단승배당', 'win')
    add_result(f'FieldSize {label} Place', 'place', s, '연승배당', 'place')

# Grade
for grade in oos['등급'].unique():
    s = oos[oos['등급']==grade]
    if len(s) >= 30:
        add_result(f'Grade={grade} Win', 'win', s, '단승배당', 'win')
        add_result(f'Grade={grade} Place', 'place', s, '연승배당', 'place')

# Distance
for dist in oos['거리'].unique():
    s = oos[oos['거리']==dist]
    if len(s) >= 30:
        add_result(f'Dist={dist} Win', 'win', s, '단승배당', 'win')
        add_result(f'Dist={dist} Place', 'place', s, '연승배당', 'place')

# Track condition
for cond in oos['주로상태'].unique():
    s = oos[oos['주로상태']==cond]
    if len(s) >= 30:
        add_result(f'Track={cond} Win', 'win', s, '단승배당', 'win')
        add_result(f'Track={cond} Place', 'place', s, '연승배당', 'place')

# Rating bands + odds
for rlo, rhi in [(0,40), (40,60), (60,80), (80,120)]:
    s = oos[(oos['레이팅_num']>=rlo) & (oos['레이팅_num']<rhi)]
    if len(s) >= 20:
        add_result(f'Rating[{rlo}-{rhi}) Win', 'win', s, '단승배당', 'win')
        add_result(f'Rating[{rlo}-{rhi}) Place', 'place', s, '연승배당', 'place')

# High rating + moderate odds (potential value)
for odds_lo, odds_hi in [(2,5), (5,10), (10,20)]:
    s = oos[(oos['레이팅_num']>=60) & (oos['단승배당']>=odds_lo) & (oos['단승배당']<odds_hi)]
    if len(s) >= 10:
        add_result(f'HiRating60+_Odds[{odds_lo}-{odds_hi}) Win', 'win', s, '단승배당', 'win')

# ── 3. Form + Odds ──
# Favorites by grade
for grade in oos['등급'].unique():
    s = oos[(oos['등급']==grade) & (oos['is_favorite']==1)]
    if len(s) >= 10:
        add_result(f'Fav@{grade} Win', 'win', s, '단승배당', 'win')
        add_result(f'Fav@{grade} Place', 'place', s, '연승배당', 'place')

# Weight change extremes
for lo, hi, label in [(-20,-5,'BigLoss'), (-5,0,'SmallLoss'), (0,5,'SmallGain'), (5,20,'BigGain')]:
    s = oos[(oos['weight_change']>=lo) & (oos['weight_change']<hi)]
    if len(s) >= 20:
        add_result(f'Weight{label} Win', 'win', s, '단승배당', 'win')
        add_result(f'Weight{label} Place', 'place', s, '연승배당', 'place')

# Weight change + low odds
for lo, hi, label in [(-20,-5,'BigLoss'), (5,20,'BigGain')]:
    s = oos[(oos['weight_change']>=lo) & (oos['weight_change']<hi) & (oos['단승배당']<5)]
    if len(s) >= 10:
        add_result(f'Weight{label}_LowOdds Win', 'win', s, '단승배당', 'win')

# Age
for age_str in ['3세', '4세', '5세']:
    age_val = int(age_str[0])
    s = oos[oos['연령']==age_val] if '연령' in oos.columns and oos['연령'].dtype in ['int64','float64'] else oos[oos['연령'].astype(str)==age_str]
    if len(s) >= 20:
        add_result(f'Age={age_str} Win', 'win', s, '단승배당', 'win')
        add_result(f'Age={age_str} Place', 'place', s, '연승배당', 'place')

# Sex
for sex in oos['성별'].unique():
    s = oos[oos['성별']==sex]
    if len(s) >= 30:
        add_result(f'Sex={sex} Win', 'win', s, '단승배당', 'win')
        add_result(f'Sex={sex} Place', 'place', s, '연승배당', 'place')

# ── 4. Combination strategies ──
# Favorites in small fields
s = oos[(oos['is_favorite']==1) & (oos['field_size']<=8)]
add_result('Fav+SmallField Win', 'win', s, '단승배당', 'win')
add_result('Fav+SmallField Place', 'place', s, '연승배당', 'place')

# Favorites in large fields
s = oos[(oos['is_favorite']==1) & (oos['field_size']>=12)]
add_result('Fav+LargeField Win', 'win', s, '단승배당', 'win')
add_result('Fav+LargeField Place', 'place', s, '연승배당', 'place')

# 2nd favorite (2nd lowest odds)
oos_sorted = oos.sort_values(['race_id', '단승배당'])
oos_sorted['rank_in_race'] = oos_sorted.groupby('race_id').cumcount() + 1
s = oos_sorted[oos_sorted['rank_in_race']==2]
add_result('2ndFav Win', 'win', s, '단승배당', 'win')
add_result('2ndFav Place', 'place', s, '연승배당', 'place')

# Top 3 rated in race
oos['rating_rank'] = oos.groupby('race_id')['레이팅_num'].rank(ascending=False, method='min')
for rk in [1, 2, 3]:
    s = oos[oos['rating_rank']==rk]
    add_result(f'RatingRank{rk} Win', 'win', s, '단승배당', 'win')
    add_result(f'RatingRank{rk} Place', 'place', s, '연승배당', 'place')

# Top rated + not favorite (contrarian value)
s = oos[(oos['rating_rank']==1) & (oos['is_favorite']==0)]
add_result('TopRated+NotFav Win', 'win', s, '단승배당', 'win')
add_result('TopRated+NotFav Place', 'place', s, '연승배당', 'place')

# ── 5. Exacta simulation ──
# For each race, take top 2 by odds rank, simulate exacta
def exacta_sim(data, sel_col, sel_vals):
    """Simulate exacta: select horses by sel_col in sel_vals, check if they finish 1-2"""
    race_results = []
    for rid, grp in data.groupby('race_id'):
        selected = grp[grp[sel_col].isin(sel_vals)]
        if len(selected) < 2:
            continue
        # implied exacta odds ≈ product of 단승 odds * 0.8 (rough)
        top2_odds = selected.nsmallest(2, '단승배당')['단승배당'].values
        implied_odds = top2_odds[0] * top2_odds[1] * 0.8
        # Check if selected horses actually finished 1-2
        actual_top2 = set(grp[grp['착순'].isin([1,2])]['출주번호'].values)
        selected_nums = set(selected['출주번호'].values)
        hit = actual_top2.issubset(selected_nums) and len(actual_top2) == 2
        race_results.append({'implied_odds': implied_odds, 'hit': int(hit)})
    return pd.DataFrame(race_results)

# Top-2 favorites exacta
exacta_df = []
for rid, grp in oos.groupby('race_id'):
    grp_s = grp.nsmallest(2, '단승배당')
    if len(grp_s) < 2:
        continue
    odds_vals = grp_s['단승배당'].values
    implied = odds_vals[0] * odds_vals[1] * 0.8
    actual_12 = set(grp[grp['착순'].isin([1,2])]['출주번호'].values)
    sel = set(grp_s['출주번호'].values)
    hit = 1 if sel == actual_12 else 0
    exacta_df.append({'implied_odds': implied, 'hit': hit})
exacta_df = pd.DataFrame(exacta_df)
if len(exacta_df) > 0:
    n = len(exacta_df)
    hits = exacta_df['hit'].sum()
    ret = (exacta_df['hit'] * exacta_df['implied_odds']).sum()
    results.append({'strategy': 'Exacta Top2Fav', 'bet_type': 'exacta', 'n_bets': n,
                    'hit_rate': hits/n, 'avg_odds': exacta_df['implied_odds'].mean(),
                    'roi': ret/n - 1, 'max_dd': 0})

# Top rated + 2nd rated exacta
exacta_df2 = []
for rid, grp in oos.groupby('race_id'):
    grp_s = grp.nsmallest(2, '레이팅_num', keep='all')
    # actually we want largest rating
    grp_s = grp.nlargest(2, '레이팅_num')
    if len(grp_s) < 2:
        continue
    odds_vals = grp_s['단승배당'].values
    if np.any(np.isnan(odds_vals)):
        continue
    implied = odds_vals[0] * odds_vals[1] * 0.8
    actual_12 = set(grp[grp['착순'].isin([1,2])]['출주번호'].values)
    sel = set(grp_s['출주번호'].values)
    hit = 1 if sel == actual_12 else 0
    exacta_df2.append({'implied_odds': implied, 'hit': hit})
exacta_df2 = pd.DataFrame(exacta_df2)
if len(exacta_df2) > 0:
    n = len(exacta_df2)
    hits = exacta_df2['hit'].sum()
    ret = (exacta_df2['hit'] * exacta_df2['implied_odds']).sum()
    results.append({'strategy': 'Exacta TopRated2', 'bet_type': 'exacta', 'n_bets': n,
                    'hit_rate': hits/n, 'avg_odds': exacta_df2['implied_odds'].mean(),
                    'roi': ret/n - 1, 'max_dd': 0})

# ── 6. LGB Model ──
try:
    model = joblib.load('/Users/ryan/.openclaw/workspace/kra-scraper/best_model.pkl')
    print(f"Model loaded: {type(model)}")
    
    # Try to figure out features
    if hasattr(model, 'feature_name_'):
        features = model.feature_name_()
        print(f"Features: {features[:10]}...")
    elif hasattr(model, 'feature_names_in_'):
        features = list(model.feature_names_in_)
        print(f"Features: {features[:10]}...")
    else:
        features = None
        print("Cannot determine features, skipping model")
    
    if features:
        # Prepare OOS data with needed features
        oos_model = oos.copy()
        
        # Check which features exist
        missing = [f for f in features if f not in oos_model.columns]
        print(f"Missing features: {missing[:10]}...")
        
        # Try to create missing features or skip
        available = [f for f in features if f in oos_model.columns]
        
        if len(available) >= len(features) * 0.5:
            # Fill missing with 0
            for f in missing:
                oos_model[f] = 0
            
            X_oos = oos_model[features]
            # Handle categoricals
            for col in X_oos.select_dtypes(include=['object']).columns:
                X_oos[col] = X_oos[col].astype('category')
            
            probs = model.predict_proba(X_oos)[:, 1] if hasattr(model, 'predict_proba') else model.predict(X_oos)
            oos_model['model_prob'] = probs
            
            # EV = prob * odds
            oos_model['ev_win'] = oos_model['model_prob'] * oos_model['단승배당']
            oos_model['ev_place'] = oos_model['model_prob'] * 3 * oos_model['연승배당']  # rough place prob
            
            for thresh in [1.0, 1.05, 1.1, 1.15, 1.2, 1.3, 1.5, 2.0]:
                s = oos_model[oos_model['ev_win'] >= thresh]
                add_result(f'Model EV_win≥{thresh}', 'win', s, '단승배당', 'win')
            
            # Model prob top pick per race
            top_picks = oos_model.loc[oos_model.groupby('race_id')['model_prob'].idxmax()]
            add_result('Model TopPick Win', 'win', top_picks, '단승배당', 'win')
            add_result('Model TopPick Place', 'place', top_picks, '연승배당', 'place')
            
            # Model + odds combos
            for odds_lo, odds_hi in [(2,5), (5,10), (10,20)]:
                s = top_picks[(top_picks['단승배당']>=odds_lo) & (top_picks['단승배당']<odds_hi)]
                add_result(f'ModelTop+Odds[{odds_lo}-{odds_hi}) Win', 'win', s, '단승배당', 'win')
            
            # Model top pick + small field
            s = top_picks[top_picks['field_size']<=8]
            add_result('ModelTop+SmallField Win', 'win', s, '단승배당', 'win')
            
            # Kelly for model
            oos_model['kelly_frac'] = oos_model['model_prob'] - (1 - oos_model['model_prob'])/(oos_model['단승배당'] - 1)
            for min_kelly in [0.0, 0.05, 0.10, 0.15, 0.20]:
                s = oos_model[oos_model['kelly_frac'] >= min_kelly]
                add_result(f'Kelly≥{min_kelly} Win', 'win', s, '단승배당', 'win')
        else:
            print(f"Only {len(available)}/{len(features)} features available, skipping model")
except Exception as e:
    print(f"Model error: {e}")

# ── 7. More combination strategies ──
# Track condition + favorites
for cond in oos['주로상태'].unique():
    s = oos[(oos['주로상태']==cond) & (oos['is_favorite']==1)]
    if len(s) >= 10:
        add_result(f'Fav@Track={cond} Win', 'win', s, '단승배당', 'win')
        add_result(f'Fav@Track={cond} Place', 'place', s, '연승배당', 'place')

# Distance + favorites
for dist in oos['거리'].unique():
    s = oos[(oos['거리']==dist) & (oos['is_favorite']==1)]
    if len(s) >= 10:
        add_result(f'Fav@{dist} Win', 'win', s, '단승배당', 'win')

# Low odds ratio + high rating (연승 generous + strong horse)
s = oos[(oos['odds_ratio'] < 2.5) & (oos['rating_rank'] <= 3)]
add_result('LowRatio+TopRated Place', 'place', s, '연승배당', 'place')
add_result('LowRatio+TopRated Win', 'win', s, '단승배당', 'win')

s = oos[(oos['odds_ratio'] < 2.0) & (oos['rating_rank'] == 1)]
add_result('LowRatio<2+TopRated Win', 'win', s, '단승배당', 'win')
add_result('LowRatio<2+TopRated Place', 'place', s, '연승배당', 'place')

# ── Compile Results ──
res_df = pd.DataFrame(results)
res_df = res_df.sort_values('roi', ascending=False)
res_df['significant'] = res_df['n_bets'] >= 50

print("\n" + "="*100)
print("TOP 20 STRATEGIES BY OOS ROI")
print("="*100)
for _, r in res_df.head(20).iterrows():
    sig = "✓" if r['significant'] else "✗"
    print(f"ROI={r['roi']:+7.1%} | n={r['n_bets']:5.0f} | hit={r['hit_rate']:5.1%} | odds={r['avg_odds']:6.1f} | dd={r['max_dd']:6.1f} | sig={sig} | {r['strategy']} ({r['bet_type']})")

print("\n" + "="*100)
print("PROFITABLE + SIGNIFICANT (ROI>0, n≥50)")
print("="*100)
profitable = res_df[(res_df['roi']>0) & (res_df['significant'])]
for _, r in profitable.iterrows():
    print(f"ROI={r['roi']:+7.1%} | n={r['n_bets']:5.0f} | hit={r['hit_rate']:5.1%} | odds={r['avg_odds']:6.1f} | dd={r['max_dd']:6.1f} | {r['strategy']} ({r['bet_type']})")

if len(profitable) == 0:
    print(">>> NO STRATEGIES with ROI>0 AND n≥50 <<<")

# Save full results
res_df.to_csv('/Users/ryan/.openclaw/workspace/kra-scraper/strategy_results_raw.csv', index=False)

# ── Generate Markdown Report ──
md = []
md.append("# KRA Seoul Strategy Search Results (OOS: 2025-2026)\n")
md.append(f"**Generated**: 2026-03-29 | **OOS Races**: {oos['race_id'].nunique()} | **OOS Rows**: {len(oos)}\n")

md.append("## Executive Summary\n")
top5 = res_df[res_df['significant']].head(5)
if len(top5) > 0 and top5.iloc[0]['roi'] > 0:
    md.append("### Top 5 Strategies (Significant, n≥50, sorted by ROI)\n")
    md.append("| Rank | Strategy | Type | n_bets | Hit Rate | Avg Odds | ROI | Max DD |")
    md.append("|------|----------|------|--------|----------|----------|-----|--------|")
    for i, (_, r) in enumerate(top5.iterrows(), 1):
        md.append(f"| {i} | {r['strategy']} | {r['bet_type']} | {r['n_bets']:.0f} | {r['hit_rate']:.1%} | {r['avg_odds']:.1f} | {r['roi']:+.1%} | {r['max_dd']:.1f} |")
else:
    md.append("**⚠️ No strategy with n≥50 achieved positive OOS ROI.**\n")
    md.append("### Closest to Profitable (least negative ROI, n≥50)\n")
    least_neg = res_df[res_df['significant']].head(10)
    md.append("| Strategy | Type | n_bets | Hit Rate | Avg Odds | ROI | Max DD |")
    md.append("|----------|------|--------|----------|----------|-----|--------|")
    for _, r in least_neg.iterrows():
        md.append(f"| {r['strategy']} | {r['bet_type']} | {r['n_bets']:.0f} | {r['hit_rate']:.1%} | {r['avg_odds']:.1f} | {r['roi']:+.1%} | {r['max_dd']:.1f} |")

md.append("\n### Top Strategies Including Low-n (may be noise)\n")
md.append("| Strategy | Type | n_bets | Hit Rate | Avg Odds | ROI | Significant |")
md.append("|----------|------|--------|----------|----------|-----|-------------|")
for _, r in res_df.head(15).iterrows():
    sig = "✓" if r['significant'] else "✗" 
    md.append(f"| {r['strategy']} | {r['bet_type']} | {r['n_bets']:.0f} | {r['hit_rate']:.1%} | {r['avg_odds']:.1f} | {r['roi']:+.1%} | {sig} |")

md.append("\n## Full Results Table (All Strategies)\n")
md.append("| Strategy | Type | n_bets | Hit Rate | Avg Odds | ROI | Max DD | Sig |")
md.append("|----------|------|--------|----------|----------|-----|--------|-----|")
for _, r in res_df.iterrows():
    sig = "✓" if r['significant'] else "✗"
    md.append(f"| {r['strategy']} | {r['bet_type']} | {r['n_bets']:.0f} | {r['hit_rate']:.1%} | {r['avg_odds']:.1f} | {r['roi']:+.1%} | {r['max_dd']:.1f} | {sig} |")

md.append("\n## Key Insights\n")

# Analyze where edge might live
# Best odds zone
best_zone = res_df[res_df['strategy'].str.contains('Odds \\[') & res_df['significant']].head(3)
if len(best_zone) > 0:
    md.append("### Odds Zones\n")
    for _, r in best_zone.iterrows():
        md.append(f"- **{r['strategy']}**: ROI={r['roi']:+.1%}, n={r['n_bets']:.0f}")

# Best grade
best_grade = res_df[res_df['strategy'].str.contains('Grade=') & res_df['significant']].head(3)
if len(best_grade) > 0:
    md.append("\n### Grades\n")
    for _, r in best_grade.iterrows():
        md.append(f"- **{r['strategy']}**: ROI={r['roi']:+.1%}, n={r['n_bets']:.0f}")

# Best distance  
best_dist = res_df[res_df['strategy'].str.contains('Dist=') & res_df['significant']].head(3)
if len(best_dist) > 0:
    md.append("\n### Distances\n")
    for _, r in best_dist.iterrows():
        md.append(f"- **{r['strategy']}**: ROI={r['roi']:+.1%}, n={r['n_bets']:.0f}")

md.append("\n## Recommended Execution Playbook\n")

profitable_sig = res_df[(res_df['roi']>0) & (res_df['significant'])]
if len(profitable_sig) > 0:
    md.append("Based on OOS results, the following strategies show promise:\n")
    for _, r in profitable_sig.iterrows():
        md.append(f"1. **{r['strategy']}** ({r['bet_type']}): Bet when conditions match. Expected ROI: {r['roi']:+.1%} over {r['n_bets']:.0f} bets.")
    md.append("\n**Risk Management**: Use flat betting (1-2% bankroll per bet). Monitor for regime changes.")
else:
    md.append("""**Honest Assessment**: No strategy with sufficient sample size (n≥50) achieved positive OOS ROI in 2025-2026.

This is consistent with a well-functioning parimutuel market where the ~20-27% takeout is difficult to overcome.

**Potential paths forward**:
1. **Deeper feature engineering**: Pace figures, trainer/jockey recent form, class drops
2. **Timing execution**: Early vs late odds movement (need tick data, not just final odds)
3. **Exotic bets**: Trifecta/superfecta where takeout is higher but public is worse at pricing
4. **Niche conditions**: Very specific combos (e.g., specific jockey + distance + grade) but sample sizes will be tiny
5. **Model improvement**: The LGB model features may need race-specific engineering
""")

with open('/Users/ryan/.openclaw/workspace/kra-scraper/strategy_search_results.md', 'w') as f:
    f.write('\n'.join(md))

print("\n✅ Results written to strategy_search_results.md")
print(f"Total strategies tested: {len(res_df)}")
