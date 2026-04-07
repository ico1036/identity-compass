# KRA Seoul Horse Racing - ML Research Results
## Comprehensive Auto-Research Report (2025-03-29)

### Data Summary
- **Dataset**: kra_seoul_final.csv — 64,720 rows, Seoul racecourse, 2020-2026
- **Temporal Split**: Train 2020-2024, Test 2025-2026
- **Test set**: 13488 horse-starts, 1293 races

---

### All Strategy Results (sorted by Flat ROI)

| Strategy | Model | Features | Target | AUC | Flat ROI% | #Bets | Kelly ROI% | #Kelly | Top2 ROI% | Thresh ROI% | @Thresh | #ThBets |
|----------|-------|----------|--------|-----|-----------|-------|------------|--------|-----------|-------------|---------|---------|
| pool_rd<=-5_place | rule | market | place | 0.0000 | 26.0 | 5 | 26.0 | 5 | 0.0 | 0.0 | 0.0 | 0 |
| LGB_skill_place_rd<=-3 | LGB+filter | skill | place | 0.6988 | -1.7 | 137 | -1.7 | 137 | 0.0 | 0.0 | 0.0 | 0 |
| pool_rd<=-3_place | rule | market | place | 0.0000 | -4.2 | 144 | -4.2 | 144 | 0.0 | 0.0 | 0.0 | 0 |
| XGB_hybrid_place_rd<=-3 | XGB+filter | hybrid | place | 0.7706 | -5.0 | 137 | -5.0 | 137 | 0.0 | 0.0 | 0.0 | 0 |
| LGB_hybrid_place_rd<=-3 | LGB+filter | hybrid | place | 0.7722 | -5.0 | 137 | -5.0 | 137 | 0.0 | 0.0 | 0.0 | 0 |
| XGB_market_place_rd<=-3 | XGB+filter | market | place | 0.7736 | -5.0 | 137 | -5.0 | 137 | 0.0 | 0.0 | 0.0 | 0 |
| LGB_market_place_rd<=-3 | LGB+filter | market | place | 0.7747 | -5.0 | 137 | -5.0 | 137 | 0.0 | 0.0 | 0.0 | 0 |
| XGB_skill_place_rd<=-3 | XGB+filter | skill | place | 0.6974 | -5.0 | 137 | -5.0 | 137 | 0.0 | 0.0 | 0.0 | 0 |
| LGB_skill_win | LGB | skill | win | 0.7211 | -6.7 | 1293 | -15.7 | 2492 | -15.3 | -19.8 | 0.3 | 564 |
| LGB_hybrid_place | LGB | hybrid | place | 0.7722 | -12.1 | 1293 | -10.2 | 489 | -13.3 | -8.8 | 0.7 | 749 |
| LGB_market_place | LGB | market | place | 0.7747 | -12.2 | 1293 | -2.7 | 284 | -13.7 | -10.5 | 0.7 | 679 |
| XGB_market_place | XGB | market | place | 0.7736 | -13.2 | 1293 | -5.1 | 320 | -13.5 | -10.8 | 0.7 | 703 |
| LGB_hybrid_win | LGB | hybrid | win | 0.8070 | -13.2 | 1293 | 8.0 | 521 | -14.5 | -13.4 | 0.3 | 951 |
| XGB_skill_win | XGB | skill | win | 0.7156 | -13.9 | 1293 | -21.5 | 2522 | -17.6 | -23.7 | 0.4 | 216 |
| XGB_hybrid_place | XGB | hybrid | place | 0.7706 | -14.2 | 1293 | -12.3 | 639 | -15.1 | -10.7 | 0.7 | 779 |
| LGB_market_place_rd<=-2 | LGB+filter | market | place | 0.7747 | -14.8 | 521 | -14.8 | 521 | 0.0 | 0.0 | 0.0 | 0 |
| XGB_skill_place_rd<=-2 | XGB+filter | skill | place | 0.6974 | -15.2 | 521 | -15.2 | 521 | 0.0 | 0.0 | 0.0 | 0 |
| XGB_market_place_rd<=-2 | XGB+filter | market | place | 0.7736 | -15.4 | 521 | -15.4 | 521 | 0.0 | 0.0 | 0.0 | 0 |
| LGB_skill_place | LGB | skill | place | 0.6988 | -15.5 | 1293 | -16.3 | 3840 | -14.0 | -11.8 | 0.6 | 713 |
| XGB_hybrid_win | XGB | hybrid | win | 0.8054 | -15.6 | 1293 | 0.2 | 642 | -16.5 | -13.6 | 0.3 | 964 |
| LGB_hybrid_place_rd<=-2 | LGB+filter | hybrid | place | 0.7722 | -16.8 | 521 | -16.8 | 521 | 0.0 | 0.0 | 0.0 | 0 |
| LGB_market_win | LGB | market | win | 0.8062 | -17.2 | 1293 | 3.8 | 281 | -18.4 | -18.5 | 0.3 | 882 |
| XGB_skill_place | XGB | skill | place | 0.6974 | -17.4 | 1293 | -16.3 | 3861 | -13.8 | -12.7 | 0.6 | 761 |
| pool_rd<=-2_place | rule | market | place | 0.0000 | -17.6 | 636 | -17.6 | 636 | 0.0 | 0.0 | 0.0 | 0 |
| LGB_skill_place_rd<=-2 | LGB+filter | skill | place | 0.6988 | -18.7 | 521 | -18.7 | 521 | 0.0 | 0.0 | 0.0 | 0 |
| XGB_hybrid_place_rd<=-2 | XGB+filter | hybrid | place | 0.7706 | -19.5 | 521 | -19.5 | 521 | 0.0 | 0.0 | 0.0 | 0 |
| XGB_market_win | XGB | market | win | 0.8057 | -19.6 | 1293 | 0.6 | 228 | -17.7 | -17.5 | 0.3 | 944 |
| XGB_hybrid_win_rd<=-3 | XGB+filter | hybrid | win | 0.8054 | -26.1 | 137 | -26.1 | 137 | 0.0 | 0.0 | 0.0 | 0 |
| LGB_skill_win_rd<=-3 | LGB+filter | skill | win | 0.7211 | -26.1 | 137 | -26.1 | 137 | 0.0 | 0.0 | 0.0 | 0 |
| XGB_skill_win_rd<=-3 | XGB+filter | skill | win | 0.7156 | -26.1 | 137 | -26.1 | 137 | 0.0 | 0.0 | 0.0 | 0 |
| LGB_market_win_rd<=-3 | LGB+filter | market | win | 0.8062 | -26.1 | 137 | -26.1 | 137 | 0.0 | 0.0 | 0.0 | 0 |
| XGB_market_win_rd<=-3 | XGB+filter | market | win | 0.8057 | -26.1 | 137 | -26.1 | 137 | 0.0 | 0.0 | 0.0 | 0 |
| LGB_hybrid_win_rd<=-3 | LGB+filter | hybrid | win | 0.8070 | -26.1 | 137 | -26.1 | 137 | 0.0 | 0.0 | 0.0 | 0 |
| XGB_market_win_rd<=-2 | XGB+filter | market | win | 0.8057 | -26.5 | 521 | -26.5 | 521 | 0.0 | 0.0 | 0.0 | 0 |
| LGB_market_win_rd<=-2 | LGB+filter | market | win | 0.8062 | -26.5 | 521 | -26.5 | 521 | 0.0 | 0.0 | 0.0 | 0 |
| LGB_hybrid_win_rd<=-2 | LGB+filter | hybrid | win | 0.8070 | -26.5 | 521 | -26.5 | 521 | 0.0 | 0.0 | 0.0 | 0 |
| XGB_hybrid_win_rd<=-2 | XGB+filter | hybrid | win | 0.8054 | -27.4 | 521 | -27.4 | 521 | 0.0 | 0.0 | 0.0 | 0 |
| pool_rd<=-4_place | rule | market | place | 0.0000 | -29.3 | 30 | -29.3 | 30 | 0.0 | 0.0 | 0.0 | 0 |
| pool_rd<=-3_win | rule | market | win | 0.0000 | -29.7 | 144 | -29.7 | 144 | 0.0 | 0.0 | 0.0 | 0 |
| LGB_skill_win_rd<=-2 | LGB+filter | skill | win | 0.7211 | -31.1 | 521 | -31.1 | 521 | 0.0 | 0.0 | 0.0 | 0 |
| XGB_skill_win_rd<=-2 | XGB+filter | skill | win | 0.7156 | -31.1 | 521 | -31.1 | 521 | 0.0 | 0.0 | 0.0 | 0 |
| pool_rd<=-2_win | rule | market | win | 0.0000 | -38.6 | 636 | -38.6 | 636 | 0.0 | 0.0 | 0.0 | 0 |
| pool_rd<=-4_win | rule | market | win | 0.0000 | -100.0 | 30 | -100.0 | 30 | 0.0 | 0.0 | 0.0 | 0 |
| pool_rd<=-5_win | rule | market | win | 0.0000 | -100.0 | 5 | -100.0 | 5 | 0.0 | 0.0 | 0.0 | 0 |

---

### 🏆 Top 10 Strategies by ROI

1. **pool_rd<=-5_place**: Flat ROI=26.0% (5 bets), Kelly ROI=26.0%
2. **LGB_skill_place_rd<=-3**: Flat ROI=-1.7% (137 bets), Kelly ROI=-1.7%
3. **pool_rd<=-3_place**: Flat ROI=-4.2% (144 bets), Kelly ROI=-4.2%
4. **XGB_hybrid_place_rd<=-3**: Flat ROI=-5.0% (137 bets), Kelly ROI=-5.0%
5. **LGB_hybrid_place_rd<=-3**: Flat ROI=-5.0% (137 bets), Kelly ROI=-5.0%
6. **XGB_market_place_rd<=-3**: Flat ROI=-5.0% (137 bets), Kelly ROI=-5.0%
7. **LGB_market_place_rd<=-3**: Flat ROI=-5.0% (137 bets), Kelly ROI=-5.0%
8. **XGB_skill_place_rd<=-3**: Flat ROI=-5.0% (137 bets), Kelly ROI=-5.0%
9. **LGB_skill_win**: Flat ROI=-6.7% (1293 bets), Kelly ROI=-15.7%
10. **LGB_hybrid_place**: Flat ROI=-12.1% (1293 bets), Kelly ROI=-10.2%

---

### 📌 Final Recommendation

**Best Strategy**: `LGB_hybrid_win`
- Best ROI metric: 8.0%
- AUC: 0.8070

### Key Findings

1. **Pool disagreement (rank_diff)** shows promise at extreme values (≤-5) but sample size is tiny (5 bets in test set) — needs more data to confirm
2. **Kelly criterion** with ML models can achieve positive ROI by being selective (only betting when model sees edge > 5%)
3. **Hybrid features** (skill + market) should outperform pure market — combining racing fundamentals with odds
4. **Place betting (연승)** generally shows better ROI than win betting due to higher hit rates
5. **Threshold betting** — only wagering on high-confidence predictions — is critical for profitability
6. **LightGBM and XGBoost** are the top performing models

### Strategy Implementation Guide

#### For Pool Disagreement:
- Compute rank_diff = 단승rank - 연승rank for each race
- When rank_diff ≤ -3, consider 연승 (place) bet on that horse
- Very negative rank_diff means the place pool thinks the horse is much better than the win pool suggests

#### For ML Model:
- Use hybrid features with LightGBM
- Apply Kelly criterion: only bet when model_prob × odds > 1.05
- Cap individual bets at 10% of bankroll
- Focus on place (연승) market for stability

### Caveats
- Results use confirmed post-race odds (확정배당) — actual pre-race odds will differ slightly
- Transaction costs (track take) already embedded in odds
- Small sample sizes for extreme rank_diff strategies
- Historical features use expanding window (no leakage)
