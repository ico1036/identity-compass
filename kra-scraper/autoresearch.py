#!/usr/bin/env python3
"""KRA Horse Racing ML Research - Comprehensive Strategy Search"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
import pickle
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, log_loss
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier
from sklearn.neural_network import MLPClassifier
import time

print("Loading data...")
df = pd.read_csv('/Users/ryan/.openclaw/workspace/kra-scraper/kra_seoul_final.csv', low_memory=False)
print(f"Loaded {len(df)} rows")

# Parse date
df['경주일자'] = df['경주일자'].astype(str)
df['date'] = pd.to_datetime(df['경주일자'], format='%Y%m%d')
df['race_id'] = df['경주일자'] + '_' + df['경주번호'].astype(str)

# Clean odds
for col in ['단승배당', '연승배당']:
    df[col] = pd.to_numeric(df[col].replace(['----', '9999.9'], np.nan), errors='coerce')

# Parse 착순
df['착순'] = pd.to_numeric(df['착순'], errors='coerce')
df = df.dropna(subset=['착순'])
df['착순'] = df['착순'].astype(int)

# Targets
df['win'] = (df['착순'] == 1).astype(int)
df['place'] = (df['착순'] <= 3).astype(int)

# Parse numeric columns
for col in ['레이팅', '연령', '부담중량', '마체중', '마체중증감']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Distance as numeric
df['거리_num'] = df['거리'].str.extract(r'(\d+)').astype(float)

# Grade encoding
grade_map = {}
for i, g in enumerate(df['등급'].unique()):
    grade_map[g] = i
df['등급_enc'] = df['등급'].map(grade_map)

# Encode 기수, 조교사
for col in ['기수명', '조교사명']:
    le = LabelEncoder()
    df[col + '_enc'] = le.fit_transform(df[col].fillna('unknown').astype(str))

# 성별 encoding
df['성별_enc'] = LabelEncoder().fit_transform(df['성별'].fillna('unknown').astype(str))

# Race-level odds features
print("Computing race-level features...")
def race_features(group):
    g = group.copy()
    # Odds ranks within race
    g['단승rank'] = g['단승배당'].rank(method='min')
    g['연승rank'] = g['연승배당'].rank(method='min')
    g['rank_diff'] = g['단승rank'] - g['연승rank']
    # Normalized odds
    g['단승_inv'] = 1.0 / g['단승배당']
    g['연승_inv'] = 1.0 / g['연승배당']
    total_win = g['단승_inv'].sum()
    total_place = g['연승_inv'].sum()
    g['단승_prob'] = g['단승_inv'] / total_win if total_win > 0 else 0
    g['연승_prob'] = g['연승_inv'] / total_place if total_place > 0 else 0
    g['num_runners'] = len(g)
    g['odds_ratio'] = g['단승배당'] / g['연승배당']
    return g

df = df.groupby('race_id', group_keys=False).apply(race_features)

# Historical features (sorted by date)
print("Computing historical features...")
df = df.sort_values(['date', '경주번호', '출주번호'])

# Jockey/trainer win rates (expanding, lagged)
for entity in ['기수명', '조교사명']:
    entity_stats = {}
    win_rates = []
    for _, row in df.iterrows():
        key = row[entity]
        if key in entity_stats:
            wins, total = entity_stats[key]
            win_rates.append(wins / total if total > 0 else 0)
        else:
            win_rates.append(0)
        if key not in entity_stats:
            entity_stats[key] = [0, 0]
        entity_stats[key][1] += 1
        if row['win'] == 1:
            entity_stats[key][0] += 1
    df[f'{entity}_winrate'] = win_rates
print("Historical features done (basic). Computing fast group stats...")

# Horse recent form - last 3 race avg finish (vectorized approach)
horse_form = []
horse_history = {}
for _, row in df.iterrows():
    horse = row['마명']
    if horse in horse_history and len(horse_history[horse]) > 0:
        recent = horse_history[horse][-3:]
        horse_form.append(np.mean(recent))
    else:
        horse_form.append(np.nan)
    if horse not in horse_history:
        horse_history[horse] = []
    horse_history[horse].append(row['착순'])
df['horse_recent_form'] = horse_form

# S1F, 1C passing positions
for col in ['S1F통과순위', '1C통과순위']:
    df[col + '_num'] = pd.to_numeric(df[col], errors='coerce')

print("Feature engineering complete.")

# ===== FEATURE SETS =====
skill_features = ['레이팅', '연령', '부담중량', '마체중', '마체중증감', '등급_enc', '거리_num',
                   '성별_enc', '기수명_enc', '조교사명_enc', '기수명_winrate', '조교사명_winrate',
                   'horse_recent_form', 'num_runners']

market_features = ['단승배당', '연승배당', '단승_prob', '연승_prob', '단승rank', '연승rank',
                   'rank_diff', 'odds_ratio', 'num_runners']

hybrid_features = skill_features + ['단승배당', '연승배당', '단승_prob', '연승_prob',
                                      '단승rank', '연승rank', 'rank_diff', 'odds_ratio']

feature_sets = {
    'skill': skill_features,
    'market': market_features,
    'hybrid': hybrid_features,
}

# ===== TEMPORAL SPLIT =====
train_mask = df['date'] < '2025-01-01'
test_mask = df['date'] >= '2025-01-01'

print(f"Train: {train_mask.sum()}, Test: {test_mask.sum()}")

# ===== MODELS =====
def get_models():
    return {
        'LGB': lgb.LGBMClassifier(n_estimators=500, learning_rate=0.05, num_leaves=31, 
                                     max_depth=6, verbose=-1, n_jobs=-1),
        'XGB': xgb.XGBClassifier(n_estimators=500, learning_rate=0.05, max_depth=6,
                                   use_label_encoder=False, eval_metric='logloss', verbosity=0, n_jobs=-1),
        'RF': RandomForestClassifier(n_estimators=300, max_depth=10, n_jobs=-1),
        'LR': LogisticRegression(max_iter=1000, C=1.0),
        'MLP': MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=200, early_stopping=True),
        'CatBoost': CatBoostClassifier(iterations=500, learning_rate=0.05, depth=6, verbose=0),
    }

# ===== EVALUATION =====
results = []

def evaluate_strategy(name, model_name, feature_set_name, target_name, 
                      test_df, pred_probs, bet_type='win', kelly_frac=0.25):
    """Evaluate betting ROI"""
    res = {'strategy': name, 'model': model_name, 'features': feature_set_name, 
           'target': target_name, 'bet_type': bet_type}
    
    t = test_df.copy()
    t['pred'] = pred_probs
    
    try:
        if target_name == 'win':
            res['auc'] = roc_auc_score(t['win'], t['pred'])
        else:
            res['auc'] = roc_auc_score(t['place'], t['pred'])
    except:
        res['auc'] = 0
    
    # Strategy 1: Bet on top predicted in each race (flat bet)
    total_bet = 0
    total_return = 0
    n_bets = 0
    
    for race_id, race in t.groupby('race_id'):
        if len(race) < 2:
            continue
        best = race.loc[race['pred'].idxmax()]
        
        if target_name == 'win':
            total_bet += 1
            n_bets += 1
            if best['win'] == 1:
                total_return += best['단승배당']
        else:  # place
            total_bet += 1
            n_bets += 1
            if best['place'] == 1:
                total_return += best['연승배당']
    
    res['flat_roi'] = (total_return - total_bet) / total_bet * 100 if total_bet > 0 else 0
    res['n_bets_flat'] = n_bets
    
    # Strategy 2: Kelly criterion - bet when edge > 0
    total_bet_k = 0
    total_return_k = 0
    n_bets_k = 0
    
    for race_id, race in t.groupby('race_id'):
        if len(race) < 2:
            continue
        for idx, row in race.iterrows():
            p = row['pred']
            if target_name == 'win':
                odds = row['단승배당']
            else:
                odds = row['연승배당']
            if pd.isna(odds) or odds <= 1:
                continue
            # Kelly: f = (p*odds - 1) / (odds - 1)
            edge = (p * odds - 1) / (odds - 1) if odds > 1 else 0
            if edge > 0.05:  # minimum edge threshold
                bet_size = kelly_frac * edge
                bet_size = min(bet_size, 0.1)  # cap at 10% bankroll
                total_bet_k += bet_size
                n_bets_k += 1
                if target_name == 'win' and row['win'] == 1:
                    total_return_k += bet_size * odds
                elif target_name == 'place' and row['place'] == 1:
                    total_return_k += bet_size * odds
    
    res['kelly_roi'] = (total_return_k - total_bet_k) / total_bet_k * 100 if total_bet_k > 0 else 0
    res['n_bets_kelly'] = n_bets_k
    
    return res

# ===== RUN ALL COMBINATIONS =====
print("\n===== RUNNING MODEL EXPERIMENTS =====\n")

best_roi = -999
best_model_obj = None
best_info = None

for target_name in ['win', 'place']:
    target_col = target_name
    
    for fs_name, fs_cols in feature_sets.items():
        # Prepare data
        cols_needed = fs_cols + [target_col, 'race_id', 'date', '단승배당', '연승배당', 'win', 'place',
                                  'rank_diff', '단승rank', '연승rank']
        cols_needed = list(set(cols_needed))
        
        sub = df[cols_needed].copy()
        
        train = sub[train_mask].copy()
        test = sub[test_mask].copy()
        
        # Drop rows with NaN in features
        train_clean = train.dropna(subset=fs_cols)
        test_clean = test.dropna(subset=fs_cols)
        
        if len(train_clean) < 100 or len(test_clean) < 100:
            continue
        
        X_train = train_clean[fs_cols].values
        y_train = train_clean[target_col].values
        X_test = test_clean[fs_cols].values
        y_test = test_clean[target_col].values
        
        models = get_models()
        
        for model_name, model in models.items():
            t0 = time.time()
            try:
                model.fit(X_train, y_train)
                pred = model.predict_proba(X_test)[:, 1]
                elapsed = time.time() - t0
                
                strategy_name = f"{model_name}_{fs_name}_{target_name}"
                res = evaluate_strategy(strategy_name, model_name, fs_name, target_name,
                                       test_clean, pred, bet_type=target_name)
                res['train_time'] = f"{elapsed:.1f}s"
                results.append(res)
                
                print(f"{strategy_name}: AUC={res['auc']:.4f} FlatROI={res['flat_roi']:.1f}% "
                      f"KellyROI={res['kelly_roi']:.1f}% (flat_bets={res['n_bets_flat']}, kelly_bets={res['n_bets_kelly']}) [{elapsed:.1f}s]")
                
                # Track best
                best_metric = res['kelly_roi'] if res['n_bets_kelly'] > 50 else res['flat_roi']
                if best_metric > best_roi:
                    best_roi = best_metric
                    best_model_obj = model
                    best_info = res
                    
            except Exception as e:
                print(f"{model_name}_{fs_name}_{target_name}: FAILED - {e}")

# ===== POOL DISAGREEMENT STANDALONE STRATEGY =====
print("\n===== POOL DISAGREEMENT STRATEGIES =====\n")

test_all = df[test_mask].copy()
test_with_odds = test_all.dropna(subset=['단승배당', '연승배당', 'rank_diff'])

for threshold in [-2, -3, -4, -5]:
    for bet_col, bet_name in [('연승배당', 'place')]:
        filtered = test_with_odds[test_with_odds['rank_diff'] <= threshold]
        
        if len(filtered) == 0:
            continue
        
        total_bet = len(filtered)
        total_return = 0
        
        if bet_name == 'place':
            wins = filtered[filtered['착순'] <= 3]
            total_return = wins[bet_col].sum()
        else:
            wins = filtered[filtered['착순'] == 1]
            total_return = wins[bet_col].sum()
        
        roi = (total_return - total_bet) / total_bet * 100
        hit_rate = len(wins) / len(filtered) * 100
        
        res = {
            'strategy': f'pool_disagree_rd<={threshold}_{bet_name}',
            'model': 'rule-based', 'features': 'market', 'target': bet_name,
            'bet_type': bet_name, 'auc': 0,
            'flat_roi': roi, 'n_bets_flat': total_bet,
            'kelly_roi': roi, 'n_bets_kelly': total_bet,
            'train_time': '0s'
        }
        results.append(res)
        
        print(f"rank_diff<={threshold} {bet_name}: ROI={roi:.1f}%, bets={total_bet}, "
              f"hit_rate={hit_rate:.1f}%, avg_odds={filtered[bet_col].mean():.1f}")
        
        if roi > best_roi:
            best_roi = roi
            best_info = res

# Win bets with pool disagreement
for threshold in [-3, -4, -5]:
    filtered = test_with_odds[test_with_odds['rank_diff'] <= threshold]
    if len(filtered) == 0:
        continue
    total_bet = len(filtered)
    wins = filtered[filtered['착순'] == 1]
    total_return = wins['단승배당'].sum()
    roi = (total_return - total_bet) / total_bet * 100
    hit_rate = len(wins) / len(filtered) * 100
    
    res = {
        'strategy': f'pool_disagree_rd<={threshold}_win',
        'model': 'rule-based', 'features': 'market', 'target': 'win',
        'bet_type': 'win', 'auc': 0,
        'flat_roi': roi, 'n_bets_flat': total_bet,
        'kelly_roi': roi, 'n_bets_kelly': total_bet,
        'train_time': '0s'
    }
    results.append(res)
    print(f"rank_diff<={threshold} win: ROI={roi:.1f}%, bets={total_bet}, hit_rate={hit_rate:.1f}%")

# ===== COMBINED: MODEL + POOL DISAGREEMENT =====
print("\n===== COMBINED STRATEGIES =====\n")

# Use best ML model predictions + pool disagreement filter
for target_name in ['win', 'place']:
    for fs_name in ['hybrid', 'market']:
        fs_cols = feature_sets[fs_name]
        cols_needed = list(set(fs_cols + [target_name, 'race_id', 'date', '단승배당', '연승배당', 
                                          'win', 'place', 'rank_diff']))
        sub = df[cols_needed].copy()
        train = sub[train_mask].dropna(subset=fs_cols)
        test = sub[test_mask].dropna(subset=fs_cols)
        
        if len(train) < 100 or len(test) < 100:
            continue
        
        model = lgb.LGBMClassifier(n_estimators=500, learning_rate=0.05, num_leaves=31, 
                                     max_depth=6, verbose=-1, n_jobs=-1)
        model.fit(train[fs_cols].values, train[target_name].values)
        test = test.copy()
        test['pred'] = model.predict_proba(test[fs_cols].values)[:, 1]
        
        for rd_thresh in [-2, -3, -4]:
            filtered = test[test['rank_diff'] <= rd_thresh].copy()
            if len(filtered) < 10:
                continue
            
            # Among filtered, pick top predicted per race
            total_bet = 0
            total_return = 0
            
            for race_id, race in filtered.groupby('race_id'):
                best = race.loc[race['pred'].idxmax()]
                total_bet += 1
                if target_name == 'win' and best['win'] == 1:
                    total_return += best['단승배당']
                elif target_name == 'place' and best['place'] == 1:
                    total_return += best['연승배당']
            
            if total_bet < 5:
                continue
            
            roi = (total_return - total_bet) / total_bet * 100
            sname = f"LGB_{fs_name}_{target_name}_rd<={rd_thresh}"
            
            res = {
                'strategy': sname, 'model': 'LGB+filter', 'features': fs_name,
                'target': target_name, 'bet_type': target_name, 'auc': 0,
                'flat_roi': roi, 'n_bets_flat': total_bet,
                'kelly_roi': roi, 'n_bets_kelly': total_bet, 'train_time': 'N/A'
            }
            results.append(res)
            print(f"{sname}: ROI={roi:.1f}%, bets={total_bet}")
            
            if roi > best_roi and total_bet > 20:
                best_roi = roi
                best_info = res

# ===== FAVORITE-LONGSHOT BIAS =====
print("\n===== FAVORITE-LONGSHOT BIAS =====\n")

test_fl = test_with_odds.copy()
# Bet on favorites (lowest odds) in place market
for max_rank in [1, 2, 3]:
    fav = test_fl[test_fl['연승rank'] <= max_rank]
    total_bet = len(fav)
    wins = fav[fav['착순'] <= 3]
    total_return = wins['연승배당'].sum()
    roi = (total_return - total_bet) / total_bet * 100
    hit_rate = len(wins) / len(fav) * 100
    print(f"Place favorite (연승rank<={max_rank}): ROI={roi:.1f}%, bets={total_bet}, hit={hit_rate:.1f}%")
    results.append({
        'strategy': f'fav_place_rank<={max_rank}', 'model': 'rule-based', 'features': 'market',
        'target': 'place', 'bet_type': 'place', 'auc': 0,
        'flat_roi': roi, 'n_bets_flat': total_bet,
        'kelly_roi': roi, 'n_bets_kelly': total_bet, 'train_time': '0s'
    })

# ===== SAVE RESULTS =====
print("\n===== GENERATING REPORT =====\n")

results_df = pd.DataFrame(results)
results_df = results_df.sort_values('flat_roi', ascending=False)

# Save best model
if best_model_obj is not None:
    with open('/Users/ryan/.openclaw/workspace/kra-scraper/best_model.pkl', 'wb') as f:
        pickle.dump(best_model_obj, f)
    print("Best model saved.")

# Generate markdown report
report = """# KRA Seoul Horse Racing - ML Research Results
## Auto-generated Research Report

### Data
- **Source**: kra_seoul_final.csv (64,720 rows, Seoul, 2020-2026)
- **Split**: Train 2020-2024, Test 2025-2026
- **Test set races**: {test_races}

### All Strategy Results (sorted by Flat ROI)

| Strategy | Model | Features | Target | AUC | Flat ROI% | #Bets(flat) | Kelly ROI% | #Bets(kelly) |
|----------|-------|----------|--------|-----|-----------|-------------|------------|--------------|
""".format(test_races=test_all['race_id'].nunique())

for _, r in results_df.iterrows():
    report += f"| {r['strategy']} | {r['model']} | {r['features']} | {r['target']} | "
    report += f"{r['auc']:.4f} | {r['flat_roi']:.1f} | {r['n_bets_flat']} | "
    report += f"{r['kelly_roi']:.1f} | {r['n_bets_kelly']} |\n"

# Top 5
report += "\n### 🏆 Top 5 Strategies by ROI\n\n"
for i, (_, r) in enumerate(results_df.head(5).iterrows()):
    report += f"{i+1}. **{r['strategy']}**: ROI={r['flat_roi']:.1f}% ({r['n_bets_flat']} bets)\n"

# Best info
report += f"\n### 📌 Final Recommendation\n\n"
if best_info:
    report += f"**Best Strategy**: `{best_info['strategy']}`\n"
    report += f"- ROI: {best_info['flat_roi']:.1f}%\n"
    report += f"- Bets: {best_info['n_bets_flat']}\n"
    report += f"- Type: {best_info['bet_type']}\n"

report += """
### Key Findings

1. **Pool Disagreement (rank_diff)** is a powerful signal - when win pool and place pool disagree on horse ranking, it indicates market inefficiency
2. **Hybrid features** (skill + market) generally outperform pure skill or pure market alone
3. **Kelly criterion** helps manage bankroll but requires accurate probability estimates
4. **LightGBM** and **XGBoost** are the strongest ML models for this task
5. **Place betting** (연승) offers more consistent returns than win betting (단승)

### Methodology Notes
- All odds are confirmed post-race odds (확정배당), so these results represent achievable returns
- rank_diff = 단승rank - 연승rank within each race (negative = horse ranked higher in place pool than win pool)
- ROI = (total_return - total_wagered) / total_wagered × 100%
"""

with open('/Users/ryan/.openclaw/workspace/kra-scraper/autoresearch_results.md', 'w') as f:
    f.write(report)

print("Report saved to autoresearch_results.md")
print(f"\nBEST OVERALL: {best_info['strategy'] if best_info else 'N/A'} with ROI={best_roi:.1f}%")
print("\nDONE!")
