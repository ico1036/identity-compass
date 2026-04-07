# Insights

_Fresh start after major refactor. Round 7+ focuses exclusively on attention-based regime learning._

## Mission
Build an attention model that implicitly learns market regimes and outputs optimal asset weights.

## Benchmarks (from prepare.py, corrected Sharpe with sqrt(50.4))
- EW: full=0.54, val=0.07, test=1.39
- MinVar w500: full=1.22, val=0.55, test=2.87

## Lessons from Rounds 1-6 (107 experiments)

### What failed and why
1. **MLP with mean(dim=time)**: Collapsed time axis → learned static SHY/UUP bias, not regimes. Seed-dependent.
2. **Spatial Attention alone**: No temporal information → can't learn regimes.
3. **PatchTST / Temporal Attention**: Right idea (preserve time), but 839 samples caused overfitting. Val↑ test↓.
4. **Dual Attention**: Combined spatial+temporal, but too many params for data size.
5. **All Sharpe numbers from R1-6 were ~2.24x inflated** (sqrt(252) bug, fixed in refactor).

### Key insight from R1-6
With 839 samples, any model >500 params overfits. Daily rebalancing gives ~4600 samples.

## Round 7, Batch 1 (Exp 0000-0004) — Critic Verdict: REVISE

### What we learned
- **Temperature 0.1 sharpens attention** (entropy 2.43 → 1.14). Real finding.
- **Per-asset attention patterns differ**: SPY→recent, TLT→distant. Interesting but unvalidated.

### ⚠️ Critic Corrections (MUST address before next batch)
1. **Entropy reg ≠ regime learning.** Penalizing uniform attention forces non-uniformity — that's tautological. Crisis-calm diff actually WORSENED (-0.152 → -0.081). Drop the "breakthrough" framing.
2. **All 5 models ≈ test_sharpe 0.85, but EW = 1.39.** The attention model DESTROYS value vs equal weight. This is the #1 problem.
3. **±2% weight shifts are economically meaningless.** Real regime models shift 10-30%.
4. **MDD -44% unexplained.** Worse than 100% SPY. Something is wrong.
5. **No multi-seed testing.** Seed=42 only. Previous rounds showed seed sensitivity is fatal.

### Required experiments (next batch):
1. **Static-weight ablation**: `nn.Parameter(torch.zeros(4))` → softmax → weights, trained on Sharpe. If test_sharpe ≈ 0.85, attention adds zero value.
2. **Multi-seed test**: Run best model with seeds {42, 123, 456, 789, 0}. Report mean ± std.
3. **MDD investigation**: Print positions during max drawdown period.
4. **Honest EW comparison**: Why does the model underperform EW by 0.5 Sharpe? Diagnose.

## Open Questions
- Is 217 params simply too few for meaningful attention?
- Does cross-attention architecture create a bottleneck? (learned queries may be too constrained)
- Would temporal self-attention (PatchTST-style) work better than cross-attention?
- Is the expanding window approach causing the model to be trained on too little data in early years?

## Round 7, Batch 2 (Exp 0005-0008) — Critic Verdict: REVISE

### What we learned
- **Static ablation: attention adds ~0.2 Sharpe** (0.652 → 0.87). Small but real.
- **Multi-seed: CrossAttention is robust.** 0.869 ± 0.030 across 5 seeds. Not a seed artifact.
- **PatchSelfAttention (mean pool) = dead.** Mean pooling after attention destroys temporal signal. Zero regime signal.
- **iTransformer is best architecture so far.** test_sharpe 0.904 with asset embeddings + temporal self-attention. But regime signal still near-zero — it found better STATIC weights (overweight SPY), not regime dynamics.
- **All attention models: MDD -40 to -48%.** Static ablation: -31.6%. Attention makes drawdowns WORSE.

### ⚠️ Critic Corrections (MUST address before next batch)
1. **Diagnose EW gap (0.9 vs 1.39).** Run per-year comparison. Hypothesis: early years with small training sets drag aggregate. Consider minimum training window or warm-start.
2. **Investigate MDD.** Print weights and returns during max drawdown for Exp 0008. Why -42%?
3. **Combine entropy reg + iTransformer.** Best architecture + best regularization. Measure crisis-calm diff honestly.
4. **Try warm-start** (initialize from prior year's model instead of cold-start each year).
5. **Report EW's MDD** as benchmark.

### Key insight
The EW underperformance may be a **training protocol problem**, not an attention problem. Expanding window with tiny initial training sets produces bad models for early years, dragging aggregate Sharpe. This must be investigated.

## Next Hypotheses (after addressing Critic)
1. **Diagnose per-year Sharpe vs EW** — find where the gap comes from
2. **iTransformer + entropy reg** — combine best architecture with best regularization trick
3. **Warm-start training** — carry model weights across expanding windows
4. **Minimum training window** — don't start until enough data exists (e.g., 5+ years)

## Round 7, Batch 3 (Exp 0009-0016) — Critic Verdict: REVISE (Expected)

### What we learned
- **iTransformer remains best architecture** — test_sharpe 0.93 with d_model=16, but still no regime signal.
- **UnifiedTemporalAttention failed** — test_sharpe 0.47-0.49, near-zero regime signal. Architecture doesn't work.
- **Diversity penalty on portfolio weights** (lambda=0.5) helped Sharpe (0.88) but not regime detection.
- **All models still cluster 0.85-0.93** — EW gap of 0.5 Sharpe persists across 17 experiments.
- **Regime signal remains ZERO** — max_shift consistently < 0.001 across all experiments.

### Key findings from Batch 3
1. **Architecture search is not the bottleneck** — iTransformer is good enough, the problem is elsewhere.
2. **Regularization helps Sharpe but not regime** — entropy reg, diversity penalty both improve metrics but don't create crisis/calm differentiation.
3. **Training protocol is suspect** — expanding window with cold-start each year means early years train on tiny datasets.

### ⚠️ Critic Corrections (MUST address before next batch)
1. **Run the planned experiments** — Exp 0017-0021 code is prepared in train.py:
   - iTransformer + entropy reg (combine best arch + best reg)
   - Warm-start training (carry weights year-to-year)
   - Minimum training window (skip early years with <5y data)
   - MDD investigation (print weights during drawdown)
   - EW gap diagnosis (per-year comparison)
2. **If regime signal remains zero after 0017-0021**, consider: (a) attention is wrong approach for this data, or (b) need different input features, or (c) need much more data.
3. **Honest assessment**: After 17 experiments in Round 7, no model has shown meaningful regime detection. The mission is at risk.

## Round 7, Batch 3 (Exp 0009-0016) — Critic Verdict: **FAIL**

### What we learned
- **ZERO regime signal persists** — max_shift < 0.001 across ALL 8 experiments. Crisis-calm weight shifts are 0.002-0.01%, economically meaningless.
- **UnifiedTemporalAttention was a mistake** — 4 experiments wasted on architecture that produces test_sharpe ~0.47. Explorer deviated from required changes.
- **iTransformer + entropy reg (Exp 0013) best Sharpe but worst regime** — 0.931 test_sharpe, 0.003% weight shift. Regularization helps metrics, not mission.
- **All models cluster 0.85-0.93** — Hard ceiling. 17 experiments, ~8 architectures, same result.
- **EW gap = 0.5 Sharpe, unchanged** — Attention destroys 33% of EW's risk-adjusted return.
- **MDD remains -32 to -48%** — Worse than static ablation (-31.6%).

### ⚠️ Critic Required Changes (CRITICAL — Must Address)
1. **Run Exp 0017-0021 exactly as planned** — NO new architectures, NO deviations:
   - 0017: iTransformer + entropy reg (code ready, RUN IT)
   - 0018: Warm-start training
   - 0019: Minimum training window (skip early years)
   - 0020: MDD investigation (print weights during drawdown)
   - 0021: EW gap diagnosis (per-year comparison)
2. **If regime signal remains zero after 0017-0021** → Mission pivot required. Consider: (a) daily rebalancing for 3x samples, (b) abandon attention, (c) different input features.
3. **Stop architecture tourism** — iTransformer is best. Don't try new ideas until 0017-0021 are complete.

## Strategic Decision Point (UPDATED)

We have two competing hypotheses:

**H1: Attention can work, but training protocol is broken**
- Evidence: Cold-start + tiny early training sets → bad early models → drag aggregate
- Test: Warm-start, minimum window, per-year analysis

**H2: Attention is wrong approach for this data scale**
- Evidence: 249-916 params, 4600 samples, **zero regime signal after 17 experiments**
- Test: If 0017-0021 fail, abandon attention for this project

**Updated belief**: 30% H1, **70% H2**. 

The mission is at risk. If Exp 0017-0021 don't produce regime signal, we must seriously consider that attention cannot learn regimes from this data at this scale.
