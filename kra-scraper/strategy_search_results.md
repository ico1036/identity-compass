# KRA Seoul Strategy Search Results (OOS: 2025-2026)

**Generated**: 2026-03-29 | **OOS Period**: 2025-01 to 2026-03 | **OOS Races**: 1,293 | **OOS Rows**: 13,753  
**Strategies Tested**: 163 | **Methodology**: Flat bet, all OOS, no lookahead

---

## Executive Summary

### 🔴 Honest Bottom Line: No reliable edge found in single-bet strategies (win/place)

**Zero strategies** with n≥50 achieved positive OOS ROI on 단승 or 연승 betting. The Seoul parimutuel market's ~20-27% takeout is extremely difficult to overcome with final odds data alone.

### Closest to Break-Even (Significant, n≥50)

| Rank | Strategy | Type | n_bets | Hit Rate | Avg Odds | ROI | Max DD |
|------|----------|------|--------|----------|----------|-----|--------|
| 1 | 연승 Underlay ratio<1.5 Place | place | 246 | 86.2% | 1.4 | **-2.2%** | 10.9 |
| 2 | High Rating 60+ @ Odds [5-10) Win | win | 347 | 13.5% | 7.2 | **-4.7%** | 43.7 |
| 3 | Favorite @ 1700M Win | win | 117 | 39.3% | 2.6 | **-5.6%** | 20.1 |
| 4 | Win Odds [8-12) | win | 1,609 | 9.9% | 9.8 | **-6.2%** | 163.6 |
| 5 | LowRatio<2 + TopRated Win | win | 164 | 49.4% | 2.0 | **-6.8%** | 21.0 |

### ⚠️ Exacta Simulations: Unreliable

The simulated exacta strategies showed +32% to +1720% ROI, but these use **approximate implied odds** (product of 단승배당). With a 0.5× multiplier the same strategy shows -14%. Without actual 복승/연승식 payout data, **these results cannot be trusted**.

### LGB Model: Unusable

The saved `best_model.pkl` was trained with engineered features (`Column_0..N`) without the preprocessing pipeline. Feature mapping is lost, making OOS inference impossible.

---

## Key Findings

### 1. The Market is Efficient
- **Baseline all-win ROI**: -25.7% (matches ~25% takeout)
- **Baseline all-place ROI**: -23.1%
- **Baseline favorites win ROI**: -17.9% (favorites do beat random but not the takeout)
- **Baseline favorites place ROI**: -12.6% (best simple baseline)

### 2. Where the Losses are Smallest (Potential Edge Zones)

**연승 Underlay (odds ratio < 1.5)**: ROI = -2.2%, n=246
- Horses where 단승/연승 ratio is abnormally low (연승 relatively generous)
- 86.2% place rate at 1.4x avg odds → nearly breaks even
- This is the closest thing to an edge: **the market slightly misprices 연승 for certain horses**

**Mid-range Win Odds [8-12)**: ROI = -6.2%, n=1,609
- This odds zone loses less than average, suggesting mid-longshots may be slightly underbet
- Classic "favorite-longshot bias" partially applies: extreme longshots (50+) lose ~50%

**High-rated horses at moderate odds [5-10)**: ROI = -4.7%, n=347
- Rating≥60 + odds 5-10x: form-validated overlays lose less
- Still negative, but suggests ratings carry real information the market doesn't fully price

### 3. Favorite-Longshot Bias Confirmed

| Odds Range | Win ROI | Place ROI | n |
|-----------|---------|-----------|---|
| [1-2) | -17.5% | -16.3% | 406 / 3,533 |
| [2-3) | -17.9% | -22.8% | 698 / 2,725 |
| [3-5) | -15.3% | -23.3% | 1,387 / 2,794 |
| [5-8) | -25.9% | -25.6% | 1,612 / 1,956 |
| **[8-12)** | **-6.2%** | -15.1% | 1,609 / 1,319 |
| [12-20) | -25.8% | -54.0% | 2,104 / 896 |
| [20-50) | -27.7% | -28.8% | 3,700 / 302 |
| [50-200) | -49.2% | -100% | 2,010 / 1 |

**Key insight**: The [8-12) win odds zone is anomalously efficient (only -6.2% vs -25.7% average). This is a mid-longshot zone where the public may slightly underbets.

### 4. Grade & Distance Effects

- **1700M distance** loses least among distances (win -9.6%)
- **국6등급 favorites** place at -7.0% (low-grade races slightly more predictable for favorites)
- **혼4등급** (mixed grade 4) favors favorites for win bets

### 5. Track Condition Effects

- **포화 (saturated)**: Favorite place ROI = -7.9% (better than 건조/다습)
- Wet conditions may slightly advantage known form horses

---

## Full Results: Top 30 Strategies

| # | Strategy | Type | n | Hit% | AvgOdds | ROI | Sig |
|---|----------|------|---|------|---------|-----|-----|
| 1 | 연승Underlay ratio<1.5 Place | place | 246 | 86.2% | 1.4 | -2.2% | ✓ |
| 2 | HiRating60+ Odds[5-10) Win | win | 347 | 13.5% | 7.2 | -4.7% | ✓ |
| 3 | Fav@1700M Win | win | 117 | 39.3% | 2.6 | -5.6% | ✓ |
| 4 | Win Odds [8-12) | win | 1609 | 9.9% | 9.8 | -6.2% | ✓ |
| 5 | LowRatio<2+TopRated Win | win | 164 | 49.4% | 2.0 | -6.8% | ✓ |
| 6 | Fav@국6등급 Place | place | 329 | 77.2% | 1.2 | -7.0% | ✓ |
| 7 | Fav@Track=포화 Place | place | 191 | 73.3% | 1.3 | -7.9% | ✓ |
| 8 | LowRatio<2+TopRated Place | place | 164 | 74.4% | 1.3 | -7.9% | ✓ |
| 9 | Fav+SmallField Place | place | 70 | 77.1% | 1.2 | -8.4% | ✓ |
| 10 | Fav@2등급 Win | win | 70 | 37.1% | 2.6 | -9.4% | ✓ |

---

## What Would Be Needed to Find Real Edge

1. **Pre-race odds movement** (tick data): The biggest edge in parimutuel markets is in odds movement. Late money = smart money. Final odds are already fully informed.

2. **Actual exotic payouts**: 복승/연승식/삼복승 payout data would let us test multi-leg strategies properly. The simulated exacta showed promise but the approximation is unreliable.

3. **Rebuild the LGB model with proper pipeline**: Save `(model, feature_names, preprocessing_fn)` together. The current model is a black box without its feature mapping.

4. **Pace/running style data**: S1F, 1C, 2C position data exists in the CSV. Building pace profiles and identifying pace scenario advantages could add signal.

5. **Trainer/jockey form features**: Rolling 30/60/90 day strike rates for 기수/조교사, especially at specific distances and grades.

6. **Pool size data**: Thin pools = bigger inefficiencies. Some race types may have less sharp money.

---

## Recommended Execution Playbook

Given no positive-ROI strategy exists, the honest recommendation is:

### If You Must Bet
1. **Focus on 연승 (place) bets** where 단승/연승 ratio < 1.5 → closest to breakeven (-2.2%)
2. **Avoid longshots** (odds > 20x) → they lose ~30-50% ROI
3. **The [8-12) win odds zone** loses least → if picking win bets, focus here
4. **1700M races and 국6등급** show slightly better favorite performance

### For Research
1. **Priority 1**: Get actual 복승/연승식 payout data. The 17.8% hit rate on top-2 favorites is genuinely high.
2. **Priority 2**: Rebuild LGB model with saved preprocessing pipeline
3. **Priority 3**: Add pace figure features from the sectional time columns
4. **Priority 4**: Get pre-race odds snapshots (even just opening vs final)
